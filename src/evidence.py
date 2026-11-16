"""Extract court-list facts and match sites without inventing treatment dates.

This module uses only the standard library. PDF extraction additionally requires
Poppler's pdftotext. Published CSV derivatives can be audited without Poppler.
"""
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DATE_FIELDS = ('pharmacy_last_open_date', 'pharmacy_first_closed_date',
               'front_store_close_date', 'replacement_open_date')


def address_key(value):
    tokens = re.findall(r'[A-Z0-9]+', value.upper())
    aliases = {'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W',
               'STREET': 'ST', 'AVENUE': 'AVE', 'ROAD': 'RD',
               'BOULEVARD': 'BLVD', 'FIFTH': '5TH'}
    return ''.join(aliases.get(t, t) for t in tokens)


def extract_schedule(text, source):
    """Parse only declared exhibit pages; reject incomplete or repeated rows."""
    pages = text.split('\f')
    first = pages[0]
    date = source['document_date']
    stamp_date = f'{date[5:7]}/{date[8:10]}/{date[2:4]}'
    if not (source['case_number'] in first and
            re.search(r'\bDoc\s+' + re.escape(source['docket_number']) + r'\b', first) and
            f'Filed {stamp_date}' in first):
        raise ValueError('Court document identity does not match the source manifest')
    records = []
    for page in source['pdf_pages']:
        for line in pages[page - 1].splitlines():
            if not re.match(r'^\s*\d+\s+\d+\s+', line):
                continue
            parts = re.split(r'\s{2,}', line.strip())
            if source['layout'] == '2023':
                if len(parts) != 5:
                    raise ValueError(f'Unexpected 2023 table layout on page {page}')
                ordinal, site_address, city, state, zipcode = parts
                store, address = site_address.split(' ', 1)
                location_code = ''
            else:
                if len(parts) != 7:
                    raise ValueError(f'Unexpected 2025 table layout on page {page}')
                ordinal, store, location_code, address, city, state, zipcode = parts
            if not re.fullmatch(r'[A-Z]{2}', state) or not re.fullmatch(r'\d{5}', zipcode):
                raise ValueError('Invalid state or ZIP in extracted row')
            records.append(dict(source_id=source['source_id'], source_row=int(ordinal),
                pdf_page=page, store_number=str(int(store)), location_code=location_code,
                address=address, city=city, state=state, zip=zipcode,
                document_date=date, evidence_type=source['evidence_type'],
                date_quality='notice_only', **{key: '' for key in DATE_FIELDS},
                eligible_for_closure_did=False, source_url=source['url']))
    if [r['source_row'] for r in records] != list(range(1, source['expected_rows'] + 1)):
        raise ValueError('Missing, duplicate or out-of-order exhibit rows')
    if len({(r['state'], r['store_number']) for r in records}) != len(records):
        raise ValueError('Duplicate store identifiers within the selected exhibit')
    return records


def match_roster(records, roster):
    """Require agreement on chain number, address and city; never fuzzy-match."""
    index = {}
    for row in roster:
        numbers = re.findall(r'\d+', row['name'])
        if len(numbers) == 1:
            index.setdefault(str(int(numbers[0])), []).append(row)
    matches = []
    for record in records:
        result = dict(record)
        candidates = index.get(record['store_number'], []) if record['state'] == 'PA' else []
        good = [r for r in candidates
                if address_key(r['address']) == address_key(record['address'])
                and r['city'].upper() == record['city'].upper()]
        result.update(roster_license_id='', roster_address='', roster_name='',
                      roster_match='not_matched_in_study_roster')
        if len(good) == 1:
            result.update(roster_license_id=good[0]['license_id'],
                          roster_address=good[0]['address'], roster_name=good[0]['name'],
                          roster_match='store_number_address_city')
        elif len(good) > 1:
            result['roster_match'] = 'ambiguous_multiple_licenses'
        elif candidates:
            result['roster_match'] = 'store_number_requires_address_review'
        elif record['state'] == 'NJ':
            result['roster_match'] = 'no_nj_inventory'
        matches.append(result)
    return matches


def summarize(records):
    philly = [r for r in records if r['city'] == 'PHILADELPHIA' and r['state'] == 'PA']
    return {
        'document_mentions': len(records),
        'distinct_state_store_pairs': len({(r['state'], r['store_number']) for r in records}),
        'pa_mentions': sum(r['state'] == 'PA' for r in records),
        'nj_mentions': sum(r['state'] == 'NJ' for r in records),
        'philadelphia_mentions': len(philly),
        'philadelphia_by_document': dict(Counter(r['source_id'] for r in philly)),
        'philadelphia_matched_to_roster': sum(r['roster_match'] == 'store_number_address_city' for r in philly),
        'eligible_closure_events': sum(str(r['eligible_for_closure_did']).lower() == 'true' for r in records),
        'scope': 'Two selected court lists, not a complete census of 2023–2025 closures',
        'interpretation': 'A filing date identifies documentary evidence, not the last operating day.'
    }


def build(download=False):
    sources = json.loads((ROOT / 'data/evidence_sources.json').read_text())
    rows = []
    controls = []
    for source in sources:
        path = ROOT / source['local_path']
        if download and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with urlopen(source['url'], timeout=60) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != source['sha256']:
                raise ValueError('Downloaded PDF changed; review before updating the manifest')
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('PDF checksum mismatch')
        text = subprocess.run(['pdftotext', '-layout', str(path), '-'],
                              capture_output=True, text=True, check=True).stdout
        extracted = extract_schedule(text, source)
        controls.append({'source_id': source['source_id'], 'national_schedule_rows': len(extracted),
                         'selected_pa_nj_rows': sum(r['state'] in {'PA', 'NJ'} for r in extracted)})
        rows.extend(r for r in extracted if r['state'] in {'PA', 'NJ'})
    with (ROOT / 'data/processed/closure_candidates_unverified.csv').open() as handle:
        rows = match_roster(rows, list(csv.DictReader(handle)))
    dest = ROOT / 'data/processed/court_store_evidence.csv'
    with dest.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = summarize(rows)
    summary['extraction_controls'] = controls
    summary['evidence_csv_sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
    (ROOT / 'outputs/public/evidence_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true', help='Fetch missing PDFs and verify pinned hashes')
    print(json.dumps(build(parser.parse_args().download), indent=2))
