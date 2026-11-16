"""Assemble a 2023–2025 source ledger, preserving date meaning and uncertainty.

The manually transcribed facts below are small, cited records from contemporaneous
reporting. A store-closing announcement is never promoted to a pharmacy-stop date.
"""
from pathlib import Path
import pandas as pd
import json
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / 'data/processed'
from sys import path
path.insert(0, str(ROOT))
from src.evidence import address_key
from src.transfers import store_number
from src.cartography import map_furniture, tract_background

NEWS = [
    dict(address='3000-02 Reed Street', evidence_year=2023, reported_date='', date_meaning='closed during autumn 2023; exact pharmacy date unspecified',
         source_date='2024-02-04', source_url='https://www.inquirer.com/business/rite-aid-bankruptcy-south-philadelphia-20240204.html',
         source_type='retrospective local interviews', receiving_destination='Rite Aid at South Broad Street and Snyder Avenue; later closes in 2025'),
    dict(address='2545 Aramingo Avenue', evidence_year=2023, reported_date='2023-12-14', date_meaning='scheduled store closure; pharmacy date not separately identified',
         source_date='2023-12-01', source_url='https://www.inquirer.com/business/rite-aid-store-closed-phamacy-bankruptcy-20231201.html',
         source_type='company statement reported by local newspaper', receiving_destination=''),
    dict(address='1628-36 Chestnut Street', evidence_year=2024, reported_date='2024-01-11', date_meaning='scheduled pharmacy closure; Thursday resolved from Monday January 8 publication',
         source_date='2024-01-08', source_url='https://www.inquirer.com/business/rite-aid-pharmacy-closed-center-city-20240108.html',
         source_type='company spokesperson reported by local newspaper', receiving_destination=''),
    dict(address='2131-59 North Broad Street', evidence_year=2024, reported_date='2024-04-23', date_meaning='scheduled pharmacy closure; front-store date unspecified',
         source_date='2024-04-08', source_url='https://www.inquirer.com/business/rite-aid-closures-philadelphia-chester-county-south-jersey-20240408.html',
         source_type='company dates reported by local newspaper', receiving_destination=''),
    dict(address='6201 Germantown Avenue', evidence_year=2024, reported_date='2024-04-16', date_meaning='pharmacy closing date reported contemporaneously; retail closure May 19',
         source_date='2024-04-16', source_url='https://resolvephilly.org/gih/rite-aid-to-close-its-germantown-avenue-location-leaving-some-residents-without-a-nearby-pharmacy/',
         source_type='local reporting; date also in April 8 Inquirer report', receiving_destination='Acme, 7010 Germantown Avenue'),
    dict(address='6731 Woodland Avenue', evidence_year=2024, reported_date='2024-04-25', date_meaning='scheduled pharmacy closure; front-store date unspecified',
         source_date='2024-04-08', source_url='https://www.inquirer.com/business/rite-aid-closures-philadelphia-chester-county-south-jersey-20240408.html',
         source_type='company dates reported by local newspaper', receiving_destination='')
]


