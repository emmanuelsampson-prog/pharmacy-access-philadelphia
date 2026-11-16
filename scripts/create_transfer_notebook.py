"""Create the dated transfer notebook with executable provenance and route analysis."""
from pathlib import Path
import nbformat as nbf
ROOT = Path(__file__).resolve().parents[1]
M = nbf.v4.new_markdown_cell; C = nbf.v4.new_code_cell
cells = [
M('''# Pharmacy closures and access in Philadelphia, 2023–2025
**Emmanuel Amissah Sampson · University of Pennsylvania**

This is the main historical-evidence and before-and-after research record. The historical ledger covers **selected 2023–2025 episodes**. The route comparison uses **24 company-reported 2025 transfers**, with final pharmacy days from June 4 to August 8. It is a focused part of the wider investigation, not a complete three-year travel panel.

The executed results measure access to former and designated receiving destinations. Actual journeys, mode shifts and causal emissions effects are not observed. The 2022–2025 mobility panel remains to be acquired.'''),
C('''from pathlib import Path
import sys, json, hashlib
ROOT = Path.cwd()
if not (ROOT / 'config.json').exists(): ROOT = ROOT.parent
assert (ROOT / 'config.json').exists()
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from IPython.display import display, Image
OUT = ROOT / 'outputs/public'
pd.set_option('display.max_columns', 12)
'''),
M('''## 1. Periods and evidence
The ACS estimates cover 2018–2022. The street graph represents mapped data through January 1, 2025, held fixed for both destinations. Company dates, court-filing dates, scheduled store closures and actual pharmacy days are different fields.

The source ledgers preserve row/page references and address disagreements. The original company archive can be retrieved with `python -m src.transfers --download`. The independent insurer directory can be checked with `python -m src.corroboration --download` (requires Poppler's `pdftotext`). Public factual derivatives are included even if the source PDFs are not redistributed.'''),
C('''history = pd.read_csv(ROOT / 'data/processed/historical_evidence_2023_2025.csv', dtype={'store_number': str})
assert len(history) == 41
assert not history.normalized_address.duplicated().any()
display(history.groupby('evidence_year').size().rename('selected_locations').to_frame())
display(history[['address','evidence_year','reported_date','date_meaning']].head(17))
display(Image(filename=str(OUT / 'closure_evidence_map.png')))
'''),
M('''## 2. Corroboration is specific to a claim
The May 5, 2025 insurer directory corroborates listed store identity, not an exact closing day. Court notices show selection for closure. Reporting that copies the company table is not an independent check of that table. No exact-address closure day is marked independently confirmed in this audit.

The Academy Road address differs between sources. It is excluded from the primary route sample, with an inclusion sensitivity. Same-site transfer at Chestnut Street is retained but does not establish uninterrupted service.'''),
C('''pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
audit = pd.read_csv(ROOT / 'data/processed/transfer_corroboration_2025.csv', dtype={'store_number': str})
assert len(pairs) == 24 and pairs.store_number.is_unique
assert audit.in_preclosure_insurer_directory.all()
assert not audit.independent_exact_address_date_confirmed.any()
assert audit.loc[audit.store_number.eq('1956'), 'primary_routing_eligible'].eq(False).all()
display(audit[['store_number','old_address','pharmacy_last_open_date','directory_address','in_selected_2025_court_notice']])
display(pd.Series(json.loads((OUT / 'transfer_corroboration_summary.json').read_text())))
'''),
M('''## 3. Network provenance
Tract centers are calculated after projecting boundaries to NAD83 / UTM zone 18N (EPSG:26918), in meters; planar catchments and maps use the same projection. Stored geographic coordinates use WGS84 (EPSG:4326). Network routes sum street-edge lengths and great-circle node-connector distances in meters, never planar distances in degrees.

The release package contains cached graph files; a Git clone must first run `python scripts/download_historical_networks.py`. The downloader retrieves the 296 MB historical Pennsylvania OSM extract and constructs walk/drive graphs. It can require several GB of working memory. The manifest records the original extract and graph hashes.

Routes minimize distance and preserve driving direction. Short straight node connectors are recorded separately. Turn restrictions, traffic delays, complete node barriers and conditional permissions are not modeled. These are mapped routes, not observed trajectories.'''),
C('''network = json.loads((ROOT / 'data/historical_network_manifest.json').read_text())
for item in network['files']:
    path = ROOT / item['file']
    assert path.exists(), 'Run scripts/download_historical_networks.py or use the cached release package'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256']
display(pd.DataFrame(network['files'])[['mode','nodes','edges','bytes']])
print('Fixed mapped network:', network['snapshot_utc'])
'''),
M('''## 4. Calculate before and after access
Assign each populated tract center to the nearest of the 24 former study pharmacies, then retain origins within 800 m for the primary sample. This is a geographic catchment rule, not an observed customer assignment. Both outcomes use the same origins and population weights. The after destination is the documented recipient, not the nearest pharmacy of any brand.

The common sample requires reachable outward and return routes, maximum endpoint-to-node distance of 200 m, and no unresolved former-address conflict. Walking minutes assume 4.8 km/h. Driving round trips are routed in both directions rather than doubling a one-way distance.'''),
C('''from src.transfer_access import build
origins, summary = build()
main = origins.loc[origins.main_included].copy()
assert len(main) == summary['tracts']
assert np.isfinite(main[['walk_before_km','walk_after_km','drive_before_roundtrip_km','drive_after_roundtrip_km']]).all().all()
assert not main.unresolved_address_conflict.any()
assert main.max_snap_m.le(200).all()
same_site = main.loc[main.same_address_transfer]
assert np.allclose(same_site.walk_delta_km, 0)
assert np.allclose(same_site.drive_delta_roundtrip_km, 0)
print('Origins are modeled residential-area proxies, not sampled travelers.')
'''),
C('''comparison = pd.DataFrame({
    'measure': ['One-way walking minutes', 'Driving round-trip km'],
    'before': [summary['weighted_walk_before_minutes'], summary['weighted_drive_before_roundtrip_km']],
    'after': [summary['weighted_walk_after_minutes'], summary['weighted_drive_after_roundtrip_km']],
    'difference': [summary['weighted_walk_delta_minutes'], summary['weighted_drive_delta_roundtrip_km']]})
display(comparison.round(2))
for file in ['transfer_timeline.png','transfer_destination_map.png','before_after_walking_map.png','walking_change_tract_map.png','before_after_comparison.png','walking_thresholds.png','transfer_by_location.png']:
    display(Image(filename=str(OUT / file)))
'''),
M('''The access maps shade the 62 eligible census tracts using the result calculated at each tract center. Before and after use identical color intervals. The change map separates longer, shorter and unchanged access; gray means no primary estimate, not zero change. Tract-wide shading does not imply that all residents have the same journey. Hatching identifies the excluded address conflict.

## 5. Neighborhood comparisons and spatial sensitivity
Poverty and household vehicle availability come from fixed 2018–2022 ACS estimates. The comparisons describe included origins and do not identify individual effects. Threshold sensitivities change the composition of the catchment sample; they are not confidence intervals.'''),
C('''display(pd.read_csv(OUT / 'before_after_equity.csv')[['group','tracts','weighted_walk_delta_minutes','weighted_drive_delta_roundtrip_km']].round(2))
display(Image(filename=str(OUT / 'before_after_equity.png')))
sensitivity = pd.read_csv(OUT / 'before_after_sensitivity.csv')
display(sensitivity[['radius_m','max_snap_m','tracts','weighted_walk_delta_minutes','weighted_drive_delta_roundtrip_km']].round(2))
print('Including the disputed Academy Road address:')
display(pd.Series(summary['including_disputed_address']))
'''),
M('''## 6. Conditional emissions
Use the paired **round-trip driving distance** difference with the EPA approximation of 400 g CO₂ per gasoline-vehicle mile. Do not add another factor of two or a detour multiplier. The hypothetical trip distribution follows the population weights; actual mode shares, trip chaining and trip counts are unknown.

The calculation holds car share fixed between before and after. It cannot measure a walking-to-driving transition or net citywide emissions.'''),
C('''from src.transfer_access import conditional_co2_kg
value = conditional_co2_kg(summary['weighted_drive_delta_roundtrip_km'], trips=1000, car_share=.5)
print(f'Conditional default: {value:.2f} kg CO₂ per 1,000 hypothetical person round trips.')
display(pd.read_csv(OUT / 'before_after_emissions.csv').round(2))
display(Image(filename=str(OUT / 'before_after_emissions.png')))
'''),
M('''## 7. Causal interpretation and unfinished outcomes
The proposed primary design is staggered difference-in-differences with direct closure exposure and separately defined spatial spillovers. Observed pretrends, panel stability, clean controls and overlapping events require evaluation. The [mobility notebook](02_mobility_event_study.ipynb) remains input-gated.

A geographic RDD would need a real discontinuity in treatment assignment at a boundary; no such rule has been identified here. A spatial IV would need a relevant, plausibly exogenous instrument satisfying exclusion; none has been established. Neither technique is presented as an estimated result.

The [academic report](../docs/study_report.md) provides the full interpretation, recommendations and limitations. [Data access](../docs/data_access.md) specifies the Penn/Dewey mobility export needed next. The proposed panel is January 2022–December 2025, with 2022 as baseline for 2023–2025 closures. Foot-traffic counts alone cannot identify walking or driving.''')]
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec':{'display_name':'Pharmacy Access','language':'python','name':'pharmacy-access'}, 'language_info':{'name':'python','version':'3.12'}})
nbf.write(nb, ROOT / 'notebooks/04_before_after_transfer_access.ipynb')
print('Created the before-and-after notebook')
