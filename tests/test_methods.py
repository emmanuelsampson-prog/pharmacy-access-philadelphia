import numpy as np
import pandas as pd
import pytest
from src.accessibility import nearest_distances
from src.emissions import incremental_co2_kg
from src.causal import cohort_time_did,validate_panel
from src.mobility import expand_home_counts,home_distance_proxy,validate_closure_events
from src.ml import spatial_splits

def test_removal_can_only_increase_nearest_distance():
    origins=np.array([[0,0],[8,0]])
    before,_=nearest_distances(origins,[[0,0],[10,0]])
    after,_=nearest_distances(origins,[[10,0]])
    np.testing.assert_allclose(before,[0,2]);np.testing.assert_allclose(after,[10,2])
    assert (after>=before).all()

def test_empty_destinations_raise():
    with pytest.raises(ValueError):nearest_distances([[0,0]],np.empty((0,2)))

def test_emissions_units_and_trip_chaining():
    assert incremental_co2_kg(1609.344,detour_factor=1)==pytest.approx(.8)
    assert incremental_co2_kg(1609.344,detour_factor=1,additional_trip_share=.5)==pytest.approx(.4)
    assert incremental_co2_kg(500,car_share=0)==0
    with pytest.raises(ValueError):incremental_co2_kg(-1)

def fixture_panel():
    # Synthetic fixture ONLY: no Philadelphia empirical effects are generated.
    rows=[]
    for i in range(60):
        g=8 if i<20 else 12 if i<40 else 0
        for t in range(1,17):
            effect=5 if g and t>=g else 0
            rows.append(dict(unit=str(i),period=t,first_treat=g,outcome=i*.1+t*.2+effect,spillover=0,cluster=str(i//2)))
    return pd.DataFrame(rows)

def test_cohort_time_recovers_known_effect_and_null_pretrend():
    r=cohort_time_did(fixture_panel(),horizons=[-4,0,2])
    np.testing.assert_allclose(r.loc[r.event_time>=0,"att"],5,atol=1e-12)
    np.testing.assert_allclose(r.loc[r.event_time<0,"att"],0,atol=1e-12)

def test_spillover_contaminated_controls_excluded():
    panel=fixture_panel()
    mask=panel.unit.astype(int).between(40,49)&(panel.period>=8)
    panel.loc[mask,"outcome"]+=100;panel.loc[mask,"spillover"]=1
    r=cohort_time_did(panel,horizons=[0])
    np.testing.assert_allclose(r.att,5,atol=1e-12)

def test_already_treated_never_used_as_controls():
    r=cohort_time_did(fixture_panel(),horizons=[0])
    assert r.loc[r.cohort==12,"n_control"].item()==20

def test_unbalanced_panel_and_missing_are_rejected():
    with pytest.raises(ValueError):validate_panel(fixture_panel().iloc[1:])
    panel=fixture_panel();panel.loc[0,"outcome"]=np.nan
    with pytest.raises(ValueError):validate_panel(panel)

def test_suppression_stays_missing_and_geoids_stay_strings():
    frame=pd.DataFrame([dict(poi_id="x",period="2022-01",home_counts='{"010010201001": null, "421010001001": 10}',coverage_ok=True,source_product="test")])
    rows=expand_home_counts(frame)
    assert rows.origin_geoid.tolist()==["421010001001"]
    assert rows.visitor_poi_count.tolist()==[10.]

def test_unmatched_distance_cannot_silently_drop():
    flows=pd.DataFrame([dict(origin_geoid="421010001001",poi_id="x",period=1,visitor_poi_count=10)])
    od=pd.DataFrame(columns=["origin_geoid","poi_id","distance_m"])
    with pytest.raises(ValueError):home_distance_proxy(flows,od)

def test_unverified_dates_not_allowed():
    e=pd.DataFrame([dict(poi_id="a",pharmacy_last_open_date="2025-06-01",pharmacy_first_closed_date="2025-06-02",source_url="https://example.org",date_quality="unverified")])
    with pytest.raises(ValueError):validate_closure_events(e)

def test_spatial_holdout_has_no_near_training_points():
    from scipy.spatial import cKDTree
    xy=np.random.default_rng(1).uniform(0,20000,size=(300,2))
    for _,train,test in spatial_splits(xy):
        assert not set(train)&set(test)
        assert cKDTree(xy[test]).query(xy[train])[0].min()>=1000
