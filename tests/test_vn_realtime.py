# -*- coding: utf-8 -*-
"""
Tests for VN Realtime Quotes V2.

Covers:
- get_realtime_quote during trading hours (T1-T3)
- get_realtime_quote off-hours / fallback (T4-T6)
- get_realtime_quote error handling (T7-T9)
- get_stock_name (T10-T13)
- _is_vn_trading_hours (T14-T18)
- Manager realtime routing (T19-T21)
- Trading calendar VN support (T22-T24)
"""

import sys
import unittest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd

# Mock heavy optional deps before importing project modules
if "litellm" not in sys.modules:
    sys.modules["litellm"] = MagicMock()
if "json_repair" not in sys.modules:
    sys.modules["json_repair"] = MagicMock()

from data_provider.realtime_types import (
    UnifiedRealtimeQuote,
    RealtimeSource,
    CircuitBreaker,
)


# ─── Helper: build a VnstocksFetcher without calling __init__ ───

def _make_fetcher():
    from data_provider.vnstocks_fetcher import VnstocksFetcher
    fetcher = VnstocksFetcher.__new__(VnstocksFetcher)
    return fetcher


# ─── T1-T3: get_realtime_quote during trading hours ───


class TestRealtimeQuoteTradingHours(unittest.TestCase):

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=True)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_intraday_quote")
    def test_t1_intraday_during_hours(self, mock_intraday, mock_hours):
        """During trading hours, get_realtime_quote uses intraday path."""
        expected = UnifiedRealtimeQuote(
            code="FPT", name="FPT Corporation", source=RealtimeSource.VNSTOCK,
            price=120.5, change_pct=1.5, pre_close=118.72,
        )
        mock_intraday.return_value = expected
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("FPT")
        self.assertIsNotNone(result)
        self.assertEqual(result.price, 120.5)
        self.assertEqual(result.source, RealtimeSource.VNSTOCK)
        mock_intraday.assert_called_once_with("FPT")

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=True)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_intraday_quote")
    def test_t2_intraday_returns_quote_fields(self, mock_intraday, mock_hours):
        """Intraday quote populates core UnifiedRealtimeQuote fields."""
        expected = UnifiedRealtimeQuote(
            code="ACB", name="ACB Bank", source=RealtimeSource.VNSTOCK,
            price=25.0, change_pct=-0.5, change_amount=-0.13,
            volume=1000000, pre_close=25.13,
        )
        mock_intraday.return_value = expected
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("ACB")
        self.assertEqual(result.code, "ACB")
        self.assertEqual(result.change_amount, -0.13)
        self.assertEqual(result.volume, 1000000)

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=True)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_intraday_quote")
    def test_t3_intraday_empty_falls_back(self, mock_intraday, mock_hours):
        """If intraday returns None, get_realtime_quote returns None (circuit breaker not tripped)."""
        mock_intraday.return_value = None
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("FPT")
        self.assertIsNone(result)


# ─── T4-T6: get_realtime_quote off-hours / fallback ───


class TestRealtimeQuoteOffHours(unittest.TestCase):

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=False)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_fallback_quote")
    def test_t4_offhours_uses_fallback(self, mock_fallback, mock_hours):
        """Outside trading hours, fallback daily close is used."""
        expected = UnifiedRealtimeQuote(
            code="FPT", name="FPT Corporation", source=RealtimeSource.VNSTOCK,
            price=118.72, change_pct=0.8, pre_close=117.78,
            open_price=118.0, high=119.0, low=117.5,
        )
        mock_fallback.return_value = expected
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("FPT")
        self.assertIsNotNone(result)
        self.assertEqual(result.price, 118.72)
        self.assertIsNotNone(result.open_price)
        mock_fallback.assert_called_once_with("FPT")

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=False)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_fallback_quote")
    def test_t5_fallback_includes_ohlc(self, mock_fallback, mock_hours):
        """Fallback quote includes OHLC from daily data."""
        expected = UnifiedRealtimeQuote(
            code="VCB", source=RealtimeSource.VNSTOCK,
            price=90.0, open_price=89.5, high=91.0, low=89.0,
        )
        mock_fallback.return_value = expected
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("VCB")
        self.assertEqual(result.open_price, 89.5)
        self.assertEqual(result.high, 91.0)
        self.assertEqual(result.low, 89.0)

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=False)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_fallback_quote")
    def test_t6_fallback_returns_none_no_data(self, mock_fallback, mock_hours):
        """Fallback returns None when no daily data available."""
        mock_fallback.return_value = None
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("INVALID")
        self.assertIsNone(result)


# ─── T7-T9: get_realtime_quote error handling ───


