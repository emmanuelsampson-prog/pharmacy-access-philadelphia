# Pharmacy Closures and Neighborhood Access in Philadelphia

A spatial scenario assessment and research agenda for travel and emissions

Emmanuel Amissah Sampson · University of Pennsylvania · 16 November 2026

## Abstract

This study examines how pharmacy loss could change neighborhood access in Philadelphia and develops a research design for measuring subsequent travel and emissions. A Pennsylvania pharmacy-license roster was combined with 2018–2022 American Community Survey estimates and Census tract boundaries. The completed analysis removes all Rite Aid-labelled records simultaneously and recalculates the nearest listed pharmacy from each tract center. Across 391 populated tracts, the population-weighted straight-line distance increases by 32.4 meters. An increase occurs in 67 tracts, while the remaining 324 have no change. Restricting the inventory to selected chain names raises the calculated increase to 282.1 meters, showing substantial sensitivity to which destinations are counted. Neighborhood comparisons show no uniform disadvantage across the groups examined. These findings identify locations for further investigation and the importance of verifying the operating pharmacy network. The study does not measure historical changes in walking, driving or emissions. It provides conditional emissions calculations and a proposed quasi-experimental study using verified events, aggregate mobility data and explicit treatment of spatial spillovers.

## Introduction

Pharmacies are everyday destinations and sources of essential services. When a nearby pharmacy closes, residents may need to travel farther, use another mode, combine the visit with other errands, arrange delivery or forgo the visit. A new pharmacy can make a destination easier to reach, although its effect depends on where it opens and how people reach it. Commercial location decisions therefore connect urban accessibility, transport and the distribution of essential services.

Philadelphia’s experience with Rite Aid closures during 2023–2025 provides a case for examining these connections. City Council raised concerns about pharmacy loss and access, and insurer communications documented closures and prescription transfers [4, 10]. Those records establish the relevance of the problem but do not provide a complete history of when each pharmacy operated.

The wider research agenda covers store openings, closures and relocations. This report concentrates on pharmacies in Philadelphia. It presents a completed spatial assessment, explains what the results imply for further research, and specifies the additional evidence needed to estimate changes in travel behavior and emissions.

## Problem statement and research questions

A count of pharmacies or a map of their locations cannot establish whether residents can obtain services conveniently. A registered location may be inactive or unavailable to the public; a nearby destination may be separated from residents by a river, a difficult crossing, limited opening hours or insurance restrictions. Similarly, a change in distance on a map does not establish how people changed their journeys.

The central problem is to distinguish changes in the geography of available destinations from changes in actual travel, and then to determine which changes can credibly be attributed to openings or closures. Surviving pharmacies may receive displaced visits, so nearby areas cannot automatically serve as unaffected comparison groups.

1. How does removing Rite Aid-labelled locations change nearest-pharmacy proximity, and how sensitive is that result to the destination inventory?
2. How are the calculated changes distributed across neighborhoods with different poverty rates and levels of vehicle availability?
3. Under what conditions would closures or openings encourage walking, driving or changes in emissions?
4. What data and comparison strategy are needed to estimate historical effects while accounting for spatial spillovers?

The first two questions are evaluated with the public spatial data. The third is addressed through transport mechanisms and conditional calculations. The fourth is developed as the next empirical stage. Store openings are part of that agenda; no opening event is estimated in the completed analysis.

## Methodology

### Study area and data

The analysis covers Philadelphia’s 408 Census tracts, of which 391 have a positive population estimate. These populated tracts contain an estimated 1,593,208 residents. The Pennsylvania roster contains 3,324 license records statewide; 817 fall within Philadelphia and a 10 km surrounding buffer on the Pennsylvania side. Of those 817 records, 109 match the Rite Aid name, including 78 inside the city. These are candidate records rather than verified counts of operating stores or historical closures [1].

Six ACS tables provide population, household vehicle availability, poverty, income, age and racial or ethnic composition [2]. Census boundaries define tract geometry and the New Jersey coverage check [3]. The public data were downloaded with source URLs, retrieval times and checksums retained in a manifest. The license roster’s portal update is July 2025. Its records are not a reconstruction of the operating network in 2023.

A separate audit matches store numbers, addresses and cities from two court-filed lists to the roster [11, 12]. Only the specified exhibits are extracted. Filing dates remain separate from operating dates, and the scenario inventory is unchanged.

