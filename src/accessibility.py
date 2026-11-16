"""Public-data scenario: remove Rite Aid-labelled license entries.

Not a reconstruction of the 2023-2025 operating network or a causal estimate.
All distances use EPSG:26918 metres, never longitude/latitude as planar units.
"""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
CRS = "EPSG:26918"

def nearest_distances(origins, destinations):
    origins = np.asarray(origins,dtype=float)
    destinations = np.asarray(destinations,dtype=float)
    if origins.ndim != 2 or destinations.ndim != 2 or origins.shape[1] != 2 or destinations.shape[1] != 2:
        raise ValueError("Expected two-column projected coordinates")
    if len(destinations)==0: raise ValueError("No candidate destinations")
    if not np.isfinite(origins).all() or not np.isfinite(destinations).all():
        raise ValueError("Coordinates must be finite")
    return cKDTree(destinations).query(origins,k=1)

def clean_acs(path):
    rows=json.loads(Path(path).read_text())
    df=pd.DataFrame(rows[1:],columns=rows[0])
    df["GEOID"]=df["state"]+df["county"]+df["tract"]
    for c in df.columns:
        if re.fullmatch(r"B\d+_\d+[EM]", c):
            df[c]=pd.to_numeric(df[c],errors="coerce")
            df.loc[df[c]<0,c]=np.nan  # Census suppression / annotation sentinel
    df["population"]=df.B01003_001E
    df["households"]=df.B08201_001E
    df["no_vehicle_households"]=df.B08201_002E
    df["poverty_rate"]=df.B17001_002E / df.B17001_001E.replace(0,np.nan)
    df["no_vehicle_share"]=df.B08201_002E / df.B08201_001E.replace(0,np.nan)
    df["median_income"]=df.B19013_001E
    df["black_share"]=df.B03002_004E / df.B03002_001E.replace(0,np.nan)
    df["hispanic_share"]=df.B03002_012E / df.B03002_001E.replace(0,np.nan)
    elder=[f"B01001_{i:03d}E" for i in [20,21,22,23,24,25,44,45,46,47,48,49]]
    df["age65plus"]=df[elder].sum(axis=1,min_count=len(elder))
    df["age65plus_share"]=df.age65plus/df.population.replace(0,np.nan)
    return df

def clean_pharmacies(path):
    df=pd.read_csv(path,dtype=str).rename(columns={
        "License Number":"license_id", "Pharmacy Name":"name", "Address":"address",
        "City":"city", "State":"state", "Zip Code":"zip", "County":"county",
        "Georeferenced Latitude & Longitude":"wkt"})
    raw_n=len(df)
    def parse(value):
        try:
            geom=wkt.loads(value)
            if geom.geom_type=="Point" and -81<geom.x<-74 and 39<geom.y<43:return geom
        except (TypeError,ValueError): pass
        return None
    df["geometry"]=df.wkt.map(parse)
    missing=int(df.geometry.isna().sum())
    df=df.dropna(subset=["geometry"]).copy()
    df["is_rite_aid"]=df.name.str.contains(r"RITE\s*AID",case=False,na=False,regex=True)
    # Compare inclusive and restricted chain-name inventories; neither gives formal bounds.
    # Neither is a manually verified community-pharmacy inventory.
    df["chain_name_match"]=df.name.str.contains(
        r"RITE\s*AID|CVS|WALGREEN|WAL.MART|WALMART|TARGET|ACME|GIANT|SHOPRITE|COSTCO|SAM.S CLUB|WEGMAN",case=False,na=False,regex=True)
    df["normalized_address"]=df.address.fillna("").str.upper().str.replace(r"[^A-Z0-9]","",regex=True)
    df["location_key"]=df.normalized_address+"|"+df.city.fillna("").str.upper()
    dup=int(df.duplicated("license_id").sum())
    df=df.drop_duplicates("license_id").copy()
    # Flag collisions; do not collapse different names/sites based on a rounded geocode.
    df["shared_geocode"]=df.wkt.duplicated(keep=False)
    df["shared_address"]=df.location_key.duplicated(keep=False)
    out=gpd.GeoDataFrame(df,geometry="geometry",crs="EPSG:4326").to_crs(CRS)
    return out,dict(registry_rows=raw_n,invalid_or_missing_coordinates=missing,
                    duplicate_licenses_removed=dup,shared_geocode_rows=int(df.shared_geocode.sum()),
                    shared_address_rows=int(df.shared_address.sum()))

