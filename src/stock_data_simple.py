"""
Simple Stock Data Fetcher - NO TR CALCULATIONS
For use in Pattern Detection and Seasonality where TR is not needed
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os

TIINGO_API_KEY = os.getenv('TIINGO_API_KEY', 'f510dea5eaff00ce87e00d98833866d7dc313b78')


def get_stock_data_simple(ticker, duration_days=365):
    """
    Fetch stock data WITHOUT TR calculations
    Much faster than analyze_stock_complete_tr
    
    Args:
        ticker: Stock symbol
        duration_days: Number of days of historical data
    
    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume
    """
    try:
        # Calculate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=duration_days + 100)  # Extra buffer
        
        # Format dates
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Tiingo API endpoint
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        
        params = {
            'startDate': start_str,
            'endDate': end_str,
            'token': TIINGO_API_KEY
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Make request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"Error: API returned status {response.status_code}")
            return None
        
        data = response.json()
        
        if not data or len(data) == 0:
            print(f"No data returned for {ticker}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Rename columns to standard format
        df = df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adjClose': 'adjClose',
            'volume': 'Volume'
        })
        
        # Convert date to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by date
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Keep only what we need
        columns_to_keep = ['Date', 'Open', 'High', 'Low', 'Close', 'adjClose', 'Volume']
        df = df[[col for col in columns_to_keep if col in df.columns]]
        
        # Use adjusted close if available
        if 'adjClose' in df.columns:
            df['Close'] = df['adjClose']
        
        # Trim to requested duration
        if len(df) > duration_days:
            df = df.tail(duration_days).reset_index(drop=True)
        
        print(f"✅ Fetched {len(df)} days of data for {ticker} (NO TR calculations)")
        
        return df
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None
