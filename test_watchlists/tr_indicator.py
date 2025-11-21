import pandas as pd
import numpy as np
import tr_calculations as tc


def ensure_numeric_data(df):
    """
    CRITICAL FIX: Ensure all numeric columns are actually numbers, not strings!
    This fixes the apostrophe issue that breaks Stage 2/3 detection
    """
    # List of columns that must be numeric
    price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    for col in price_cols:
        if col in df.columns:
            # Convert to string, remove apostrophes, convert to float
            if df[col].dtype == 'object' or df[col].astype(str).str.contains("'").any():
                df[col] = df[col].astype(str).str.replace("'", "").astype(float)
    
    return df


def calculate_all_indicators(data):
    """
    Calculate all technical indicators needed for TR
    
    Args:
        data (pd.DataFrame): Stock data with OHLC
    
    Returns:
        pd.DataFrame: Data with all indicators added
    """
    df = data.copy()
    
    # CRITICAL: Fix data types FIRST!
    df = ensure_numeric_data(df)
    
    # Calculate EMAs
    df['EMA_3'] = tc.calculate_ema(df, 3)
    df['EMA_9'] = tc.calculate_ema(df, 9)
    df['EMA_20'] = tc.calculate_ema(df, 20)
    df['EMA_34'] = tc.calculate_ema(df, 34)
    
    # Calculate PPO
    ppo = tc.calculate_ppo(df)
    df['PPO_Line'] = ppo['ppo_line']
    df['PPO_Signal'] = ppo['ppo_signal']
    df['PPO_Histogram'] = ppo['ppo_histogram']
    
    # Calculate PMO
    pmo = tc.calculate_pmo(df)
    df['PMO_Line'] = pmo['pmo_line']
    df['PMO_Signal'] = pmo['pmo_signal']
    
    # Calculate slopes
    df['EMA_9_Rising'] = tc.calculate_slope(df['EMA_9'])
    df['EMA_34_Rising'] = tc.calculate_slope(df['EMA_34'])
    df['PPO_Rising'] = tc.calculate_slope(df['PPO_Line'])
    df['PMO_Rising'] = tc.calculate_slope(df['PMO_Line'])
    
    df['EMA_9_Declining'] = ~df['EMA_9_Rising']
    df['EMA_34_Declining'] = ~df['EMA_34_Rising']
    df['PPO_Declining'] = ~df['PPO_Rising']
    df['PMO_Declining'] = ~df['PMO_Rising']
    
    return df


def check_uptrend_stage1(df, idx):
    """
    Uptrend Stage 1: EMA 3 crosses EMA 9 from bottom
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 1 uptrend condition met
    """
    if idx < 1:
        return False
    
    # EMA 3 crosses above EMA 9
    crossover = tc.detect_crossover(df['EMA_3'], df['EMA_9'])
    
    return crossover.iloc[idx]


def check_uptrend_stage2(df, idx):
    """
    Uptrend Stage 2:
    - PPO > 0
    - PPO rising (positive slope)
    - EMA 34 rising
    - PPO line above PPO Signal
    - EMA 9 above EMA 20
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 2 uptrend condition met
    """
    if idx < 34:  # Need enough data for EMA 34
        return False
    
    row = df.iloc[idx]
    
    conditions = [
        row['PPO_Line'] > 0,
        row['PPO_Rising'],
        row['EMA_34_Rising'],
        row['PPO_Line'] > row['PPO_Signal'],
        row['EMA_9'] > row['EMA_20']
    ]
    
    return all(conditions)


def check_uptrend_stage3(df, idx):
    """
    Uptrend Stage 3:
    - PPO > 0
    - PPO rising
    - EMA 9 rising
    - EMA 34 rising
    - PMO > 0
    - PPO line above PPO Signal
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 3 uptrend condition met
    """
    if idx < 34:
        return False
    
    row = df.iloc[idx]
    
    conditions = [
        row['PPO_Line'] > 0,
        row['PPO_Rising'],
        row['EMA_9_Rising'],
        row['EMA_34_Rising'],
        row['PMO_Line'] > 0,
        row['PPO_Line'] > row['PPO_Signal']
    ]
    
    return all(conditions)


