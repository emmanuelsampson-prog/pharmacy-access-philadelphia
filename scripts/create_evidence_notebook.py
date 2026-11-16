"""Create the documentary-evidence audit notebook; no mobility data required."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
MD = nbf.v4.new_markdown_cell
CODE = nbf.v4.new_code_cell
cells = [
MD("""# Pharmacy closure records and inventory timing
**Emmanuel Amissah Sampson · University of Pennsylvania · 16 November 2026**

This notebook audits two court-filed store lists and links their Pennsylvania and New Jersey entries to the existing study inventory where possible. It establishes documentary references for 101 locations, including 16 Philadelphia sites. It does not establish the last day that any pharmacy served customers.

The 2023 document is a motion identifying stores for closing sales. The 2025 document is a notice of additional closing locations. Their filing dates describe the documents. They are deliberately kept separate from pharmacy closure dates. These are two selected lists, not an exhaustive inventory of the 2023–2025 closures."""),
CODE("""from pathlib import Path
import sys, csv, json, hashlib
import pandas as pd
from IPython.display import display
ROOT = Path.cwd()
if not (ROOT / 'config.json').exists():
    ROOT = ROOT.parent
assert (ROOT / 'config.json').exists()
sys.path.insert(0, str(ROOT))
from src.evidence import DATE_FIELDS, match_roster, summarize
pd.set_option('display.max_colwidth', 90)
sources = json.loads((ROOT / 'data/evidence_sources.json').read_text())
display(pd.DataFrame(sources)[['source_id', 'document_date', 'pdf_pages', 'expected_rows']])"""),
MD("""## 1. Source and extraction checks
Court case numbers, docket numbers and filing stamps were checked in the downloaded PDFs. The PDFs are primary documents hosted by news organizations. The extraction selects pages 54–56 of document 37 and pages 5–8 of document 743. It checks complete row sequences of 154 and 207 respectively, then retains Pennsylvania and New Jersey entries.

The repeated 2023 schedule and older lists embedded in the 2025 filing are excluded. Counting every table in either PDF would duplicate or misdate evidence. The original PDF hashes and exact URLs are retained in the evidence manifest. PDFs remain outside the public archive; the factual derived CSV is included.

To reproduce PDF extraction, install Poppler (`pdftotext`) and run `python -m src.evidence --download`. The following audit runs from the published CSV without downloading the PDFs."""),
CODE("""path = ROOT / 'data/processed/court_store_evidence.csv'
saved = json.loads((ROOT / 'outputs/public/evidence_audit.json').read_text())
assert hashlib.sha256(path.read_bytes()).hexdigest() == saved['evidence_csv_sha256']
with path.open() as f:
    records = list(csv.DictReader(f))
assert len({(r['source_id'], r['source_row']) for r in records}) == len(records)
actual = summarize(records)
for key, value in actual.items():
    assert value == saved[key], key
display(pd.DataFrame(saved['extraction_controls']))
display(pd.Series({k: actual[k] for k in ['document_mentions', 'pa_mentions', 'nj_mentions',
                                         'philadelphia_mentions', 'eligible_closure_events']}, name='Count').to_frame())"""),
MD("""## 2. Link addresses to the study roster
A match requires the Rite Aid store number, normalized address and city to agree. Normalization handles common street abbreviations and the documented FIFTH/5TH spelling difference. Store number alone is insufficient because a store can relocate. Multiple matching licenses remain ambiguous.

The existing roster covers only the Pennsylvania study buffer. An unmatched entry does not establish that a pharmacy did not exist. New Jersey entries have no inventory against which to match."""),
CODE("""with (ROOT / 'data/processed/closure_candidates_unverified.csv').open() as f:
    roster = list(csv.DictReader(f))
recomputed = match_roster(records, roster)
for original, checked in zip(records, recomputed):
    assert original['roster_match'] == checked['roster_match']
    assert original['roster_license_id'] == checked['roster_license_id']
df = pd.DataFrame(recomputed)
philly = df.loc[df.city.eq('PHILADELPHIA') & df.state.eq('PA')].copy()
display(philly[['document_date', 'store_number', 'address', 'roster_license_id', 'pdf_page']])
print(f'{len(philly)} Philadelphia addresses are matched to the study roster.')
display(philly.groupby('document_date').size().rename('Philadelphia sites').to_frame())"""),
MD("""## 3. Keep unknown operating dates unknown
Eleven Philadelphia addresses appear in the October 2023 closing-sales motion and five in the June 2025 notice. All 16 remain in the roster used in the scenario. This is evidence that the roster combines locations with different documentary histories; its July 2025 portal date should not be interpreted as confirmation that every entry was operating then.

These filings do not prove when dispensing ended, whether plans changed, or whether another operator replaced a store. No notice-only row is promoted to a verified event or used in the difference-in-differences workflow."""),
CODE("""assert all(not r[field] for r in records for field in DATE_FIELDS)
assert all(r['date_quality'] == 'notice_only' for r in records)
assert all(r['eligible_for_closure_did'] == 'False' for r in records)
print('Verified pharmacy closure dates from these lists: 0')
print('Causal estimates calculated from these lists: 0')
print('The spatial scenario remains 32.4 meters; this audit does not change its inventory.')"""),
MD("""## 4. New Jersey coverage and the next data step
The [New Jersey Division of Consumer Affairs](https://www.njconsumeraffairs.gov/requestlist/Pages/default.aspx) offers free licensee lists. Its [public download folder](https://app.box.com/v/DCAStandardFiles), inspected on 16 November 2026, listed a facilities file dated 2 November 2026. That source can support a future current inventory, but it is not a contemporaneous 2023–2025 operating network. It was not merged into the historical scenario. The 26 NJ entries extracted here are selected closing-list locations, not a complete inventory of alternatives.

The original 50-tract border flag therefore remains applicable. Resolving it requires time-matched community-pharmacy records, coordinates, service verification and routed crossings. Historical pharmacy-stop dates and an authorized aggregate mobility extract remain necessary to measure visit redistribution. Walking or driving claims additionally need validated mode evidence.

### Sources
1. Rite Aid Corporation et al. Case 23-18993-MBK, document 37, filed 16 October 2023, Exhibit A Schedule 1, PDF pages 54–56. [PDF](https://cdns.abclocal.go.com/three/kabc/101823-kabc-rite-aid-doc.pdf)
2. New Rite Aid LLC et al. Case 25-14861-MBK, document 743, filed 6 June 2025, Exhibit 1, PDF pages 5–8. [PDF](https://npr.brightspotcdn.com/f8/c8/faad678e424db35665a541d7ce0a/25-06-06-store-closure-filing.pdf)

See the [evidence audit](../docs/evidence_audit.md), [source manifest](../data/evidence_sources.json) and [data dictionary](../docs/data_dictionary.md) for field definitions and limits.""")]
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.12'}})
nbf.write(nb, ROOT / 'notebooks/03_closure_evidence_audit.ipynb')
print('Created documentary-evidence notebook')
