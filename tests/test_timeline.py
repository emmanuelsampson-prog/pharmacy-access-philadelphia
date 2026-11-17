"""Guard weekly boundaries, zero periods and the record-count denominator."""
import pandas as pd
import pytest
from src.timeline import timeline_data


def test_weekly_counts_keep_sunday_and_monday_separate_and_include_empty_weeks():
    pairs = pd.DataFrame({'store_number': ['a', 'b', 'c', 'd'],
                          'pharmacy_last_open_date': ['2025-06-08', '2025-06-09', '2025-06-09', '2025-06-30']})
    _, weekly, daily, summary = timeline_data(pairs)
    assert weekly.records.tolist() == [1, 2, 0, 0, 1]
    assert str(weekly.week_start.iloc[0].date()) == '2025-06-02'
    assert daily.records.sum() == 4
    assert summary['peak_week_records'] == 2
    assert summary['distinct_dates'] == 3


def test_invalid_records_cannot_silently_change_the_chart_denominator():
    duplicate = pd.DataFrame({'store_number': ['a', 'a'], 'pharmacy_last_open_date': ['2025-06-04', '2025-06-05']})
    with pytest.raises(ValueError):
        timeline_data(duplicate)
    missing = pd.DataFrame({'store_number': ['a'], 'pharmacy_last_open_date': [None]})
    with pytest.raises(ValueError):
        timeline_data(missing)