### Measuring proximity under removal

Each tract is represented by its geometric center, calculated in a meter-based coordinate system, EPSG:26918. The code measures the straight-line distance to the nearest eligible pharmacy, removes all Rite Aid-labelled entries at once, and repeats the calculation. The difference is the modeled one-way proximity increase. A population-weighted mean gives more weight to tracts with larger populations; it is not an average of residents’ observed trips.

Two inventories are compared. The first includes all listed pharmacy records in the study area. The second retains selected recognizable chain names. The restricted inventory omits independent pharmacies and may still contain inactive records. The two results are sensitivity scenarios rather than lower and upper bounds on the historical effect.

### The New Jersey coverage check

New Jersey pharmacy locations are absent from the available inventory. Fifty populated tracts have centers less than 2 km from New Jersey county geometry. A nearby pharmacy across the state boundary could therefore be missing from their calculated alternatives. The 2 km threshold is a practical data-coverage screen; it is not a walking-distance standard.

Table 1. Treatment of tracts near New Jersey

| Analysis | Tracts included | Treatment of the 50 flagged tracts |
| --- | --- | --- |
| Main maps and proximity results | 391 | Included |
| Separate border sensitivity | 341 | Excluded for comparison |
| Secondary prediction comparison | 341 | Excluded from fitting and evaluation |

The main descriptive analysis therefore retains all 391 populated tracts. Excluding the 50 flagged tracts lowers the population-weighted increase from 32.4 to 30.3 meters. This comparison does not correct the missing inventory, and some origins farther from the boundary may also use New Jersey pharmacies.

### Equity and prediction comparisons

The study compares population-weighted changes across neighborhood groups, using a 20% poverty threshold and a 30% threshold for households without a vehicle. Tracts with missing group information are omitted from that comparison. These descriptive contrasts do not include significance tests and cannot identify the experience of individuals within a tract.

A secondary exercise tests whether baseline access and neighborhood characteristics predict the calculated proximity increase. A training-sample median, ridge regression and random forest are evaluated on five contiguous geographic holdouts. Training origins within 1 km of test origins are excluded, and preprocessing is fitted within each training sample. The target is a calculated scenario outcome, not observed travel. This comparison assesses predictive information in the chosen features; prediction is not needed to calculate the spatial scenario itself.

## Results

### Court records show why the inventory needs historical verification

The two selected court lists contain 101 Pennsylvania and New Jersey locations, including 16 Philadelphia sites. Eleven city sites appear in the October 2023 motion and five in the June 2025 notice. All 16 match records in the scenario roster [11, 12]. The presence of the 2023-listed sites shows why a July 2025 portal update cannot certify that every entry was operating then. The filings identify closure plans, but none supplies a verified last pharmacy-operating day. This partial collection therefore strengthens the inventory audit without identifying historical treatment dates.

### Access changes are concentrated in a minority of tracts

With all listed destinations eligible, the population-weighted nearest distance rises from 421.2 to 453.6 meters, an increase of 32.4 meters. Sixty-seven tracts (17.1% of populated tracts) have an increase greater than one meter. The other 324 have no calculated increase because a remaining listed destination is already as close or closer than the removed records.

The 67 tracts contain an estimated 281,655 residents. That number describes the population of those tracts; it does not count people observed to have lost access. A citywide average also conceals the larger changes in some individual areas.

### The inventory changes the result substantially

The selected chain-name inventory produces a population-weighted increase of 282.1 meters, about 8.7 times the all-listed result. This difference shows how strongly the calculated loss depends on the alternatives counted. It does not establish which inventory is correct. The all-listed inventory may overstate usable alternatives, while the chain-name restriction excludes legitimate independent pharmacies.

![Philadelphia tract maps of the removal scenario and the share of households without a vehicle](../outputs/public/access_equity_map.png)

Figure 1. Modeled proximity changes and household vehicle availability. The left map removes all Rite Aid-labelled records; the right map shows the ACS share of households without a vehicle. The points are license records. Straight-line distances and tract centers do not represent actual journeys. New Jersey pharmacies are missing.

Table 2. Descriptive neighborhood comparisons

