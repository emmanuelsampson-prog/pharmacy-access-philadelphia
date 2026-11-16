"""Validate a licensed export without treating suppression as zero.

Only normalized AGGREGATED records are accepted. This module neither requests
nor publishes individual device trajectories. Provider field definitions must
be checked against the exact licensed product before making a crosswalk.
"""
import json
import numpy as np
import pandas as pd

def expand_home_counts(frame, geoid_digits=12):
    """Expand provider POI-period home-area counts; no unique-person interpretation.

    Input: poi_id, period, home_counts (JSON object), coverage_ok (bool),
    and source_product. Output counts remain vendor estimates/sample counts;
    a person's visits to different POIs may be counted repeatedly.
    """
    required={"poi_id","period","home_counts","coverage_ok","source_product"}
    if not required.issubset(frame):raise ValueError(f"Missing fields {required-set(frame)}")
    if frame.duplicated(["poi_id","period"]).any():raise ValueError("Duplicate POI-period records")
    if not frame.coverage_ok.isin([True,False]).all():raise ValueError("coverage_ok must be boolean")
    rows=[]
    for r in frame.itertuples():
        if not r.coverage_ok or pd.isna(r.home_counts):continue
        counts=json.loads(r.home_counts) if isinstance(r.home_counts,str) else r.home_counts
        if not isinstance(counts,dict):raise ValueError("home_counts must be a JSON mapping")
        for origin,value in counts.items():
            if not isinstance(origin,str) or len(origin)!=geoid_digits or not origin.isdigit():
                raise ValueError(f"Expected a {geoid_digits}-digit GEOID string; verify vendor geography vintage")
            if value is None:continue # suppressed/unknown is missing
            count=float(value)
            if not np.isfinite(count) or count<0:raise ValueError("Invalid origin count")
            rows.append(dict(poi_id=r.poi_id,period=r.period,origin_geoid=origin,
                visitor_poi_count=count,source_product=r.source_product))
    return pd.DataFrame(rows,columns=["poi_id","period","origin_geoid","visitor_poi_count","source_product"])

def home_distance_proxy(flows,od_distances):
    """Visitor-POI-count-weighted home-origin separation; not observed trip distance.

    od_distances must use independently calculated nonnegative metres from
    home-area origins to POIs. An unmatched OD pair raises instead of disappearing.
    """
    merged=flows.merge(od_distances,on=["origin_geoid","poi_id"],how="left",validate="many_to_one")
    if merged.distance_m.isna().any():raise ValueError("Missing OD distances")
    if not np.isfinite(merged.distance_m).all() or (merged.distance_m<0).any():raise ValueError("Invalid OD distances")
    merged["numerator"]=merged.visitor_poi_count*merged.distance_m
    result=merged.groupby(["origin_geoid","period"],as_index=False).agg(
        total_visitor_poi_count=("visitor_poi_count","sum"),distance_numerator=("numerator","sum"))
    result["home_to_poi_proxy_m"]=result.distance_numerator/result.total_visitor_poi_count.replace(0,np.nan)
    return result

def validate_closure_events(events):
    required={"poi_id","pharmacy_last_open_date","pharmacy_first_closed_date","source_url","date_quality"}
    if not required.issubset(events):raise ValueError("Missing closure verification fields")
    if events.empty:raise ValueError("No verified closure events")
    if events[list(required)].isna().any().any() or (events[list(required)].astype(str)=="").any().any():
        raise ValueError("All closure fields must be completed")
    if not events.date_quality.eq("verified").all():raise ValueError("Unverified events are ineligible")
    if events.poi_id.duplicated().any():raise ValueError("Use one permanent closure per POI; adjudicate reopenings")
    last=pd.to_datetime(events.pharmacy_last_open_date,errors="raise")
    closed=pd.to_datetime(events.pharmacy_first_closed_date,errors="raise")
    if (closed<=last).any():raise ValueError("First closed date must be after last open date")
    if ((closed-last).dt.days>7).any():raise ValueError("Closure interval exceeds one week; use interval sensitivity, not false exact timing")
    return events.copy()
