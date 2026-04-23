"""Tests for analytics metric aggregations on the canonical frame."""

from __future__ import annotations

import pandas as pd
import pytest

from app.services.analytics_service import AnalyticsService


def test_get_dashboard_summary_empty_frame_has_stable_shape():
    svc = AnalyticsService()
    result = svc.get_dashboard_summary(pd.DataFrame())
    for key in (
        'total_revenue', 'total_transactions', 'avg_transaction',
        'today_sales', 'today_transactions', 'this_month_sales',
        'top_product', 'top_store', 'daily_change', 'weekly_change',
        'yesterday_sales', 'this_week_sales',
    ):
        assert key in result


def test_get_dashboard_summary_total_revenue_matches_sum(prepared_df):
    svc = AnalyticsService()
    result = svc.get_dashboard_summary(prepared_df)
    # Fixture totals: 40 + 50 + 30 (fallback) + 20 = 140
    assert result['total_revenue'] == pytest.approx(140.0)
    assert result['total_transactions'] == len(prepared_df)


def test_get_dashboard_summary_top_product_and_store(prepared_df):
    svc = AnalyticsService()
    result = svc.get_dashboard_summary(prepared_df)
    # Store A: 40 + 50 = 90; Store B: 30 + 20 = 50 -> top = Store A
    assert result['top_store'] == 'Store A'
    # T-Shirt: 40 + 20 = 60; Hoodie: 50; Cap: 30 -> top = T-Shirt
    assert result['top_product'] == 'T-Shirt'


def test_get_day_analytics_empty_frame_stable_shape():
    svc = AnalyticsService()
    result = svc.get_day_analytics(pd.DataFrame())
    assert result == {'stats': [], 'peak_day': None, 'avg_daily_revenue': 0.0}


def test_get_day_analytics_uses_canonical_columns(prepared_df):
    svc = AnalyticsService()
    result = svc.get_day_analytics(prepared_df)
    assert result['stats'], 'expected day-of-week rows'
    first = result['stats'][0]
    for key in ('day_of_week', 'total_revenue', 'total_items',
                'avg_sale', 'transaction_count'):
        assert key in first
    totals = sum(row['total_revenue'] for row in result['stats'])
    assert totals == pytest.approx(140.0)


def test_get_monthly_analytics_empty_frame_stable_shape():
    svc = AnalyticsService()
    result = svc.get_monthly_analytics(pd.DataFrame())
    assert result == {
        'stats': [], 'peak_month': None, 'avg_monthly_revenue': 0.0,
    }


def test_get_monthly_analytics_aggregates_by_month(prepared_df):
    svc = AnalyticsService()
    result = svc.get_monthly_analytics(prepared_df)
    assert len(result['stats']) == 2  # Jan + Feb 2024
    jan = next(r for r in result['stats'] if r['month'].startswith('January'))
    feb = next(r for r in result['stats'] if r['month'].startswith('February'))
    assert jan['total_revenue'] == pytest.approx(120.0)  # 40 + 50 + 30
    assert feb['total_revenue'] == pytest.approx(20.0)
    assert result['peak_month'].startswith('January')


def test_get_store_analytics_revenue_split(prepared_df):
    svc = AnalyticsService()
    result = svc.get_store_analytics(prepared_df)
    stats_by_store = {r['store_name']: r for r in result['stats']}
    assert stats_by_store['Store A']['total_revenue'] == pytest.approx(90.0)
    assert stats_by_store['Store B']['total_revenue'] == pytest.approx(50.0)
    assert result['peak_store'] == 'Store A'
    assert result['worst_store'] == 'Store B'


def test_get_category_analytics_revenue_split(prepared_df):
    svc = AnalyticsService()
    result = svc.get_category_analytics(prepared_df)
    stats_by_cat = {r['product_category']: r for r in result['stats']}
    # Apparel: 40 + 50 + 20 = 110; Accessories: 30
    assert stats_by_cat['Apparel']['total_revenue'] == pytest.approx(110.0)
    assert stats_by_cat['Accessories']['total_revenue'] == pytest.approx(30.0)


def test_generate_reports_returns_best_and_worst_buckets(prepared_df):
    svc = AnalyticsService()
    result = svc.generate_reports(prepared_df)
    for key in ('best_products', 'worst_products',
                'best_stores', 'worst_stores',
                'best_categories', 'worst_categories',
                'best_days', 'worst_days'):
        assert key in result
