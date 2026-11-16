# Research protocol

## Working title and scope

**Pharmacy Closures and Neighborhood Access in Philadelphia: Research Protocol for Travel and Spatial Spillovers.**

The proposed study connects commercial location decisions with urban sustainability. A pharmacy closure changes both the geography of destinations and the set of choices available to nearby residents. Its effects may spread to competing pharmacies and surrounding retail destinations. The project asks whether these changes produce longer access journeys, redirect visits, or leave some neighborhoods with fewer practical options.

The semester project should concentrate on Philadelphia pharmacies. Use 2022–2025 observations, allowing 2022 to establish baseline patterns. Include nearby suburban and New Jersey alternatives in the eventual routing and mobility network; limit the primary population to Philadelphia residents. Treat grocery stores, general retail openings and longer-term location-allocation optimization as extensions. The course rubric and deadline have not yet been provided; the scope should be checked against them.

## Questions and distinct estimands

| Question | Outcome | Interpretation |
|---|---|---|
| Does the available destination network change? | Nearest pharmacy distance/time and number reachable within 15/30 minutes | Modeled accessibility; meaningful even without observed visits |
| Does the geography of sampled pharmacy visits change? | Home-origin-to-POI distance proxy, pharmacy visitor-POI counts per sampled device, destination diversity | Observed sample behavior with geography and panel limitations |
| Which alternatives gain visits? | Stable, surviving pharmacy visit counts relative to preperiod; neighboring-store category visits | Demand redistribution; a surviving competitor may be a spillover outcome rather than a valid control |
| Who faces larger burdens? | Heterogeneity by baseline no-vehicle share, poverty, older population and neighborhood composition | Area-level distribution, not individual causal effects |
| What are the potential emissions consequences? | Conditional incremental vehicle distance × tailpipe factor | Scenario unless modes, trip chaining and route distances are observed/validated |

Primary empirical estimand: the average change in the mobility-based outcome for origins first directly exposed to a verified closure, relative to an eligible unexposed comparison trend. A second, separate analysis estimates redistribution to surviving pharmacies in distance rings. Do not combine these into one treatment variable or interpret closure-site visits falling to zero as evidence of reduced neighborhood demand.

## The prediction task

**Current executable benchmark:** predict the modeled change in nearest-pharmacy distance under a specified inventory-removal scenario using baseline inventory features and ACS context. Compare random forest, ridge regression and a median prediction. Use five contiguous geographic folds and remove training origins within 1 km of each test fold. All imputing and scaling occur inside each training fold. Parameters are fixed in advance; the held-out folds are not used to tune them. Report pooled held-out MAE, RMSE and R², fold results, and held-out permutation importance. Negative or near-zero predictive gains are valid results.

This benchmark is a transparent implementation exercise. The target is computed from the same inventory being studied, so successful prediction is not a novel empirical finding. The roster may already reflect treatment-period changes and cannot serve as verified pretreatment features for historical causal analysis.

**Proposed prediction task after mobility access:** predict untreated pharmacy activity or home-origin access outcomes using only preclosure training observations and appropriate untreated observations. Compare regularized regression with a tree ensemble using both spatial separation and a final time holdout. Use baseline accessibility, land use, category supply, preperiod trends, demographics and seasonality. Assess temporal drift and subgroup errors. Keep prediction and treatment-effect estimation conceptually distinct. Use ML as a nuisance model in an established doubly robust DiD method only if the implementation and sample support it; an accurate prediction model does not establish exchangeability or parallel trends.

## Data and event construction

1. **Operating network:** combine dated POI snapshots and official licensing records, with manual validation of community-pharmacy status. Include independent, grocery and chain pharmacies; remove inpatient-only, mail-order and nonpublic dispensing sites. Stable IDs must survive name changes and relocations. A license may persist after closure.
2. **Events:** record the last confirmed pharmacy-operating date and first confirmed pharmacy-closed date, source URL, document date, event confidence, front-store closure, receiving pharmacy, and any same-site reopening. Announcement, court filing, liquidation and pharmacy closure dates are distinct. Never use a notice issue date as a universal treatment date.
3. **Mobility:** prefer licensed POI-period aggregates, origin distributions and active-panel denominators. Verify whether each field measures visits, devices, estimated visitors or unique visitors and document suppression/noise. Preserve missing and suppressed values. Retain a consistent POI universe, including stores that later close. Audit zero-count weeks against coverage indicators.
4. **Demographics:** use a fixed pretreatment ACS vintage (2018–2022 estimates), retaining estimates and MOEs. Check Census geography vintages; vendor 2010 CBGs cannot be joined directly to 2020 tracts without a crosswalk. Use population-weighted block origins when available, rather than unweighted tract centroids.
5. **Networks:** use appropriate historical street and transit data or a clearly dated constant-network approximation. Walking routing must respect crossings and barriers. Transit travel time includes access walk, wait, transfer and service calendars. A nearby bus stop is not a travel-time measure. Current GTFS cannot be silently treated as 2023 service.
6. **Emissions:** combine validated route changes with a declared vehicle factor and assumptions about mode, occupancy, trip chaining, delivery and forgone visits. A visitor's home-to-store separation is not necessarily the actual trip's origin or distance.

Current downloaded data support a public **scenario** only: a July-2025-labelled PA license roster, 2018–2022 ACS tables, 2022 cartographic geography and a June 2025 closure notice. None supplies a verified historical panel of pharmacy operation.

## Exposure, spillovers and controls

