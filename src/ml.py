"""Spatially held-out ML benchmark for a modeled vulnerability target."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.base import clone
from sklearn.cluster import KMeans
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES=["population_density","median_income","poverty_rate","no_vehicle_share",
          "age65plus_share","baseline_sites_1km","rite_aid_sites_1km","all_listed_before_m"]
SEED=20261116

def spatial_splits(xy,n_splits=5,buffer_m=1000):
    xy=np.asarray(xy,dtype=float)
    groups=KMeans(n_clusters=n_splits,random_state=SEED,n_init=20).fit_predict(xy)
    for fold in range(n_splits):
        test=np.flatnonzero(groups==fold)
        candidates=np.flatnonzero(groups!=fold)
        nearest=cKDTree(xy[test]).query(xy[candidates],k=1)[0]
        train=candidates[nearest>=buffer_m]
        if len(train)<30 or len(test)<10:raise ValueError("Insufficient spatial fold support")
        yield fold,train,test

def run_ml(tracts,outdir):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    frame=tracts[(tracts.population>0)&~tracts.near_nj_2km].copy().reset_index(drop=True)
    X=frame[FEATURES];y=frame.all_listed_delta_m.to_numpy()
    xy=frame[["origin_x","origin_y"]].to_numpy()
    models={
        "Median baseline":make_pipeline(SimpleImputer(strategy="median"),DummyRegressor(strategy="median")),
        "Ridge":make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),Ridge(alpha=10)),
        "Random forest":make_pipeline(SimpleImputer(strategy="median"),RandomForestRegressor(
            n_estimators=300,min_samples_leaf=8,max_features=.8,random_state=SEED,n_jobs=2))}
    predictions=[];scores=[];importances=[]
    for fold,train,test in spatial_splits(xy):
        for name,prototype in models.items():
            model=clone(prototype).fit(X.iloc[train],y[train])
            pred=np.maximum(model.predict(X.iloc[test]),0)
            scores.append(dict(model=name,fold=fold,n_train=len(train),n_test=len(test),
                mae_m=mean_absolute_error(y[test],pred),rmse_m=np.sqrt(mean_squared_error(y[test],pred))))
            for idx,prediction in zip(test,pred):
                predictions.append(dict(GEOID=frame.loc[idx,"GEOID"],fold=fold,model=name,
                    observed_scenario_m=float(y[idx]),predicted_scenario_m=float(prediction)))
            if name=="Random forest":
                perm=permutation_importance(model,X.iloc[test],y[test],scoring="neg_mean_absolute_error",n_repeats=10,random_state=SEED)
                importances.extend(dict(fold=fold,feature=f,increase_mae_m=float(v)) for f,v in zip(FEATURES,perm.importances_mean))
    prediction_frame=pd.DataFrame(predictions)
    summary=[]
    for name,p in prediction_frame.groupby("model"):
        actual=p.observed_scenario_m.to_numpy();pred=p.predicted_scenario_m.to_numpy()
        summary.append(dict(model=name,n=len(p),mae_m=mean_absolute_error(actual,pred),
            rmse_m=np.sqrt(mean_squared_error(actual,pred)),r2=r2_score(actual,pred),
            validation="5 contiguous spatial folds; 1 km training exclusion buffer",
            target="hypothetical nearest-distance increase; not observed travel"))
    pd.DataFrame(scores).to_csv(outdir/"ml_fold_metrics.csv",index=False)
    pd.DataFrame(summary).to_csv(outdir/"ml_metrics.csv",index=False)
    prediction_frame.to_csv(outdir/"ml_out_of_fold.csv",index=False)
    pd.DataFrame(importances).to_csv(outdir/"ml_permutation_importance.csv",index=False)
    return pd.DataFrame(summary),prediction_frame
