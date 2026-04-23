"""Shared fixtures for the MoMetriX test suite.

These tests focus on the analytics layer, which is pure-pandas once the
canonical frame is built. We deliberately avoid spinning up a full Flask
app / DB here: analytics methods are fed DataFrames directly, which keeps
the suite fast and framework-agnostic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('FLASK_TESTING', 'true')


@pytest.fixture
def raw_sales_rows():
    """A small, deterministic raw sales dataset.

    Covers: multiple stores, multiple categories, both payment methods,
    two consecutive months, and a row with ``total=0`` so the revenue
    fallback rule (``card + cash``) is exercised.
    """
    return [
        {
            'sale_id': 1,
            'sale_date': '2024-01-02',
            'store_name': 'Store A',
            'product_category': 'Apparel',
            'product_name': 'T-Shirt',
            'quantity': 2,
            'total': 40.0,
            'card_amount': 40.0,
            'cash_amount': 0.0,
            'payment_method': 'Card',
            'embellishments': 'None',
            'notes': None,
        },
        {
            'sale_id': 2,
            'sale_date': '2024-01-03',
            'store_name': 'Store A',
            'product_category': 'Apparel',
            'product_name': 'Hoodie',
            'quantity': 1,
            'total': 50.0,
            'card_amount': 0.0,
            'cash_amount': 50.0,
            'payment_method': 'Cash',
            'embellishments': 'None',
            'notes': None,
        },
        {
            'sale_id': 3,
            'sale_date': '2024-01-15',
            'store_name': 'Store B',
            'product_category': 'Accessories',
            'product_name': 'Cap',
            'quantity': 3,
            'total': 0.0,  # forces fallback to card+cash
            'card_amount': 15.0,
            'cash_amount': 15.0,
            'payment_method': 'Both (Card + Cash)',
            'embellishments': 'Logo',
            'notes': None,
        },
        {
            'sale_id': 4,
            'sale_date': '2024-02-05',
            'store_name': 'Store B',
            'product_category': 'Apparel',
            'product_name': 'T-Shirt',
            'quantity': 1,
            'total': 20.0,
            'card_amount': 20.0,
            'cash_amount': 0.0,
            'payment_method': 'Card',
            'embellishments': 'None',
            'notes': None,
        },
    ]


@pytest.fixture
def raw_sales_df(raw_sales_rows):
    return pd.DataFrame(raw_sales_rows)


@pytest.fixture
def prepared_df(raw_sales_df):
    from app.services.analytics_service import AnalyticsService
    return AnalyticsService._prepare(raw_sales_df)
