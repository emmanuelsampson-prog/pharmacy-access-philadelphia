# Pharmacy closure evidence audit

Emmanuel Amissah Sampson · University of Pennsylvania · 16 November 2026

Two court-filed lists now provide documentary references for **101 Pennsylvania and New Jersey locations, including 16 Philadelphia sites**. These lists identify stores selected for closing sales or additional closure. They do not provide the exact date that each pharmacy stopped dispensing. No new causal estimate is claimed.

## What was obtained

| Court document | Selected PDF pages | National exhibit rows | PA and NJ rows retained | Philadelphia sites |
|---|---|---:|---:|---:|
| Case 23-18993-MBK, document 37, filed October 16, 2023 | 54–56 | 154 | 51 | 11 |
| Case 25-14861-MBK, document 743, filed June 6, 2025 | 5–8 | 207 | 50 | 5 |
| Total | | 361 | 101 | 16 |

The retained records comprise 75 Pennsylvania and 26 New Jersey locations. The 101 state-and-store-number pairs are distinct within these selected lists. This is a partial evidence collection, not a complete list of closures or a sample representative of all closures. There is no 2024 filing in this collection.

The primary documents were downloaded from public news-hosted mirrors. Their court stamps, case numbers and docket numbers were checked directly. The script checks the full exhibit sequence before selecting PA and NJ. The repeated schedule in the 2023 PDF and older lists embedded in the 2025 PDF are deliberately excluded. Search-result metadata can describe an embedded exhibit rather than the enclosing filing; the PDF itself is the authority.

## What the roster comparison shows

All 16 Philadelphia addresses match entries in the existing scenario roster using store number, normalized address and city. Eleven were already named in the October 2023 motion. This demonstrates why the roster's July 2025 portal update cannot be treated as confirmation that all records were operating pharmacies at that time. A listed closure plan also does not prove when dispensing ended, whether plans changed or whether a successor opened.

The spatial scenario remains unchanged: the population-weighted proximity increase is 32.4 meters. The audit strengthens the interpretation of that calculation as an inventory scenario. It does not supply a pretreatment network, observed trips or treatment dates.

Every record retains blank last-open, first-closed, front-store-close and replacement-open dates. `document_date` records the filing date only; `date_quality` is `notice_only` and `eligible_for_closure_did` is false. None of the 101 rows qualifies as a verified pharmacy closure event.

## New Jersey coverage

The [NJ Division of Consumer Affairs](https://www.njconsumeraffairs.gov/requestlist/Pages/default.aspx) offers free licensee lists. Its [public download folder](https://app.box.com/v/DCAStandardFiles) listed a facilities roster dated November 2, 2026 when inspected on November 16. This is a potential source for a current inventory. It cannot silently substitute for a verified 2023–2025 network.

The current facilities file was not incorporated into the analysis. The 26 NJ court-list locations also cannot serve as a destination inventory: they selectively describe closing locations. The original NJ coverage limitation and 50-tract flag therefore remain. A defensible correction requires dated records of community pharmacies on both sides of the river and routes that respect actual crossings.

## Reproduction

The executed [third notebook](../notebooks/03_closure_evidence_audit.ipynb) verifies the published CSV's checksum, recalculates counts, repeats roster matching and confirms that no filing date has become an operating-stop date. It needs no restricted data or PDF software.

To reproduce extraction from the source PDFs, install Poppler so `pdftotext` is on PATH and run from the repository root:

```bash
python -m src.evidence --download
```

The script downloads missing files into the ignored raw-data folder and verifies their pinned SHA-256 hashes. If a source changes, it stops for review. It then writes `data/processed/court_store_evidence.csv` and `outputs/public/evidence_audit.json`. The public package includes the factual CSV and provenance; it does not redistribute the full court PDFs.

## Sources

- [2023 court motion, document 37](https://cdns.abclocal.go.com/three/kabc/101823-kabc-rite-aid-doc.pdf), Exhibit A Schedule 1. The motion requests permission to continue or initiate closing sales at the listed stores.
- [2025 sixth closing-location notice, document 743](https://npr.brightspotcdn.com/f8/c8/faad678e424db35665a541d7ce0a/25-06-06-store-closure-filing.pdf), Exhibit 1. Its filing date is June 6, 2025.
- [Evidence source manifest](../data/evidence_sources.json), containing exact URLs, hashes, selected pages and document limitations.