def check_downtrend_stage1(df, idx):
    """
    Downtrend Stage 1: EMA 3 crosses EMA 9 from top
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 1 downtrend condition met
    """
    if idx < 1:
        return False
    
    # EMA 3 crosses below EMA 9
    crossunder = tc.detect_crossunder(df['EMA_3'], df['EMA_9'])
    
    return crossunder.iloc[idx]


def check_downtrend_stage2(df, idx):
    """
    Downtrend Stage 2 (Sell Zone):
    - PPO < 0
    - PPO declining (negative slope)
    - PPO below PPO Signal
    - EMA 9 declining
    - EMA 34 declining
    - EMA 9 below EMA 20
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 2 downtrend condition met
    """
    if idx < 34:
        return False
    
    row = df.iloc[idx]
    
    conditions = [
        row['PPO_Line'] < 0,
        row['PPO_Declining'],
        row['PPO_Line'] < row['PPO_Signal'],
        row['EMA_9_Declining'],
        row['EMA_34_Declining'],
        row['EMA_9'] < row['EMA_20']
    ]
    
    return all(conditions)


def check_downtrend_stage3(df, idx):
    """
    Downtrend Stage 3 (Strong Sell):
    - PPO <= 0
    - PPO declining
    - EMA 9 declining
    - EMA 34 declining
    - PMO declining
    - PMO line below PMO Signal
    - EMA 9 below EMA 34
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        bool: True if Stage 3 downtrend condition met
    """
    if idx < 34:
        return False
    
    row = df.iloc[idx]
    
    conditions = [
        row['PPO_Line'] <= 0,
        row['PPO_Declining'],
        row['EMA_9_Declining'],
        row['EMA_34_Declining'],
        row['PMO_Declining'],
        row['PMO_Line'] < row['PMO_Signal'],
        row['EMA_9'] < row['EMA_34']
    ]
    
    return all(conditions)


def get_tr_status(df, idx):
    """
    Get TR status with CORRECTED priority logic
    
    FIXED: Now checks Stage 2 before Stage 3 so "Buy" actually appears!
    
    Priority (highest to lowest):
    1. Stage 2 Uptrend (Buy) - Must check BEFORE Stage 3
    2. Stage 3 Uptrend (Strong Buy) - Only if Stage 2 + extra conditions
    3. Stage 2 Downtrend (Sell) - Must check BEFORE Stage 3
    4. Stage 3 Downtrend (Strong Sell) - Only if Stage 2 + extra conditions
    5. Stage 1 Uptrend (Neutral Buy)
    6. Stage 1 Downtrend (Neutral Sell)
    7. Neutral (no signals)
    
    Args:
        df (pd.DataFrame): Data with indicators
        idx (int): Current index
    
    Returns:
        str: TR status
    """
    
    # Check Stage 2 FIRST, then Stage 3
    # This way, "Buy" appears before upgrading to "Strong Buy"
    
    # UPTREND: Check Stage 2, then upgrade to Stage 3 if all conditions met
    if check_uptrend_stage2(df, idx):
        # If Stage 3 conditions also met, upgrade to Strong Buy
        if check_uptrend_stage3(df, idx):
            return "Strong Buy"
        # Otherwise, stay at Stage 2
        return "Buy"
    
    # DOWNTREND: Check Stage 2, then upgrade to Stage 3 if all conditions met
    if check_downtrend_stage2(df, idx):
        # If Stage 3 conditions also met, upgrade to Strong Sell
        if check_downtrend_stage3(df, idx):
            return "Strong Sell"
        # Otherwise, stay at Stage 2
        return "Sell"
    
    # Check Stage 1 (entry signals)
    if check_uptrend_stage1(df, idx):
        return "Neutral Buy"
    
    if check_downtrend_stage1(df, idx):
        return "Neutral Sell"
    
    # No signals
    return "Neutral"


def analyze_tr_indicator(data):
    """
    Main function: Calculate TR indicator for entire dataset
    
    Args:
        data (pd.DataFrame): Stock data (OHLC)
    
    Returns:
        pd.DataFrame: Data with TR status for each date
    """
    # Calculate all indicators (now includes dtype fixing!)
    df = calculate_all_indicators(data)
    
    # Calculate TR status for each row
    tr_status = []
    for idx in range(len(df)):
        status = get_tr_status(df, idx)
        tr_status.append(status)
    
    df['TR_Status'] = tr_status
    
    return df