| Tract group | Number of tracts | Weighted increase in meters |
| --- | --- | --- |
| All populated tracts | 391 | 32.4 |
| Poverty rate at least 20% | 192 | 34.6 |
| Poverty rate below 20% | 197 | 30.0 |
| Households without a vehicle at least 30% | 176 | 26.0 |
| Households without a vehicle below 30% | 212 | 37.3 |

Higher-poverty tracts have a slightly larger calculated increase than lower-poverty tracts, at 34.6 versus 30.0 meters. The pattern reverses for vehicle availability: tracts where at least 30% of households lack a vehicle have an increase of 26.0 meters, compared with 37.3 meters elsewhere. These results do not support a claim that every disadvantaged group experiences the largest geographic change. They also do not imply that a smaller distance change is easy for residents without a car.

### The simple baseline has the lowest absolute error

Table 3. Prediction errors in held-out geographic areas

| Method | Mean absolute error in meters | Root mean squared error in meters | R squared |
| --- | --- | --- | --- |
| Median baseline | 28.3 | 109.5 | -0.071 |
| Ridge | 47.2 | 104.4 | 0.027 |
| Random forest | 49.3 | 105.6 | 0.005 |

Mean absolute error is the average absolute gap between a prediction and the calculated proximity increase; lower values indicate closer predictions. The median baseline performs best on this measure. Most tracts have no increase, which helps explain its performance. Ridge and random forest have slightly lower root mean squared errors, which place greater weight on large mistakes, but their R squared values are close to zero. These results do not support using the fitted models to forecast real closure impacts.

## Walking driving and emissions

The completed calculation shows reduced proximity under removal. It does not show that residents switched from walking to driving. Holding origins and all other destinations fixed, removing a destination cannot shorten the distance to the nearest remaining option; adding a destination cannot lengthen it. The behavioral and emissions consequences require further evidence.

Table 4. Possible travel responses to location change

| Location change | Possible response | Conditional emissions implication |
| --- | --- | --- |
| Loss of a nearby pharmacy | Longer walking or driving trip; some journeys may switch to a car | Additional gasoline vehicle travel increases tailpipe CO₂ |
| Opening near residents and a usable walking route | A shorter walk or drive may replace a longer car journey | Lower vehicle travel can reduce tailpipe CO₂ |
| Opening that attracts additional car journeys | More trips or diversion to a car-oriented destination | Total vehicle travel and emissions may increase |
| Closure followed by delivery, combined errands or forgone visits | Travel is reorganized or a visit does not occur | The net direction cannot be determined from proximity alone |

EPA guidance connects nearby destinations and transport options with opportunities to walk, cycle or use transit [5]. Applying that mechanism here, a conveniently located opening could support walking, while a closure could make walking less practical. Neither statement is an observed mode result from this project. A reduction in travel because someone cannot obtain essential services should not be treated as an access improvement.

### Conditional emissions calculation

For illustration, the emissions calculation applies the 32.3893-meter population-weighted increase to 1,000 hypothetical person round trips. It assumes one traveler per vehicle and the EPA factor of approximately 400 grams of tailpipe CO₂ per gasoline-vehicle mile [6]. Car share, route detour and the proportion of journeys creating additional travel are varied explicitly.

With half of trips made by car, a route multiplier of 1.3 and all of the modeled extension counted as additional travel, the result is 10.47 kg of additional tailpipe CO₂ per 1,000 person round trips. Across the 24 specified combinations, the result ranges from 2.01 to 25.76 kg. These values are sensitivity calculations, not observed emissions or confidence intervals.

The calculation multiplies the one-way distance increase by two, the route multiplier, the number of person trips, the car share and the additional-travel share, then converts meters to miles and grams to kilograms. Its results are nonnegative by construction because it models added gasoline travel. It therefore cannot establish that closures always increase net emissions. It also omits transit operations, delivery logistics, electricity use and vehicle lifecycle emissions.

## Discussion

The strongest substantive finding is that estimated access loss depends heavily on how the pharmacy network is defined. A modest average increase of 32.4 meters could be interpreted as little consequence if read alone. The concentration in 67 tracts and the much larger result under the chain-name inventory show why that interpretation would be premature. Before debating the magnitude of a historical effect, the analysis needs a verified set of destinations that residents could actually use.

