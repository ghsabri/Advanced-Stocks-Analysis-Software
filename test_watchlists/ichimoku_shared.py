"""
Shared Ichimoku Module - REUSES EXISTING CODE
Extracted from 6_Indicator_Chart.py to avoid duplication

This module is used by:
1. Indicator Chart page (existing)
2. ML scanner (new)

ONE implementation, TWO uses!
"""

import pandas as pd
import numpy as np


# ============================================================================
# CALCULATION FUNCTIONS (From Indicator Chart)
# ============================================================================

def calculate_ema(prices, period):
    """
    Calculate EMA (Exponential Moving Average)
    REUSED from Indicator Chart
    
    Args:
        prices (pd.Series or np.array): Price data
        period (int): EMA period
    
    Returns:
        pd.Series or np.array: EMA values
    """
    try:
        if isinstance(prices, np.ndarray):
            # Convert to Series for calculation
            s = pd.Series(prices)
            ema = s.ewm(span=period, adjust=False).mean()
            return ema.values
        else:
            # Already a Series
            ema = prices.ewm(span=period, adjust=False).mean()
            return ema
    except:
        if isinstance(prices, np.ndarray):
            return np.full(len(prices), np.nan)
        else:
            return pd.Series([None] * len(prices))


def calculate_ichimoku(df):
    """
    Calculate Ichimoku Cloud components
    EXACT COPY from Indicator Chart (lines 161-188)
    
    Args:
        df (pd.DataFrame): DataFrame with High, Low, Close columns
    
    Returns:
        tuple: (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span)
    """
    try:
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        nine_period_high = df['High'].rolling(window=9).max()
        nine_period_low = df['Low'].rolling(window=9).min()
        tenkan_sen = (nine_period_high + nine_period_low) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        twenty_six_period_high = df['High'].rolling(window=26).max()
        twenty_six_period_low = df['Low'].rolling(window=26).min()
        kijun_sen = (twenty_six_period_high + twenty_six_period_low) / 2
        
        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        fifty_two_period_high = df['High'].rolling(window=52).max()
        fifty_two_period_low = df['Low'].rolling(window=52).min()
        senkou_span_b = ((fifty_two_period_high + fifty_two_period_low) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close plotted 26 days in the past
        chikou_span = df['Close'].shift(-26)
        
        return tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
    except:
        none_series = pd.Series([None] * len(df))
        return none_series, none_series, none_series, none_series, none_series


def find_ichimoku_signals(df, tenkan, kijun, senkou_a, senkou_b, ema_13, ema_30):
    """
    Find buy/sell signals for Ichimoku + EMA crossover strategy
    EXACT COPY from Indicator Chart (lines 328-373)
    
    Buy Signal: 13 EMA crosses above 30 EMA AND price is in/above cloud
    Sell Signal: 13 EMA crosses below 30 EMA AND price is in/below cloud
    
    Args:
        df (pd.DataFrame): Price data
        tenkan, kijun, senkou_a, senkou_b: Ichimoku components
        ema_13, ema_30: EMA lines
    
    Returns:
        tuple: (buy_signals, sell_signals) - lists of indices
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect crossover
    if len(df) < 2:
        return buy_signals, sell_signals
    
    for i in range(1, len(df)):
        # Get values - just convert to float directly
        try:
            ema13_curr = float(ema_13.iloc[i])
            ema30_curr = float(ema_30.iloc[i])
            ema13_prev = float(ema_13.iloc[i-1])
            ema30_prev = float(ema_30.iloc[i-1])
        except (ValueError, TypeError):
            continue  # Skip if can't convert
        
        # Check all EMAs are valid
        if pd.notna(ema13_curr) and pd.notna(ema30_curr) and \
           pd.notna(ema13_prev) and pd.notna(ema30_prev):
            
            try:
                price = float(df['Close'].iloc[i])
                senkou_a_val = float(senkou_a.iloc[i]) if pd.notna(senkou_a.iloc[i]) else None
                senkou_b_val = float(senkou_b.iloc[i]) if pd.notna(senkou_b.iloc[i]) else None
            except (ValueError, TypeError):
                continue
            
            # Determine cloud boundaries (top and bottom)
            if senkou_a_val is not None and senkou_b_val is not None:
                cloud_top = max(senkou_a_val, senkou_b_val)
                cloud_bottom = min(senkou_a_val, senkou_b_val)
                
                # Check if price is in or above cloud
                price_in_or_above_cloud = price >= cloud_bottom
                
                # Check if price is in or below cloud
                price_in_or_below_cloud = price <= cloud_top
                
                # BUY SIGNAL: 13 EMA crosses ABOVE 30 EMA from below
                if ema13_prev <= ema30_prev and ema13_curr > ema30_curr:
                    if price_in_or_above_cloud:
                        buy_signals.append(i)
                
                # SELL SIGNAL: 13 EMA crosses BELOW 30 EMA from above
                if ema13_prev >= ema30_prev and ema13_curr < ema30_curr:
                    if price_in_or_below_cloud:
                        sell_signals.append(i)
    
    return buy_signals, sell_signals


# ============================================================================
# HELPER FUNCTIONS FOR ML SCANNER
# ============================================================================

def add_all_indicators(df):
    """
    Add all Ichimoku + EMA indicators to DataFrame
    Uses the existing calculation functions above
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
    
    Returns:
        pd.DataFrame: DataFrame with all indicators added
    """
    df = df.copy()
    
    # Calculate EMAs (13, 30, 200)
    df['EMA_13'] = calculate_ema(df['Close'], 13)
    df['EMA_30'] = calculate_ema(df['Close'], 30)
    df['EMA_200'] = calculate_ema(df['Close'], 200)
    
    # Calculate Ichimoku Cloud (using existing function)
    tenkan, kijun, senkou_a, senkou_b, chikou = calculate_ichimoku(df)
    df['Tenkan'] = tenkan
    df['Kijun'] = kijun
    df['Senkou_A'] = senkou_a
    df['Senkou_B'] = senkou_b
    df['Chikou'] = chikou
    
    # Add cloud boundaries
    df['Cloud_Top'] = df[['Senkou_A', 'Senkou_B']].max(axis=1)
    df['Cloud_Bottom'] = df[['Senkou_A', 'Senkou_B']].min(axis=1)
    
    # Add EMA cross detection (vectorized)
    df['EMA_Cross_Bullish'] = False
    df['EMA_Cross_Bearish'] = False
    
    # Calculate crosses vectorized
    ema13_curr = df['EMA_13']
    ema30_curr = df['EMA_30']
    ema13_prev = df['EMA_13'].shift(1)
    ema30_prev = df['EMA_30'].shift(1)
    
    # Valid data mask
    valid_data = ema13_curr.notna() & ema30_curr.notna() & ema13_prev.notna() & ema30_prev.notna()
    
    # Bullish cross: 13 EMA crosses above 30 EMA
    bullish_cross = valid_data & (ema13_prev <= ema30_prev) & (ema13_curr > ema30_curr)
    df.loc[bullish_cross, 'EMA_Cross_Bullish'] = True
    
    # Bearish cross: 13 EMA crosses below 30 EMA
    bearish_cross = valid_data & (ema13_prev >= ema30_prev) & (ema13_curr < ema30_curr)
    df.loc[bearish_cross, 'EMA_Cross_Bearish'] = True
    
    # Add price vs cloud position (simple iterative approach - reliable)
    price_positions = []
    
    for i in range(len(df)):
        # Get values - just convert to float/str directly
        try:
            close_price = float(df['Close'].iloc[i])
            cloud_top_val = df['Cloud_Top'].iloc[i]
            cloud_bottom_val = df['Cloud_Bottom'].iloc[i]
        except (ValueError, TypeError):
            price_positions.append('unknown')
            continue
        
        # Check if cloud data exists
        if pd.isna(cloud_top_val) or pd.isna(cloud_bottom_val):
            price_positions.append('unknown')
        else:
            try:
                cloud_top = float(cloud_top_val)
                cloud_bottom = float(cloud_bottom_val)
            except (ValueError, TypeError):
                price_positions.append('unknown')
                continue
            
            if close_price > cloud_top:
                price_positions.append('above')
            elif close_price < cloud_bottom:
                price_positions.append('below')
            else:  # close_price is between cloud_bottom and cloud_top
                price_positions.append('inside')
    
    df['Price_Position'] = price_positions
    
    return df


def calculate_atr(df, period=14):
    """
    Calculate Average True Range
    
    Args:
        df (pd.DataFrame): DataFrame with High, Low, Close
        period (int): ATR period
    
    Returns:
        pd.Series: ATR values
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


if __name__ == '__main__':
    """Test the shared module"""
    import yfinance as yf
    
    print("Testing shared Ichimoku module...")
    print("="*60)
    
    # Download test data
    ticker = 'AAPL'
    print(f"\nTesting with {ticker}...")
    df = yf.download(ticker, start='2023-01-01', end='2024-12-31', progress=False)
    
    # Add indicators using shared function
    print("\nAdding indicators...")
    df = add_all_indicators(df)
    
    print(f"✅ Added indicators:")
    print(f"  - EMA_13, EMA_30, EMA_200")
    print(f"  - Tenkan, Kijun, Senkou_A, Senkou_B, Chikou")
    print(f"  - Cloud_Top, Cloud_Bottom")
    print(f"  - Price_Position")
    
    # Check for signals using existing function
    print("\nChecking for signals...")
    buy_signals, sell_signals = find_ichimoku_signals(
        df, 
        df['Tenkan'], 
        df['Kijun'], 
        df['Senkou_A'], 
        df['Senkou_B'], 
        df['EMA_13'], 
        df['EMA_30']
    )
    
    print(f"✅ Found {len(buy_signals)} buy signals")
    print(f"✅ Found {len(sell_signals)} sell signals")
    
    if len(buy_signals) > 0:
        idx = buy_signals[0]
        print(f"\nFirst buy signal:")
        print(f"  Date: {df.index[idx]}")
        
        # Get values - just convert to python types directly
        try:
            price = float(df['Close'].iloc[idx])
            ema13 = float(df['EMA_13'].iloc[idx])
            ema30 = float(df['EMA_30'].iloc[idx])
            position = str(df['Price_Position'].iloc[idx])
            
            print(f"  Price: ${price:.2f}")
            print(f"  EMA 13: ${ema13:.2f}")
            print(f"  EMA 30: ${ema30:.2f}")
            print(f"  Position: {position}")
        except Exception as e:
            print(f"  Error displaying values: {e}")
    
    print("\n✅ Shared Ichimoku module working!")
    print("="*60)
    print("\nThis module reuses code from Indicator Chart")
    print("NO DUPLICATION - ONE implementation, multiple uses!")
