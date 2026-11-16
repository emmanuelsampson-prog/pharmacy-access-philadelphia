# OPTIONAL EMPIRICAL EXTENSION -- NOT EXECUTED IN THE PUBLIC PILOT.
# Requires R package did and a verified, coverage-audited origin panel.
# Run from repo root: Rscript scripts/estimate_did.R data/restricted/origin_panel.csv
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Supply one verified origin-panel CSV")
if (!requireNamespace("did", quietly = TRUE)) stop("Install the did package first")
d <- read.csv(args[1], colClasses = c(unit = "character", cluster = "character"))
covars <- c("baseline_outcome", "population_density", "poverty_rate", "no_vehicle_share")
required <- c("unit", "period", "first_treat", "outcome", "spillover", "cluster", covars)
if (!all(required %in% names(d))) stop("Missing panel columns")
if (anyNA(d[required])) stop("Missing observations require an explicit sampling rule")
if (anyDuplicated(d[c("unit", "period")])) stop("Duplicate unit-period records")
if (!all(d$spillover %in% c(0,1))) stop("Spillover must be binary")
for (v in c("first_treat", "cluster", covars)) {
  if (any(tapply(d[[v]], d$unit, function(x) length(unique(x))) != 1L)) {
    stop(paste(v, "must be fixed within unit"))
  }
}
if (!all(table(d$unit) == length(unique(d$period)))) stop("Use an audited balanced panel")
# Conservative restriction: no separately flagged competing/indirect exposure at any date.
# This changes the target population and must be reported; it is not the same
# sample rule as the Python cohort-window estimator.
clean <- names(which(tapply(d$spillover, d$unit, max) == 0))
d <- d[d$unit %in% clean, ]
if (length(unique(d$cluster)) < 20L) stop("Insufficient spatial clusters for this specification")
d$unit_id <- as.integer(factor(d$unit))
d$cluster_id <- as.integer(factor(d$cluster))
set.seed(20261116)
fit <- did::att_gt(
  yname = "outcome", tname = "period", idname = "unit_id", gname = "first_treat",
  xformla = ~ baseline_outcome + population_density + poverty_rate + no_vehicle_share,
  data = d, panel = TRUE, allow_unbalanced_panel = FALSE,
  control_group = "notyettreated", anticipation = 1,
  est_method = "dr", base_period = "universal",
  bstrap = TRUE, cband = TRUE, biters = 999,
  clustervars = c("unit_id", "cluster_id")
)
dynamic <- did::aggte(fit, type = "dynamic", min_e = -6, max_e = 6)
dir.create("outputs/private", recursive = TRUE, showWarnings = FALSE)
saveRDS(list(group_time = fit, dynamic = dynamic), "outputs/private/did_results.rds")
capture.output(summary(fit), summary(dynamic), sessionInfo(),
               file = "outputs/private/did_summary.txt")
message("Saved privately. Check support, pretrends, assumptions and licenses before release.")
