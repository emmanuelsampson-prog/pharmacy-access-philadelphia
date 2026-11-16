"""Company-reported 2025 pharmacy closures and designated transfer destinations.

The table records pharmacy operations, not front-store closure or observed trips.
Geocodes locate documented addresses; a license row does not establish operation.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re
import requests
import pandas as pd
import geopandas as gpd
from .evidence import address_key

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = 'https://web.archive.org/web/20251004155916id_/https://content.riteaid.com/new-pharmacy-location.html'
CITATION_URL = 'https://web.archive.org/web/20251004155916/https://content.riteaid.com/new-pharmacy-location.html'
HEADER = ['Store Number', 'Old Pharmacy Name', 'Old Address', 'Old City', 'Old State',
          'Old Zip', 'Last Day of Pharmacy Business', 'New Pharmacy Name', 'New Address',
          'New City', 'New State', 'New Zip', 'New Phone']
COLUMNS = ['store_number', 'old_name', 'old_address', 'old_city', 'old_state', 'old_zip',
           'last_day_reported', 'receiving_name', 'receiving_address', 'receiving_city',
           'receiving_state', 'receiving_zip', 'receiving_phone']

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == 'tr': self.row = []
        if tag in ('td', 'th'): self.cell = []
    def handle_data(self, text):
        if self.cell is not None: self.cell.append(text)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            if self.row is not None: self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row:
            self.rows.append(self.row); self.row = None

def parse_transfer_table(html):
    parser = TableParser(); parser.feed(html)
    if not parser.rows or parser.rows[0] != HEADER:
        raise ValueError('Historical transfer-table schema changed or table is absent')
    if any(len(row) != len(HEADER) for row in parser.rows):
        raise ValueError('Malformed transfer-table row')
    df = pd.DataFrame(parser.rows[1:], columns=COLUMNS)
    if df.store_number.duplicated().any():
        raise ValueError('Duplicate store numbers need manual reconciliation')
    dates = pd.to_datetime(df.last_day_reported, format='%m/%d/%Y', errors='raise')
    if not dates.dt.year.eq(2025).all(): raise ValueError('Unexpected closure year')
    df['pharmacy_last_open_date'] = dates.dt.strftime('%Y-%m-%d')
    # Date + 1 defines the first modeled closed day. This is not a second observation.
    df['modeled_first_closed_date'] = (dates + pd.Timedelta(days=1)).dt.strftime('%Y-%m-%d')
    df['date_evidence'] = 'company-reported last day of pharmacy business'
    df['source_url'] = CITATION_URL
    df['source_table_row'] = range(1, len(df)+1)
    return df.drop(columns=['receiving_phone'])

def store_number(name):
    if not re.search(r'RITE\s*AID', name, re.I): return None
    numbers = re.findall(r'\d+', name)
    return str(int(numbers[0])) if len(numbers) == 1 else None

# Explicit address reconciliations reviewed against the public PA license roster.
# These resolve formatting/range differences, never store-number-only matches.
REVIEWED_ADDRESSES = {
    ('old', '11126'): ('9910 Frankford Avenue', 'Source appends the state and a truncated suite label'),
    ('old', '11125'): ('7418-32 Oxford Avenue', 'Source uses first number of the roster street-number range'),
    ('old', '11130'): ('7700 Crittenden Street Suite 101C', 'Source appends the state and truncates suite 101C'),
    ('receiving', '3434'): ('2320 Fairmount Avenue #26', 'Same numbered range written as 2320-26 in the transfer table')
}

def geocode_pairs(city, roster, census):
    roster = roster.to_crs(4326).copy()
    roster['store_number_match'] = roster.name.map(store_number)
    rows = []
    reviews = []
    for rec in city.to_dict('records'):
        for side in ['old', 'receiving']:
            raw_address = rec[side+'_address']; city_name = rec[side+'_city']
            address, review_note = REVIEWED_ADDRESSES.get((side, rec['store_number']), (raw_address, ''))
            matches = roster[(roster.address.map(address_key) == address_key(address)) &
                             (roster.city.str.upper() == city_name.upper())]
            if side == 'old':
                matches = matches[matches.store_number_match == rec['store_number']]
            if side == 'receiving' and rec['receiving_name'] == 'UNITY PHARMACY':
                # Same street address: reuse the site's coordinate, not Rite Aid's identity.
                note = 'Same-address transfer; coordinate reused, successor opening timing is unknown'
            else: note = review_note
            if address_key(raw_address) == address_key('12301 Knights Road') and side == 'receiving':
                geocodes = census['result']['addressMatches']
                if len(geocodes) != 1 or not geocodes[0]['matchedAddress'].startswith('12301 KNIGHTS RD, PHILADELPHIA'):
                    raise ValueError('Knights Road geocode requires review')
                coord = geocodes[0]['coordinates']; lon, lat = coord['x'], coord['y']
                method = 'Census address-range geocode, Public_AR_Current, retrieved 2026-11-16'
                license_id = ''; matched_address = geocodes[0]['matchedAddress']
            else:
                if len(matches) != 1:
                    raise ValueError(f'Ambiguous or missing coordinate match: {rec["store_number"]} {side} {address}')
                m = matches.iloc[0]; lon, lat = m.geometry.x, m.geometry.y
                method = 'PA public license roster address coordinate'
                license_id = m.license_id; matched_address = m.address
            rec[side+'_longitude'] = lon; rec[side+'_latitude'] = lat
            rec[side+'_coordinate_method'] = method
            rec[side+'_coordinate_license_id'] = license_id
            rec[side+'_matched_address'] = matched_address
            if note: reviews.append({'store_number': rec['store_number'], 'side': side,
                                     'source_address': raw_address, 'matched_address': matched_address, 'note': note})
        rec['same_address_transfer'] = (address_key(rec['old_address']) == address_key(rec['receiving_address'])
                                        and rec['old_city'] == rec['receiving_city'])
        rows.append(rec)
    return pd.DataFrame(rows), pd.DataFrame(reviews)

def build(download=False):
    raw = ROOT / 'data/raw/riteaid_transfer_20251004.html'
    if not raw.exists():
        if not download: raise FileNotFoundError('Run python -m src.transfers --download')
        response = requests.get(ARCHIVE, timeout=60); response.raise_for_status()
        body = response.content
        if body[:2] == b'\x1f\x8b': body = gzip.decompress(body)
        raw.write_bytes(body)
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    manifest_path = ROOT / 'data/transfer_source_manifest.json'
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous['decoded_html_sha256'] != digest: raise ValueError('Archived transfer source checksum differs')
    table = parse_transfer_table(raw.read_text())
    if len(table) != 1025: raise ValueError('Unexpected archive row count')
    regional = table[table.old_state.isin(['PA', 'NJ'])]
    regional.to_csv(ROOT/'data/processed/pharmacy_transfers_pa_nj_2025.csv', index=False)
    city = table[(table.old_city == 'PHILADELPHIA') & (table.old_state == 'PA')]
    if len(city) != 24: raise ValueError('Unexpected Philadelphia cohort count')
    census_path = ROOT/'data/raw/cvs_knights_census_geocode.json'
    if not census_path.exists():
        if not download: raise FileNotFoundError('Missing cached Census geocode; run --download')
        response = requests.get('https://geocoding.geo.census.gov/geocoder/locations/onelineaddress',
                                params={'address':'12301 Knights Road Philadelphia PA 19154',
                                        'benchmark':'Public_AR_Current','format':'json'}, timeout=60)
        response.raise_for_status(); census_path.write_text(json.dumps(response.json(), indent=2))
    pairs, reviews = geocode_pairs(city, gpd.read_file(ROOT/'data/processed/pharmacy_candidates.geojson'),
                                  json.loads(census_path.read_text()))
    pairs.to_csv(ROOT/'data/processed/philadelphia_transfer_pairs_2025.csv', index=False)
    reviews.to_csv(ROOT/'data/processed/transfer_geocode_review.csv', index=False)
    manifest_path.write_text(json.dumps({
        'title': 'Rite Aid Pharmacy Closure and Transfer List', 'original_url': 'https://content.riteaid.com/new-pharmacy-location.html',
        'archive_url': CITATION_URL, 'download_url': ARCHIVE, 'archive_capture_utc': '2025-10-04T15:59:16Z',
        'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'decoded_html_sha256': digest,
        'raw_file': str(raw.relative_to(ROOT)), 'national_rows': len(table), 'pa_nj_rows': len(regional),
        'philadelphia_rows': len(city), 'philadelphia_first_last_day': pairs.pharmacy_last_open_date.min(),
        'philadelphia_final_last_day': pairs.pharmacy_last_open_date.max(),
        'scope': 'Locations present in this archived table; not a complete census of Philadelphia closures',
        'date_interpretation': 'Company-reported last day of pharmacy business; +1 day is a modeling boundary only',
        'receiving_interpretation': 'Designated prescription-file recipient; actual patient use and start-of-operation date are not observed',
        'geocode_census_file': str(census_path.relative_to(ROOT)),
        'geocode_census_sha256': hashlib.sha256(census_path.read_bytes()).hexdigest(),
        'related_study': 'https://doi.org/10.1001/jamahealthforum.2026.2070'
    }, indent=2)+'\n')
    print(f'Extracted {len(regional)} PA/NJ records and {len(pairs)} Philadelphia dated transfer pairs')
    return pairs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--download', action='store_true')
    build(parser.parse_args().download)
