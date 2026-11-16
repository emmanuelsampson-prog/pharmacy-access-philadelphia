# Data dictionary and provenance

## Downloaded public inputs

| Dataset | Local source file | Coverage and use | Critical caveat |
|---|---|---|---|
| PA licensed pharmacy list | `data/raw/pa_pharmacies.csv` | 3,324 statewide registry rows; spatially select PA alternatives within 10 km of Philadelphia | July 1, 2025 portal update is not a historical operating date; nonretail/closed entries and approximate geocodes may remain |
| ACS 2018–2022 five-year | Six `acs2022_*_philadelphia.dat` files | 408 Philadelphia tracts per table; estimates and 90% MOEs preserved | Overlapping multiyear estimates, sampling error and geographic vintage |
| Normalized ACS join | `acs_2022_philadelphia.json` | Derived from those exact bulk extracts; same Census variable convention as the API | Derived file, not another independent source |
| Census 2022 tract boundaries | `cb_2022_42_tract_500k.zip` | Philadelphia county FIPS 42101, simplified 1:500,000 geography | Centroids do not represent within-tract population locations |
| Census 2022 county boundaries | `cb_2022_us_county_500k.zip` | Select state FIPS 34; flag origins within 2 km of New Jersey | No NJ destination inventory is included |
| June 5, 2025 closure notice | `rite_aid_closure_notice_2025.pdf` | Source reference describing closure or imminent closure | Not store-level event timing; raw third-party PDF is excluded from Git |

Each downloaded input has a provenance sidecar. `data/source_manifest.json` consolidates URLs, retrieval times, licenses, limitations and SHA-256 hashes. The Census bulk extraction selects `GEO_ID` starting with `1400000US42101`. A full national response hash and a retained subset hash are both recorded. A fresh upstream download can differ from the stored run; inspect differences before replacing the run record.

## ACS variables

| Concept | Estimate numerator | Denominator / aggregation |
|---|---|---|
| Population | `B01003_001E` | Total persons |
| Median household income | `B19013_001E` | Dollars in 2022 inflation-adjusted terms |
| Poverty rate | `B17001_002E` | `B17001_001E`: population for whom poverty status is determined |
| Households without a vehicle | `B08201_002E` | `B08201_001E`: households |
| Non-Hispanic Black share | `B03002_004E` | `B03002_001E`: persons |
| Hispanic share | `B03002_012E` | `B03002_001E`: persons; any race |
| Age 65+ | Sum `B01001_020E`–`025E` and `044E`–`049E` | `B01003_001E`: persons |

Matching `M` fields contain 90% margins of error. Negative Census sentinel values are converted to missing, not used as numerical observations. Zero denominators produce missing ratios. The pilot retains MOEs but does not propagate them through ratios, weights or model comparisons; do not treat displayed decimals as precision guarantees.

## Processed scenario fields

| Field | Unit / meaning |
|---|---|
| `GEOID` | 11-character 2022 Census tract identifier; always read as text |
| `origin_x`, `origin_y` | Geometric centroid, NAD83 / UTM zone 18N, EPSG:26918, meters |
| `origin_lon`, `origin_lat` | Same centroid transformed to WGS84 |
| `all_listed_before_m`, `all_listed_after_m` | Distance to nearest roster entry before/after hypothetical Rite Aid removal |
| `all_listed_delta_m` | Nonnegative difference between those distances |
| `chain_names_*` | Same calculations using an explicit chain-name filter; excludes independents and is not a formal bound |
| `baseline_sites_1km` | Number of roster entries within 1 km of the origin; licenses may share an address/geocode |
| `rite_aid_sites_1km` | Rite Aid-labelled roster entries within 1 km |
| `near_nj_2km` | Centroid lies within 2 km of NJ geometry; flag, not complete cross-border correction |
| `any_increase` | Scenario increment exceeds 1 meter |
| `scenario_status` | Explicit label preventing confusion with a historical estimate |

The geospatial pharmacy table retains license ID, name, address, name-match flags and geocode/address collision flags. Collision counts in `data_quality.json` describe the statewide source; study-buffer counts are recorded separately. Spatial inclusion and the provider's county label may disagree; the pilot uses spatial inclusion.

## Closure candidate ledger

`data/processed/closure_candidates_unverified.csv` contains name-matched **candidates**, not verified treatments. Empty dates are intentional. To produce a verified event table, resolve a stable mobility `poi_id`, last open and first closed pharmacy dates, front-store close date, source URL, date quality, replacement opening and reviewer. Source issue dates must be recorded separately. A PDF or court list containing an address is not proof of the exact operating-stop date.

For the mobility module, `date_quality` must equal `verified`, closure bounds must be no more than seven days apart, and each permanent closure must have a unique POI ID. Wider date intervals require a different explicitly interval-based specification. Do not put invented precise dates into the template to make the code run.

## Required restricted inputs (not obtained)

| File | Required columns / contract |
|---|---|
| `data/restricted/verified_closures.csv` | `poi_id`, `pharmacy_last_open_date`, `pharmacy_first_closed_date`, `source_url`, `date_quality` |
| Normalized aggregate origin export | `poi_id`, `period`, `home_counts` (JSON), `coverage_ok` (boolean), `source_product` |
| Origin-to-POI matrix | `origin_geoid`, `poi_id`, `distance_m`; unique pair; documented origin and routing method |
| `data/restricted/origin_panel.csv` | `unit` (text), `period` (positive integer), `first_treat` (0=never; otherwise first treated period), `outcome`, `spillover` (0/1), `cluster` (fixed spatial block) |
| Optional R covariates | `baseline_outcome`, `population_density`, `poverty_rate`, `no_vehicle_share`, fixed before exposure |

The causal panel must be balanced and complete. Suppressed/missing mobility values are not zero and cannot be mechanically imputed to satisfy this contract. The panel needs a coverage-based construction rule defined before analysis; complete-case restrictions can themselves select the sample and must be reported. `spillover` must flag indirect/competing event exposure separately from the unit's direct treatment. Spatial clusters and treatment dates must remain fixed within a unit. Period indexes must be accompanied by a saved calendar crosswalk.

The normalized origin module accepts a configurable Census identifier length (default 12 for block groups). Preserve leading zeros and verify the provider's geography vintage. Its distance output is a visitor-POI-count-weighted home-to-destination proxy; repeated people across POIs are not deduplicated. It is not individual travel distance, trip frequency, or travel mode.
