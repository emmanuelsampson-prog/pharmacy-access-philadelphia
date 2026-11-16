"""Transparent unadjusted cohort-time DiD with explicit clean-control selection.

This is NOT the doubly robust Callaway-Sant'Anna estimator. It implements the
simple mean-change identifying contrast. Conditional adjustment and the choice
of defensible controls require the research protocol, not a causal label.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED={"unit","period","first_treat","outcome","spillover","cluster"}

def validate_panel(panel):
    missing=REQUIRED-set(panel.columns)
    if missing:raise ValueError(f"Missing columns: {sorted(missing)}")
    if panel.empty:raise ValueError("No panel rows; verified dates and mobility outcomes required")
    if panel[list(REQUIRED)].isna().any().any():raise ValueError("Missing panel values are not zero")
    if panel.duplicated(["unit","period"]).any():raise ValueError("Duplicate unit-period")
    if not np.isfinite(panel[["period","first_treat","outcome"]].to_numpy(dtype=float)).all():raise ValueError("Nonfinite numeric value")
    if not panel.spillover.isin([0,1]).all():raise ValueError("spillover must be binary")
    if (panel.first_treat<0).any():raise ValueError("first_treat=0 means never treated; use positive integer periods")
    if (panel.period<1).any() or not (panel.period%1==0).all() or not (panel.first_treat%1==0).all():
        raise ValueError("Use integer month/week indexes beginning at 1")
    for column in ["first_treat","cluster"]:
        if panel.groupby("unit")[column].nunique().max()!=1:raise ValueError(f"{column} must be fixed within unit")
    times=sorted(panel.period.unique())
    if times!=list(range(times[0],times[-1]+1)):raise ValueError("Periods must be consecutive")
    if (panel.groupby("unit").size()!=len(times)).any():raise ValueError("Panel must be balanced; do not fill suppressed counts with zero")

def cohort_time_did(panel,horizons=range(-6,7),anticipation=1,min_group=5):
    validate_panel(panel)
    if anticipation<0:raise ValueError("anticipation must be nonnegative")
    outcome=panel.pivot(index="unit",columns="period",values="outcome")
    exposure=panel.pivot(index="unit",columns="period",values="spillover")
    meta=panel.groupby("unit").first().reindex(outcome.index)
    rows=[]
    for g in sorted(meta.loc[meta.first_treat>0,"first_treat"].unique()):
        base=int(g)-anticipation-1
        for event_time in horizons:
            t=int(g)+event_time
            if base not in outcome.columns or t not in outcome.columns:continue
            # Exclude the anticipation interval and reference period from effect contrasts.
            if -anticipation-1<=event_time<0:continue
            window=[p for p in outcome.columns if min(base,t)<=p<=max(base,t)]
            clean=(exposure[window].max(axis=1)==0)
            # Exclude ANY separately flagged competing/indirect closure exposure from treated and control.
            treated=(meta.first_treat==g)&clean
            controls=((meta.first_treat==0)|(meta.first_treat>max(base,t)+anticipation))&(meta.first_treat!=g)&clean
            changes=outcome[t]-outcome[base]
            nt,nc=int(treated.sum()),int(controls.sum())
            supported=nt>=min_group and nc>=min_group
            estimate=float(changes[treated].mean()-changes[controls].mean()) if supported else np.nan
            rows.append(dict(cohort=int(g),period=t,event_time=event_time,reference_period=base,
                n_treated=nt,n_control=nc,att=estimate,
                status="estimated" if supported else "insufficient_clean_support"))
    return pd.DataFrame(rows)

def event_summary(estimates):
    valid=estimates[estimates.status=="estimated"]
    rows=[]
    for event_time,frame in valid.groupby("event_time"):
        rows.append(dict(event_time=int(event_time),att=float(np.average(frame.att,weights=frame.n_treated)),
            cohort_count=len(frame),treated_contributions=int(frame.n_treated.sum())))
    return pd.DataFrame(rows)

def spatial_cluster_bootstrap(panel,horizons=range(-6,7),repetitions=499,seed=20261116):
    validate_panel(panel)
    clusters=panel.cluster.unique()
    if len(clusters)<20:raise ValueError("Fewer than 20 spatial clusters: redesign inference before estimating intervals")
    rng=np.random.default_rng(seed);draws=[]
    for b in range(repetitions):
        pieces=[]
        for j,c in enumerate(rng.choice(clusters,size=len(clusters),replace=True)):
            part=panel[panel.cluster==c].copy()
            part["unit"]=str(j)+"_"+part.unit.astype(str)
            pieces.append(part)
        estimate=cohort_time_did(pd.concat(pieces,ignore_index=True),horizons)
        if estimate.empty:continue
        dynamic=event_summary(estimate)
        if not dynamic.empty:dynamic["bootstrap"]=b;draws.append(dynamic)
    if not draws:raise ValueError("No bootstrap support")
    draws=pd.concat(draws)
    summary=draws.groupby("event_time").att.agg(
        ci_low=lambda x:x.quantile(.025),ci_high=lambda x:x.quantile(.975),valid_draws="count").reset_index()
    # Missing support is reported; intervals require adequate replication.
    summary.loc[summary.valid_draws<.9*repetitions,["ci_low","ci_high"]]=np.nan
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel",required=True,type=Path)
    args=parser.parse_args()
    panel=pd.read_csv(args.panel,dtype={"unit":str,"cluster":str})
    estimates=cohort_time_did(panel)
    if estimates.empty:raise ValueError("No supported cohort-time windows")
    out=Path(__file__).resolve().parents[1]/"outputs/private";out.mkdir(parents=True,exist_ok=True)
    estimates.to_csv(out/"cohort_time_did.csv",index=False)
    event_summary(estimates).to_csv(out/"event_study.csv",index=False)
    spatial_cluster_bootstrap(panel).to_csv(out/"event_study_intervals.csv",index=False)
    print("Estimates saved privately. Validate parallel trends, selection, and privacy before publication.")

if __name__=="__main__":main()