def build():
    court = pd.read_csv(PROCESSED / 'court_store_evidence.csv', dtype=str).fillna('')
    court = court.loc[court.city.str.upper().eq('PHILADELPHIA') & court.source_id.eq('riteaid_2023_doc37')]
    rows = []
    for record in court.itertuples():
        rows.append(dict(store_number=record.store_number, address=record.address, evidence_year=2023, reported_date='',
                         date_meaning='court motion listing; operating date not established', source_date=record.document_date,
                         source_url=record.source_url, source_type='court-filed list', receiving_destination='',
                         evidence_locator=f'PDF page {record.pdf_page}; schedule row {record.source_row}'))
    for row in NEWS:
        rows.append({'store_number': '', 'evidence_locator': 'Article body', **row})
    transfers = pd.read_csv(PROCESSED / 'philadelphia_transfer_pairs_2025.csv', dtype=str).fillna('')
    for record in transfers.itertuples():
        rows.append(dict(store_number=record.store_number, address=record.old_address, evidence_year=2025,
                         reported_date=record.pharmacy_last_open_date, date_meaning='company-reported last day of pharmacy business',
                         source_date='2025-10-04', source_url=record.source_url, source_type='archived company transfer table',
                         receiving_destination=f'{record.receiving_name}, {record.receiving_address}',
                         evidence_locator=f'Table row {record.source_table_row}; store {record.store_number}'))
    ledger = pd.DataFrame(rows)
    ledger['city'] = 'Philadelphia'
    ledger['study_period'] = '2023–2025'
    ledger['normalized_address'] = ledger.address.map(address_key)
    if ledger.normalized_address.duplicated().any():
        raise ValueError('Overlapping records require adjudication, not double counting')
    ledger['eligible_for_empirical_did'] = False
    ledger['did_limit'] = 'Mobility outcome panel and complete operating/replacement history not obtained'
    roster = gpd.read_file(PROCESSED / 'pharmacy_candidates.geojson')
    roster = roster.loc[roster.is_rite_aid].copy()
    roster['store_number'] = roster.name.map(store_number)
    roster['address_key'] = roster.address.map(address_key)
    for i, row in ledger.iterrows():
        matches = roster.loc[roster.store_number.eq(row.store_number)] if row.store_number else roster.loc[roster.address_key.eq(row.normalized_address)]
        if len(matches) != 1:
            raise ValueError(f'Ambiguous ledger geocode: {row.address}')
        ledger.loc[i, ['longitude', 'latitude', 'coordinate_license_id']] = [matches.geometry.iloc[0].x, matches.geometry.iloc[0].y, matches.license_id.iloc[0]]
    ledger.to_csv(PROCESSED / 'historical_evidence_2023_2025.csv', index=False)
    summary = {'study_period': '2023–2025', 'selected_city_locations': len(ledger),
               'records_by_evidence_year': {str(k): int(v) for k, v in ledger.groupby('evidence_year').size().items()},
               'records_with_reported_pharmacy_day': 28,
               'company_table_last_operating_days_2025': 24,
               'scheduled_or_contemporaneously_reported_pharmacy_dates_2024': 4,
               'store_only_scheduled_date_2023': 1,
               'scope': 'Selected documented locations, not a comprehensive city census or annual closure count',
               'mobility_panel_period_planned': 'January 2022–December 2025; not yet obtained'}
    (ROOT / 'outputs/public/historical_evidence_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    points = gpd.GeoDataFrame(ledger, geometry=gpd.points_from_xy(ledger.longitude, ledger.latitude), crs=4326).to_crs(26918)
    tracts = gpd.read_file(PROCESSED / 'tract_scenarios.geojson').to_crs(26918)
    boundary = tracts.dissolve()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'savefig.facecolor': 'white'})
    fig, axes = plt.subplots(1, 3, figsize=(11.6, 5.6))
    for ax, year in zip(axes, [2023, 2024, 2025]):
        tract_background(ax, tracts)
        boundary.boundary.plot(ax=ax, color='#75878b', linewidth=.7)
        subset = points.loc[points.evidence_year.eq(year)]
        subset.plot(ax=ax, color='#137c86', markersize=42, edgecolor='white', linewidth=.7, zorder=3)
        map_furniture(ax, boundary.total_bounds)
        ax.set_title(f'{year}\n{len(subset)} selected locations', loc='left', fontweight='bold'); ax.set_axis_off()
    fig.text(.5, .055, 'Each point is a documented pharmacy location; tract lines provide geographic context.', ha='center', fontsize=10, color='#4e6268')
    fig.text(.5, .015, 'Selected evidence, not complete annual closure counts. Sources: court records, company table, local reporting and Census.', ha='center', fontsize=8.5, color='#4e6268')
    fig.subplots_adjust(left=.015, right=.99, bottom=.13, top=.85, wspace=.06)
    fig.savefig(ROOT / 'outputs/public/closure_evidence_map.png', dpi=200); plt.close(fig)


if __name__ == '__main__':
    build()
