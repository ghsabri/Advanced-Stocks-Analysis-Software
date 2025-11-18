"""
Cached Data Module - Uses Streamlit's Built-in Caching
Provides get_shared_stock_data() function for all pages
"""

import streamlit as st
from tr_enhanced import analyze_stock_complete_tr


@st.cache_data(ttl=3600, show_spinner=False)
def get_shared_stock_data(ticker, duration_days, timeframe='daily', api_source='yahoo'):
    """
    Fetch stock data with TR analysis - CACHED using @st.cache_data
    
    Uses Streamlit's built-in caching decorator which persists across reruns.
    The stock data AND SPY (for RS calc) will both be cached via universal_cache.
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'TSLA')
        duration_days (int): Number of days of history (180, 365, 1095, 1825)
        timeframe (str): 'daily' or 'weekly'
        api_source (str): 'yahoo' or 'tiingo'
    
    Returns:
        pd.DataFrame: Complete stock data with TR analysis, RS, Chaikin, etc.
    
    Cache Details:
        - Cached with @st.cache_data (Streamlit's built-in caching)
        - TTL: 1 hour (3600 seconds)
        - Cache key: ticker + duration_days + timeframe + api_source
        - Additionally, raw stock data is cached in universal_cache (.pkl files)
    """
    
    print(f"📊 Analyzing {ticker} ({duration_days} days, {timeframe}, {api_source})")
    
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe=timeframe,
        duration_days=duration_days,
        api_source=api_source  # Pass api_source through!
    )
    
    if df is not None and not df.empty:
        print(f"✅ Analysis complete: {ticker} ({len(df)} rows)")
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
    
    print(f"📊 Getting simple data for {ticker} ({duration_days} days)")
    
    df = get_stock_data_formatted(
        ticker=ticker,
        timeframe=timeframe,
        days=duration_days,
        save=False
    )
    
    return df


def clear_cache():
    """Clear all cached stock data"""
    st.cache_data.clear()
    print("🗑️ Streamlit cache cleared!")
