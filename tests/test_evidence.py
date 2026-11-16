"""Checks against turning documentary notices into unsupported closure dates."""
import csv
import json
from src.evidence import ROOT, DATE_FIELDS, extract_schedule, match_roster, summarize
import pytest


def test_published_notice_ledger_retains_unknown_dates():
    with (ROOT / 'data/processed/court_store_evidence.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert all(not r[field] for r in rows for field in DATE_FIELDS)
    assert all(r['eligible_for_closure_did'] == 'False' for r in rows)
    summary = summarize(rows)
    expected = json.loads((ROOT / 'outputs/public/evidence_audit.json').read_text())
    for key, value in summary.items():
        assert value == expected[key]
    assert len({(r['source_id'], r['source_row']) for r in rows}) == len(rows)


def test_store_number_alone_cannot_match_relocation():
    notice = dict(store_number='225', address='5612 N. FIFTH STREET', city='PHILADELPHIA', state='PA')
    roster = [dict(name='Rite Aid 225', address='99 N Fifth Street', city='Philadelphia', license_id='A')]
    result = match_roster([notice], roster)[0]
    assert result['roster_license_id'] == ''
    assert result['roster_match'] == 'store_number_requires_address_review'
    roster[0]['address'] = '5612 N 5th Street'
    assert match_roster([notice], roster)[0]['roster_license_id'] == 'A'
    roster.append(dict(roster[0], license_id='B'))
    assert match_roster([notice], roster)[0]['roster_match'] == 'ambiguous_multiple_licenses'


def test_parser_rejects_wrong_document_and_duplicate_schedule():
    source = dict(source_id='test', case_number='23-18993-MBK', docket_number='37',
                  document_date='2023-10-16', pdf_pages=[2], expected_rows=1,
                  layout='2023', evidence_type='notice', url='https://example.org')
    header = 'Case 23-18993-MBK Doc 37 Filed 10/16/23'
    line = '1  225 5612 N. FIFTH STREET  PHILADELPHIA  PA  19120\n'
    record = extract_schedule(header + '\f' + line, source)[0]
    assert record['document_date'] == '2023-10-16'
    assert record['pharmacy_first_closed_date'] == ''
    with pytest.raises(ValueError, match='identity'):
        extract_schedule(header.replace('37', '38') + '\f' + line, source)
    with pytest.raises(ValueError, match='duplicate'):
        extract_schedule(header + '\f' + line + line, source)
