"""Tract choropleths for existing access estimates; no new route calculations."""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from src.cartography import map_furniture, tract_background

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'
INK = '#183b43'
GRAY = '#e5e8e9'


def access_maps(main, tracts=None, records=None):
    """Join each eligible origin's result to its own tract, leaving others missing."""
    if tracts is None:
        tracts = gpd.read_file(ROOT / 'data/processed/tract_scenarios.geojson').to_crs(26918)
    if records is None:
        records = pd.read_csv(ROOT / 'data/processed/before_after_access_origins.csv', dtype={'GEOID': str})
    cols = ['GEOID', 'walk_before_minutes', 'walk_after_minutes', 'walk_delta_minutes']
    areas = tracts[['GEOID', 'geometry']].merge(main[cols], on='GEOID', how='left', validate='one_to_one')
    included = areas.loc[areas.walk_before_minutes.notna()].copy()
    assert len(included) == len(main) == main.GEOID.nunique()
    assert np.isfinite(included[cols[1:]]).all().all()
    excluded_ids = records.loc[records.unresolved_address_conflict & records.distance_to_former_m.le(800), 'GEOID']
    disputed = areas.loc[areas.GEOID.isin(excluded_ids)]
    boundary = tracts.dissolve()
    bounds = boundary.total_bounds

    def base(ax):
        tract_background(ax, tracts, facecolor=GRAY, edgecolor='#ffffff', linewidth=.35)
        if not disputed.empty:
            disputed.plot(ax=ax, facecolor=GRAY, edgecolor='#64747b', linewidth=.5, hatch='////', zorder=3)
        map_furniture(ax, bounds)
        ax.set_axis_off()

    colors = ['#fff2b2', '#fed476', '#fca34e', '#ef6b35', '#ca3828', '#8e1024']
    bins = [0, 5, 10, 15, 20, 30, 60]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bins, cmap.N, clip=True)
    assert included[['walk_before_minutes', 'walk_after_minutes']].max().max() <= bins[-1]
    fig = plt.figure(figsize=(11.6, 7.8), facecolor='white')
    axes = [fig.add_axes([.025, .25, .46, .58]), fig.add_axes([.515, .25, .46, .58])]
    for ax, phase, label in zip(axes, ['before', 'after'], ['Before: former Rite Aid', 'After: designated recipient']):
        base(ax)
        included.plot(ax=ax, column=f'walk_{phase}_minutes', cmap=cmap, norm=norm,
                      edgecolor='#ffffff', linewidth=.55, zorder=2)
        boundary.boundary.plot(ax=ax, color='#75878b', linewidth=.8, zorder=4)
        ax.set_title(label, loc='left', fontsize=13, color=INK, fontweight='bold', pad=7)
    fig.text(.025, .96, 'Walking access before and after pharmacy transfers', fontsize=18, fontweight='bold', color=INK)
    fig.text(.025, .913, 'Philadelphia, 2025  |  The same 62 tracts and color intervals in both panels', fontsize=11, color='#4e6268')
    labels = ['0–<5 min', '5–<10 min', '10–<15 min', '15–<20 min', '20–<30 min', '30–60 min']
    fig.legend([Patch(facecolor=c) for c in colors], labels, loc='lower center',
               bbox_to_anchor=(.5, .133), ncol=6, frameon=False, fontsize=10.5,
               title='Modeled walking time, one way', title_fontsize=11)
    fig.legend([Patch(facecolor=GRAY, edgecolor='#aeb9bd'),
                Patch(facecolor=GRAY, edgecolor='#64747b', hatch='////')],
               ['Other tracts: not analyzed', 'Address conflict: excluded'],
               loc='lower center', bbox_to_anchor=(.5, .075), ncol=2, frameon=False, fontsize=10)
    fig.text(.5, .043, 'Each shaded tract displays its center’s route estimate; travel time varies within a tract.',
             ha='center', fontsize=10, color='#4e6268')
    fig.text(.5, .016, 'Walking speed: 4.8 km/h. Sources: Census, Rite Aid transfer records, PA roster and OpenStreetMap.',
             ha='center', fontsize=9, color='#4e6268')
    fig.savefig(OUT / 'before_after_walking_map.png', dpi=200)
    plt.close(fig)

    # Match the report's one-meter tolerance for unchanged walking distance.
    tolerance = .001 / 4.8 * 60
    delta = included.walk_delta_minutes
    included['change_class'] = np.select(
        [delta < -5, delta < -tolerance, delta.abs() <= tolerance,
         delta <= 5, delta <= 15, delta <= 30], [0, 1, 2, 3, 4, 5], default=6)
    change_colors = ['#11676c', '#8cc6c3', '#fff7df', '#f9c7a9', '#ef955c', '#ce502e', '#862126']
    change_labels = ['More than 5 min shorter', 'Up to 5 min shorter', 'Unchanged (within 1 meter)',
                     'Up to 5 min longer', 'Over 5 to 15 min longer',
                     'Over 15 to 30 min longer', 'More than 30 min longer']
    fig = plt.figure(figsize=(9.4, 7.6), facecolor='white')
    ax = fig.add_axes([.02, .12, .59, .71])
    base(ax)
    for k, color in enumerate(change_colors):
        subset = included.loc[included.change_class.eq(k)]
        if not subset.empty:
            subset.plot(ax=ax, color=color, edgecolor='white', linewidth=.6, zorder=2)
    boundary.boundary.plot(ax=ax, color='#75878b', linewidth=.8, zorder=4)
    fig.text(.025, .95, 'Where the modeled walk becomes longer or shorter', fontsize=16, fontweight='bold', color=INK)
    longer, shorter, unchanged = (int((delta > tolerance).sum()), int((delta < -tolerance).sum()), int((delta.abs() <= tolerance).sum()))
    fig.text(.025, .904, f'Philadelphia, 2025  |  {longer} tracts longer · {shorter} shorter · {unchanged} unchanged', fontsize=11, color='#4e6268')
    counts = included.change_class.value_counts()
    handles = [Patch(facecolor=c, edgecolor='#d8dedd', label=f'{label} ({int(counts.get(k, 0))})')
               for k, (c, label) in enumerate(zip(change_colors, change_labels))]
    handles += [Patch(facecolor=GRAY, edgecolor='#aeb9bd', label='Other tracts: not analyzed'),
                Patch(facecolor=GRAY, edgecolor='#64747b', hatch='////', label='Address conflict: excluded')]
    fig.legend(handles=handles, loc='center left', bbox_to_anchor=(.60, .48), frameon=False,
               fontsize=9.5, labelspacing=1.2, title='After minus before\nNumber of tracts in parentheses', title_fontsize=10.5)
    fig.text(.5, .064, 'Each tract carries the estimate from its center; gray does not mean no change.',
             ha='center', fontsize=10, color='#4e6268')
    fig.text(.5, .032, 'Designated recipient compared with former Rite Aid. Sources: Census, company records and OpenStreetMap.',
             ha='center', fontsize=8.8, color='#4e6268')
    fig.savefig(OUT / 'walking_change_tract_map.png', dpi=200)
    plt.close(fig)


