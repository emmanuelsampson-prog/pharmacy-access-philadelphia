"""Build readable notebook source. Execute with scripts/execute_notebooks.py."""
from pathlib import Path
import nbformat as nbf
from report_content import get_sections, markdown_sections, REFERENCES

ROOT=Path(__file__).resolve().parents[1]
MD=nbf.v4.new_markdown_cell;CODE=nbf.v4.new_code_cell
setup="""from pathlib import Path
import sys, json, hashlib
ROOT = Path.cwd()
if not (ROOT / 'config.json').exists():
    ROOT = ROOT.parent
assert (ROOT / 'config.json').exists(), 'Open this notebook inside the project folder'
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown
pd.set_option('display.max_columns', 12)
"""

cells=[
MD("""# Pharmacy Closures and Neighborhood Access in Philadelphia
## Spatial assessment and research record
**Emmanuel Amissah Sampson · University of Pennsylvania**  
Urban studies research project · 16 November 2026

**Research status: executed public-data feasibility pilot.** This notebook preserves the supplementary inventory-removal experiment. The main dated analysis is in notebook 04. It does not estimate the historical causal effects of the 2023–2025 Rite Aid closures. A separate ledger now contains company-reported 2025 dates; a complete operating history and licensed human-mobility panel remain unavailable.

The completed calculation removes Rite Aid-labelled entries from a licensed-pharmacy roster. It measures a hypothetical change in straight-line proximity from tract centroids. All results must retain that interpretation."""),
MD("""## 1. Questions and scope
The eventual study asks how pharmacy closures alter destinations, sampled travel patterns, nearby demand and unequal access. Philadelphia pharmacies are the semester-sized case; other retail openings and relocations remain the longer-term agenda.

This public pilot answers three narrower questions:
1. Can we assemble a reproducible spatial analysis from accessible public data?
2. How sensitive is a removal scenario to the definition of the candidate pharmacy inventory?
3. Do baseline access and neighborhood features predict the scenario better than a simple median?

Observed travel mode and emissions changes are not identified by these data."""),
CODE(setup),
MD("""## 2. Provenance and checks
The source manifest records exact URLs, retrieval times, licenses and hashes. Six official bulk ACS tables were streamed and filtered to Philadelphia tract rows. This route does not require a Census API key. Analytical source inputs are kept in `data/raw`; these are included in the project archive but excluded from Git. The optional insurer notice is a contextual reference, excluded from the archive; its source URL remains in the manifest.

If starting from a Git clone, first run `python -m src.download` at the project root. This notebook stops if required analytical inputs are missing or their recorded bytes have changed. The contextual insurer notice is optional and is not used to calculate results."""),
CODE("""manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
for item in manifest:
    path = ROOT / item['local_path']
    if item['id'] == 'closure_notice_2025' and not path.exists():
        print('Optional insurer reference PDF not included; source URL retained in manifest.')
        continue
    assert item['status'] != 'failed', item['id']
    assert path.exists(), f'Missing {path}; run python -m src.download'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Changed input: {path}'
display(pd.DataFrame(manifest)[['id','status','rows','local_path']].fillna(''))
print('Every required analytical input and available reference matches its recorded SHA-256 hash.')"""),
MD("""## 3. Join geography, demographics and the candidate inventory
ACS estimates describe 2018–2022. We preserve margins of error and turn negative sentinel values into missing values. The denominator for no-vehicle share is households; the poverty denominator is the population for whom poverty status is determined.

Distances use EPSG:26918 (meters). Origins are projected geometric tract centroids, not people's actual homes. PA destinations in a 10 km city buffer are included. Fifty populated tract centers are less than 2 km from New Jersey county geometry and are flagged because NJ pharmacies are missing. All 391 populated tracts remain in the maps and primary proximity results. Only the secondary prediction comparison excludes the 50 flagged tracts, leaving 341. The 2 km rule checks data coverage; it is not a walking threshold and does not correct every cross-border bias."""),
CODE("""from src.accessibility import prepare
tracts, pharmacies, quality = prepare()
display(pd.Series(quality, name='count').to_frame())
print('Analysis CRS:', tracts.crs)
display(tracts[['GEOID','population','poverty_rate','no_vehicle_share','age65plus_share','near_nj_2km']].head())"""),
MD("""### What the inventory can and cannot tell us
A license entry is not necessarily an operating community pharmacy. The roster may retain inactive, inpatient-only or nonpublic dispensing locations. Some source geocodes are approximate; several records share addresses or coordinates. A Rite Aid name creates an **unverified closure candidate**, not a dated treatment event.

The code generates `closure_candidates_unverified.csv` with deliberately empty operating dates for manual verification. An announcement date is not automatically a pharmacy closure date."""),
CODE("""candidates = pd.read_csv(ROOT / 'data/processed/closure_candidates_unverified.csv', dtype=str)
print(f'{len(candidates)} Rite Aid-labelled candidates in the PA study buffer; none has a verified event date in this run.')
display(candidates[['license_id','name','address','city','date_quality']].head(8))"""),
MD(r"""## 4. The modeled access scenario
For each tract origin i, compare its nearest listed destination before and after removing all Rite Aid-labelled records:

$$\Delta d_i=\min_{j\in P\setminus R}\|x_i-x_j\|-\min_{j\in P}\|x_i-x_j\|.$$

This quantity cannot be negative when the same origin and distance metric are used. It is not an observed journey, and the roster cannot reconstruct actual 2023–2025 operations.

We repeat the calculation using a restricted chain-name inventory. These are **two sensitivity scenarios, not formal lower and upper bounds**."""),
CODE("""populated = tracts.loc[tracts.population > 0].copy()
assert (populated.all_listed_delta_m >= -1e-6).all()
comparison = pd.DataFrame({
    'inventory': ['All listed licenses', 'Recognizable chain names'],
    'population_weighted_increment_m': [
        np.average(populated.all_listed_delta_m, weights=populated.population),
        np.average(populated.chain_names_delta_m, weights=populated.population)]})
display(comparison.round(2))
print('These are modeled one-way straight-line changes, not estimated closure effects.')"""),
MD("""## 5. Prediction comparison with spatial validation
The target is the scenario distance increment. Predictors use scenario-baseline inventory features and ACS context, excluding the post-removal nearest distance. Models: training-fold median, ridge regression and random forest. Five contiguous coordinate clusters are held out in turn; training origins within 1 km of the held-out region's sample points are removed. Imputation and scaling use training observations only.

This comparison tests whether the baseline features predict variation in a mechanically calculated target. The comparison is secondary to the direct spatial calculation. No claim is made that the model predicts historical closure effects. The roster's timing also prevents treating these features as verified preclosure covariates."""),
CODE("""from src.ml import run_ml, FEATURES
OUT = ROOT / 'outputs/public'
OUT.mkdir(parents=True, exist_ok=True)
metrics, predictions = run_ml(tracts, OUT)
display(metrics[['model','n','mae_m','rmse_m','r2']].round(3))
display(pd.DataFrame({'feature': FEATURES}))"""),
CODE("""from src.pilot import summarize, figures
summary, equity = summarize(tracts, quality, metrics)
figures(tracts, pharmacies, metrics, equity)
display(Image(filename=str(OUT / 'access_equity_map.png')))
display(Image(filename=str(OUT / 'model_and_equity.png')))"""),
MD("""### Interpretation of prediction errors
Lower MAE/RMSE is better; negative R² is possible out of sample. A zero-heavy target rewards the median baseline on MAE. A small improvement in RMSE alongside worse MAE does not establish useful predictive performance. Do not tune on these held-out results and then present the same folds as untouched validation.

The substantial inventory sensitivity is a data-validity warning. Before estimating historical impacts, the operating network needs manual and temporal validation."""),
CODE("""ranking = metrics.sort_values('mae_m')
print('Lowest spatially held-out MAE:', ranking.iloc[0]['model'])
rf = metrics.set_index('model').loc['Random forest']
base = metrics.set_index('model').loc['Median baseline']
print(f'Random forest MAE: {rf.mae_m:.1f} m; median baseline MAE: {base.mae_m:.1f} m.')
print('The prediction comparison does not establish a causal effect or useful prediction of real travel.')
display(pd.read_csv(OUT / 'ml_fold_metrics.csv').round(2))"""),
MD("""## 6. Equity is an area-level comparison
The table weights tract-origin scenarios by tract population. A second weighting by households without a vehicle is also reported. It cannot reveal the experience of individual residents, and group-specific sample means do not estimate causal heterogeneity. ACS uncertainty is retained in the source but not propagated in these pilot summaries."""),
CODE("""display(equity.round(2))
display(pd.Series({
    'Populated tracts': summary['tracts_populated'],
    'Tract centroids with an increase >1 m': summary['populated_tracts_with_any_increase'],
    'Population-weighted scenario increase, m': summary['population_weighted_increment_m'],
    'No-vehicle-household-weighted increase, m': summary['no_vehicle_household_weighted_increment_m'],
    'Nonborder population-weighted increase, m': summary['nonborder_population_weighted_increment_m']
}, name='scenario_summary').round(2))"""),
MD(r"""## 7. Conditional emissions scenarios
For 1,000 **hypothetical** person round trips, assume a car share, a route-detour factor and the share of journeys that create additional travel. The EPA's approximately 400 g CO₂ per gasoline-vehicle mile is a tailpipe factor; this is not lifecycle CO₂e or a measured Philadelphia fleet factor.

$$\Delta E=\Delta d\times 2\times r/1609.344\times N\times s_{car}\times s_{additional}\times 400/1000.$$

We assume one traveler per vehicle. There are no observed trips or mode shares in this pilot. A citywide annual emissions total would require unsupported assumptions and is not calculated."""),
CODE("""from src.emissions import incremental_co2_kg
emissions = pd.read_csv(OUT / 'emissions_sensitivity.csv')
display(emissions.query('detour_factor == 1.3')[[
    'hypothetical_person_round_trips','car_share','additional_trip_share','additional_tailpipe_co2_kg']].round(2))
print('Scenario only. Changing trip chaining or mode assumptions changes these results.')"""),
MD("""## 8. What is required before the causal study can run

| Input | Current status |
|---|---|
| Store-specific pharmacy dates | 24 company-reported 2025 last days plus four reported 2024 dates; independent date checks incomplete |
| Historical operating pharmacy network and replacements | Missing |
| Licensed 2022–2025 origin/POI mobility panel and coverage denominators | Not obtained |
| Historical street/transit routing; NJ alternatives | January 2025 PA streets acquired in notebook 04; transit and full NJ choice set missing |
| Validated mode information | Not obtained; foot traffic alone is insufficient |

The companion notebook checks for verified inputs before running any empirical contrast. The Python estimator excludes already-treated and flagged spillover controls, but still requires defensible parallel trends and selection assumptions. An optional R extension uses the authors' `did` implementation for a covariate-adjusted analysis; it has not been run.

Read [the full research protocol](../docs/research_protocol.md), [data access instructions](../docs/data_access.md), and [data dictionary](../docs/data_dictionary.md)."""),
MD("""## 9. Results and interpretation
The tables and figures above preserve the original supplementary calculation. The expanded historical study has a different sample and destination rule."""),
MD('This supplementary exercise estimates an all-at-once inventory sensitivity. Its 32.4-meter all-listed result and 282.1-meter chain-name result are not historical closure effects. Read [notebook 04](04_before_after_transfer_access.ipynb) for the dated transfer comparison and the full report for its interpretation.'),
MD("## References\n\n" + "\n\n".join(f"{i}. {label} [Source]({url})" for i,(label,url) in enumerate(REFERENCES,1)) + "\n\nSee [additional source notes](../docs/references.md) for mobility and software documentation."),
]

