"""Tests for the analytics canonical frame (`AnalyticsService._prepare`)."""

from __future__ import annotations

import pandas as pd
import pytest

from app.services.analytics_service import AnalyticsService


def test_prepare_returns_empty_frame_with_canonical_columns_when_input_is_empty():
    df = AnalyticsService._prepare(pd.DataFrame())
    assert df.empty
    for col in AnalyticsService.CANONICAL_COLUMNS:
        assert col in df.columns


def test_prepare_returns_empty_frame_when_input_is_none():
    df = AnalyticsService._prepare(None)
    assert df.empty


def test_prepare_coerces_sale_date_to_datetime(prepared_df):
    assert pd.api.types.is_datetime64_any_dtype(prepared_df['sale_date'])


def test_prepare_derives_day_month_year(prepared_df):
    row = prepared_df.iloc[0]
    assert row['day_of_week'] in {
        'Monday', 'Tuesday', 'Wednesday', 'Thursday',
        'Friday', 'Saturday', 'Sunday',
    }
    assert isinstance(row['month'], str) and len(row['month']) > 0
    assert int(row['year']) == 2024


def test_prepare_applies_revenue_fallback_when_total_is_zero(prepared_df):
    # sale_id == 3 had total=0 with card=15, cash=15 -> total should be 30.
    fallback_row = prepared_df.loc[prepared_df['sale_id'] == 3].iloc[0]
    assert fallback_row['total'] == pytest.approx(30.0)


def test_prepare_drops_rows_without_usable_date():
    raw = pd.DataFrame([
        {'sale_id': 1, 'sale_date': '2024-01-01', 'total': 10.0},
        {'sale_id': 2, 'sale_date': 'not-a-date', 'total': 20.0},
        {'sale_id': 3, 'sale_date': None,         'total': 30.0},
    ])
    prepared = AnalyticsService._prepare(raw)
    assert list(prepared['sale_id']) == [1]


def test_prepare_fills_missing_money_columns():
    raw = pd.DataFrame([
        {'sale_id': 1, 'sale_date': '2024-01-01'},
    ])
    prepared = AnalyticsService._prepare(raw)
    row = prepared.iloc[0]
    assert row['total'] == 0.0
    assert row['card_amount'] == 0.0
    assert row['cash_amount'] == 0.0
    assert row['quantity'] == 1


def test_prepare_preserves_extra_columns():
    raw = pd.DataFrame([
        {
            'sale_id': 1,
            'sale_date': '2024-01-01',
            'total': 10.0,
            'source': 'shopify',
            'external_id': 'shp_123',
        },
    ])
    prepared = AnalyticsService._prepare(raw)
    assert 'source' in prepared.columns
    assert 'external_id' in prepared.columns
    assert prepared.iloc[0]['source'] == 'shopify'
