# Obtaining the remaining data

## Penn mobility access

[Penn Libraries' Dewey access page](https://www.library.upenn.edu/lippincott/datapoints/data-access-dewey-2025) states that current Penn students, staff and faculty can sign in with their university email at [Dewey](https://app.deweydata.io). Entitlement to a particular product/version and its permitted uses must be checked in the signed-in catalog.

1. Sign in through Penn and create a project for this course research.
2. Find **Advan Research Foot Traffic / Weekly Patterns or Monthly Patterns**, its POI metadata and any compatible panel-normalization tables. Inspect the exact version and documentation. A provider's home-origin field can vary by product: do not assume 12-digit block groups if the actual product supplies 11-digit tracts.
3. Start with January 2022–December 2025 and pharmacy/drug-store POIs in Philadelphia plus a regional buffer. The legacy NAICS code is often 446110; the 2022 NAICS pharmacy/drug-retailer code is 456110. Check the product's taxonomy and include pharmacy departments within grocery/general-merchandise locations when separately identifiable. Confirm those codes in the actual export rather than relying on string matches alone.
4. Include stable POI IDs, addresses, coordinates, category and brand history, period dates, visits/devices, home-origin distributions, coverage flags and active-panel denominator where available. Request historic POI snapshots to capture closed stores, not only the current POI universe.
5. Request a small city/time sample first. Validate counts, suppression, missingness, geography vintage, provider methodology breaks and availability before downloading multiple years.
6. Use Dewey's current **Get Data** instructions to export into `data/restricted/`. Keep credentials in a local environment variable or approved secret store, never in a notebook or repository. The exact project URL/ID is account-generated and has not been guessed or inserted here.

[Penn's API help](https://faq.library.upenn.edu/business/faq/421473) and [Dewey's current data access instructions](https://docs.deweydata.io/article/data-access-options) describe the signed-in export route. Dewey's documented Python client is `deweypy`; follow the commands generated for your project. No mobility API call has been executed and no entitlement has been assumed in this package.

Do not use a POI's median `distance_from_home` as a road distance or treat a weighted average of POI medians as a citywide median. For origin-based outcomes, use origin distributions and documented origin-to-destination calculations. Count-based products cannot by themselves identify driving, walking or transit. A mode-change claim needs validated mode labels or a suitable trajectory/travel survey dataset. Device-level records bring additional access and privacy requirements; they are not necessary for the first aggregate analysis.

## Historical pharmacy status

Use archived official store/transfer notices, dated POI snapshots, licensing status and credible contemporaneous reports to verify pharmacy operation. Retain original evidence references and date intervals. Check community access, opening hours, receiving pharmacy, same-site successor and intervening reopenings. The current candidate ledger deliberately contains no invented event dates. The separate [court evidence audit](evidence_audit.md) now links 16 Philadelphia sites to two selected filings, but it still supplies no verified pharmacy-stop dates.

The June 2025 notice downloaded here states closures or imminent closures; it cannot distinguish a June pharmacy shutdown from a later front-store closing. The Philadelphia City Council document cited in the references supplies historical context, not a complete geocoded dated event file.

## Transit, streets and cross-border alternatives

[SEPTA publishes GTFS](https://www3.septa.org/developer/) under its license. The current feed inspected for this project was updated in October 2026, so it was not downloaded as evidence of 2023–2025 service. Obtain archived feeds for the study dates or explicitly report a constant-network approximation. Include schedules and service calendars, not just stop coordinates. Add New Jersey pharmacy records and PATCO/NJ Transit service where relevant. The [NJ official licensee-list page](https://www.njconsumeraffairs.gov/requestlist/Pages/default.aspx) links to a free facilities roster. The public folder inspected on November 16, 2026 listed a November 2, 2026 file; this current snapshot was not merged into the 2023–2025 study.

Use historical OpenStreetMap extracts or another appropriate street network with travel-mode permissions, barriers and crossing information. These have not been downloaded in the pilot. Current road distances, straight-line distances and actual trajectories are different measurements. Save network vintage, CRS, routing engine and travel-time settings alongside any generated matrix.

## Publication boundary

The public repository may contain original code, source references, approved aggregate outputs and publicly licensed inputs/derivatives. It must not contain API keys, device IDs, individual trajectories or source files whose license prohibits redistribution. The provided `.gitignore` protects standard restricted paths; it cannot recognize a sensitive file copied elsewhere. Inspect the exact staged files and notebook outputs before publishing. No attempt is made to infer an individual's diagnosis or medication from pharmacy visits.
