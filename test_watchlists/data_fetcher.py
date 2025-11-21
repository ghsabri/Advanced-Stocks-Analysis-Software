"""
Data Fetcher - Unified interface for stock data
Supports both Yahoo Finance (free, unlimited) and Tiingo (professional)
"""

import pandas as pd
import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
import json

# Try to load config, use defaults if not available
try:
    from config.config import TIINGO_API_KEY, DEFAULT_DATA_SOURCE
except ImportError:
    TIINGO_API_KEY = None
    DEFAULT_DATA_SOURCE = "yahoo"  # Default to Yahoo Finance


def fetch_stock_data_yahoo(symbol, start_date=None, end_date=None, interval='1d'):
    """
    Fetch stock data from Yahoo Finance (FREE, UNLIMITED)
    
    Args:
        symbol (str): Stock ticker symbol
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval ('1d' for daily, '1wk' for weekly)
    
    Returns:
        pd.DataFrame: Stock data
    """
    
    try:
        # Default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            print(f"⚠️ No data returned for {symbol} from Yahoo Finance")
            return None
        
        # Standardize column names
        df = df.reset_index()
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Add symbol column
        df['symbol'] = symbol.upper()
        
        # Select and reorder columns
        df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching {symbol} from Yahoo Finance: {str(e)}")
        return None


def fetch_stock_data_tiingo(symbol, start_date=None, end_date=None, interval='daily'):
    """
    Fetch stock data from Tiingo API (PROFESSIONAL, RATE LIMITED)
    Requires TIINGO_API_KEY in config
    
    Args:
        symbol (str): Stock ticker symbol
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
        interval (str): Data interval ('daily' or 'weekly')
    
    Returns:
        pd.DataFrame: Stock data
    """
    
    if not TIINGO_API_KEY:
        print("⚠️ Tiingo API key not configured. Please add TIINGO_API_KEY to config/config.py")
        print("💡 Falling back to Yahoo Finance...")
        return fetch_stock_data_yahoo(symbol, start_date, end_date, '1d' if interval == 'daily' else '1wk')
    
    try:
        # Default dates if not provided
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Build Tiingo API URL
        base_url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'token': TIINGO_API_KEY
        }
        
        # Add resampling for weekly data
        if interval == 'weekly':
            params['resampleFreq'] = 'weekly'
        
        # Make API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print(f"⚠️ No data returned for {symbol} from Tiingo")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Standardize column names
        df = df.rename(columns={
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Add symbol column
        df['symbol'] = symbol.upper()
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Select and reorder columns
        df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
        
        return df
    
    except Exception as e:
        print(f"❌ Error fetching {symbol} from Tiingo: {str(e)}")
        print("💡 Falling back to Yahoo Finance...")
        return fetch_stock_data_yahoo(symbol, start_date, end_date, '1d' if interval == 'daily' else '1wk')


def fetch_stock_data(symbol, source=None, start_date=None, end_date=None, 
                     timeframe='daily', duration_days=365):
    """
    Unified function to fetch stock data from Yahoo or Tiingo
    
    Args:
        symbol (str): Stock ticker symbol
        source (str): 'yahoo' or 'tiingo' (default: from config or 'yahoo')
        start_date (str): Start date (YYYY-MM-DD) - optional
        end_date (str): End date (YYYY-MM-DD) - optional
        timeframe (str): 'daily' or 'weekly'
        duration_days (int): Number of days of history (if start_date not provided)
    
    Returns:
        pd.DataFrame: Stock data in standardized format
    """
    
    # Determine data source
    if source is None:
        source = DEFAULT_DATA_SOURCE
    
    source = source.lower()
    
    # Calculate start date if not provided
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=duration_days)).strftime('%Y-%m-%d')
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Map timeframe to interval
    interval = 'daily' if timeframe.lower() == 'daily' else 'weekly'
    
    print(f"📡 Fetching {symbol} data from {source.upper()}...")
    print(f"   Period: {start_date} to {end_date} ({timeframe})")
    
    # Fetch from selected source
    if source == 'tiingo':
        df = fetch_stock_data_tiingo(symbol, start_date, end_date, interval)
    else:  # Default to Yahoo
        yahoo_interval = '1d' if interval == 'daily' else '1wk'
        df = fetch_stock_data_yahoo(symbol, start_date, end_date, yahoo_interval)
    
    if df is not None and not df.empty:
        print(f"✅ Fetched {len(df)} data points for {symbol}")
        return df
    else:
        print(f"❌ Failed to fetch data for {symbol}")
        return None


# Test function
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 DATA FETCHER TEST")
    print("="*80)
    
    # Test Yahoo Finance
    print("\n1️⃣ Testing Yahoo Finance (FREE, UNLIMITED):")
    print("-"*80)
    df_yahoo = fetch_stock_data('AAPL', source='yahoo', duration_days=30, timeframe='daily')
    if df_yahoo is not None:
        print(f"✅ Yahoo: Retrieved {len(df_yahoo)} days of data")
        print(df_yahoo.tail(3))
    
    # Test Tiingo
    print("\n2️⃣ Testing Tiingo API (if configured):")
    print("-"*80)
    df_tiingo = fetch_stock_data('AAPL', source='tiingo', duration_days=30, timeframe='daily')
    if df_tiingo is not None:
        print(f"✅ Tiingo: Retrieved {len(df_tiingo)} days of data")
        print(df_tiingo.tail(3))
    
    print("\n" + "="*80)
    print("✅ DATA FETCHER TEST COMPLETE!")
    print("="*80)
