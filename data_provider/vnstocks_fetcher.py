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

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS

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

    def __init__(self):
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
