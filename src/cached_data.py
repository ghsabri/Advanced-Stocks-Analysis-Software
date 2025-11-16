"""
Shared Data Cache Module
This module provides a single cached data fetching function that ALL pages use.
This ensures data is fetched once and shared across TR Indicator, Pattern Detection, etc.

IMPORTANT: Uses @st.cache_data for efficient caching
"""

import streamlit as st
import pandas as pd


# Dictionary to store cached data globally
_global_cache = {}


def get_shared_stock_data(ticker, duration_days, timeframe='daily', api_source='yahoo', include_tr=False):
    """
    Fetch stock data with OPTIONAL TR analysis - SHARED CACHE across all pages
    
    Uses a global dictionary cache that persists across all pages.
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'TSLA')
        duration_days (int): Number of days of history (180, 365, 1095, 1825)
        timeframe (str): 'daily' or 'weekly'
        api_source (str): 'yahoo' or 'tiingo'
        include_tr (bool): If True, include TR analysis (default: False for speed)
    
    Returns:
        pd.DataFrame: Stock data with OHLCV + optional TR analysis
    
    Cache Details:
        - Cached globally across ALL pages
        - Cache key: ticker + duration_days + timeframe + api_source + include_tr
    """
    
    # NORMALIZE parameters to ensure cache key matches!
    ticker = ticker.upper().strip()
    timeframe = timeframe.lower().strip()
    api_source = api_source.lower().strip()
    duration_days = int(duration_days)
    
    # Create normalized cache key
    cache_key = f"{ticker}_{duration_days}_{timeframe}_{api_source}_tr{include_tr}"
    
    # Check if data is in global cache
    if cache_key in _global_cache:
        print(f"✅ USING CACHED DATA: {cache_key}")
        return _global_cache[cache_key]
    
    # Data not in cache - fetch it
    print(f"🔄 FETCHING NEW DATA: {cache_key}")
    
    # Choose fetching method based on include_tr flag
    if include_tr:
        # Full TR analysis (for TR Indicator page)
        df = _fetch_with_tr_analysis(ticker, timeframe, duration_days)
    else:
        # Simple OHLCV data (for Indicator Chart, Seasonality, etc.)
        df = _fetch_simple_data(ticker, timeframe, duration_days, api_source)
    
    if df is not None and not df.empty:
        # Store in global cache
        _global_cache[cache_key] = df
        print(f"💾 DATA CACHED GLOBALLY: {cache_key} ({len(df)} rows)")
    else:
        print(f"❌ NO DATA: {ticker}")
    
    return df


def _fetch_with_tr_analysis(ticker, timeframe, duration_days):
    """
    Fetch stock data WITH full TR analysis
    Used only by TR Indicator page
    """
    try:
        from tr_enhanced import analyze_stock_complete_tr
        
        print(f"📊 Running TR analysis for {ticker}...")
        
        df = analyze_stock_complete_tr(
            ticker=ticker,
            timeframe=timeframe,
            duration_days=duration_days
        )
        
        return df
        
    except ImportError:
        print("⚠️ TR modules not available - falling back to simple data")
        return _fetch_simple_data(ticker, timeframe, duration_days, 'yahoo')
    except Exception as e:
        print(f"❌ TR analysis error: {e}")
        return None


def _fetch_simple_data(ticker, timeframe, duration_days, api_source):
    """
    Fetch simple OHLCV stock data WITHOUT TR analysis
    Used by Indicator Chart, Seasonality, Pattern Detection pages
    Much faster!
    """
    try:
        if api_source == 'yahoo':
            return _fetch_yahoo_data(ticker, timeframe, duration_days)
        elif api_source == 'tiingo':
            return _fetch_tiingo_data(ticker, timeframe, duration_days)
        else:
            # Default to Yahoo
            return _fetch_yahoo_data(ticker, timeframe, duration_days)
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        return None


def _fetch_yahoo_data(ticker, timeframe, duration_days):
    """Fetch data from Yahoo Finance"""
    import yfinance as yf
    from datetime import datetime, timedelta
    
    print(f"📥 Fetching {ticker} from Yahoo Finance...")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=duration_days)
    
    # Fetch data
    stock = yf.Ticker(ticker)
    
    if timeframe == 'weekly':
        df = stock.history(start=start_date, end=end_date, interval='1wk')
    else:  # daily
        df = stock.history(start=start_date, end=end_date, interval='1d')
    
    if df.empty:
        return None
    
    # Reset index to make Date a column
    df = df.reset_index()
    
    # Standardize column names
    df.columns = [col.replace(' ', '_') for col in df.columns]
    
    # Ensure we have Date column
    if 'Date' not in df.columns and df.index.name == 'Date':
        df = df.reset_index()
    
    return df


def _fetch_tiingo_data(ticker, timeframe, duration_days):
    """Fetch data from Tiingo API"""
    # TODO: Implement Tiingo fetching if needed
    print(f"⚠️ Tiingo not implemented yet, falling back to Yahoo")
    return _fetch_yahoo_data(ticker, timeframe, duration_days)


@st.cache_data(ttl=3600, show_spinner=False)
def get_simple_stock_data(ticker, duration_days, timeframe='daily'):
    """
    Legacy function - kept for backward compatibility
    Fetch simple stock data (price only, no TR calculations)
    
    Args:
        ticker (str): Stock symbol
        duration_days (int): Days of history
        timeframe (str): 'daily' or 'weekly'
    
    Returns:
        pd.DataFrame: Basic OHLCV data
    """
    
    return get_shared_stock_data(
        ticker=ticker,
        duration_days=duration_days,
        timeframe=timeframe,
        api_source='yahoo',
        include_tr=False  # No TR analysis
    )


def clear_cache():
    """Clear all cached stock data"""
    global _global_cache
    _global_cache.clear()
    st.cache_data.clear()
    print("🗑️ All caches cleared!")


# Convenience functions for common use cases

def get_stock_for_indicator_chart(ticker, duration_days, timeframe='daily', api_source='yahoo'):
    """
    Get stock data for Indicator Chart page
    NO TR analysis - just OHLCV data
    FAST!
    """
    return get_shared_stock_data(
        ticker=ticker,
        duration_days=duration_days,
        timeframe=timeframe,
        api_source=api_source,
        include_tr=False  # Fast mode
    )


def get_stock_for_tr_analysis(ticker, duration_days, timeframe='daily'):
    """
    Get stock data for TR Indicator page
    WITH full TR analysis
    Slower but includes all TR calculations
    """
    return get_shared_stock_data(
        ticker=ticker,
        duration_days=duration_days,
        timeframe=timeframe,
        api_source='yahoo',
        include_tr=True  # Full TR analysis
    )


def get_stock_for_patterns(ticker, duration_days, timeframe='daily', api_source='yahoo'):
    """
    Get stock data for Pattern Detection page
    NO TR analysis - just OHLCV data
    FAST!
    """
    return get_shared_stock_data(
        ticker=ticker,
        duration_days=duration_days,
        timeframe=timeframe,
        api_source=api_source,
        include_tr=False  # Fast mode
    )


def get_stock_for_seasonality(ticker, duration_days, timeframe='daily', api_source='yahoo'):
    """
    Get stock data for Seasonality page
    NO TR analysis - just OHLCV data
    FAST!
    """
    return get_shared_stock_data(
        ticker=ticker,
        duration_days=duration_days,
        timeframe=timeframe,
        api_source=api_source,
        include_tr=False  # Fast mode
    )