The equity comparisons also require more than a ranking of distances. Higher-poverty areas show a somewhat larger geographic increase, but areas with more households lacking vehicles do not. Vehicle availability can nevertheless change the burden of a given distance. Walking conditions, disability, opening hours and pharmacy eligibility may matter more than a small difference in the neighborhood average. Those dimensions should be measured directly rather than inferred from demographic categories.

The findings establish a reproducible way to identify candidate areas for field checking and test how inventory choices alter the answer. They do not resolve the central behavioral question. Actual changes in visits, transport modes and emissions remain empirical questions, and the study’s next stage must distinguish displacement to other pharmacies from reduced access to pharmacy services overall.

## Proposed quasi experimental study

The next stage would construct a 2022–2025 panel, with 2022 as the preperiod, from verified store operating intervals and authorized aggregate origin-to-pharmacy mobility records. Closure dates would distinguish pharmacy operations from front-store operations and announcement dates. Same-site replacements, prescription transfers and nearby openings would be recorded. No licensed mobility panel or verified event ledger has been obtained for the completed analysis [9].

A cohort-specific difference-in-differences design would compare changes around a closure with changes in never-treated or not-yet-treated areas. Callaway and Sant’Anna provide the methodological basis for multiple treatment periods [7]. Spatial exposure would separate areas directly losing a nearby destination from areas receiving displaced demand, following the interference concerns discussed by Butts [8]. Initial 800-meter direct and 800–1,600-meter spillover distances would be tested against alternative thresholds and observed preclosure catchments.

Bankruptcy does not randomly assign closure locations or timing. Declining demand and neighborhood change may affect both closure and subsequent travel. Pretrend checks, event-date uncertainty, alternative comparison groups and spatial uncertainty are therefore central to interpretation. Aggregate origin-to-destination records provide distance proxies and visitation patterns; validated mode information and historical routes are still needed to estimate walking, driving and emissions.

The companion notebook contains input checks and an unadjusted cohort-time mean-change estimator. An optional R extension uses the established did package for covariate-adjusted estimation. Neither has produced empirical treatment effects in this project. The full protocol documents sample rules, anticipation, comparison support and the handling of overlapping events.

## Recommendations

First, verify the operating pharmacy inventory before using these results for resource allocation. Audit the 109 Rite Aid-labelled buffer records, confirm public access and operating dates, retain independent pharmacies, and add New Jersey alternatives. The 67 tracts with a calculated increase are a practical starting list for investigation, not a validated list of neighborhoods with unmet need.

Second, evaluate access through usable routes and services. A local assessment should combine walking and transit travel times with opening hours, insurance acceptance, prescription capacity and replacement arrangements. Tracts with many households without vehicles deserve attention even when their straight-line increase is small.

Third, assess proposed openings and closure responses against existing travel patterns. A nearby pharmacy with safe pedestrian access may reduce the need for longer car journeys. A car-oriented opening may attract additional vehicle travel. Planning decisions should compare these possibilities using routed access and observed journeys rather than assuming that every opening lowers emissions.

Finally, collect the evidence needed for a historical evaluation before making causal or carbon claims. Track total pharmacy visitation as well as receiving-store gains, preserve mobility-panel coverage information, and assess who is missing from the sample. Prediction models should be reconsidered only after the inventory and outcomes are improved; the current models offer no advantage over the median baseline on average absolute error.

## Limitations

The main limitation is temporal validity. The available license roster is a snapshot that may include inactive, nonretail or nonpublic locations. Removing all Rite Aid-labelled entries at once does not reproduce the sequence of 2023–2025 closures. The study consequently estimates a spatial scenario, not a historical treatment effect.

Geographic measurement is also incomplete. Geometric tract centers conceal variation within neighborhoods, straight lines omit route barriers, and some pharmacy coordinates are approximate. New Jersey alternatives are missing from every main result. Excluding 50 nearby origins from the prediction comparison does not remove that limitation from the descriptive analysis.

The ACS estimates describe areas during 2018–2022. Margins of error are retained in the inputs but are not propagated into the reported comparisons. Missing covariates change subgroup sample sizes, and neighborhood characteristics cannot identify an individual resident’s experience. The study does not measure pharmacy capacity, service compatibility, disability or unmet medication need.

