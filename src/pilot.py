"""Run the public scenario, spatial ML benchmark and report-ready figures."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm,ListedColormap
from src.accessibility import prepare
from src.ml import run_ml
from src.emissions import incremental_co2_kg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/public"
TEAL="#087e8b";NAVY="#172d45";ORANGE="#d96832"

def weighted_mean(values,weights):
    valid=np.isfinite(values)&np.isfinite(weights)&(weights>0)
    return float(np.average(np.asarray(values)[valid],weights=np.asarray(weights)[valid])) if valid.any() else None

def summarize(tracts,qa,metrics):
    df=tracts[tracts.population>0].copy()
    pop=float(df.population.sum())
    summary=dict(status="MODELED SCENARIO; NOT A HISTORICAL OR CAUSAL EFFECT",**qa,
        acs_population_included=int(pop),
        populated_tracts_with_any_increase=int((df.all_listed_delta_m>1).sum()),
        population_in_tracts_with_any_increase=int(df.loc[df.all_listed_delta_m>1,"population"].sum()),
        population_weighted_increment_m=weighted_mean(df.all_listed_delta_m,df.population),
        population_weighted_baseline_m=weighted_mean(df.all_listed_before_m,df.population),
        population_weighted_remaining_m=weighted_mean(df.all_listed_after_m,df.population),
        no_vehicle_household_weighted_increment_m=weighted_mean(df.all_listed_delta_m,df.no_vehicle_households),
        population_weighted_chain_inventory_increment_m=weighted_mean(df.chain_names_delta_m,df.population),
        nj_border_tracts_excluded_from_ml=int(df.near_nj_2km.sum()),
        nonborder_population_weighted_increment_m=weighted_mean(df.loc[~df.near_nj_2km,"all_listed_delta_m"],df.loc[~df.near_nj_2km,"population"]),
        ml=metrics.to_dict(orient="records"))
    rows=[]
    for label,mask in [("All populated tracts",np.ones(len(df),dtype=bool)),
        ("Poverty rate at least 20%",df.poverty_rate>=.2),
        ("Poverty rate below 20%",df.poverty_rate<.2),
        ("No-vehicle share at least 30%",df.no_vehicle_share>=.3),
        ("No-vehicle share below 30%",df.no_vehicle_share<.3),
        ("Age 65+ share at least 20%",df.age65plus_share>=.2),
        ("Non-Hispanic Black share at least 50%",df.black_share>=.5),
        ("Hispanic share at least 50%",df.hispanic_share>=.5)]:
        g=df.loc[mask]
        rows.append(dict(group=label,n_tracts=len(g),population=int(g.population.sum()),
            population_weighted_increment_m=weighted_mean(g.all_listed_delta_m,g.population)))
    equity=pd.DataFrame(rows);equity.to_csv(OUT/"equity_scenario.csv",index=False)
    assumptions=[]
    delta=summary["population_weighted_increment_m"]
    for car_share in [.25,.5,.75,1.]:
        for detour in [1.,1.3,1.6]:
            for additional in [.5,1.]:
                kg=incremental_co2_kg(delta,trips=1000,car_share=car_share,detour_factor=detour,additional_trip_share=additional)
                assumptions.append(dict(hypothetical_person_round_trips=1000,car_share=car_share,
                    detour_factor=detour,additional_trip_share=additional,occupants_per_vehicle=1,
                    gasoline_vehicle_g_co2_mile=400,additional_tailpipe_co2_kg=float(kg),
                    status="scenario only; no observed trip/mode/emissions data"))
    pd.DataFrame(assumptions).to_csv(OUT/"emissions_sensitivity.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    return summary,equity

def figures(tracts,pharmacies,metrics,equity):
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig,axs=plt.subplots(1,2,figsize=(12,7.4))
    cmap=ListedColormap(["#edf4f4","#bfdfdc","#66b9b1","#178d90","#175468"])
    bounds=[0,1,100,250,500,10000]
    populated=tracts[tracts.population>0]
    tracts.plot(ax=axs[0],facecolor="#f5f1e9",edgecolor="white",linewidth=.2)
    populated.plot(ax=axs[0],column="all_listed_delta_m",cmap=cmap,norm=BoundaryNorm(bounds,cmap.N),edgecolor="white",linewidth=.2)
    rites=pharmacies[pharmacies.is_rite_aid&pharmacies.inside_philadelphia]
    rites.plot(ax=axs[0],color=ORANGE,markersize=10,alpha=.8,label="Rite Aid-labelled license")
    axs[0].legend(loc="lower left",frameon=False,fontsize=8)
    axs[0].set_title("Where potential access changes\nAll-listed inventory scenario",color=NAVY,pad=14)
    tracts.plot(ax=axs[1],column="no_vehicle_share",cmap="YlOrBr",vmin=0,vmax=.8,edgecolor="white",linewidth=.2,
        legend=True,legend_kwds={"label":"Share of households without a vehicle","shrink":.55})
    axs[1].set_title("Households without a vehicle\n2018-2022 ACS context",color=NAVY,pad=14)
    for ax in axs:
        ax.set_axis_off()
    from matplotlib.patches import Patch
    labels=["0-1 m","1-100 m","100-250 m","250-500 m",">500 m"]
    fig.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(cmap.colors,labels)],loc="lower center",ncol=5,bbox_to_anchor=(.29,.075),frameon=False,title="Modeled one-way straight-line increase")
    fig.suptitle("Pharmacy access under a hypothetical Rite Aid removal",fontsize=17,color=NAVY,x=.5,y=.98)
    fig.text(.5,.025,"License roster is not a verified operating network. Tract centroids are not residents' homes. NJ alternatives are missing.",ha="center",fontsize=9,color="#555555")
    fig.subplots_adjust(bottom=.18,top=.84,wspace=.1)
    fig.savefig(OUT/"access_equity_map.png",dpi=180,bbox_inches="tight");plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,4.8))
    p=metrics.sort_values("mae_m")
    axs[0].barh(p.model,p.mae_m,color=[TEAL if n=="Random forest" else "#9eb4bc" for n in p.model])
    for i,v in enumerate(p.mae_m):axs[0].text(v+2,i,f"{v:.1f}",va="center")
    axs[0].set_xlim(0,p.mae_m.max()*1.25)
    axs[0].set_xlabel("Held-out MAE (meters); lower is better")
    axs[0].set_title("Does machine learning improve prediction?",color=NAVY)
    e=equity.iloc[1:5].copy()
    axs[1].barh(["Poverty >=20%","Poverty <20%","No vehicle >=30%","No vehicle <30%"],e.population_weighted_increment_m,color=[TEAL,"#b2c9cb",ORANGE,"#e6c2b0"])
    axs[1].set_xlabel("Population-weighted scenario increase (meters)")
    axs[1].set_title("Neighborhood context",color=NAVY)
    fig.text(.5,.015,"Prediction target is modeled access change, not observed travel. Equity groups describe areas, not individuals.",ha="center",fontsize=9,color="#555555")
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(OUT/"model_and_equity.png",dpi=180,bbox_inches="tight");plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    tracts,pharmacies,qa=prepare()
    metrics,_=run_ml(tracts,OUT)
    summary,equity=summarize(tracts,qa,metrics)
    figures(tracts,pharmacies,metrics,equity)
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
