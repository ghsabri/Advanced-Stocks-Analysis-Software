"""
Shared Data Cache Module
This module provides a single cached data fetching function that ALL pages use.
This ensures data is fetched once and shared across TR Indicator, Pattern Detection, etc.

IMPORTANT: Uses @st.cache_resource for GLOBAL cache sharing across pages!
"""

import streamlit as st
from tr_enhanced import analyze_stock_complete_tr


# Dictionary to store cached data globally
_global_cache = {}


def get_shared_stock_data(ticker, duration_days, timeframe='daily', api_source='yahoo'):
    """
    Fetch stock data with TR analysis - SHARED CACHE across all pages
    
    Uses a global dictionary cache that persists across all pages.
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'TSLA')
        duration_days (int): Number of days of history (180, 365, 1095, 1825)
        timeframe (str): 'daily' or 'weekly'
        api_source (str): 'yahoo' or 'tiingo'
    
    Returns:
        pd.DataFrame: Complete stock data with TR analysis, RS, Chaikin, etc.
    
    Cache Details:
        - Cached globally across ALL pages
        - Same data shared across TR Indicator, Pattern Detection, Seasonality pages
        - Cache key: ticker + duration_days + timeframe + api_source
    """
    
    # NORMALIZE parameters to ensure cache key matches!
    ticker = ticker.upper().strip()
    timeframe = timeframe.lower().strip()
    api_source = api_source.lower().strip()
    duration_days = int(duration_days)
    
    # Create normalized cache key
    cache_key = f"{ticker}_{duration_days}_{timeframe}_{api_source}"
    
    # Check if data is in global cache
    if cache_key in _global_cache:
        print(f"✅ USING CACHED DATA: {cache_key}")
        return _global_cache[cache_key]
    
    # Data not in cache - fetch it
    print(f"🔄 FETCHING NEW DATA: {cache_key}")
    
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe=timeframe,
        duration_days=duration_days
    )
    
    if df is not None and not df.empty:
        # Store in global cache
        _global_cache[cache_key] = df
        print(f"💾 DATA CACHED GLOBALLY: {cache_key} ({len(df)} rows)")
    else:
        print(f"❌ NO DATA: {ticker}")
    
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_simple_stock_data(ticker, duration_days, timeframe='daily'):
    """
    Fetch simple stock data (price only, no TR calculations)
    Use this for Seasonality page which doesn't need TR
    
    Args:
        ticker (str): Stock symbol
        duration_days (int): Days of history
        timeframe (str): 'daily' or 'weekly'
    
    Returns:
        pd.DataFrame: Basic OHLCV data
    """
    
    from stock_data_formatter import get_stock_data_formatted
    
    print(f"🔄 FETCHING SIMPLE DATA: {ticker} ({duration_days} days)")
    
    df = get_stock_data_formatted(
        ticker=ticker,
        timeframe=timeframe,
        days=duration_days,
        save=False
    )
    
    return df


def clear_cache():
    """Clear all cached stock data"""
    global _global_cache
    _global_cache.clear()
    print("🗑️ Global cache cleared!")
