"""Paired origin-to-pharmacy access around company-reported 2025 transfers.

These are destination scenarios grounded in dated records, not observed journeys.
The fixed January 2025 mapped network isolates destination change from street change.
"""
from pathlib import Path
import hashlib
import json
import gc
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial.distance import cdist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.cartography import map_furniture, tract_background
from src.tract_maps import access_maps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'
PROCESSED = ROOT / 'data/processed'
WALK_KMH = 4.8
MAIN_RADIUS_M = 800
MAX_SNAP_M = 200


def directed_matrix(graph):
    """Preserve direction and the shortest of any parallel edges, never their sum."""
    nodes = list(graph.nodes)
    index = {node: i for i, node in enumerate(nodes)}
    best = {}
    for u, v, data in graph.edges(data=True):
        key = (index[u], index[v])
        length = float(data['length'])
        if length < 0 or not np.isfinite(length):
            raise ValueError('Invalid edge length')
        best[key] = min(best.get(key, np.inf), length)
    rows, cols = zip(*best)
    matrix = csr_matrix((list(best.values()), (rows, cols)), shape=(len(nodes), len(nodes)))
    return matrix, index


def paired_distances(matrix, origin_indices, destination_indices):
    """Outbound and return distances in meters; directed road trips can differ."""
    unique, inverse = np.unique(destination_indices, return_inverse=True)
    outbound = dijkstra(matrix.T.tocsr(), directed=True, indices=unique)
    inbound = dijkstra(matrix, directed=True, indices=unique)
    return (outbound[inverse, origin_indices], inbound[inverse, origin_indices])


def conditional_co2_kg(roundtrip_delta_km, trips=1000, car_share=.5,
                       additional_share=1., factor_g_per_mile=400.):
    if trips < 0 or not 0 <= car_share <= 1 or not 0 <= additional_share <= 1 or factor_g_per_mile < 0:
        raise ValueError('Invalid emissions assumption')
    # Round-trip distance is already computed, including directed returns.
    return roundtrip_delta_km / 1.609344 * trips * car_share * additional_share * factor_g_per_mile / 1000


def _weighted(frame, column):
    return float(np.average(frame[column], weights=frame['population']))


def summarize(frame):
    if frame.empty:
        return {'tracts': 0}
    result = {'tracts': len(frame), 'population_context': int(frame.population.sum()),
              'represented_transfer_pairs': int(frame.store_number.nunique())}
    for col in ['walk_before_km', 'walk_after_km', 'walk_delta_km',
                'walk_before_minutes', 'walk_after_minutes', 'walk_delta_minutes',
                'drive_before_roundtrip_km', 'drive_after_roundtrip_km', 'drive_delta_roundtrip_km']:
        result['weighted_' + col] = _weighted(frame, col)
        result['median_' + col] = float(frame[col].median())
    result.update({
        'walk_increase_tracts': int((frame.walk_delta_km > .001).sum()),
        'walk_decrease_tracts': int((frame.walk_delta_km < -.001).sum()),
        'walk_unchanged_tracts': int((frame.walk_delta_km.abs() <= .001).sum()),
        'drive_increase_tracts': int((frame.drive_delta_roundtrip_km > .001).sum()),
        'drive_decrease_tracts': int((frame.drive_delta_roundtrip_km < -.001).sum()),
        'walk_within_15min_before_tracts': int((frame.walk_before_minutes <= 15).sum()),
        'walk_within_15min_after_tracts': int((frame.walk_after_minutes <= 15).sum()),
        'conditional_kg_per_1000_at_half_car': conditional_co2_kg(_weighted(frame, 'drive_delta_roundtrip_km'))
    })
    return result


