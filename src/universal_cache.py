"""
UNIVERSAL STOCK DATA CACHE - MULTIPROCESSING COMPATIBLE
========================================================
Caches ALL stock/ETF data with multiprocessing support
Works across parallel worker processes

Features:
- Caches any ticker (AAPL, MSFT, SPY, QQQ, etc.)
- SHARED cache across parallel workers
- Thread-safe and process-safe
- Works in scanner and Streamlit
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import pickle
from pathlib import Path

# Use file-based cache for multiprocessing compatibility
CACHE_DIR = Path(__file__).parent / '.stock_cache'
CACHE_DIR.mkdir(exist_ok=True)

def _get_cache_key(ticker, start_date, end_date, interval='1d'):
    """Generate unique cache key"""
    start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
    end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
    return f"{ticker.upper()}_{start_str}_{end_str}_{interval}"

def _get_cache_file(cache_key):
    """Get cache file path"""
    return CACHE_DIR / f"{cache_key}.pkl"

def _fetch_from_yahoo(ticker, start_date, end_date, interval='1d'):
    """Fetch data from Yahoo Finance"""
    try:
        import yfinance as yf
        
        print(f"   🔍 Fetching {ticker} from Yahoo Finance... ({interval})")
        
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False
        )
        
        if df.empty:
            print(f"   ⚠️  No data returned for {ticker}")
            return None
        
        # Handle multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Reset index to get Date as column
        df = df.reset_index()
        
        # Ensure Date column
        if 'Date' not in df.columns:
            df['Date'] = df.index
        
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df
        
    except Exception as e:
        print(f"   ❌ Yahoo error for {ticker}: {str(e)[:100]}")
        return None

def _fetch_from_tiingo(ticker, start_date, end_date):
    """Fetch data from Tiingo API"""
    try:
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('TIINGO_API_KEY')
        
        if not api_key:
            print(f"   ❌ TIINGO_API_KEY not found in environment!")
            return None
        
        print(f"   🔍 Fetching {ticker} from Tiingo API...")
        
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {api_key}'
        }
        
        params = {
            'startDate': pd.to_datetime(start_date).strftime('%Y-%m-%d'),
            'endDate': pd.to_datetime(end_date).strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"   ❌ Tiingo API error: {response.status_code}")
            return None
        
        data = response.json()
        
        if not data:
            print(f"   ⚠️  No data returned for {ticker}")
            return None
        
        # Convert to DataFrame
        rows = []
        for day in data:
            rows.append({
                'Date': day['date'][:10],
                'Open': day['open'],
                'High': day['high'],
                'Low': day['low'],
                'Close': day['close'],
                'Volume': day['volume'],
                'Adj Close': day['adjClose']
            })
        
        df = pd.DataFrame(rows)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df
        
    except Exception as e:
        print(f"   ❌ Tiingo error for {ticker}: {str(e)[:100]}")
        return None

def get_stock_data(ticker, start_date, end_date, interval='1d', api_source='yahoo', force_refresh=False):
    """
    Get stock data with file-based caching (multiprocessing compatible)
    
    Args:
        ticker: Stock symbol (AAPL, SPY, etc.)
        start_date: Start date
        end_date: End date
        interval: '1d' (daily) or '1wk' (weekly)
        api_source: 'yahoo' or 'tiingo'
        force_refresh: Force fetch even if cached
    
    Returns:
        DataFrame with OHLCV data, or None if error
    """
    ticker = ticker.upper()
    cache_key = _get_cache_key(ticker, start_date, end_date, interval)
    cache_file = _get_cache_file(cache_key)
    
    # Check cache first (unless force refresh)
    if not force_refresh and cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                df = pickle.load(f)
            print(f"   📦 Using cached data for {ticker} ({interval}, {api_source})")
            return df.copy()
        except:
            pass  # Cache corrupted, fetch fresh
    
    # Fetch from API based on source
    if api_source.lower() == 'tiingo':
        df = _fetch_from_tiingo(ticker, start_date, end_date)
    else:
        df = _fetch_from_yahoo(ticker, start_date, end_date, interval)
    
    if df is not None and not df.empty:
        print(f"   ✅ Fetched & cached {len(df)} periods for {ticker} ({api_source})")
        
        # Cache it
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except:
            pass  # Cache write failed, not critical
        
        return df.copy()
    
    return None

def get_market_data(market_ticker='SPY', start_date=None, end_date=None, interval='1d'):
    """
    Get market data (SPY, QQQ, DIA, etc.) for RS calculation
    
    Returns DataFrame with Date and Close columns
    """
    df = get_stock_data(market_ticker, start_date, end_date, interval)
    
    if df is None or df.empty:
        return None
    
    # Return only Date and Close for RS calculation
    return df[['Date', 'Close']].copy()

def clear_cache():
    """Clear all cached data"""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)
    print("   🗑️  Cache cleared")

def get_cache_stats():
    """Get cache statistics"""
    if not CACHE_DIR.exists():
        return {'cached_files': 0}
    
    files = list(CACHE_DIR.glob('*.pkl'))
    return {
        'cached_files': len(files),
        'cache_dir': str(CACHE_DIR)
    }

def prewarm_cache(tickers, start_date, end_date, interval='1d'):
    """
    Pre-fetch multiple tickers into cache
    Works across multiprocessing workers
    
    Args:
        tickers: List of tickers to cache
        start_date: Start date
        end_date: End date  
        interval: '1d' or '1wk'
    """
    print(f"\n🔥 Prewarming cache for {len(tickers)} tickers...")
    
    success = 0
    for ticker in tickers:
        df = get_stock_data(ticker, start_date, end_date, interval)
        if df is not None:
            success += 1
    
    print(f"✅ Prewarmed {success}/{len(tickers)} tickers\n")
    return success
