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

## Court evidence ledger

`data/processed/court_store_evidence.csv` contains 101 PA/NJ entries from two selected court exhibits. It is separate from the unverified roster candidates and does not overwrite them.

| Field | Meaning |
|---|---|
| `source_id`, `source_row`, `pdf_page` | Locate the exact exhibit entry; page numbers are one-based PDF pages |
| `store_number`, `location_code` | Operator identifiers as text; location code is absent from the 2023 list |
| `address`, `city`, `state`, `zip` | Address reported in the court exhibit; ZIP remains text |
| `document_date` | Court filing date, never automatically a treatment date |
| `evidence_type` | Initial closing-sales motion or additional closing-location notice |
| `date_quality` | `notice_only`; none of these records meets the verified-event contract |
| Four operating-date fields | Intentionally blank: last open, first closed, front-store close and replacement open |
| `eligible_for_closure_did` | False for every current row |
| `roster_match` | Store number/address/city agreement, address review needed, ambiguous, unmatched, or no NJ inventory |
| `roster_license_id`, `roster_address`, `roster_name` | Matched study-roster record; blank when a unique defensible match is unavailable |
| `source_url` | Downloadable primary court document hosted by a news organization |

`data/evidence_sources.json` records document identity, SHA-256, selected pages and expected exhibit counts. `outputs/public/evidence_audit.json` records extraction controls, derived counts and the CSV checksum. The evidence notebook rechecks both the counts and matching. The list is partial and cannot estimate the total number of closures.

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

## Dated transfers and corroboration

| File or field | Meaning | Limits |
|---|---|---|
| `historical_evidence_2023_2025.csv` | 41 selected city locations with source and date meaning | Not a complete closure census |
| `pharmacy_transfers_pa_nj_2025.csv` | 326 PA/NJ rows in the archived company table | Not all closures in either state |
| `philadelphia_transfer_pairs_2025.csv` | 24 former sites and designated recipients | Actual patient destination is unknown |
| `pharmacy_last_open_date` in the company table | Company-reported last pharmacy-business day | Not independently verified for every store |
| `modeled_first_closed_date` | Reported last day plus one calendar day | Modeling convention, not a separate observation |
| `same_address_transfer` | Former and recipient addresses identify the same site | Does not establish uninterrupted service |
| `transfer_corroboration_2025.csv` | Insurer ID match, selected court match and source dependence | Identity corroboration is not date confirmation |
| `insurer_directory_philadelphia_20250505.csv` | 34 city Rite Aid entries in the retail directory | Insurer network listing, not a complete operating census |
| `transfer_geocode_review.csv` | Explicit reviewed address normalization | Approximate address points, not entrances |

## Before and after route outputs

`before_after_access_origins.csv` contains candidate tract origins within 1,000 meters for sensitivity analysis. The main flag retains origins within 800 meters, with all routes reachable, no endpoint-to-node distance over 200 meters, and no unresolved Academy Road address conflict.

| Field pattern | Unit and meaning |
|---|---|
| `distance_to_former_m` | Straight-line origin distance to nearest of the 24 former study sites |
| `walk_before_km`, `walk_after_km` | Shortest mapped one-way walking route plus straight connectors, km |
| `walk_*_minutes` | Walking distance divided by assumed 4.8 km/h |
| `drive_*_roundtrip_km` | Separately routed outward + return distance plus both connectors, km |
| `*_outbound_network_m`, `*_return_network_m` | Mapped graph distance excluding connectors, meters |
| `*_connector_m` | Origin and destination straight node-attachment lengths, meters |
| `*_snap_m` | Individual endpoint distance to selected network node, meters |
| `*_delta_*` | After minus before; negative values are possible for designated recipients |
| `main_included` | Primary common-sample eligibility |
| `all_routes_reachable` | Both directions reachable under both mode networks |
| `unresolved_address_conflict` | Assigned former site is store 1956; excluded in primary sample |

`before_after_summary.json`, `before_after_by_event.csv`, `before_after_equity.csv` and `before_after_sensitivity.csv` summarize these modeled origins with fixed ACS population weights. They do not contain observed trips. `before_after_emissions.csv` holds eight conditional fixed-car-share scenarios, with 1,000 hypothetical person round trips, one traveler per gasoline vehicle and 400 g tailpipe CO2/vehicle-mile.