class TestRealtimeQuoteErrors(unittest.TestCase):

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._is_vn_trading_hours", return_value=True)
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._fetch_intraday_quote",
           side_effect=Exception("API timeout"))
    def test_t7_exception_returns_none(self, mock_intraday, mock_hours):
        """Exception during fetch returns None gracefully."""
        fetcher = _make_fetcher()
        result = fetcher.get_realtime_quote("FPT")
        self.assertIsNone(result)

    def test_t8_circuit_breaker_blocks_after_failures(self):
        """After 3 consecutive failures, circuit breaker blocks requests."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=300)
        cb.record_failure("vnstock_FPT")
        cb.record_failure("vnstock_FPT")
        cb.record_failure("vnstock_FPT")
        self.assertFalse(cb.is_available("vnstock_FPT"))

    def test_t9_circuit_breaker_recovers_after_success(self):
        """Circuit breaker resets after a successful call."""
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=300)
        cb.record_failure("vnstock_FPT")
        cb.record_failure("vnstock_FPT")
        cb.record_success("vnstock_FPT")
        self.assertTrue(cb.is_available("vnstock_FPT"))


# ─── T10-T13: get_stock_name ───


class TestGetStockName(unittest.TestCase):

    def setUp(self):
        # Reset class-level cache before each test
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        VnstocksFetcher._vn_name_cache = {}
        VnstocksFetcher._vn_name_cache_ts = 0

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._refresh_name_cache")
    def test_t10_returns_name_from_cache(self, mock_refresh):
        """get_stock_name returns name after cache is populated."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        import time as _time
        VnstocksFetcher._vn_name_cache = {"FPT": "FPT Corporation"}
        VnstocksFetcher._vn_name_cache_ts = _time.time()

        fetcher = _make_fetcher()
        result = fetcher.get_stock_name("FPT")
        self.assertEqual(result, "FPT Corporation")
        mock_refresh.assert_not_called()

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._refresh_name_cache")
    def test_t11_cache_hit_no_api_call(self, mock_refresh):
        """Cached name does not trigger API call."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        import time as _time
        VnstocksFetcher._vn_name_cache = {"ACB": "ACB Bank"}
        VnstocksFetcher._vn_name_cache_ts = _time.time()

        fetcher = _make_fetcher()
        fetcher.get_stock_name("ACB")
        fetcher.get_stock_name("ACB")
        mock_refresh.assert_not_called()

    def test_t12_unknown_code_returns_empty(self):
        """Unknown stock code returns empty string."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        import time as _time
        VnstocksFetcher._vn_name_cache = {"FPT": "FPT Corporation"}
        VnstocksFetcher._vn_name_cache_ts = _time.time()

        fetcher = _make_fetcher()
        result = fetcher.get_stock_name("ZZZZZ")
        self.assertEqual(result, "")

    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._refresh_name_cache",
           side_effect=Exception("Network error"))
    def test_t13_refresh_failure_returns_stale_or_empty(self, mock_refresh):
        """If cache refresh fails, returns from stale cache or empty."""
        fetcher = _make_fetcher()
        result = fetcher.get_stock_name("FPT")
        self.assertEqual(result, "")


# ─── T14-T18: _is_vn_trading_hours ───


