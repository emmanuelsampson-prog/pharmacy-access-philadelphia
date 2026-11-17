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
from src.figure_style import (publication_style, new_figure, footer, save_figure,
                              INK, MUTED, GRAY, BEFORE, BOUNDARY,
                              WALK_COLORS, CHANGE_COLORS, TEAL_COLORS,
                              PANEL, TICK, LEGEND, NOTE)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'


@publication_style
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

    colors = WALK_COLORS
    bins = [0, 5, 10, 15, 20, 30, 60]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bins, cmap.N, clip=True)
    assert included[['walk_before_minutes', 'walk_after_minutes']].max().max() <= bins[-1]
    fig = new_figure(7.8, 'Walking access before and after pharmacy transfers',
                     'Philadelphia, 2025 | The same 62 tracts and color intervals in both panels')
    axes = [fig.add_axes([.04, .29, .44, .51]), fig.add_axes([.52, .29, .44, .51])]
    for ax, phase, label in zip(axes, ['before', 'after'], ['Before: former Rite Aid', 'After: designated recipient']):
        base(ax)
        included.plot(ax=ax, column=f'walk_{phase}_minutes', cmap=cmap, norm=norm,
                      edgecolor='#ffffff', linewidth=.55, zorder=2)
        boundary.boundary.plot(ax=ax, color=BOUNDARY, linewidth=.8, zorder=4)
        ax.set_title(label, loc='left', fontsize=PANEL, color=INK, fontweight='bold', pad=7)
    labels = ['0–<5 min', '5–<10 min', '10–<15 min', '15–<20 min', '20–<30 min', '30–60 min']
    fig.legend([Patch(facecolor=c) for c in colors], labels, loc='lower center',
               bbox_to_anchor=(.5, .14), ncol=3, frameon=False, fontsize=LEGEND,
               title='Modeled walking time, one way', title_fontsize=LEGEND)
    fig.legend([Patch(facecolor=GRAY, edgecolor='#aeb9bd'),
                Patch(facecolor=GRAY, edgecolor='#64747b', hatch='////')],
               ['Other tracts: not analyzed', 'Address conflict: excluded'],
               loc='lower center', bbox_to_anchor=(.5, .085), ncol=2, frameon=False, fontsize=LEGEND)
    footer(fig, 'Each shaded tract displays its center’s route estimate; travel time varies within a tract.',
           second_line='Walking speed: 4.8 km/h. Sources: Census, Rite Aid records, PA roster and OpenStreetMap.')
    save_figure(fig, OUT / 'before_after_walking_map.png')

    # Match the report's one-meter tolerance for unchanged walking distance.
    tolerance = .001 / 4.8 * 60
    delta = included.walk_delta_minutes
    included['change_class'] = np.select(
        [delta < -5, delta < -tolerance, delta.abs() <= tolerance,
         delta <= 5, delta <= 15, delta <= 30], [0, 1, 2, 3, 4, 5], default=6)
    change_colors = CHANGE_COLORS
    change_labels = ['More than 5 min shorter', 'Up to 5 min shorter', 'Unchanged (within 1 meter)',
                     'Up to 5 min longer', 'Over 5 to 15 min longer',
                     'Over 15 to 30 min longer', 'More than 30 min longer']
    longer, shorter, unchanged = (int((delta > tolerance).sum()), int((delta < -tolerance).sum()), int((delta.abs() <= tolerance).sum()))
    fig = new_figure(7.6, 'Where the modeled walk becomes longer or shorter',
                     f'Philadelphia, 2025 | {longer} tracts longer · {shorter} shorter · {unchanged} unchanged')
    ax = fig.add_axes([.03, .14, .54, .67])
    base(ax)
    for k, color in enumerate(change_colors):
        subset = included.loc[included.change_class.eq(k)]
        if not subset.empty:
            subset.plot(ax=ax, color=color, edgecolor='white', linewidth=.6, zorder=2)
    boundary.boundary.plot(ax=ax, color=BOUNDARY, linewidth=.8, zorder=4)
    counts = included.change_class.value_counts()
    handles = [Patch(facecolor=c, edgecolor='#d8dedd', label=f'{label} ({int(counts.get(k, 0))})')
               for k, (c, label) in enumerate(zip(change_colors, change_labels))]
    handles += [Patch(facecolor=GRAY, edgecolor='#aeb9bd', label='Other tracts: not analyzed'),
                Patch(facecolor=GRAY, edgecolor='#64747b', hatch='////', label='Address conflict: excluded')]
    fig.legend(handles=handles, loc='center left', bbox_to_anchor=(.56, .47), frameon=False,
               fontsize=LEGEND, labelspacing=1.2, title='After minus before\nNumber of tracts in parentheses', title_fontsize=LEGEND)
    footer(fig, 'Each tract carries the estimate from its center; gray does not mean no change.',
           second_line='Designated recipient versus former Rite Aid. Sources: Census, company records and OpenStreetMap.')
    save_figure(fig, OUT / 'walking_change_tract_map.png')


