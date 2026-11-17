"""Auditable weekly counts and publication figures for the dated transfer table."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from src.figure_style import (RC, new_figure, save_figure, footer, INK, MUTED, TEAL,
                              RUST, GRID, PANEL, TICK, NOTE)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'
LIGHT = '#cee1df'


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
    monthly = records.groupby(records.date.dt.to_period('M')).size()
    busiest_month = monthly.idxmax()
    month_count = int(monthly.max())
    month_name = busiest_month.to_timestamp().strftime('%B')
    peak_index = int(weekly.records.idxmax())
    peak = weekly.loc[peak_index]
    start = weekly.week_start.min()
    end = weekly.week_end.max() + pd.Timedelta(days=1)
    max_count = int(weekly.records.max())
    ceiling = max(4, int(np.ceil((max_count + 1) / 2) * 2))
    colors = [RUST if i == peak_index else TEAL for i in weekly.index]
    with plt.rc_context(RC):
        fig = new_figure(6.4, f'{month_count / total:.0%} of documented transfers fell in {month_name}',
                         f'{total} locations · {summary["distinct_dates"]} reported dates · '
                         f'{records.date.min():%-d %B}–{records.date.max():%-d %B %Y}',
                         kicker='PHILADELPHIA / RITE AID TRANSFER RECORDS / 2025')
        fig.add_artist(Line2D([.065, .965], [.815, .815], transform=fig.transFigure, color=GRID, lw=.9))
        fig.text(.065, .770, 'A   Records per week', fontsize=PANEL, fontweight='bold')
        fig.text(.965, .770, 'Monday–Sunday; numbers above bars are counts',
                 fontsize=NOTE, color=MUTED, ha='right')
        ax = fig.add_axes([.085, .385, .88, .345])
        centers = weekly.week_start + pd.Timedelta(days=3.5)
        ax.set_xlim(start, end)
        ax.set_ylim(0, ceiling + .65)
        ax.set_axisbelow(True)
        ax.grid(axis='y', color=GRID, lw=.7)
        ax.set_yticks(range(0, ceiling + 1, 2))
        ax.tick_params(axis='both', length=0, pad=7, labelsize=TICK)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.bar(centers, weekly.records, width=5.1, color=colors, zorder=3)
        for center, row, color in zip(centers, weekly.itertuples(), colors):
            if row.records == 0:
                ax.plot([center - pd.Timedelta(days=2.55), center + pd.Timedelta(days=2.55)],
                        [0, 0], color=LIGHT, lw=3, solid_capstyle='butt', clip_on=False)
            ax.text(center, row.records + .15, str(row.records), ha='center',
                    fontsize=PANEL, color=color if row.records else MUTED, fontweight='bold')
        ax.set_xticks(centers)
        ax.set_xticklabels([f'{d:%-d}\n{d:%b}' for d in weekly.week_start], linespacing=1.4)
        ax.text(0, -.29, 'Week starting', transform=ax.transAxes, fontsize=NOTE, color=MUTED)
        # The peak callout sits in the open space, so it never covers a bar.
        peak_center = centers.iloc[peak_index]
        ax.annotate(f'Busiest week: {peak.week_start:%-d}–{peak.week_end:%-d %B}\n'
                    f'{max_count} of {total} records ({max_count / total:.0%})',
                    xy=(peak_center - pd.Timedelta(days=2.7), max_count - .15), xytext=(.32, .87),
                    textcoords='axes fraction', color=RUST, fontsize=TICK,
                    ha='left', va='top', linespacing=1.5,
                    arrowprops={'arrowstyle': '-', 'color': RUST, 'lw': .9,
                                'connectionstyle': 'angle,angleA=0,angleB=90,rad=0'})
        fig.text(.065, .257, 'B   Each square is one location', fontsize=PANEL, fontweight='bold')
        fig.text(.965, .257, 'Exact reported day; stacked squares share a date',
                 fontsize=NOTE, color=MUTED, ha='right')
        detail = fig.add_axes([.085, .132, .88, .105])
        detail.set(xlim=(start, end), ylim=(.35, 3.8))
        detail.set_axis_off()
        for row in daily.itertuples():
            color = RUST if peak.week_start <= row.date <= peak.week_end else TEAL
            detail.scatter([row.date] * row.records, range(1, row.records + 1),
                           marker='s', s=27, color=color, edgecolors='white', linewidths=.45, zorder=3)
        for boundary in pd.date_range(start, end, freq='MS'):
            detail.axvline(boundary, color=GRID, lw=.8, zorder=1)
        for month, count in monthly.items():
            left = max(start, month.start_time)
            right = min(end, (month + 1).start_time)
            center = left + (right - left) / 2
            detail.text(center, -.12, f'{month.start_time:%B}  ·  {int(count)} records',
                        ha='center', va='top', fontsize=TICK, color=MUTED)
        footer(fig, 'Source: Rite Aid archived transfer table. Dates are company-reported last pharmacy-business days.',
               second_line='Selected records, not all city closures. Zero bars mean no records in this table; patient travel is not measured.')
        save_figure(fig, destination / 'transfer_timeline.png', vector=True)
    return summary


if __name__ == '__main__':
    pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    print(json.dumps(render_timeline(pairs), indent=2))