class TestIsVnTradingHours(unittest.TestCase):

    @patch("data_provider.vnstocks_fetcher.datetime")
    def test_t14_session1_is_true(self, mock_dt):
        """10:00 on Monday (session 1) -> True."""
        from zoneinfo import ZoneInfo
        mock_now = datetime(2026, 3, 23, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))  # Monday
        mock_dt.now.return_value = mock_now
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        result = VnstocksFetcher._is_vn_trading_hours()
        self.assertTrue(result)

    @patch("data_provider.vnstocks_fetcher.datetime")
    def test_t15_between_sessions_is_false(self, mock_dt):
        """12:00 on Monday (between sessions) -> False."""
        from zoneinfo import ZoneInfo
        mock_now = datetime(2026, 3, 23, 12, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        mock_dt.now.return_value = mock_now
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        result = VnstocksFetcher._is_vn_trading_hours()
        self.assertFalse(result)

    @patch("data_provider.vnstocks_fetcher.datetime")
    def test_t16_session2_is_true(self, mock_dt):
        """14:00 on Wednesday (session 2) -> True."""
        from zoneinfo import ZoneInfo
        mock_now = datetime(2026, 3, 25, 14, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))  # Wednesday
        mock_dt.now.return_value = mock_now
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        result = VnstocksFetcher._is_vn_trading_hours()
        self.assertTrue(result)

    @patch("data_provider.vnstocks_fetcher.datetime")
    def test_t17_weekend_is_false(self, mock_dt):
        """Saturday 10:00 -> False."""
        from zoneinfo import ZoneInfo
        mock_now = datetime(2026, 3, 28, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))  # Saturday
        mock_dt.now.return_value = mock_now
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        result = VnstocksFetcher._is_vn_trading_hours()
        self.assertFalse(result)

    @patch("data_provider.vnstocks_fetcher.datetime")
    def test_t18_after_hours_is_false(self, mock_dt):
        """17:00 on Monday (after close) -> False."""
        from zoneinfo import ZoneInfo
        mock_now = datetime(2026, 3, 23, 17, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
        mock_dt.now.return_value = mock_now
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        result = VnstocksFetcher._is_vn_trading_hours()
        self.assertFalse(result)


# ─── T19-T21: Manager realtime routing ───


class _DummyRealtimeFetcher:
    def __init__(self, name, priority, supported_markets=None, quote_result=None):
        self.name = name
        self.priority = priority
        self.supported_markets = supported_markets or set()
        self.quote_result = quote_result
        self.realtime_calls = []

    def get_realtime_quote(self, stock_code, source=""):
        self.realtime_calls.append(stock_code)
        return self.quote_result


class TestManagerRealtimeRouting(unittest.TestCase):

    @patch("src.config.get_config")
    def test_t19_vn_fpt_routes_to_vnstocks(self, mock_config):
        """VN:FPT realtime routes to VnstocksFetcher."""
        mock_config.return_value.enable_realtime_quote = True
        vn_quote = UnifiedRealtimeQuote(
            code="FPT", source=RealtimeSource.VNSTOCK, price=120.5
        )
        vn = _DummyRealtimeFetcher("VnstocksFetcher", 3, {'vn'}, vn_quote)
        us = _DummyRealtimeFetcher("YfinanceFetcher", 4)

        from data_provider.base import DataFetcherManager
        manager = DataFetcherManager(fetchers=[us, vn])
        result = manager.get_realtime_quote("VN:FPT")

        self.assertIsNotNone(result)
        self.assertEqual(result.price, 120.5)
        self.assertEqual(vn.realtime_calls, ["FPT"])
        self.assertEqual(us.realtime_calls, [])

    @patch("src.config.get_config")
    def test_t20_vnm_does_not_route_to_vnstocks(self, mock_config):
        """VNM (US ETF) does NOT route to VnstocksFetcher for realtime."""
        mock_config.return_value.enable_realtime_quote = True
        us_quote = UnifiedRealtimeQuote(
            code="VNM", source=RealtimeSource.STOOQ, price=15.0
        )
        vn = _DummyRealtimeFetcher("VnstocksFetcher", 3, {'vn'})
        us = _DummyRealtimeFetcher("YfinanceFetcher", 4, quote_result=us_quote)

        from data_provider.base import DataFetcherManager
        manager = DataFetcherManager(fetchers=[us, vn])
        result = manager.get_realtime_quote("VNM")

        self.assertEqual(vn.realtime_calls, [])

    @patch("src.config.get_config")
    def test_t21_vn_fallback_returns_none(self, mock_config):
        """VN stock with no fetcher returns None gracefully."""
        mock_config.return_value.enable_realtime_quote = True
        us = _DummyRealtimeFetcher("YfinanceFetcher", 4)

        from data_provider.base import DataFetcherManager
        manager = DataFetcherManager(fetchers=[us])
        result = manager.get_realtime_quote("VN:FPT")

        self.assertIsNone(result)


# ─── T22-T24: Trading calendar VN support ───


class TestTradingCalendarVN(unittest.TestCase):

    def test_t22_market_open_weekday(self):
        """VN market is open on weekdays."""
        from src.core.trading_calendar import is_market_open
        monday = date(2026, 3, 23)  # Monday
        self.assertTrue(is_market_open("vn", monday))

    def test_t23_market_closed_weekend(self):
        """VN market is closed on weekends."""
        from src.core.trading_calendar import is_market_open
        saturday = date(2026, 3, 28)  # Saturday
        self.assertFalse(is_market_open("vn", saturday))

    def test_t24_get_market_for_stock_vn(self):
        """get_market_for_stock returns 'vn' for VN:FPT."""
        from src.core.trading_calendar import get_market_for_stock
        self.assertEqual(get_market_for_stock("VN:FPT"), "vn")


# ─── T25-T28: Integration tests (DataFrame→Quote mapping) ───


class TestIntradayQuoteMapping(unittest.TestCase):
    """Test _fetch_intraday_quote with real DataFrame, mock at vnstock.Quote level."""

    def setUp(self):
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        import time as _time
        VnstocksFetcher._vn_name_cache = {"FPT": "FPT Corporation"}
        VnstocksFetcher._vn_name_cache_ts = _time.time()

    @patch("vnstock.Quote")
    @patch("data_provider.vnstocks_fetcher.VnstocksFetcher._get_previous_close", return_value=118.0)
    def test_t25_intraday_dataframe_to_quote(self, mock_prev, mock_quote_cls):
        """Full intraday pipeline: DataFrame → safe_float → change_pct → UnifiedRealtimeQuote."""
        mock_api = MagicMock()
        mock_quote_cls.return_value = mock_api
        mock_api.intraday.return_value = pd.DataFrame({
            'time': ['09:15:00'],
            'price': [120.5],
            'volume': [5000],
            'match_type': ['ATO'],
            'id': [1],
        })

        fetcher = _make_fetcher()
        result = fetcher._fetch_intraday_quote("FPT")

        self.assertIsNotNone(result)
        self.assertEqual(result.price, 120.5)
        self.assertEqual(result.pre_close, 118.0)
        self.assertAlmostEqual(result.change_pct, round((120.5 - 118.0) / 118.0 * 100, 2))
        self.assertEqual(result.change_amount, round(120.5 - 118.0, 2))
        self.assertEqual(result.volume, 5000)
        self.assertEqual(result.name, "FPT Corporation")
        self.assertEqual(result.source, RealtimeSource.VNSTOCK)


class TestFallbackQuoteMapping(unittest.TestCase):
    """Test _fetch_fallback_quote with real DataFrame, mock at vnstock.Quote level."""

    def setUp(self):
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        import time as _time
        VnstocksFetcher._vn_name_cache = {"FPT": "FPT Corporation"}
        VnstocksFetcher._vn_name_cache_ts = _time.time()

    @patch("vnstock.Quote")
    def test_t26_fallback_dataframe_to_quote_with_ohlc(self, mock_quote_cls):
        """Full fallback pipeline: 2-day history → OHLC + change_pct → UnifiedRealtimeQuote."""
        mock_api = MagicMock()
        mock_quote_cls.return_value = mock_api
        mock_api.history.return_value = pd.DataFrame({
            'time': ['2026-03-20', '2026-03-21'],
            'open': [115.0, 117.0],
            'high': [116.0, 119.5],
            'low': [114.5, 116.5],
            'close': [115.5, 118.7],
            'volume': [100000, 120000],
        })

        fetcher = _make_fetcher()
        result = fetcher._fetch_fallback_quote("FPT")

        self.assertIsNotNone(result)
        self.assertEqual(result.price, 118.7)
        self.assertEqual(result.pre_close, 115.5)
        self.assertAlmostEqual(result.change_pct, round((118.7 - 115.5) / 115.5 * 100, 2))
        self.assertEqual(result.open_price, 117.0)
        self.assertEqual(result.high, 119.5)
        self.assertEqual(result.low, 116.5)
        self.assertEqual(result.volume, 120000)

    @patch("vnstock.Quote")
    def test_t27_fallback_single_day_no_preclose(self, mock_quote_cls):
        """Fallback with only 1 day of data: pre_close is None, no change_pct."""
        mock_api = MagicMock()
        mock_quote_cls.return_value = mock_api
        mock_api.history.return_value = pd.DataFrame({
            'time': ['2026-03-21'],
            'open': [117.0],
            'high': [119.5],
            'low': [116.5],
            'close': [118.7],
            'volume': [120000],
        })

        fetcher = _make_fetcher()
        result = fetcher._fetch_fallback_quote("FPT")

        self.assertIsNotNone(result)
        self.assertEqual(result.price, 118.7)
        self.assertIsNone(result.pre_close)
        self.assertIsNone(result.change_pct)
        self.assertIsNone(result.change_amount)


class TestPreviousCloseDefense(unittest.TestCase):
    """Test _get_previous_close partial-day defense (Issue 1 fix)."""

    @patch("vnstock.Quote")
    def test_t28_previous_close_skips_today_partial(self, mock_quote_cls):
        """If last history row is today, use the row before it."""
        from data_provider.vnstocks_fetcher import VnstocksFetcher
        from datetime import datetime as real_dt

        mock_api = MagicMock()
        mock_quote_cls.return_value = mock_api
        today_str = real_dt.now().strftime('%Y-%m-%d')
        mock_api.history.return_value = pd.DataFrame({
            'time': ['2026-03-20', today_str],
            'close': [115.5, 118.0],
        })

        fetcher = _make_fetcher()
        result = fetcher._get_previous_close("FPT", "VCI")

        # Should return 115.5 (yesterday), not 118.0 (today's partial)
        self.assertEqual(result, 115.5)


if __name__ == "__main__":
    unittest.main()