def prepare():
    out=ROOT/"data/processed";out.mkdir(parents=True,exist_ok=True)
    shapes=gpd.read_file(ROOT/"data/raw/cb_2022_42_tract_500k.zip")
    shapes=shapes[shapes.COUNTYFP=="101"].to_crs(CRS)
    acs=clean_acs(ROOT/"data/raw/acs_2022_philadelphia.json")
    tracts=shapes.merge(acs,on="GEOID",how="left",validate="one_to_one",suffixes=("_shape",""))
    if tracts.population.isna().any(): raise ValueError("ACS join missing population; inspect geography")
    tracts["area_km2"]=pd.to_numeric(tracts.ALAND)/1e6
    tracts["population_density"]=tracts.population/tracts.area_km2.replace(0,np.nan)
    centroids=tracts.geometry.centroid
    tracts["origin_x"]=centroids.x;tracts["origin_y"]=centroids.y
    ll=gpd.GeoSeries(centroids,crs=CRS).to_crs(4326)
    tracts["origin_lon"]=ll.x;tracts["origin_lat"]=ll.y
    nj_counties=gpd.read_file(ROOT/"data/raw/cb_2022_us_county_500k.zip")
    nj=nj_counties[nj_counties.STATEFP=="34"].to_crs(CRS).geometry.union_all()
    tracts["near_nj_2km"]=centroids.distance(nj)<2000
    pharmacies,qa=clean_pharmacies(ROOT/"data/raw/pa_pharmacies.csv")
    city=tracts.geometry.union_all()
    # PA sites in a 10 km buffer include nearby suburban alternatives; NJ is flagged as missing.
    pharmacies=pharmacies[pharmacies.geometry.distance(city)<=10000].copy()
    pharmacies["inside_philadelphia"]=pharmacies.geometry.covered_by(city)
    qa.update(tracts_total=len(tracts),tracts_populated=int((tracts.population>0).sum()),
              study_buffer_registry_sites=len(pharmacies),
              rite_aid_labelled_buffer_sites=int(pharmacies.is_rite_aid.sum()),
              philadelphia_registry_sites=int(pharmacies.inside_philadelphia.sum()),
              rite_aid_labelled_philadelphia_sites=int((pharmacies.is_rite_aid & pharmacies.inside_philadelphia).sum()))
    xy=tracts[["origin_x","origin_y"]].to_numpy()
    for label,mask in [("all_listed",np.ones(len(pharmacies),dtype=bool)),("chain_names",pharmacies.chain_name_match.to_numpy())]:
        baseline=pharmacies.loc[mask]
        remaining=baseline[~baseline.is_rite_aid]
        before,nearest=nearest_distances(xy,np.c_[baseline.geometry.x,baseline.geometry.y])
        after,_=nearest_distances(xy,np.c_[remaining.geometry.x,remaining.geometry.y])
        tracts[label+"_before_m"]=before;tracts[label+"_after_m"]=after
        tracts[label+"_delta_m"]=np.maximum(after-before,0)
        if (after+1e-6<before).any():raise AssertionError("Removing destinations improved minimum distance")
    # Baseline supply features for ML. The target's nearest surviving distance is never a feature.
    coords=np.c_[pharmacies.geometry.x,pharmacies.geometry.y]
    tracts["baseline_sites_1km"]=[len(v) for v in cKDTree(coords).query_ball_point(xy,1000)]
    rites=pharmacies[pharmacies.is_rite_aid]
    tracts["rite_aid_sites_1km"]=[len(v) for v in cKDTree(np.c_[rites.geometry.x,rites.geometry.y]).query_ball_point(xy,1000)]
    tracts["any_increase"]=tracts.all_listed_delta_m>1
    tracts["scenario_status"]="hypothetical removal from license roster; not historical effect"
    tracts.to_crs(4326).to_file(out/"tract_scenarios.geojson",driver="GeoJSON")
    tracts.drop(columns="geometry").to_csv(out/"tract_scenarios.csv",index=False)
    pharmacies.to_crs(4326).drop(columns="wkt").to_file(out/"pharmacy_candidates.geojson",driver="GeoJSON")
    ledger=pharmacies[pharmacies.is_rite_aid].drop(columns=["geometry","wkt"]).copy()
    for c in ["pharmacy_last_open_date","pharmacy_first_closed_date","front_store_close_date","source_url","verified_by","replacement_open_date"]:ledger[c]=""
    ledger["date_quality"]="unverified";ledger["event_type"]="closure_candidate"
    ledger["evidence_note"]="Rite Aid name in license roster; no verified store-level operating date"
    ledger.to_csv(out/"closure_candidates_unverified.csv",index=False)
    (out/"data_quality.json").write_text(json.dumps(qa,indent=2)+"\n")
    return tracts,pharmacies,qa
