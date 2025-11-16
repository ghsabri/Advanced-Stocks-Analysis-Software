"""
Relative Strength (RS) Calculator
Compares stock performance vs market (S&P 500) using IBD methodology
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


def fetch_market_data(timeframe='daily', duration_days=365):
    """
    Fetch S&P 500 market data for comparison
    
    Args:
        timeframe (str): 'daily' or 'weekly'
        duration_days (int): How many days of history
    
    Returns:
        pd.DataFrame: Market data
    """
    
    try:
        # Use SPY (S&P 500 ETF) as market benchmark
        market_symbol = 'SPY'
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=duration_days + 100)  # Extra buffer for calculations
        
        # Fetch market data
        interval = '1d' if timeframe == 'daily' else '1wk'
        market = yf.Ticker(market_symbol)
        df = market.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            print(f"⚠️ Could not fetch market data ({market_symbol})")
            return None
        
        df = df.reset_index()
        df = df.rename(columns={'Date': 'date', 'Close': 'close'})
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        return df[['date', 'close']]
    
    except Exception as e:
        print(f"⚠️ Error fetching market data: {e}")
        return None


def calculate_performance(prices, periods):
    """
    Calculate price performance over different time periods
    
    Args:
        prices (pd.Series): Price series
        periods (list): List of periods (e.g., [21, 63, 126, 252] for trading days)
    
    Returns:
        dict: Performance for each period
    """
    
    performance = {}
    
    for period in periods:
        if len(prices) > period:
            current_price = prices.iloc[-1]
            past_price = prices.iloc[-period]
            
            if past_price > 0:
                perf = ((current_price - past_price) / past_price) * 100
                performance[period] = perf
            else:
                performance[period] = 0
        else:
            performance[period] = 0
    
    return performance


def calculate_relative_strength_ibd(stock_df, market_df=None, timeframe='daily'):
    """
    Calculate Relative Strength using IBD methodology
    Compares stock performance vs market over multiple timeframes
    
    IBD RS Rating weights:
    - 40% weight: Last 12 months (252 trading days)
    - 20% weight: Last 6 months (126 trading days)
    - 20% weight: Last 3 months (63 trading days)
    - 20% weight: Last 1 month (21 trading days)
    
    Args:
        stock_df (pd.DataFrame): Stock data with 'Close' column
        market_df (pd.DataFrame): Market data (optional, will fetch if None)
        timeframe (str): 'daily' or 'weekly'
    
    Returns:
        pd.Series: RS values (0-99 percentile)
    """
    
    # Determine periods based on timeframe
    if timeframe.lower() == 'daily':
        periods = {
            'year': 252,   # ~252 trading days = 1 year
            '6month': 126, # ~126 trading days = 6 months
            '3month': 63,  # ~63 trading days = 3 months
            'month': 21    # ~21 trading days = 1 month
        }
    else:  # weekly
        periods = {
            'year': 52,    # 52 weeks = 1 year
            '6month': 26,  # 26 weeks = 6 months
            '3month': 13,  # 13 weeks = 3 months
            'month': 4     # 4 weeks = 1 month
        }
    
    # Fetch market data if not provided
    if market_df is None or market_df.empty:
        duration_days = 365 if timeframe == 'daily' else 365
        market_df = fetch_market_data(timeframe, duration_days)
    
    # If still no market data, return 50 (neutral) for all
    if market_df is None or market_df.empty:
        print("⚠️ No market data available, using RS = 50 (neutral)")
        return pd.Series([50] * len(stock_df), index=stock_df.index)
    
    # Calculate RS for each row
    rs_values = []
    
    for idx in range(len(stock_df)):
        # Get stock data up to current point
        stock_prices = stock_df['Close'].iloc[:idx+1]
        
        # Get corresponding market data
        stock_date = stock_df['Date'].iloc[idx]
        market_subset = market_df[market_df['date'] <= stock_date]
        
        if len(market_subset) < 2:
            rs_values.append(50)  # Not enough data
            continue
        
        market_prices = market_subset['close']
        
        # Calculate performance for stock and market
        stock_perf = calculate_performance(stock_prices, list(periods.values()))
        market_perf = calculate_performance(market_prices, list(periods.values()))
        
        # Calculate relative performance (stock vs market) for each period
        rel_perf = {}
        for period_name, period_days in periods.items():
            if stock_perf[period_days] == 0 and market_perf[period_days] == 0:
                rel_perf[period_name] = 0
            else:
                # Relative strength = Stock performance - Market performance
                rel_perf[period_name] = stock_perf[period_days] - market_perf[period_days]
        
        # Calculate weighted RS score using IBD methodology
        # 40% last year, 20% last 6mo, 20% last 3mo, 20% last month
        weighted_rs = (
            rel_perf['year'] * 0.40 +
            rel_perf['6month'] * 0.20 +
            rel_perf['3month'] * 0.20 +
            rel_perf['month'] * 0.20
        )
        
        # Convert to percentile-like score (0-99)
        # Normalize around 0, where positive = outperforming market
        # Map to 0-99 scale where:
        #   - RS = 99: Stock significantly outperforming (+50% better than market)
        #   - RS = 50: Stock matching market performance (neutral)
        #   - RS = 1: Stock significantly underperforming (-50% worse than market)
        
        if weighted_rs >= 50:
            rs_score = 99  # Capped at 99
        elif weighted_rs <= -50:
            rs_score = 1   # Floored at 1
        else:
            # Linear mapping: -50 to +50 maps to 1 to 99
            rs_score = ((weighted_rs + 50) / 100) * 98 + 1
        
        rs_values.append(round(rs_score, 1))
    
    return pd.Series(rs_values, index=stock_df.index)


def calculate_simple_rs(stock_df, market_df=None, timeframe='daily'):
    """
    Simplified RS calculation - compares 6-month performance
    Faster and simpler than full IBD methodology
    
    Args:
        stock_df (pd.DataFrame): Stock data with 'Close' column
        market_df (pd.DataFrame): Market data (optional)
        timeframe (str): 'daily' or 'weekly'
    
    Returns:
        pd.Series: RS values (0-99)
    """
    
    # Determine lookback period
    lookback = 126 if timeframe == 'daily' else 26  # 6 months
    
    # Fetch market data if needed
    if market_df is None or market_df.empty:
        market_df = fetch_market_data(timeframe, 365)
    
    if market_df is None or market_df.empty:
        return pd.Series([50] * len(stock_df), index=stock_df.index)
    
    rs_values = []
    
    for idx in range(len(stock_df)):
        if idx < lookback:
            rs_values.append(50)  # Not enough history
            continue
        
        # Calculate stock performance
        current_price = stock_df['Close'].iloc[idx]
        past_price = stock_df['Close'].iloc[idx - lookback]
        
        if past_price > 0:
            stock_perf = ((current_price - past_price) / past_price) * 100
        else:
            stock_perf = 0
        
        # Calculate market performance
        stock_date = stock_df['Date'].iloc[idx]
        market_subset = market_df[market_df['date'] <= stock_date].tail(lookback + 1)
        
        if len(market_subset) >= 2:
            market_current = market_subset['close'].iloc[-1]
            market_past = market_subset['close'].iloc[0]
            
            if market_past > 0:
                market_perf = ((market_current - market_past) / market_past) * 100
            else:
                market_perf = 0
        else:
            market_perf = 0
        
        # Calculate relative strength
        rel_perf = stock_perf - market_perf
        
        # Map to 0-99 scale
        if rel_perf >= 50:
            rs_score = 99
        elif rel_perf <= -50:
            rs_score = 1
        else:
            rs_score = ((rel_perf + 50) / 100) * 98 + 1
        
        rs_values.append(round(rs_score, 1))
    
    return pd.Series(rs_values, index=stock_df.index)


# Test function
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 TESTING RS CALCULATOR")
    print("="*80)
    
    # Test with a sample stock
    symbol = 'AAPL'
    
    print(f"\n📊 Fetching {symbol} data...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period='1y', interval='1d')
    df = df.reset_index()
    df = df.rename(columns={'Date': 'Date', 'Close': 'Close'})
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    print(f"✅ Got {len(df)} days of data")
    
    print(f"\n📊 Calculating RS...")
    rs_series = calculate_simple_rs(df, timeframe='daily')
    
    print(f"\n✅ RS Calculation Complete!")
    print(f"   Latest RS: {rs_series.iloc[-1]}")
    print(f"   RS Range: {rs_series.min():.1f} - {rs_series.max():.1f}")
    print(f"   Average RS: {rs_series.mean():.1f}")
    
    if rs_series.iloc[-1] >= 95:
        print(f"   ⭐ {symbol} is a MARKET LEADER! (RS ≥ 95)")
    elif rs_series.iloc[-1] >= 80:
        print(f"   ✨ {symbol} is OUTPERFORMING (RS ≥ 80)")
    elif rs_series.iloc[-1] <= 20:
        print(f"   ⚠️ {symbol} is UNDERPERFORMING (RS ≤ 20)")
    else:
        print(f"   📊 {symbol} has NEUTRAL performance")
    
    print("\n" + "="*80)
