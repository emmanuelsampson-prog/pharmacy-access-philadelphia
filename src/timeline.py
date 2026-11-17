"""Auditable weekly counts and publication figures for the dated transfer table."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.figure_style import (RC, new_figure, save_figure, footer, INK, MUTED, BLUE,
                              ORANGE, GRID, PANEL, TICK, NOTE)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'


def timeline_data(pairs):
    """One record per store; weeks run Monday through Sunday, including zeros."""
    records = pairs.copy()
    if records.empty or records.store_number.isna().any() or records.store_number.duplicated().any():
        raise ValueError('Timeline requires a nonempty table with one record per store')
    dates = pd.to_datetime(records.pharmacy_last_open_date, errors='raise').dt.normalize()
    if dates.isna().any():
        raise ValueError('Every timeline record must have a reported date')
    records['date'] = dates
    records = records.sort_values(['date', 'store_number']).reset_index(drop=True)
    starts = dates - pd.to_timedelta(dates.dt.day_of_week, unit='D')
    weekly_index = pd.date_range(starts.min(), starts.max(), freq='7D')
    weekly = starts.value_counts().reindex(weekly_index, fill_value=0).rename_axis('week_start').reset_index(name='records')
    weekly['week_end'] = weekly.week_start + pd.Timedelta(days=6)
    weekly = weekly[['week_start', 'week_end', 'records']]
    daily = records.groupby('date').size().rename('records').reset_index()
    monthly = records.groupby(records.date.dt.to_period('M')).size()
    peak = weekly.loc[weekly.records.idxmax()]
    summary = {
        'records': len(records), 'distinct_dates': len(daily),
        'first_date': str(dates.min().date()), 'last_date': str(dates.max().date()),
        'monthly_records': {str(month): int(n) for month, n in monthly.items()},
        'peak_week_start': str(peak.week_start.date()),
        'peak_week_end': str(peak.week_end.date()), 'peak_week_records': int(peak.records),
        'week_definition': 'Monday through Sunday',
        'date_definition': 'Company-reported last day of pharmacy business',
        'scope': 'Selected Philadelphia transfer records; not a complete citywide closure count',
    }
    assert weekly.records.sum() == daily.records.sum() == len(records)
    return records, weekly, daily, summary


def render_timeline(pairs, destination=OUT):
    """Build the figure and its download tables from the same dated records."""
    records, weekly, daily, summary = timeline_data(pairs)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(destination / 'transfer_timeline_weekly.csv', index=False, date_format='%Y-%m-%d')
    daily.to_csv(destination / 'transfer_timeline_daily.csv', index=False, date_format='%Y-%m-%d')
    (destination / 'transfer_timeline_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    total = summary['records']
    peak_index = int(weekly.records.idxmax())
    peak = weekly.loc[peak_index]
    start = weekly.week_start.min()
    end = weekly.week_end.max() + pd.Timedelta(days=1)
    ceiling = max(4, int(np.ceil((weekly.records.max() + 1) / 2) * 2))
    with plt.style.context('default'), plt.rc_context(RC):
        fig = new_figure(5.5, 'Documented pharmacy transfers in Philadelphia, 2025',
                         f'{total} locations; {summary["distinct_dates"]} reported dates; '
                         f'{records.date.min():%-d %B}–{records.date.max():%-d %B %Y}')
        ax = fig.add_axes([.10, .46, .85, .34])
        centers = weekly.week_start + pd.Timedelta(days=3.5)
        colors = [ORANGE if i == peak_index else BLUE for i in weekly.index]
        bars = ax.bar(centers, weekly.records, width=5.1, color=colors)
        ax.bar_label(bars, padding=3, fontsize=9)
        ax.set(xlim=(start, end), ylim=(0, ceiling + 1),
               ylabel='Number of locations', xlabel='Week starting')
        ax.set_title('Weekly records (Monday–Sunday)')
        ax.set_yticks(range(0, ceiling + 1, 2))
        ax.set_xticks(centers)
        ax.set_xticklabels([f'{d:%-d %b}' for d in weekly.week_start])
        ax.grid(axis='y')
        detail = fig.add_axes([.10, .19, .85, .13])
        for row in daily.itertuples():
            color = ORANGE if peak.week_start <= row.date <= peak.week_end else BLUE
            detail.scatter([row.date] * row.records, range(1, row.records + 1),
                           marker='o', s=22, color=color)
        ticks = pd.date_range(start, end, freq='14D')
        detail.set(xlim=(start, end), ylim=(.5, daily.records.max() + .5),
                   yticks=list(range(1, int(daily.records.max()) + 1)),
                   ylabel='Records on date', xlabel='Reported last pharmacy day')
        detail.set_xticks(ticks)
        detail.set_xticklabels([f'{d:%-d %b}' for d in ticks])
        detail.set_title('Individual dates (one point per location)')
        footer(fig, 'Source: archived Rite Aid transfer table. Dates are company-reported last pharmacy-business days.',
               second_line='June: 3 records; July: 18; August: 3. Selected records, not all city closures or observed patient journeys.')
        save_figure(fig, destination / 'transfer_timeline.png', vector=True)
    return summary


if __name__ == '__main__':
    pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    print(json.dumps(render_timeline(pairs), indent=2))