def supplementary_map(tracts, pharmacies):
    """Retain the older scenario's different estimand, with comparable panel sizes."""
    tracts = tracts.to_crs(26918)
    pharmacies = pharmacies.to_crs(26918)
    boundary = tracts.dissolve()
    fig = plt.figure(figsize=(11.6, 8.2), facecolor='white')
    axes = [fig.add_axes([.025, .27, .46, .56]), fig.add_axes([.515, .27, .46, .56])]
    for ax in axes:
        tract_background(ax, tracts, facecolor=GRAY, edgecolor='white', linewidth=.3)
        map_furniture(ax, boundary.total_bounds)
        ax.set_axis_off()
    populated = tracts.loc[tracts.population.gt(0)]
    colors = ['#f3f8ed', '#b9dcd3', '#69b6ae', '#2a898a', '#145365']
    populated.plot(ax=axes[0], column='all_listed_delta_m', cmap=ListedColormap(colors),
                   norm=BoundaryNorm([0, 1, 100, 250, 500, 10000], len(colors), clip=True),
                   edgecolor='white', linewidth=.45)
    rites = pharmacies.loc[pharmacies.is_rite_aid & pharmacies.inside_philadelphia]
    rites.plot(ax=axes[0], color='#ac552d', markersize=8, edgecolor='white', linewidth=.25, zorder=3)
    vehicle = tracts.loc[tracts.population.gt(0) & tracts.households.gt(0) & tracts.no_vehicle_share.notna()]
    amber = ['#fff2b2', '#fed476', '#fca34e', '#ef6b35', '#ca3828', '#8e1024']
    vehicle.plot(ax=axes[1], column='no_vehicle_share', cmap=ListedColormap(amber),
                 norm=BoundaryNorm([0, .1, .2, .3, .4, .6, 1.00001], len(amber), clip=True),
                 edgecolor='white', linewidth=.45)
    for ax in axes:
        boundary.boundary.plot(ax=ax, color='#75878b', linewidth=.8, zorder=4)
    axes[0].set_title('Nearest listed pharmacy: distance increase', loc='left', fontsize=12, fontweight='bold', color=INK)
    axes[1].set_title('Households without a vehicle', loc='left', fontsize=12, fontweight='bold', color=INK)
    fig.text(.025, .96, 'Supplement: access scenario and neighborhood context', fontsize=17, fontweight='bold', color=INK)
    fig.text(.025, .917, 'All-at-once inventory removal  |  2018–2022 ACS characteristics', fontsize=11, color='#4e6268')
    fig.legend([Patch(facecolor=c) for c in colors], ['0–<1 m', '1–<100 m', '100–<250 m', '250–<500 m', '500 m or more'],
               loc='lower center', bbox_to_anchor=(.255, .17), ncol=3, frameon=False, fontsize=9,
               title='Modeled straight-line increase', title_fontsize=10)
    fig.legend([Patch(facecolor=c) for c in amber], ['0–<10%', '10–<20%', '20–<30%', '30–<40%', '40–<60%', '60–100%'],
               loc='lower center', bbox_to_anchor=(.75, .17), ncol=3, frameon=False, fontsize=9,
               title='Share of households', title_fontsize=10)
    fig.legend([Line2D([0], [0], marker='o', linestyle='', color='#ac552d', markersize=5), Patch(facecolor=GRAY)],
               ['Rite Aid-labelled license', 'No populated-origin estimate / no household estimate'],
               loc='lower center', bbox_to_anchor=(.5, .09), ncol=2, frameon=False, fontsize=9)
    fig.text(.5, .055, 'The roster is not a verified operating network; New Jersey alternatives are missing.', ha='center', fontsize=10, color='#4e6268')
    fig.text(.5, .027, 'Tract shading represents center-based proximity or household context. Sources: Census ACS, boundaries and PA license roster.',
             ha='center', fontsize=9, color='#4e6268')
    fig.savefig(OUT / 'access_equity_map.png', dpi=200)
    plt.close(fig)


if __name__ == '__main__':
    frame = pd.read_csv(ROOT / 'data/processed/before_after_access_origins.csv', dtype={'GEOID': str})
    access_maps(frame.loc[frame.main_included].copy(), records=frame)