@publication_style
def supplementary_map(tracts, pharmacies):
    """Retain the older scenario's different estimand, with comparable panel sizes."""
    tracts = tracts.to_crs(26918)
    pharmacies = pharmacies.to_crs(26918)
    boundary = tracts.dissolve()
    fig = new_figure(8.2, 'Supplement: access scenario and neighborhood context',
                     'All-at-once inventory removal | 2018–2022 ACS characteristics')
    axes = [fig.add_axes([.04, .30, .44, .50]), fig.add_axes([.52, .30, .44, .50])]
    for ax in axes:
        tract_background(ax, tracts, facecolor=GRAY, edgecolor='white', linewidth=.3)
        map_furniture(ax, boundary.total_bounds)
        ax.set_axis_off()
    populated = tracts.loc[tracts.population.gt(0)]
    colors = [WALK_COLORS[i] for i in [0, 1, 2, 4, 5]]
    populated.plot(ax=axes[0], column='all_listed_delta_m', cmap=ListedColormap(colors),
                   norm=BoundaryNorm([0, 1, 100, 250, 500, 10000], len(colors), clip=True),
                   edgecolor='white', linewidth=.45)
    rites = pharmacies.loc[pharmacies.is_rite_aid & pharmacies.inside_philadelphia]
    rites.plot(ax=axes[0], color=BEFORE, markersize=8, edgecolor='white', linewidth=.25, zorder=3)
    vehicle = tracts.loc[tracts.population.gt(0) & tracts.households.gt(0) & tracts.no_vehicle_share.notna()]
    context_colors = TEAL_COLORS
    vehicle.plot(ax=axes[1], column='no_vehicle_share', cmap=ListedColormap(context_colors),
                 norm=BoundaryNorm([0, .1, .2, .3, .4, .6, 1.00001], len(context_colors), clip=True),
                 edgecolor='white', linewidth=.45)
    for ax in axes:
        boundary.boundary.plot(ax=ax, color=BOUNDARY, linewidth=.8, zorder=4)
    axes[0].set_title('Nearest listed pharmacy:\ndistance increase', loc='left', fontsize=PANEL, fontweight='bold', color=INK)
    axes[1].set_title('Households without\na vehicle', loc='left', fontsize=PANEL, fontweight='bold', color=INK)
    fig.legend([Patch(facecolor=c) for c in colors], ['0–<1 m', '1–<100 m', '100–<250 m', '250–<500 m', '500 m or more'],
               loc='lower center', bbox_to_anchor=(.255, .16), ncol=2, frameon=False, fontsize=LEGEND,
               title='Modeled straight-line increase', title_fontsize=LEGEND)
    fig.legend([Patch(facecolor=c) for c in context_colors], ['0–<10%', '10–<20%', '20–<30%', '30–<40%', '40–<60%', '60–100%'],
               loc='lower center', bbox_to_anchor=(.75, .16), ncol=2, frameon=False, fontsize=LEGEND,
               title='Share of households', title_fontsize=LEGEND)
    fig.legend([Line2D([0], [0], marker='o', linestyle='', color=BEFORE, markersize=5), Patch(facecolor=GRAY)],
               ['Rite Aid-labelled license', 'No populated-origin estimate / no household estimate'],
               loc='lower center', bbox_to_anchor=(.5, .09), ncol=2, frameon=False, fontsize=LEGEND)
    footer(fig, 'The roster is not a verified operating network; New Jersey alternatives are missing.',
           second_line='Tracts show center-based proximity or household context. Sources: Census ACS and PA license roster.')
    save_figure(fig, OUT / 'access_equity_map.png')


if __name__ == '__main__':
    frame = pd.read_csv(ROOT / 'data/processed/before_after_access_origins.csv', dtype={'GEOID': str})
    access_maps(frame.loc[frame.main_included].copy(), records=frame)
