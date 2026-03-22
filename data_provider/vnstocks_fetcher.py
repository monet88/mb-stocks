# -*- coding: utf-8 -*-
"""
===================================
VnstocksFetcher - Vietnam Market Data Source
===================================

Data source: vnstock library (https://github.com/thinh-vu/vnstock)
Supports: Daily historical data for Vietnamese stocks (HOSE, HNX, UPCOM)

Convention: Use VN: prefix (e.g. VN:FPT, VN:ACB, VN:VCB)
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS
from .realtime_types import (
    UnifiedRealtimeQuote,
    RealtimeSource,
    safe_float,
    safe_int,
    get_realtime_circuit_breaker,
)

logger = logging.getLogger(__name__)


class VnstocksFetcher(BaseFetcher):
    """
    Vietnam stock market data source via vnstock library.

    Priority: configurable via VNSTOCK_PRIORITY env var (default: 3)
    Data source: VCI (default), configurable via VNSTOCK_SOURCE env var
    """

    name = "VnstocksFetcher"
    priority = int(os.getenv("VNSTOCK_PRIORITY", "3"))
    supported_markets = {'vn'}

    # Stock name cache (class-level, shared across instances)
    _vn_name_cache: dict = {}
    _vn_name_cache_ts: float = 0

    def __init__(self):
        # Fail fast if vnstock is not installed
        import vnstock  # noqa: F401

        api_key = os.getenv("VNSTOCK_API_KEY", "").strip()
        if api_key:
            try:
                from vnstock import register_user
                register_user(api_key=api_key)
                logger.info("[VnstocksFetcher] API key registered (Community/Sponsor tier)")
            except Exception as e:
                logger.warning(
                    f"[VnstocksFetcher] API key registration failed: {e}. "
                    "Using Guest tier (20 req/min)"
                )
        else:
            logger.info("[VnstocksFetcher] No VNSTOCK_API_KEY, using Guest tier (20 req/min)")

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        from vnstock import Quote

        source = os.getenv("VNSTOCK_SOURCE", "VCI")
        quote = Quote(symbol=stock_code, source=source)
        df = quote.history(start=start_date, end=end_date, interval='1D')
        if df is None or df.empty:
            raise DataFetchError(
                f"vnstock returned no data for {stock_code} (source={source})"
            )
        return df

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        required = {'time', 'open', 'high', 'low', 'close', 'volume'}
        missing = required - set(df.columns)
        if missing:
            raise DataFetchError(
                f"vnstock returned unexpected schema for {stock_code}: "
                f"missing columns {missing}"
            )

        df = df.copy()
        df = df.rename(columns={'time': 'date'})

        if 'volume' in df.columns and 'close' in df.columns:
            df['amount'] = df['volume'] * df['close']
        else:
            df['amount'] = 0

        if 'close' in df.columns:
            df['pct_chg'] = df['close'].pct_change() * 100
            df['pct_chg'] = df['pct_chg'].fillna(0).round(2)

        df['code'] = stock_code

        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]
        return df

    # ──────────────────────────────────────────────
    # Realtime Quote (V2)
    # ──────────────────────────────────────────────

    def get_realtime_quote(self, stock_code: str, source: str = "") -> Optional[UnifiedRealtimeQuote]:
        """
        Hybrid realtime quote for VN stocks.

        During VN trading hours: fetch latest tick via quote.intraday()
        + previous close via quote.history() for change_pct computation.
        Outside trading hours: fallback to last daily close.

        Args:
            stock_code: VN stock symbol WITHOUT VN: prefix (e.g. 'FPT')
            source: ignored, kept for interface compatibility
        """
        circuit_breaker = get_realtime_circuit_breaker()
        cb_key = f"vnstock_{stock_code}"

        if not circuit_breaker.is_available(cb_key):
            logger.debug(f"[VnstocksFetcher] circuit breaker open for {stock_code}")
            return None

        try:
            if self._is_vn_trading_hours():
                quote = self._fetch_intraday_quote(stock_code)
            else:
                quote = self._fetch_fallback_quote(stock_code)

            if quote is not None:
                circuit_breaker.record_success(cb_key)
            return quote
        except Exception as e:
            logger.warning(f"[VnstocksFetcher] realtime quote failed for {stock_code}: {e}")
            circuit_breaker.record_failure(cb_key, str(e))
            return None

    def _fetch_intraday_quote(self, stock_code: str) -> Optional[UnifiedRealtimeQuote]:
        """Fetch latest tick from intraday API + previous close for change_pct."""
        from vnstock import Quote

        vn_source = os.getenv("VNSTOCK_SOURCE", "VCI")
        quote_api = Quote(symbol=stock_code, source=vn_source)

        # Get latest intraday tick
        df_intraday = quote_api.intraday(symbol=stock_code)
        if df_intraday is None or df_intraday.empty:
            logger.warning(f"[VnstocksFetcher] intraday empty for {stock_code}, falling back to daily")
            return self._fetch_fallback_quote(stock_code)

        latest = df_intraday.iloc[-1]
        price = safe_float(latest.get('price'))
        if price is None:
            return self._fetch_fallback_quote(stock_code)

        volume = safe_int(latest.get('volume'))

        # Get previous close from daily history for change_pct
        pre_close = self._get_previous_close(stock_code, vn_source)
        change_pct = None
        change_amount = None
        if pre_close and pre_close > 0:
            change_amount = round(price - pre_close, 2)
            change_pct = round((price - pre_close) / pre_close * 100, 2)

        name = self.get_stock_name(stock_code)

        return UnifiedRealtimeQuote(
            code=stock_code,
            name=name,
            source=RealtimeSource.VNSTOCK,
            price=price,
            change_pct=change_pct,
            change_amount=change_amount,
            volume=volume,
            pre_close=pre_close,
        )

    def _fetch_fallback_quote(self, stock_code: str) -> Optional[UnifiedRealtimeQuote]:
        """Fallback: use last daily close as realtime quote."""
        from vnstock import Quote

        vn_source = os.getenv("VNSTOCK_SOURCE", "VCI")
        quote_api = Quote(symbol=stock_code, source=vn_source)

        end = datetime.now().strftime('%Y-%m-%d')
        # Fetch last 10 days to ensure we get at least 2 trading days
        from datetime import timedelta
        start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

        df = quote_api.history(start=start, end=end, interval='1D')
        if df is None or df.empty:
            return None

        latest = df.iloc[-1]
        price = safe_float(latest.get('close'))
        if price is None:
            return None

        pre_close = safe_float(df.iloc[-2].get('close')) if len(df) >= 2 else None
        change_pct = None
        change_amount = None
        if pre_close and pre_close > 0:
            change_amount = round(price - pre_close, 2)
            change_pct = round((price - pre_close) / pre_close * 100, 2)

        open_price = safe_float(latest.get('open'))
        high = safe_float(latest.get('high'))
        low = safe_float(latest.get('low'))
        volume = safe_int(latest.get('volume'))

        name = self.get_stock_name(stock_code)

        return UnifiedRealtimeQuote(
            code=stock_code,
            name=name,
            source=RealtimeSource.VNSTOCK,
            price=price,
            change_pct=change_pct,
            change_amount=change_amount,
            volume=volume,
            pre_close=pre_close,
            open_price=open_price,
            high=high,
            low=low,
        )

    def _get_previous_close(self, stock_code: str, vn_source: str) -> Optional[float]:
        """Get previous trading day close price."""
        try:
            from vnstock import Quote
            from datetime import timedelta

            quote_api = Quote(symbol=stock_code, source=vn_source)
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            df = quote_api.history(start=start, end=end, interval='1D')
            if df is not None and len(df) >= 1:
                return safe_float(df.iloc[-1].get('close'))
        except Exception as e:
            logger.debug(f"[VnstocksFetcher] previous close failed for {stock_code}: {e}")
        return None

    # ──────────────────────────────────────────────
    # Stock Name (V2)
    # ──────────────────────────────────────────────

    def get_stock_name(self, stock_code: str) -> str:
        """
        Fetch VN stock name from vnstock listing API with 24h TTL cache.

        Args:
            stock_code: VN stock symbol WITHOUT VN: prefix (e.g. 'FPT')

        Returns:
            Company name (e.g. 'FPT Corporation') or empty string
        """
        # Check cache freshness (24h TTL)
        if (time.time() - VnstocksFetcher._vn_name_cache_ts < 86400
                and VnstocksFetcher._vn_name_cache):
            return VnstocksFetcher._vn_name_cache.get(stock_code.upper(), "")

        try:
            self._refresh_name_cache()
        except Exception as e:
            logger.warning(f"[VnstocksFetcher] name cache refresh failed: {e}")
            # Return from stale cache if available
            return VnstocksFetcher._vn_name_cache.get(stock_code.upper(), "")

        return VnstocksFetcher._vn_name_cache.get(stock_code.upper(), "")

    def _refresh_name_cache(self):
        """Refresh the stock name cache from vnstock listing API."""
        from vnstock import Listing

        listing = Listing()
        df = listing.all_symbols()
        if df is not None and not df.empty:
            # Columns: ['symbol', 'organ_name', ...] per eng review V2
            VnstocksFetcher._vn_name_cache = dict(
                zip(df['symbol'].str.upper(), df['organ_name'])
            )
            VnstocksFetcher._vn_name_cache_ts = time.time()
            logger.info(
                f"[VnstocksFetcher] name cache refreshed: {len(VnstocksFetcher._vn_name_cache)} symbols"
            )

    # ──────────────────────────────────────────────
    # VN Trading Hours
    # ──────────────────────────────────────────────

    @staticmethod
    def _is_vn_trading_hours() -> bool:
        """
        Check if current time is within VN trading hours.

        VN trading sessions (GMT+7 / Asia/Ho_Chi_Minh):
        - Session 1: 09:00 - 11:30
        - Session 2: 13:00 - 15:00
        Weekdays only (Mon-Fri). Fail-open on timezone errors.
        """
        try:
            from zoneinfo import ZoneInfo

            now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            # Weekend check
            if now.weekday() >= 5:
                return False
            t = now.hour * 60 + now.minute  # minutes since midnight
            session_1 = (9 * 60) <= t < (11 * 60 + 30)   # 09:00 - 11:30
            session_2 = (13 * 60) <= t < (15 * 60)         # 13:00 - 15:00
            return session_1 or session_2
        except Exception as e:
            logger.warning(f"[VnstocksFetcher] trading hours check failed: {e}")
            return False  # Fail-closed: use fallback (daily close) on error