def build():
    pairs = pd.read_csv(PROCESSED / 'philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    tracts = pd.read_csv(PROCESSED / 'tract_scenarios.csv', dtype={'GEOID': str})
    tracts = tracts.loc[tracts.population > 0].copy()
    sites = gpd.GeoSeries(gpd.points_from_xy(pairs.old_longitude, pairs.old_latitude), crs=4326).to_crs(26918)
    distances = cdist(tracts[['origin_x', 'origin_y']], np.c_[sites.x, sites.y])
    closest = distances.argmin(axis=1)
    tracts['assigned_pair_index'] = closest
    tracts['distance_to_former_m'] = distances[np.arange(len(tracts)), closest]
    origins = tracts.loc[tracts.distance_to_former_m <= 1000,
        ['GEOID', 'population', 'households', 'no_vehicle_households', 'poverty_rate', 'no_vehicle_share',
         'origin_lon', 'origin_lat', 'assigned_pair_index', 'distance_to_former_m']].reset_index(drop=True)
    records = origins.merge(pairs, left_on='assigned_pair_index', right_index=True, validate='many_to_one')
    manifest = json.loads((ROOT / 'data/historical_network_manifest.json').read_text())
    for item in manifest['files']:
        mode = item['mode']
        path = ROOT / item['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], 'Changed graph input'
        graph = ox.load_graphml(path)
        matrix, index = directed_matrix(graph)
        origin_nodes, origin_snap = ox.distance.nearest_nodes(graph, records.origin_lon,
                                                             records.origin_lat, return_dist=True)
        oi = np.array([index[node] for node in origin_nodes])
        records[mode + '_origin_snap_m'] = origin_snap
        snapped_destinations = {}
        for prefix, phase in [('old', 'before'), ('receiving', 'after')]:
            dn, snap = ox.distance.nearest_nodes(graph, records[prefix + '_longitude'],
                                                records[prefix + '_latitude'], return_dist=True)
            di = np.array([index[node] for node in dn])
            snapped_destinations[phase] = (di, snap)
        del graph, index
        gc.collect()
        for phase, (di, snap) in snapped_destinations.items():
            outbound, inbound = paired_distances(matrix, oi, di)
            # Approximate straight connectors attach address points to mapped nodes.
            # They are retained separately and screened; they are not mapped paths.
            connector = np.asarray(origin_snap) + np.asarray(snap)
            records[f'{mode}_{phase}_destination_snap_m'] = snap
            records[f'{mode}_{phase}_outbound_network_m'] = outbound
            records[f'{mode}_{phase}_return_network_m'] = inbound
            records[f'{mode}_{phase}_connector_m'] = connector
            records[f'{mode}_{phase}_km'] = (outbound + connector) / 1000
            records[f'{mode}_{phase}_roundtrip_km'] = (outbound + inbound + 2 * connector) / 1000
        records[mode + '_delta_km'] = records[mode + '_after_km'] - records[mode + '_before_km']
        records[mode + '_delta_roundtrip_km'] = records[mode + '_after_roundtrip_km'] - records[mode + '_before_roundtrip_km']
        del matrix
        gc.collect()
    for phase in ['before', 'after', 'delta']:
        records['walk_' + phase + '_minutes'] = records['walk_' + phase + '_km'] / WALK_KMH * 60
    snapcols = [c for c in records if c.endswith('_snap_m')]
    routecols = [f'{mode}_{phase}_roundtrip_km' for mode in ['walk', 'drive'] for phase in ['before', 'after']]
    records['max_snap_m'] = records[snapcols].max(axis=1)
    records['all_routes_reachable'] = np.isfinite(records[routecols]).all(axis=1)
    records['unresolved_address_conflict'] = records.store_number.eq('1956')
    records['main_included'] = ((records.distance_to_former_m <= MAIN_RADIUS_M)
                                & (records.max_snap_m <= MAX_SNAP_M) & records.all_routes_reachable
                                & ~records.unresolved_address_conflict)
    records.replace([np.inf, -np.inf], np.nan).to_csv(PROCESSED / 'before_after_access_origins.csv', index=False)
    main = records.loc[records.main_included].copy()
    summary = summarize(main)
    summary.update({'study_period': '2023–2025', 'dated_analysis_period': '2025-06-04 to 2025-08-08',
                    'documented_transfers': len(pairs), 'same_address_transfers': int(pairs.same_address_transfer.sum()),
                    'network_snapshot': manifest['snapshot_utc'], 'radius_m': MAIN_RADIUS_M,
                    'max_snap_m': MAX_SNAP_M, 'walking_speed_kmh': WALK_KMH,
                    'eligible_origins_within_800m': int((records.distance_to_former_m <= MAIN_RADIUS_M).sum()),
                    'within_800m_unreachable': int(((records.distance_to_former_m <= MAIN_RADIUS_M) & ~records.all_routes_reachable).sum()),
                    'within_800m_snap_excluded': int(((records.distance_to_former_m <= MAIN_RADIUS_M) & (records.max_snap_m > MAX_SNAP_M)).sum()),
                    'within_800m_address_conflict': int(((records.distance_to_former_m <= MAIN_RADIUS_M) & records.unresolved_address_conflict).sum()),
                    'interpretation': 'Fixed-origin routed before/after destination scenarios for designated transfers; no observed journey or causal mode effect',
                    'sensitivity': []})
    for radius in [500, 800, 1000]:
        for snap in [100, 200, 300]:
            keep = records.loc[(records.distance_to_former_m <= radius) & (records.max_snap_m <= snap) & records.all_routes_reachable & ~records.unresolved_address_conflict]
            summary['sensitivity'].append({'radius_m': radius, 'max_snap_m': snap, **summarize(keep)})
    summary['including_disputed_address'] = summarize(records.loc[(records.distance_to_former_m <= MAIN_RADIUS_M)
        & (records.max_snap_m <= MAX_SNAP_M) & records.all_routes_reachable])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'before_after_summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    pd.DataFrame(summary['sensitivity']).to_csv(OUT / 'before_after_sensitivity.csv', index=False)
    equity = []
    for column, cutoff, names in [('poverty_rate', .2, ['Poverty below 20%', 'Poverty at least 20%']),
                                  ('no_vehicle_share', .3, ['No vehicle below 30%', 'No vehicle at least 30%'])]:
        for high, name in enumerate(names):
            group = main.loc[main[column].notna() & ((main[column] >= cutoff) == bool(high))]
            equity.append({'group': name, **summarize(group)})
    pd.DataFrame(equity).to_csv(OUT / 'before_after_equity.csv', index=False)
    events = pairs[['store_number', 'old_address', 'pharmacy_last_open_date', 'receiving_name', 'receiving_address', 'same_address_transfer']].copy()
    event_results = pd.DataFrame([{'store_number': key, **summarize(group)} for key, group in main.groupby('store_number')])
    events.merge(event_results, on='store_number', how='left').to_csv(OUT / 'before_after_by_event.csv', index=False)
    co2 = [{'car_share': car, 'additional_travel_share': additional, 'hypothetical_person_roundtrips': 1000,
            'tailpipe_co2_delta_kg': conditional_co2_kg(summary['weighted_drive_delta_roundtrip_km'], car_share=car, additional_share=additional)}
           for car in [.25, .5, .75, 1.] for additional in [.5, 1.]]
    pd.DataFrame(co2).to_csv(OUT / 'before_after_emissions.csv', index=False)
    figures(main, pairs)
    print(json.dumps({k: v for k, v in summary.items() if k != 'sensitivity'}, indent=2))
    return records, summary


def figures(main, pairs):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'savefig.facecolor': 'white'})
    tracts = gpd.read_file(PROCESSED / 'tract_scenarios.geojson').to_crs(26918)
    boundary = tracts.dissolve()
    access_maps(main, tracts)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), layout='constrained')
    for ax, before, after, label in [(axes[0], 'walk_before_minutes', 'walk_after_minutes', 'Walking minutes, one way'),
                                    (axes[1], 'drive_before_roundtrip_km', 'drive_after_roundtrip_km', 'Driving kilometers, round trip')]:
        hi = max(main[before].max(), main[after].max()) * 1.05
        ax.plot([0, hi], [0, hi], '--', color='#83929a', linewidth=1, label='No change')
        ax.scatter(main[before], main[after], color='#137c86', alpha=.7, s=22)
        ax.set(xlim=(0, hi), ylim=(0, hi), xlabel='Before', ylabel='After', title=label)
        ax.legend(frameon=False, loc='lower right'); ax.grid(alpha=.15)
    fig.savefig(OUT / 'before_after_comparison.png', dpi=180); plt.close(fig)
    dated = pd.to_datetime(pairs.pharmacy_last_open_date).value_counts().sort_index().cumsum()
    fig, ax = plt.subplots(figsize=(10, 3.1), layout='constrained')
    ax.step(dated.index, dated.values, where='post', color='#137c86', linewidth=2)
    ax.scatter(dated.index, dated.values, color='#137c86', s=18)
    ax.set(ylabel='Cumulative listed events', xlabel='Company-reported last day of pharmacy business', ylim=(0, 25))
    ax.grid(axis='y', alpha=.2)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    fig.savefig(OUT / 'transfer_timeline.png', dpi=180); plt.close(fig)
    # Thresholds describe origin access under an assumed speed, not mode shares.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    thresholds = [10, 15, 20, 30]
    before = [100 * np.average(main.walk_before_minutes <= t, weights=main.population) for t in thresholds]
    after = [100 * np.average(main.walk_after_minutes <= t, weights=main.population) for t in thresholds]
    x = np.arange(len(thresholds))
    axes[0].bar(x - .17, before, .34, color='#137c86', label='Before')
    axes[0].bar(x + .17, after, .34, color='#ba663e', label='After')
    axes[0].set(xticks=x, xticklabels=[str(t) for t in thresholds], xlabel='Walking threshold in minutes',
                ylabel='Share of included tract population (%)', ylim=(0, 105), title='Reachability at an assumed 4.8 km/h')
    axes[0].legend(frameon=False)
    axes[1].hist(main.walk_delta_minutes, bins=15, color='#137c86', edgecolor='white')
    axes[1].axvline(0, color='#111', linewidth=1)
    axes[1].set(xlabel='After minus before walking minutes', ylabel='Number of tract origins', title='Changes vary across origins')
    fig.savefig(OUT / 'walking_thresholds.png', dpi=180); plt.close(fig)
    eq = pd.read_csv(OUT / 'before_after_equity.csv')
    fig, ax = plt.subplots(figsize=(10, 3.4), layout='constrained')
    labels = [f'{r.group.replace("No vehicle", "Households without a vehicle")} (n={r.tracts})' for r in eq.itertuples()]
    bars = ax.barh(labels, eq.weighted_walk_delta_minutes, color=['#a8cdd0', '#137c86', '#a8cdd0', '#137c86'])
    ax.bar_label(bars, fmt='%.1f', padding=5, fontsize=9)
    ax.set_xlim(0, eq.weighted_walk_delta_minutes.max() * 1.13)
    ax.invert_yaxis(); ax.set(xlabel='Population-weighted modeled walking increase in minutes', title='Neighborhood comparisons within the route sample')
    ax.grid(axis='x', alpha=.15)
    fig.savefig(OUT / 'before_after_equity.png', dpi=180); plt.close(fig)
    co2 = pd.read_csv(OUT / 'before_after_emissions.csv')
    fig, ax = plt.subplots(figsize=(10, 3.4), layout='constrained')
    for additional, color in [(.5, '#9abacb'), (1., '#137c86')]:
        subset = co2.loc[co2.additional_travel_share.eq(additional)]
        ax.plot(subset.car_share * 100, subset.tailpipe_co2_delta_kg, marker='o', color=color,
                label=f'{additional:.0%} of distance change treated as additional travel')
    ax.set(xlabel='Assumed share of person trips made by gasoline car (%)', ylabel='Additional tailpipe CO₂ (kg)',
           title='Conditional emissions per 1,000 hypothetical round trips', xticks=[25, 50, 75, 100])
    ax.legend(frameon=False, fontsize=9); ax.grid(alpha=.15)
    fig.savefig(OUT / 'before_after_emissions.png', dpi=180); plt.close(fig)
    # Destination links are not street routes or observed trips.
    old = gpd.GeoSeries(gpd.points_from_xy(pairs.old_longitude, pairs.old_latitude), crs=4326).to_crs(26918)
    new = gpd.GeoSeries(gpd.points_from_xy(pairs.receiving_longitude, pairs.receiving_latitude), crs=4326).to_crs(26918)
    fig, ax = plt.subplots(figsize=(7.4, 7.2), layout='constrained')
    tract_background(ax, tracts)
    boundary.boundary.plot(ax=ax, color='#75828b', linewidth=.7)
    for a, b in zip(old, new):
        ax.annotate('', xy=(b.x, b.y), xytext=(a.x, a.y),
                    arrowprops={'arrowstyle': '-|>', 'color': '#566d75', 'lw': 1.1, 'alpha': .9})
    ax.scatter(old.x, old.y, s=38, c='#ba663e', edgecolors='white', linewidths=.5, label='Former Rite Aid', zorder=3)
    ax.scatter(new.x, new.y, s=36, c='#137c86', marker='s', edgecolors='white', linewidths=.5, label='Designated recipient', zorder=4)
    disputed = pairs.store_number.astype(str).eq('1956')
    ax.scatter(old[disputed].x, old[disputed].y, s=100, facecolors='none', edgecolors='#ad3434', linewidths=1.3, label='Address disputed', zorder=5)
    same = pairs.same_address_transfer
    ax.scatter(old[same].x, old[same].y, s=150, facecolors='none', marker='D', edgecolors='#6f5483', linewidths=1.2, label='Same-address transfer', zorder=5)
    ax.set_title('Where prescriptions were designated to transfer', loc='left', fontweight='bold', fontsize=13)
    ax.legend(loc='lower right', frameon=True, framealpha=.95, fontsize=9)
    map_furniture(ax, boundary.total_bounds)
    ax.set_axis_off()
    fig.savefig(OUT / 'transfer_destination_map.png', dpi=180); plt.close(fig)
    events = pd.read_csv(OUT / 'before_after_by_event.csv').dropna(subset=['weighted_walk_delta_minutes']).sort_values('weighted_walk_delta_minutes')
    fig, ax = plt.subplots(figsize=(8.5, 7.2), layout='constrained')
    labels = [f'{r.old_address.replace("STREETPA SUITE 1", "STREET").replace("AVENUEPA SUITE", "AVENUE").title()} (n={int(r.tracts)})' for r in events.itertuples()]
    bars = ax.barh(labels, events.weighted_walk_delta_minutes,
                   color=np.where(events.weighted_walk_delta_minutes >= 0, '#ba663e', '#137c86'))
    ax.bar_label(bars, fmt='%+.1f', padding=4, fontsize=8)
    ax.axvline(0, color='#344b55', linewidth=.8)
    ax.set(xlim=(min(-5, events.weighted_walk_delta_minutes.min() - 3), events.weighted_walk_delta_minutes.max() + 4),
           xlabel='Population-weighted walking-time change (minutes, one way)',
           title='Modeled access changes vary by former location')
    ax.tick_params(axis='y', labelsize=10.5); ax.grid(axis='x', alpha=.15)
    fig.savefig(OUT / 'transfer_by_location.png', dpi=180); plt.close(fig)


if __name__ == '__main__':
    build()