No observed trip histories, validated mode shares or local emissions measurements are available. The emissions exercise assumes additional gasoline vehicle travel and does not estimate net transport emissions. Future device-based data may underrepresent older, lower-income or less digitally visible residents. Even with those data, closure selection and spillovers may limit the credibility of causal comparisons.

## Conclusion

The completed study shows that removing Rite Aid-labelled records increases modeled nearest-pharmacy distance in a minority of Philadelphia tracts and that the magnitude depends strongly on the destination inventory. It also shows that neighborhood disadvantage does not map uniformly onto the calculated distance change. The project delivers a reproducible spatial assessment, documented public data, an executed notebook and a design for extending the analysis to historical outcomes.

Closures can make walking less practical and increase emissions when they create additional car travel. Well-located openings can support walking and reduce vehicle travel when they replace longer journeys. The present evidence does not establish that either behavioral change occurred in Philadelphia. Verifying operating destinations and measuring actual travel are the necessary next steps.

## References

1. Pennsylvania Department of State and Department of Health. Find Naloxone at a Pharmacy Near Me Current Statewide. Dataset ysdx-4vmi; portal update July 1, 2025. [Source](https://data.pa.gov/Opioid-Related/Find-Naloxone-at-a-Pharmacy-Near-Me-Current-Statew/ysdx-4vmi/about_data)

2. U.S. Census Bureau. 2022 American Community Survey five-year Summary File. Tables B01001, B01003, B03002, B08201, B17001 and B19013; estimates cover 2018–2022. [Source](https://www.census.gov/programs-surveys/acs/data/summary-file.2022.html)

3. U.S. Census Bureau. 2022 Cartographic Boundary Files. Pennsylvania census tracts and United States counties at 1:500,000 scale. [Source](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html)

4. Philadelphia City Council. Resolution 240071. Pharmacy closures and access concerns. [Source](https://phila.legistar.com/LegislationDetail.aspx?ID=6503447&GUID=E7438EA1-5E3E-460A-9902-FCDE7D12D48B&FullText=1)

5. U.S. Environmental Protection Agency. Smart Growth and Transportation. Access to destinations and transportation choices. [Source](https://www.epa.gov/smartgrowth/smart-growth-and-transportation)

6. U.S. Environmental Protection Agency. Greenhouse Gas Emissions from a Typical Passenger Vehicle. Approximately 400 grams of tailpipe CO₂ per gasoline-vehicle mile. [Source](https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle)

7. Callaway, B., and Sant’Anna, P. H. C. (2021). Difference-in-Differences with Multiple Time Periods. Journal of Econometrics, 225(2), 200–230. [Source](https://doi.org/10.1016/j.jeconom.2020.12.001)

8. Butts, K. Difference-in-Differences Estimation with Spatial Spillovers. Working paper, arXiv:2105.03737. [Source](https://arxiv.org/abs/2105.03737)

9. Penn Libraries (2025). Penn Data Access Unlocked via Dewey Platform. May 21. [Source](https://www.library.upenn.edu/lippincott/datapoints/data-access-dewey-2025)

10. AmeriHealth Caritas Pennsylvania and Community HealthChoices (2025). Rite Aid pharmacy closure notice. June 5. Contextual evidence of closures and prescription transfers; not a store-specific event ledger. [Source](https://www.amerihealthcaritaschc.com/content/dam/amerihealth-caritas/acpchc/pdf/provider/resources/communications/2025/20250605-rite-aid-pharmacy-closure-notice.pdf.coredownload.inline.pdf)

11. Rite Aid Corporation et al. (2023). Store closing sales motion. U.S. Bankruptcy Court, District of New Jersey, case 23-18993-MBK, document 37, filed October 16. Exhibit A Schedule 1, PDF pages 54–56. Public mirror of court-filed document. [Source](https://cdns.abclocal.go.com/three/kabc/101823-kabc-rite-aid-doc.pdf)

12. New Rite Aid LLC et al. (2025). Sixth notice of additional closing locations. U.S. Bankruptcy Court, District of New Jersey, case 25-14861-MBK, document 743, filed June 6. Exhibit 1, PDF pages 5–8. Public mirror of court-filed document. [Source](https://npr.brightspotcdn.com/f8/c8/faad678e424db35665a541d7ce0a/25-06-06-store-closure-filing.pdf)
