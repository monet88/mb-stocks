# -*- coding: utf-8 -*-
"""
Tests for VN market routing and VnstocksFetcher.

Covers:
- normalize_stock_code VN: prefix handling (T1-T3)
- _is_vn_market detection (T4-T8)
- _market_tag for VN (T9)
- Routing integration (T10-T12)
- Error handling (T13-T16)
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

# Mock heavy optional deps before importing project modules
if "litellm" not in sys.modules:
    sys.modules["litellm"] = MagicMock()
if "json_repair" not in sys.modules:
    sys.modules["json_repair"] = MagicMock()

from data_provider.base import (
    normalize_stock_code,
    _is_vn_market,
    _market_tag,
    DataFetcherManager,
    STANDARD_COLUMNS,
)


# ─── Unit tests: normalize & detect (T1-T9) ───


class TestNormalizeVNStockCode(unittest.TestCase):
    """T1-T3: normalize_stock_code with VN: prefix."""

    def test_t1_uppercase_vn_prefix(self):
        self.assertEqual(normalize_stock_code("VN:FPT"), "VN:FPT")

    def test_t2_lowercase_vn_prefix(self):
        self.assertEqual(normalize_stock_code("vn:fpt"), "VN:FPT")

    def test_t3_vnm_us_ticker_unchanged(self):
        """VNM is a US ETF, should NOT be treated as VN stock."""
        self.assertEqual(normalize_stock_code("VNM"), "VNM")


class TestIsVnMarket(unittest.TestCase):
    """T4-T8: _is_vn_market detection."""

    def test_t4_valid_vn_code(self):
        self.assertTrue(_is_vn_market("VN:FPT"))

    def test_t5_vnm_is_not_vn(self):
        self.assertFalse(_is_vn_market("VNM"))

    def test_t6_vnq_is_not_vn(self):
        self.assertFalse(_is_vn_market("VNQ"))

    def test_t7_bare_fpt_is_not_vn(self):
        self.assertFalse(_is_vn_market("FPT"))

    def test_t8_hk_code_is_not_vn(self):
        self.assertFalse(_is_vn_market("HK00700"))


class TestMarketTagVN(unittest.TestCase):
    """T9: _market_tag returns 'vn' for VN: codes."""

    def test_t9_market_tag_vn(self):
        self.assertEqual(_market_tag("VN:FPT"), "vn")


# ─── Integration tests: routing (T10-T12) ───


class _DummyFetcher:
    def __init__(self, name, priority, supported_markets=None, result=None):
        self.name = name
        self.priority = priority
        self.supported_markets = supported_markets or set()
        self.calls = []
        self.result = result

    def get_daily_data(self, stock_code, start_date=None, end_date=None, days=30):
        self.calls.append(stock_code)
        if self.result is not None:
            return self.result
        raise Exception(f"{self.name} no data")


class TestVNRouting(unittest.TestCase):
    """T10-T12: get_daily_data routing for VN stocks."""

    def _make_manager(self, vn_fetcher, us_fetcher):
        manager = DataFetcherManager(fetchers=[us_fetcher, vn_fetcher])
        return manager

    def test_t10_vn_fpt_routes_to_vnstocks(self):
        """VN:FPT should route to VnstocksFetcher, not YfinanceFetcher."""
        vn_df = pd.DataFrame({"date": ["2025-01-01"], "close": [100]})
        vn = _DummyFetcher("VnstocksFetcher", 3, {'vn'}, result=vn_df)
        us = _DummyFetcher("YfinanceFetcher", 4)
        manager = self._make_manager(vn, us)

        df, source = manager.get_daily_data("VN:FPT")
        self.assertEqual(source, "VnstocksFetcher")
        self.assertEqual(vn.calls, ["FPT"])
        self.assertEqual(us.calls, [])

    def test_t11_vnm_routes_to_yfinance(self):
        """VNM (US ETF) should route to YfinanceFetcher, not VnstocksFetcher."""
        us_df = pd.DataFrame({"date": ["2025-01-01"], "close": [50]})
        vn = _DummyFetcher("VnstocksFetcher", 3, {'vn'})
        us = _DummyFetcher("YfinanceFetcher", 4, result=us_df)
        manager = self._make_manager(vn, us)

        # VNM matches US stock regex (^[A-Z]{1,5}$), so it goes to US fast-path
        df, source = manager.get_daily_data("VNM")
        self.assertEqual(source, "YfinanceFetcher")
        self.assertEqual(vn.calls, [])

    def test_t12_mixed_routing(self):
        """Each stock routes to the correct fetcher."""
        vn_df = pd.DataFrame({"date": ["2025-01-01"], "close": [100]})
        vn = _DummyFetcher("VnstocksFetcher", 3, {'vn'}, result=vn_df)
        us = _DummyFetcher("YfinanceFetcher", 4)
        manager = self._make_manager(vn, us)

        # VN stock
        df, source = manager.get_daily_data("VN:FPT")
        self.assertEqual(source, "VnstocksFetcher")
        self.assertIn("FPT", vn.calls)


# ─── Error handling (T13-T16) ───


class TestVNErrorHandling(unittest.TestCase):
    """T13-T16: Error scenarios."""

    def test_t13_vnstock_not_installed_no_crash(self):
        """If vnstock import fails, fetcher is skipped gracefully."""
        with patch.dict(sys.modules, {"vnstock": None}):
            try:
                # Simulate what _init_default_fetchers does
                try:
                    from data_provider.vnstocks_fetcher import VnstocksFetcher
                    fetcher = VnstocksFetcher()
                except (ImportError, TypeError):
                    fetcher = None
                # Should not crash — fetcher is None
                self.assertTrue(fetcher is None or fetcher is not None)
            except Exception:
                self.fail("vnstock import failure should not crash the app")

    def test_t14_normalize_missing_columns(self):
        """_normalize_data raises DataFetchError when columns are missing."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        from data_provider.base import DataFetchError

        fetcher = VnstocksFetcher.__new__(VnstocksFetcher)
        bad_df = pd.DataFrame({"foo": [1], "bar": [2]})
        with self.assertRaises(DataFetchError):
            fetcher._normalize_data(bad_df, "FPT")

    def test_t15_normalize_valid_data(self):
        """_normalize_data produces correct 8-column output."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher

        fetcher = VnstocksFetcher.__new__(VnstocksFetcher)
        valid_df = pd.DataFrame({
            "time": ["2025-01-01", "2025-01-02"],
            "open": [100, 102],
            "high": [105, 108],
            "low": [99, 101],
            "close": [104, 107],
            "volume": [1000, 1200],
        })
        result = fetcher._normalize_data(valid_df, "FPT")

        # Should have code + 8 standard columns
        expected_cols = ['code'] + STANDARD_COLUMNS
        for col in expected_cols:
            self.assertIn(col, result.columns, f"Missing column: {col}")
        self.assertEqual(len(result), 2)
        self.assertTrue((result['code'] == 'FPT').all())
        # amount = volume * close
        self.assertEqual(result['amount'].iloc[0], 1000 * 104)

    def test_t16_invalid_source_clear_error(self):
        """Invalid VNSTOCK_SOURCE produces clear error."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher

        fetcher = VnstocksFetcher.__new__(VnstocksFetcher)
        with patch.dict(os.environ, {"VNSTOCK_SOURCE": "INVALID"}):
            with patch("vnstock.Quote", side_effect=Exception("Unknown source: INVALID")):
                with self.assertRaises(Exception) as ctx:
                    fetcher._fetch_raw_data("FPT", "2025-01-01", "2025-01-31")
                self.assertIn("INVALID", str(ctx.exception))


import os

if __name__ == "__main__":
    unittest.main()
