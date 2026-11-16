"""Cross-check the 2025 transfer list without confusing repetition with confirmation.

The insurer directory corroborates a listed provider identity, not an exact final
operating day. Court notices corroborate selection for closure, not execution.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY_URL = 'https://q1.keystonefirstvipchoice.com/content/dam/keystone-first/vip-choice/pdf/2025-pharmacy-directory.pdf.coredownload.inline.pdf'
JULY_REPORT = 'https://www.inquirer.com/business/rite-aid-philadelphia-stores-closing-20250709.html'
AUGUST_REPORT = 'https://www.inquirer.com/business/health/rite-aid-pharmacies-closed-pennsylvania-new-jersey-20250823.html'
FAST_COMPANY = 'https://www.fastcompany.com/91375399/rite-aid-store-closures-list-dates-prescription-transfers-timeline'


def directory_records(text):
    rows = []
    pattern = r'RITE AID PHARMACY\s+0*(\d+)[^\n]*\nNPI:\s*(\d+)\n((?:[^\n]+\n){1,3}?)PHILADELPHIA, PA\s+(\d{5})'
    for page_no, page in enumerate(text.split('\f'), 1):
        if page_no >= 122:  # Stop before mail order, infusion, LTC and index pages.
            break
        for match in re.finditer(pattern, page):
            rows.append({'store_number': str(int(match[1])), 'npi': match[2],
                         'directory_address': match[3].strip().replace('\n', ' '),
                         'directory_zip': match[4], 'pdf_page': page_no,
                         'printed_page': page_no - 2, 'directory_as_of': '2025-05-05',
                         'source_url': DIRECTORY_URL})
    result = pd.DataFrame(rows)
    if result.empty or result.store_number.duplicated().any():
        raise ValueError('Directory parsing failed or produced duplicate store IDs')
    return result


def build(download=False):
    path = ROOT / 'data/raw/keystone_2025_directory.pdf'
    if not path.exists() and download:
        response = requests.get(DIRECTORY_URL, timeout=90)
        response.raise_for_status(); path.write_bytes(response.content)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path = ROOT / 'data/corroboration_source_manifest.json'
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous['directory_sha256'] != digest:
            raise ValueError('Directory bytes changed; inspect the new vintage before use')
    text = subprocess.run(['pdftotext', '-raw', str(path), '-'], check=True, capture_output=True, text=True).stdout
    assert 'updated on May 05, 2025' in text[:1500], 'Unexpected directory vintage'
    directory = directory_records(text)
    directory.to_csv(ROOT / 'data/processed/insurer_directory_philadelphia_20250505.csv', index=False)
    pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    court = pd.read_csv(ROOT / 'data/processed/court_store_evidence.csv', dtype={'store_number': str})
    audit = pairs[['store_number', 'old_address', 'pharmacy_last_open_date', 'receiving_name', 'receiving_address']].merge(
        directory, on='store_number', how='left', validate='one_to_one')
    audit['in_preclosure_insurer_directory'] = audit.npi.notna()
    audit['in_selected_2025_court_notice'] = audit.store_number.isin(court.loc[court.source_id.eq('riteaid_2025_doc743'), 'store_number'])
    audit['date_evidence_status'] = 'company-reported; exact day not independently confirmed'
    audit['independent_exact_address_date_confirmed'] = False
    audit['additional_source_url'] = ''
    audit['additional_source_interpretation'] = ''
    audit.loc[audit.store_number.eq('479'), ['additional_source_url', 'additional_source_interpretation']] = [
        JULY_REPORT, 'Independent staff interview reports July 24 for Eastwick pharmacy. Branch-address link is inferred, so not counted as exact-address confirmation.']
    audit.loc[audit.store_number.eq('1764'), ['additional_source_url', 'additional_source_interpretation']] = [
        FAST_COMPANY, 'August 8 and Chestnut address repeated from Rite Aid table; same underlying source, not independent date verification.']
    audit['address_review'] = 'Store number and Philadelphia listing matched; address formatting retained for inspection'
    audit.loc[audit.store_number.eq('1956'), 'address_review'] = 'CONFLICT: directory says 12353 Academy Road; company table, court and license roster say 12311. Primary route sample excludes this store; inclusion is a sensitivity.'
    audit['primary_routing_eligible'] = ~audit.store_number.eq('1956')
    audit.to_csv(ROOT / 'data/processed/transfer_corroboration_2025.csv', index=False)
    result = {'directory_as_of': '2025-05-05', 'directory_philadelphia_rite_aids': len(directory),
              'transfer_sites': len(pairs), 'transfer_sites_with_directory_identity_match': int(audit.in_preclosure_insurer_directory.sum()),
              'transfer_sites_in_selected_court_notice': int(audit.in_selected_2025_court_notice.sum()),
              'exact_dates_independently_confirmed': 0, 'neighborhood_level_date_consistency': 1,
              'address_conflicts': 1,
              'interpretation': 'Corroborated listed site identities and selected closure intentions; date-level independent verification remains incomplete.'}
    (ROOT / 'outputs/public/transfer_corroboration_summary.json').write_text(json.dumps(result, indent=2) + '\n')
    manifest = {'directory_title': 'Keystone First VIP Choice 2025 Pharmacy Directory',
                'directory_url': DIRECTORY_URL, 'directory_as_of': '2025-05-05',
                'directory_sha256': digest, 'directory_file': str(path.relative_to(ROOT)),
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'extracted_scope': 'Philadelphia Rite Aid entries from the retail directory only; page 107–110 in the PDF',
                'directory_limit': 'Insurer-network listing; may lag operating changes; not proof of daily operation or a complete city inventory',
                'independent_context_reports': [JULY_REPORT, AUGUST_REPORT],
                'repeated_company_evidence': [FAST_COMPANY],
                'source_dependency_note': 'A news article reproducing the company table is not an independent check of its dates.'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return audit, result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--download', action='store_true')
    build(parser.parse_args().download)