For the eventual empirical analysis, define direct origin exposure as a verified closure within 800 m of the origin (prefer residential population-weighted origins). Define indirect exposure in the 800–1,600 m ring. These are starting specifications, not facts about how far effects travel. Repeat with alternative thresholds (400/800 m, 800/1,600 m, 1.6/3.2 km) and with preperiod visit-based catchments. Freeze behavioral catchments using only preperiod observations.

Use first verified direct exposure as the cohort date. Identify additional closures, competitor changes, same-site replacement and overlapping exposure windows. For an isolated-event specification, censor or remove affected windows rather than pretending these are single permanent treatments. A first-exposure estimand that includes subsequent closures is a different estimand and must be labelled accordingly. Reopening violates a simple absorbing-treatment interpretation.

Choose controls that are never directly exposed or remain unexposed beyond the target period plus a declared anticipation window, and are not indirectly exposed during the comparison interval. Assess baseline outcome trends, density, poverty, supply and transit access. Nearby surviving pharmacies often gain displaced demand and are not automatically clean controls. Wider regional controls can increase support but introduce different local trends; diagnose that tradeoff rather than assuming comparability.

Philadelphia's widespread closures may leave too few clean controls. If support fails, shorten event windows, narrow cohorts, add a defensible comparison geography, or present descriptive/scenario analysis. Do not force a causal result.

## Identification and estimator

For cohort g and period t, with clean comparison units C and baseline b:

`ATT(g,t) = mean(Y_it − Y_ib | G_i = g) − mean(Y_it − Y_ib | i in C(g,t))`.

The Python implementation uses a **one-period anticipation window**, so b = g − 2; it omits the anticipation period and reference period. This is an unadjusted cohort-time mean-change contrast, not the full Callaway–Sant'Anna doubly robust estimator. It excludes already-treated controls and separately flagged spillover exposure. Covariate adjustment should be implemented and checked with an established estimator before a final conditional-parallel-trends claim. The included R script documents that extension but has not been executed in this environment.

Identification requires no unaccounted anticipation, appropriate parallel counterfactual trends, treatment/measurement consistency, common support, and a defensible representation of interference. Bankruptcy does not make store-specific closure timing random: declining demand, lease terms, staffing, neighborhood conditions and firm strategy can select sites. Pretrend tests can reveal problems; passing them cannot prove the assumption.

Report event-time effects with sample/cohort support at each horizon. Composition can change across horizons, so provide a fixed-cohort sensitivity where feasible. Use the same geography units over time and clustering that reflects spatially shared shocks. The supplied bootstrap resamples complete spatial clusters and reports pointwise percentile intervals; it refuses fewer than 20 clusters and drops intervals with inadequate bootstrap support. Twenty clusters is a computational safeguard, not a guarantee of valid inference. Test alternative cluster sizes, and consider spatial HAC or wild-cluster procedures for the final analysis. Joint pretrend inference and simultaneous event-study bands are not implemented in the pilot.

## Diagnostics and robustness

- Validate closure dates with independent sources; compare lower/upper date bounds and exclude ambiguous events.
- Check pretreatment trends, anticipation, placebo dates and unaffected destination categories chosen before looking at results.
- Audit active-device composition, provider methodology changes, home-area coverage, suppressed cells and POI ID churn. Do not interpret changing panel coverage as travel changes.
- Compare distance and travel-time measures; use residential origins and border buffers; include NJ alternatives.
- Vary direct/indirect exposure thresholds, control buffers, cohort windows, replacement treatment and overlapping-event handling.
- Report the total pharmacy category as well as individual destinations to distinguish redistribution from category contraction.
- Present missingness, ACS uncertainty, model performance and negative results. Do not infer prescription adherence, health outcomes, customer spending or medication purchases from a pharmacy visit.

## Emissions accounting

For an illustrative one-way straight-line increase Δd (meters), the scenario calculates:

`extra kg CO2 = Δd × 2 × route-detour factor / 1609.344 × person round trips × car share × additional-trip share × 400 / 1000`.

This assumes one traveler per gasoline vehicle. The factor of two assumes a round trip; the additional-trip share captures the share treated as dedicated extra travel. The 400 g CO2/vehicle-mile value comes from the EPA's typical passenger-vehicle explanation, not a Philadelphia fleet estimate. Walk/bike have zero vehicle tailpipe emissions in this narrow accounting. Transit marginal emissions are not estimated. Report a parameter grid rather than a single citywide tonnage. Carbon results could rise, fall or be ambiguous when trip chaining, delivery and forgone visits are considered.

## Four-stage completion plan

| Stage | Work | Decision needed to proceed |
|---|---|---|
| 1 | Obtain rubric; verify Penn/Dewey product coverage; build and audit operating-history ledger | Adequate sample, dates and allowed use |
| 2 | Construct balanced origin and survivor panels; routing; coverage and border diagnostics | Outcomes and clean controls are defensible |
| 3 | Execute spatial prediction validation and the prespecified causal design; sensitivity and placebo tests | Results survive identification and measurement checks |
| 4 | Write final interpretation, limitations and reproducible notebooks; publish permitted outputs | Author verifies findings and course requirements |

The present package completes a public-data feasibility run and the preparatory method implementation. It does not claim stages 1–4 are finished. GitHub publication of a working pilot is appropriate when clearly labelled; calling it a final empirical causal study is premature.

## Longer-term research agenda

Extend to grocery, bank and retail openings/closures; distinguish demand creation, within-firm cannibalization and competitive diversion; compare transit-rich and car-dependent neighborhoods; study openings as a separate nonabsorbing treatment; model capacity constraints at surviving pharmacies; and evaluate replacement-site scenarios. A later location-allocation model could minimize travel burden subject to capacity and equity constraints. These extensions connect this course project with research on commercial location decisions, urban form and access without overloading the first empirical study.
