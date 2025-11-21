import pandas as pd
import numpy as np

def calculate_ema(data, period, column='Close'):
    """
    Calculate Exponential Moving Average
    
    Args:
        data (pd.DataFrame): Stock data
        period (int): EMA period (3, 9, 20, 34)
        column (str): Column to calculate EMA on
    
    Returns:
        pd.Series: EMA values
    """
    return data[column].ewm(span=period, adjust=False).mean()


def calculate_ppo(data, fast=12, slow=26, signal=9):
    """
    Calculate Price Percentage Oscillator (PPO)
    
    PPO = ((EMA_fast - EMA_slow) / EMA_slow) * 100
    PPO Signal = EMA of PPO
    
    Args:
        data (pd.DataFrame): Stock data with Close prices
        fast (int): Fast EMA period (default 12)
        slow (int): Slow EMA period (default 26)
        signal (int): Signal line period (default 9)
    
    Returns:
        dict: PPO line, PPO signal line, PPO histogram
    """
    # Calculate fast and slow EMAs
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    
    # Calculate PPO
    ppo_line = ((ema_fast - ema_slow) / ema_slow) * 100
    
    # Calculate PPO Signal line (EMA of PPO)
    ppo_signal = ppo_line.ewm(span=signal, adjust=False).mean()
    
    # Calculate PPO Histogram
    ppo_histogram = ppo_line - ppo_signal
    
    return {
        'ppo_line': ppo_line,
        'ppo_signal': ppo_signal,
        'ppo_histogram': ppo_histogram
    }


def calculate_pmo(data, smooth1=35, smooth2=20, signal=10):
    """
    Calculate Price Momentum Oscillator (PMO)
    
    Args:
        data (pd.DataFrame): Stock data with Close prices
        smooth1 (int): First smoothing period
        smooth2 (int): Second smoothing period
        signal (int): Signal line period
    
    Returns:
        dict: PMO line and PMO signal line
    """
    # Calculate Rate of Change (ROC)
    roc = data['Close'].pct_change() * 100
    
    # Apply first smoothing
    pmo_smooth1 = roc.ewm(span=smooth1, adjust=False).mean()
    
    # Apply second smoothing
    pmo_line = pmo_smooth1.ewm(span=smooth2, adjust=False).mean() * 10
    
    # Calculate signal line
    pmo_signal = pmo_line.ewm(span=signal, adjust=False).mean()
    
    return {
        'pmo_line': pmo_line,
        'pmo_signal': pmo_signal
    }


def calculate_slope(series, periods=3):
    """
    Calculate slope (rising or declining) of a series
    
    Args:
        series (pd.Series): Data series
        periods (int): Number of periods to look back
    
    Returns:
        pd.Series: Boolean series (True = rising, False = declining)
    """
    # Compare current value to value N periods ago
    rising = series > series.shift(periods)
    return rising


def detect_crossover(series1, series2):
    """
    Detect when series1 crosses above series2
    
    Args:
        series1 (pd.Series): First series (e.g., EMA 3)
        series2 (pd.Series): Second series (e.g., EMA 9)
    
    Returns:
        pd.Series: Boolean series (True = bullish crossover occurred)
    """
    # Current: series1 > series2
    # Previous: series1 <= series2
    crossover = (series1 > series2) & (series1.shift(1) <= series2.shift(1))
    return crossover


def detect_crossunder(series1, series2):
    """
    Detect when series1 crosses below series2
    
    Args:
        series1 (pd.Series): First series (e.g., EMA 3)
        series2 (pd.Series): Second series (e.g., EMA 9)
    
    Returns:
        pd.Series: Boolean series (True = bearish crossover occurred)
    """
    # Current: series1 < series2
    # Previous: series1 >= series2
    crossunder = (series1 < series2) & (series1.shift(1) >= series2.shift(1))
    return crossunder


def is_above_zero(series):
    """Check if series is above zero"""
    return series > 0


def is_below_zero(series):
    """Check if series is below zero"""
    return series < 0


def is_series1_above_series2(series1, series2):
    """Check if series1 is above series2"""
    return series1 > series2


def is_series1_below_series2(series1, series2):
    """Check if series1 is below series2"""
    return series1 < series2