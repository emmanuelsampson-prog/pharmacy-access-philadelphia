# Before and after access: methods and interpretation

The historical investigation covers **2023–2025**. The route calculations use a focused subset of **24 company-reported pharmacy transfers**, with reported final operating days between **June 4 and August 8, 2025**. They measure access to the named recipients, not actual journeys or the causal effect of closure. The main record is [notebook 04](../notebooks/04_before_after_transfer_access.ipynb).

## Evidence and corroboration

`historical_evidence_2023_2025.csv` contains 41 selected Philadelphia locations, not a comprehensive census. Date meanings remain explicit: court filing, scheduled retail closure, reported pharmacy closure or company-reported last pharmacy-business day. The four reported 2024 pharmacy dates are not promoted to a complete operating history.

The archived company table contains 1,025 national records and 24 Philadelphia records. Every Philadelphia store number matches the May 5, 2025 Keystone First VIP Choice insurer directory. Five also appear in the selected June 6 court notice. This corroborates identities and closure selection, not all final operating days. Repetition of company-table dates in another publication is not independent confirmation. The audit contains no independently confirmed exact-address final operating day.

Store 1956 has an unresolved address conflict: the insurer lists **12353 Academy Road**, while other sources list **12311 Academy Road**. It is excluded from the primary route sample. A separate sensitivity includes the latter coordinate. One Chestnut Street transfer names a same-address successor; this establishes a designated address, not uninterrupted dispensing service.

## Origins, assignment and common sample

1. Retain the 391 populated Philadelphia tracts in the Census/ACS geography.
2. Assign each geometric tract center to its nearest former pharmacy among the 24 study sites using EPSG:26918 distances. This does not identify the nearest pharmacy of any brand or actual customers.
3. Select centers within 800 m in straight-line distance. Retain a wider 1,000 m pool for sensitivity analysis.
4. Route from each fixed origin to its former pharmacy and to the named recipient. Require reachable outward and return routes in both travel modes, all endpoint-to-node connectors no longer than 200 m, and no unresolved former-address conflict.
5. Hold origins and ACS population weights constant in both comparisons. The primary sample contains **62 origins representing 22 transfers**. Academy Road is excluded; Krewstown Road has no origin within the main catchment. Absence of an estimate is not a zero effect.

## Historical network and routing

The source is the **January 1, 2025 Geofabrik Pennsylvania OpenStreetMap extract**, timestamp `2025-01-01T21:21:00Z`. The downloader records the PBF hash, filters and derived graph hashes in `data/historical_network_manifest.json`. Both destinations use the same map to isolate differences associated with the designated destination. No historical travel speeds are inferred.

The walk graph is bidirectional, with walking access filters. The drive graph preserves mapped one-way direction and motor-access filters. Routes minimize edge length. Parallel edges are reduced by minimum length, not summed. Outward and return driving routes are solved separately. Straight endpoint connectors are added to each leg, recorded separately and screened; they are not mapped pedestrian or vehicle paths. Walking time assumes **4.8 km/h**.

The graphs omit full turn-restriction relations, comprehensive node barriers and conditional access rules. They contain the largest weakly connected component inside the stated study bounding box, which can omit small isolated paths. Routes do not establish safety, wheelchair accessibility or real-world travel. Pennsylvania-only extraction does not reconstruct a complete cross-border choice set. The selected recipients are in Pennsylvania.

## Summary, equity and sensitivity

For origin i with fixed ACS population weight pᵢ, the weighted change is `sum(pᵢ × (afterᵢ − beforeᵢ)) / sum(pᵢ)`. These weights describe residential context, not observed trip volumes. The reported population of 262,710 must not be called a count of affected customers.

The main comparison gives **9.0 → 16.0 minutes** of modeled one-way walking and **1.61 → 2.75 km** of modeled driving per round trip. Walking increases at 44 origins, decreases at 13 and changes by no more than one meter at five. The latter five are assigned to the same-address transfer.

Sensitivity combinations use catchment radii of 500/800/1,000 m and connector thresholds of 100/200/300 m. They change sample composition and are not uncertainty intervals. Poverty (20%) and household vehicle availability (30% without a vehicle) are separate descriptive classifications. They are not causal subgroup analyses; ACS margins of error are not propagated.

## Conditional emissions

`kg CO₂ = Δ driving round-trip km / 1.609344 × hypothetical person round trips × gasoline-car share × additional-travel share × 400 / 1000`

No additional doubling or road-detour multiplier applies. Under 1,000 hypothetical trips, 50% gasoline-car share, one traveler per vehicle and 100% additional travel, the result is **142.19 kg of additional tailpipe CO₂**. The assumed distribution of trips follows population weights. Car share is fixed before and after, so this is not an estimate of walking-to-driving transitions or net citywide emissions.

## Reproduction and licensing

The release package includes the cached derived graph files and public analytical inputs. A Git clone needs `python -m src.download`, `python -m src.pilot`, and `python scripts/download_historical_networks.py` before `python -m src.transfer_access`. The raw historical PBF is about 296 MB; building and loading graphs can require several GB of RAM. Use the release cache to avoid reconstructing them. The graph manifest detects changed inputs.

To refresh the factual ledgers from their sources, use `python -m src.transfers --download`, `python -m src.corroboration --download` (requires Poppler), then `python scripts/build_historical_evidence.py`. Review source/address changes before accepting new results. The extraction scripts preserve source row/page references.

OpenStreetMap-derived network data are © OpenStreetMap contributors under **ODbL 1.0**, with extracts supplied by Geofabrik. The code's MIT license does not relicense these databases. Source articles and insurer PDFs are not redistributed in the release.