nb=nbf.v4.new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Pharmacy Access","language":"python","name":"pharmacy-access"},"language_info":{"name":"python","version":"3.12"}})
(ROOT/"notebooks").mkdir(exist_ok=True)
nbf.write(nb,ROOT/"notebooks/01_public_data_pilot.ipynb")

second=[
MD("""# Mobility and closure event study — input-gated research record
**Emmanuel Amissah Sampson · Philadelphia pharmacy closures, 2023–2025**

This companion notebook intentionally produces no empirical effect estimates until verified closures and an authorized aggregate mobility panel exist. No synthetic data are substituted. The unit-test fixtures elsewhere in the repository are only software tests.

Before using this notebook, follow the research protocol to construct exposure, coverage and clean comparisons. A statistical function cannot verify the causal assumptions."""),
CODE(setup),
MD("""## 1. Input availability
Keep licensed source data and the panel inside `data/restricted/`. The directory is ignored by Git. Store a calendar crosswalk for numeric periods and an audit trail linking each origin's exposure to verified store events. Review any outputs before sharing."""),
CODE("""paths = {
    'verified_closures': ROOT / 'data/restricted/verified_closures.csv',
    'origin_panel': ROOT / 'data/restricted/origin_panel.csv'}
display(pd.DataFrame([{'input': k, 'available': p.exists()} for k,p in paths.items()]))
ready = all(p.exists() for p in paths.values())
if not ready:
    print('NOT RUN: a complete adjudicated event file and licensed mobility outcomes are unavailable. Reported dates exist in the public evidence ledger.')"""),
MD("""## 2. Validate timing and outcome completeness
Closure bounds must distinguish last open from first closed pharmacy date, and be verified. Do not substitute front-store closure or announcement dates. The balanced panel contract rejects missing observations; an explicit, defensible coverage rule is needed before constructing that panel. Missing/suppressed counts are not zero.

`spillover` flags separately defined indirect or competing events, not the primary treatment itself. Already-treated areas are excluded from comparisons; events with overlapping exposure need a prespecified handling rule."""),
CODE("""from src.mobility import validate_closure_events
from src.causal import validate_panel, cohort_time_did, event_summary, spatial_cluster_bootstrap
if ready:
    events = validate_closure_events(pd.read_csv(paths['verified_closures'], dtype={'poi_id': str}))
    panel = pd.read_csv(paths['origin_panel'], dtype={'unit': str, 'cluster': str})
    validate_panel(panel)
    print('Structural checks passed. Event-to-origin mapping, sample coverage and identification still require review.')"""),
MD("""## 3. Cohort-time contrasts
The supplied Python method is an unadjusted mean-change estimator. With a one-period anticipation window, the reference is g−2. It omits the reference and anticipation period, checks clean controls within the comparison window, and records unsupported cells. It is not a doubly robust estimator.

The optional R script implements a more restrictive, always-unexposed-to-spillovers sample and covariate-adjusted `did::att_gt`. Its sample differs from the Python window-specific exclusions and must not be compared as if only the estimator changed."""),
CODE("""if ready:
    estimates = cohort_time_did(panel)
    if estimates.empty:
        raise ValueError('No eligible cohort-time windows; redesign the analysis')
    private = ROOT / 'outputs/private'
    private.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(private / 'cohort_time_did.csv', index=False)
    dynamic = event_summary(estimates)
    dynamic.to_csv(private / 'event_study.csv', index=False)
    print('Saved estimates privately. Inspect cohort support and pretrends before interpretation.')
else:
    print('No causal estimates calculated.')"""),
MD("""## 4. Spatial uncertainty
The bootstrap resamples entire spatial clusters. It requires at least 20 clusters, a computational guard rather than a guarantee of reliable inference. Intervals are pointwise; simultaneous bands and joint pretrend tests are not provided by this Python routine. Examine alternative cluster sizes and fixed-cohort event windows."""),
CODE("""if ready:
    intervals = spatial_cluster_bootstrap(panel, repetitions=499)
    intervals.to_csv(private / 'event_study_intervals.csv', index=False)
    print('Pointwise intervals saved privately. No licensed results are embedded in notebook output.')"""),
MD("""## 5. Reporting and publication
Interpret closure selection, parallel trends, mode uncertainty, vendor sampling, geography changes and nearby spillovers. Compare category-wide and receiving-store outcomes. Do not interpret visits as prescriptions, adherence or health outcomes.

Only permitted aggregate results belong in the public repository after a disclosure and license review. This notebook's current executed output documents **missing inputs**, not completed empirical research. See [the protocol](../docs/research_protocol.md) and [references](../docs/references.md)."""),
]
nb2=nbf.v4.new_notebook(cells=second,metadata=nb.metadata)
nbf.write(nb2,ROOT/"notebooks/02_mobility_event_study.ipynb")
print('Created both notebooks.')
