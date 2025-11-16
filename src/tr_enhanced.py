import pandas as pd
import numpy as np

# Universal caching system - works everywhere
try:
    from universal_cache import get_stock_data, get_market_data, prewarm_cache
    USE_UNIVERSAL_CACHE = True
except ImportError:
    USE_UNIVERSAL_CACHE = False

# Conditional Streamlit import - works in both app and scanner
try:
    import streamlit as st
    IN_STREAMLIT = True
except ImportError:
    IN_STREAMLIT = False
    # Create dummy st object for when running outside Streamlit
    class DummyStreamlit:
        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    st = DummyStreamlit()

from tr_calculations import (
    calculate_ema, 
    calculate_ppo, 
    calculate_pmo,
    calculate_slope,
    detect_crossover,
    detect_crossunder
)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: RELATIVE STRENGTH & CHAIKIN A/D
# ═══════════════════════════════════════════════════════════════════

def fix_all_numeric_dtypes_before_save(df):
    """
    CRITICAL FIX: Force all numeric columns to proper float dtype BEFORE saving CSV
    This prevents apostrophes from appearing in saved CSV files
    """
    df = df.copy()
    
    numeric_columns = [
        'Open', 'High', 'Low', 'Close', 'Volume',
        'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34',
        'PPO_Line', 'PPO_Signal', 'PPO_Histogram',
        'PMO_Line', 'PMO_Signal',
        'RS', 'Chaikin_AD',
        'Buy_Point', 'Buy_Zone_Lower', 'Buy_Zone_Upper',
        'Stop_Loss', 'Risk_Per_Share', 'Distance_From_BP'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def calculate_relative_strength_ibd(df, market_data=None):
    """
    Calculate Relative Strength using IBD method
    NOW ACTUALLY FETCHES MARKET DATA AND COMPARES TO S&P 500!
    
    Args:
        df (pd.DataFrame): Stock data
        market_data (pd.DataFrame): Market data (optional, will fetch if None)
    
    Returns:
        pd.Series: RS Rating (0-99)
    """
    
    # Detect timeframe
    if 'TimeFrame' in df.columns:
        timeframe = df['TimeFrame'].iloc[0].lower()
    else:
        timeframe = 'daily'
    
    # FETCH MARKET DATA IF NOT PROVIDED
    if market_data is None:
        try:
            from datetime import timedelta
            
            start_date = pd.to_datetime(df['Date'].min()) - timedelta(days=400)
            end_date = pd.to_datetime(df['Date'].max()) + timedelta(days=1)
            
            interval = '1d' if timeframe == 'daily' else '1wk'
            
            # USE UNIVERSAL CACHE IF AVAILABLE
            if USE_UNIVERSAL_CACHE:
                market_df = get_market_data('SPY', start_date, end_date, interval)
                if market_df is not None and not market_df.empty:
                    market_data = market_df
                else:
                    return pd.Series([50] * len(df), index=df.index)
            else:
                # Fallback to direct yfinance call
                import yfinance as yf
                spy = yf.Ticker('SPY')
                market_df = spy.history(start=start_date, end=end_date, interval=interval)
                
                if not market_df.empty:
                    market_df = market_df.reset_index()
                    market_df['Date'] = pd.to_datetime(market_df['Date']).dt.date
                    market_data = market_df[['Date', 'Close']].copy()
                    print(f"   ✅ Fetched {len(market_data)} periods of S&P 500 data for RS calculation")
                else:
                    return pd.Series([50] * len(df), index=df.index)
        except Exception as e:
            print(f"   ⚠️ Error fetching market data: {e}, using RS = 50")
            return pd.Series([50] * len(df), index=df.index)
    
    # Set periods based on timeframe
    periods = {'1yr': 252, '6mo': 126, '3mo': 63, '1mo': 21} if timeframe == 'daily' else {'1yr': 52, '6mo': 26, '3mo': 13, '1mo': 4}
    
    # Calculate RS for each row
    rs_values = []
    for idx in range(len(df)):
        if idx < periods['1mo']:
            rs_values.append(50)
            continue
        
        # Stock performance
        stock_close = df['Close'].iloc[idx]
        stock_perf = {}
        for period_name, period_len in periods.items():
            if idx >= period_len:
                past_price = df['Close'].iloc[idx - period_len]
                stock_perf[period_name] = ((stock_close - past_price) / past_price) * 100 if past_price > 0 else 0
            else:
                stock_perf[period_name] = 0
        
        # Market performance
        stock_date = pd.to_datetime(df['Date'].iloc[idx])
        market_subset = market_data[pd.to_datetime(market_data['Date']) <= stock_date]
        
        if len(market_subset) < periods['1mo']:
            rs_values.append(50)
            continue
        
        market_close = market_subset['Close'].iloc[-1]
        market_perf = {}
        for period_name, period_len in periods.items():
            if len(market_subset) >= period_len:
                past_market = market_subset['Close'].iloc[-period_len]
                market_perf[period_name] = ((market_close - past_market) / past_market) * 100 if past_market > 0 else 0
            else:
                market_perf[period_name] = 0
        
        # Relative performance (stock vs market)
        rel_perf = {k: stock_perf[k] - market_perf[k] for k in periods.keys()}
        
        # Weighted composite (IBD method)
        composite = rel_perf['1yr'] * 0.4 + rel_perf['6mo'] * 0.2 + rel_perf['3mo'] * 0.2 + rel_perf['1mo'] * 0.2
        
        # Convert to 0-99 scale
        rs_score = 99 if composite >= 50 else (1 if composite <= -50 else ((composite + 50) / 100) * 98 + 1)
        rs_values.append(round(rs_score, 1))
    
    return pd.Series(rs_values, index=df.index)


def calculate_chaikin_ad(df):
    """
    Calculate Chaikin Accumulation/Distribution Line
    
    TIMEFRAME AWARE:
    - Adjusts ranking window based on timeframe
    
    Formula:
    Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
    Money Flow Volume = Money Flow Multiplier × Volume
    AD Line = Cumulative sum of Money Flow Volume
    
    Args:
        df (pd.DataFrame): Stock data with OHLCV and TimeFrame
    
    Returns:
        pd.Series: Chaikin A/D Line percentile rank (0-100)
    """
    # Detect timeframe
    if 'TimeFrame' in df.columns:
        timeframe = df['TimeFrame'].iloc[0].lower()
    else:
        timeframe = 'daily'
    
    # Set ranking period based on timeframe
    if timeframe == 'daily':
        ranking_period = min(252, len(df))  # 1 year
    elif timeframe == 'weekly':
        ranking_period = min(52, len(df))   # 1 year
    elif timeframe == 'monthly':
        ranking_period = min(12, len(df))   # 1 year
    else:
        ranking_period = min(252, len(df))
    
    # Avoid division by zero
    high_low_diff = df['High'] - df['Low']
    high_low_diff = high_low_diff.replace(0, 0.0001)
    
    # Money Flow Multiplier
    mf_multiplier = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / high_low_diff
    
    # Money Flow Volume
    mf_volume = mf_multiplier * df['Volume']
    
    # AD Line (cumulative)
    ad_line = mf_volume.cumsum()
    
    # Percentile rank over appropriate period
    min_periods = max(10, ranking_period // 4)
    
    ad_percentile = ad_line.rolling(ranking_period, min_periods=min_periods).apply(
        lambda x: (pd.Series(x).rank(pct=True).iloc[-1] * 100) if len(x) >= min_periods else 50,
        raw=False
    )
    
    return ad_percentile.fillna(50).clip(0, 100)


def add_strength_indicators(df, market_data=None):
    """
    Add Relative Strength and Chaikin A/D to dataframe
    
    Args:
        df (pd.DataFrame): Stock data
        market_data (pd.DataFrame): Market data (optional)
    
    Returns:
        pd.DataFrame: Data with RS and Chaikin_AD columns
    """
    # Calculate RS using IBD method (timeframe-aware)
    df['RS'] = calculate_relative_strength_ibd(df, market_data)
    
    # Calculate Chaikin A/D
    df['Chaikin_AD'] = calculate_chaikin_ad(df)
    
    return df


def check_strong_stock(df, idx, rs_threshold=95, ad_threshold=95):
    """
    Check if stock is strong (RS ≥ 95% AND Chaikin A/D ≥ 95%)
    
    Args:
        df (pd.DataFrame): Data with RS and AD
        idx (int): Current index
        rs_threshold (float): RS percentile threshold
        ad_threshold (float): AD percentile threshold
    
    Returns:
        bool: True if stock is strong
    """
    if 'RS' not in df.columns or 'Chaikin_AD' not in df.columns:
        return False
    
    rs = df.iloc[idx]['RS']
    ad = df.iloc[idx]['Chaikin_AD']
    
    return rs >= rs_threshold and ad >= ad_threshold


def add_star_for_strong_stocks(df):
    """
    Add * to TR status for strong stocks (RS ≥ 95% AND Chaikin A/D ≥ 95%)
    
    Args:
        df (pd.DataFrame): Data with TR_Status_Enhanced, RS, Chaikin_AD
    
    Returns:
        pd.DataFrame: Data with updated TR_Status_Enhanced
    """
    enhanced_status = []
    
    for idx in range(len(df)):
        status = df.iloc[idx]['TR_Status_Enhanced']
        
        # Add star if strong stock
        if check_strong_stock(df, idx):
            status = f"{status} *"
        
        enhanced_status.append(status)
    
    df['TR_Status_Enhanced'] = enhanced_status
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: PEAKS & VALLEYS DETECTION
# ═══════════════════════════════════════════════════════════════════

def identify_peaks(df, lookback=5, threshold=0.02):
    """
    Identify swing highs (peaks) in price data
    
    A peak is a local maximum where:
    - Price is highest within lookback periods on both sides
    - Significant enough (threshold % move)
    
    Args:
        df (pd.DataFrame): Stock data with High prices
        lookback (int): Periods to look back/forward
        threshold (float): Minimum % move to qualify (default 2%)
    
    Returns:
        pd.Series: Boolean series (True = peak)
    """
    peaks = pd.Series([False] * len(df), index=df.index)
    
    for i in range(lookback, len(df) - lookback):
        # Get window around current point
        window_before = df['High'].iloc[i - lookback:i]
        window_after = df['High'].iloc[i + 1:i + lookback + 1]
        current_high = df['High'].iloc[i]
        
        # Check if current is highest in window
        is_highest_before = all(current_high >= window_before)
        is_highest_after = all(current_high >= window_after)
        
        if is_highest_before and is_highest_after:
            # Check if move is significant enough
            window_low = df['Low'].iloc[i - lookback:i + lookback + 1].min()
            if window_low > 0:
                pct_move = (current_high - window_low) / window_low
                if pct_move >= threshold:
                    peaks.iloc[i] = True
    
    return peaks


def identify_valleys(df, lookback=5, threshold=0.02):
    """
    Identify swing lows (valleys) in price data
    
    A valley is a local minimum where:
    - Price is lowest within lookback periods on both sides
    - Significant enough (threshold % move)
    
    Args:
        df (pd.DataFrame): Stock data with Low prices
        lookback (int): Periods to look back/forward
        threshold (float): Minimum % move to qualify (default 2%)
    
    Returns:
        pd.Series: Boolean series (True = valley)
    """
    valleys = pd.Series([False] * len(df), index=df.index)
    
    for i in range(lookback, len(df) - lookback):
        # Get window around current point
        window_before = df['Low'].iloc[i - lookback:i]
        window_after = df['Low'].iloc[i + 1:i + lookback + 1]
        current_low = df['Low'].iloc[i]
        
        # Check if current is lowest in window
        is_lowest_before = all(current_low <= window_before)
        is_lowest_after = all(current_low <= window_after)
        
        if is_lowest_before and is_lowest_after:
            # Check if move is significant enough
            window_high = df['High'].iloc[i - lookback:i + lookback + 1].max()
            if current_low > 0:
                pct_move = (window_high - current_low) / current_low
                if pct_move >= threshold:
                    valleys.iloc[i] = True
    
    return valleys


def add_peaks_and_valleys(df, lookback=5):
    """
    Add peak and valley indicators to dataframe
    
    Args:
        df (pd.DataFrame): Stock data
        lookback (int): Lookback period for peak/valley detection
    
    Returns:
        pd.DataFrame: Data with Peak and Valley columns
    """
    df['Peak'] = identify_peaks(df, lookback)
    df['Valley'] = identify_valleys(df, lookback)
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: BUY POINTS (FROM PEAKS)
# ═══════════════════════════════════════════════════════════════════

def calculate_buy_points(df, lookback=50):
    """
    Calculate buy points as the nearest previous PEAK (pivot high)
    
    TR/IBD Buy Point Rules:
    1. Identify pivot highs (peaks in price)
    2. Buy point = The peak high price
    3. Entry trigger = Price breaks above buy point
    4. Ideal buy zone = Within ±5% of buy point
    
    Example Timeline:
    Day 1: Peak at $100 (this becomes the buy point)
    Day 2-10: Price pulls back to $95
    Day 11: Price in range $95-$105 with Stage 2/3 → BUY SIGNAL!
    
    Args:
        df (pd.DataFrame): Data with Peak column
        lookback (int): Max bars to look back for recent peak
    
    Returns:
        pd.DataFrame: Data with Buy_Point and Days_From_Peak columns
    """
    buy_points = pd.Series([np.nan] * len(df), index=df.index)
    days_from_peak = pd.Series([np.nan] * len(df), index=df.index)
    peak_dates = pd.Series([''] * len(df), index=df.index)
    
    if 'Peak' not in df.columns:
        df['Buy_Point'] = buy_points
        df['Days_From_Peak'] = days_from_peak
        df['Peak_Date'] = peak_dates
        return df
    
    for i in range(len(df)):
        # Find the most recent peak before current bar
        search_start = max(0, i - lookback)
        search_window = df.iloc[search_start:i]
        
        # Get all peaks in the window
        peaks_in_window = search_window[search_window['Peak'] == True]
        
        if not peaks_in_window.empty:
            # Get the most recent peak
            most_recent_peak = peaks_in_window.iloc[-1]
            peak_high = most_recent_peak['High']
            peak_date = most_recent_peak['Date']
            
            # Calculate days from peak
            peak_position = df.index.get_loc(peaks_in_window.index[-1])
            days_since = i - peak_position
            
            # Set buy point as the peak high
            buy_points.iloc[i] = peak_high
            days_from_peak.iloc[i] = days_since
            peak_dates.iloc[i] = peak_date
    
    df['Buy_Point'] = buy_points
    df['Days_From_Peak'] = days_from_peak
    df['Peak_Date'] = peak_dates
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: BUY ZONE (±5% OF BUY POINT)
# ═══════════════════════════════════════════════════════════════════

def add_buy_zone_indicator(df, threshold=5.0):
    """
    Add column indicating if price is in buy zone
    
    Buy Zone = ±5% of buy point (both above and below)
    
    Args:
        df (pd.DataFrame): Data with Buy_Point
        threshold (float): Percentage threshold (default 5%)
    
    Returns:
        pd.DataFrame: Data with In_Buy_Zone and Distance_From_BP columns
    """
    in_buy_zone = []
    distance_from_bp = []
    buy_zone_lower = []
    buy_zone_upper = []
    
    for i in range(len(df)):
        buy_point = df.iloc[i].get('Buy_Point', np.nan)
        current_price = df.iloc[i]['Close']
        
        if pd.notna(buy_point) and buy_point > 0:
            # Calculate distance from buy point
            distance_pct = ((current_price - buy_point) / buy_point) * 100
            
            # Check if in buy zone
            in_zone = -threshold <= distance_pct <= threshold
            
            # Calculate zone boundaries
            lower_bound = buy_point * (1 - threshold / 100)
            upper_bound = buy_point * (1 + threshold / 100)
            
            in_buy_zone.append(in_zone)
            distance_from_bp.append(distance_pct)
            buy_zone_lower.append(lower_bound)
            buy_zone_upper.append(upper_bound)
        else:
            in_buy_zone.append(False)
            distance_from_bp.append(np.nan)
            buy_zone_lower.append(np.nan)
            buy_zone_upper.append(np.nan)
    
    df['In_Buy_Zone'] = in_buy_zone
    df['Distance_From_BP'] = distance_from_bp
    df['Buy_Zone_Lower'] = buy_zone_lower
    df['Buy_Zone_Upper'] = buy_zone_upper
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: STOP LOSS (8% BELOW BUY POINT)
# ═══════════════════════════════════════════════════════════════════

def calculate_atr_simple(df, period=14):
    """
    Calculate Average True Range (ATR)
    
    True Range = max of:
    - High - Low
    - |High - Previous Close|
    - |Low - Previous Close|
    
    ATR = Average of True Range over period
    
    Args:
        df (pd.DataFrame): Stock data
        period (int): ATR period (default 14)
    
    Returns:
        pd.Series: ATR values
    """
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(period).mean()
    
    return atr


def calculate_stop_loss(df, stop_percentage=8.0):
    """
    Calculate stop loss as 8% below the buy point
    
    TR INDICATOR STOP LOSS RULE:
    - Stop Loss = Buy Point × (1 - 0.08)
    - This gives a fixed 8% risk per trade
    
    Example:
    - Buy Point (peak): $100
    - Stop Loss: $100 × 0.92 = $92
    - Risk per share: $8
    - Buy Zone: $95 - $105
    - Stop: $92 (clearly below buy zone)
    
    Args:
        df (pd.DataFrame): Data with Buy_Point column
        stop_percentage (float): Stop loss percentage below buy point (default 8%)
    
    Returns:
        pd.DataFrame: Data with Stop_Loss column
    """
    stop_loss = pd.Series([np.nan] * len(df), index=df.index)
    risk_per_share = pd.Series([np.nan] * len(df), index=df.index)
    risk_percentage = pd.Series([np.nan] * len(df), index=df.index)
    
    for i in range(len(df)):
        buy_point = df.iloc[i].get('Buy_Point', np.nan)
        
        if pd.notna(buy_point) and buy_point > 0:
            # Stop loss = Buy point - 8%
            stop_price = buy_point * (1 - stop_percentage / 100)
            stop_loss.iloc[i] = stop_price
            
            # Calculate risk metrics
            risk_per_share.iloc[i] = buy_point - stop_price
            risk_percentage.iloc[i] = stop_percentage
    
    df['Stop_Loss'] = stop_loss
    df['Risk_Per_Share'] = risk_per_share
    df['Risk_Percentage'] = risk_percentage
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: BUY & EXIT SIGNALS
# ═══════════════════════════════════════════════════════════════════

def identify_buy_and_exit_signals(df):
    """
    Generate buy and exit signals based on TR strategy
    
    BUY SIGNAL CRITERIA (ALL must be true):
    1. Price is within buy zone (±5% of buy point)
    2. TR Status is Stage 2 (Buy) or Stage 3 (Strong Buy)
    3. Fresh entry (just entered uptrend or buy zone)
    
    EXIT SIGNAL CRITERIA (ANY triggers exit):
    1. Price closes below stop loss (buy point - 8%)
    2. TR Status changes to Sell/Strong Sell
    3. TR Status drops to Neutral Sell (optional - conservative exit)
    
    Args:
        df (pd.DataFrame): Data with all indicators
    
    Returns:
        pd.DataFrame: Data with Buy_Signal and Exit_Signal columns
    """
    buy_signals = []
    exit_signals = []
    exit_reasons = []
    
    for i in range(len(df)):
        buy_signal = False
        exit_signal = False
        exit_reason = ''
        
        current_status = df.iloc[i]['TR_Status']
        current_price = df.iloc[i]['Close']
        in_buy_zone = df.iloc[i].get('In_Buy_Zone', False)
        stop_loss = df.iloc[i].get('Stop_Loss', np.nan)
        
        # ═══════════════════════════════════════════════════════
        # BUY SIGNAL LOGIC
        # ═══════════════════════════════════════════════════════
        if in_buy_zone and current_status in ['Buy', 'Strong Buy']:
            if i > 0:
                prev_status = df.iloc[i - 1]['TR_Status']
                prev_in_zone = df.iloc[i - 1].get('In_Buy_Zone', False)
                
                # Scenario 1: Just entered Stage 2 or 3 while in buy zone
                just_entered_uptrend = (
                    current_status in ['Buy', 'Strong Buy'] and
                    prev_status not in ['Buy', 'Strong Buy'] and
                    in_buy_zone
                )
                
                # Scenario 2: Just entered buy zone while already in uptrend
                just_entered_zone = (
                    in_buy_zone and 
                    not prev_in_zone and
                    current_status in ['Buy', 'Strong Buy']
                )
                
                # Scenario 3: Upgraded from Buy to Strong Buy while in zone
                upgraded_to_stage3 = (
                    current_status == 'Strong Buy' and
                    prev_status == 'Buy' and
                    in_buy_zone
                )
                
                if just_entered_uptrend or just_entered_zone or upgraded_to_stage3:
                    buy_signal = True
            else:
                # First bar - check if conditions already met
                if in_buy_zone and current_status in ['Buy', 'Strong Buy']:
                    buy_signal = True
        
        # ═══════════════════════════════════════════════════════
        # EXIT SIGNAL LOGIC
        # ═══════════════════════════════════════════════════════
        if i > 0:
            prev_status = df.iloc[i - 1]['TR_Status']
            
            # Exit 1: Hit stop loss (8% below buy point)
            if pd.notna(stop_loss) and current_price <= stop_loss:
                exit_signal = True
                exit_reason = f'Stop Loss Hit (${stop_loss:.2f})'
            
            # Exit 2: TR status changed to Sell or Strong Sell
            elif current_status in ['Sell', 'Strong Sell'] and prev_status not in ['Sell', 'Strong Sell']:
                exit_signal = True
                exit_reason = f'TR Sell Signal ({current_status})'
            
            # Exit 3: Dropped to Neutral Sell (conservative exit)
            elif current_status == 'Neutral Sell' and prev_status in ['Buy', 'Strong Buy', 'Neutral Buy']:
                exit_signal = True
                exit_reason = 'Downtrend Starting (Neutral Sell)'
        
        buy_signals.append(buy_signal)
        exit_signals.append(exit_signal)
        exit_reasons.append(exit_reason)
    
    df['Buy_Signal'] = buy_signals
    df['Exit_Signal'] = exit_signals
    df['Exit_Reason'] = exit_reasons
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: ARROWS & CHECKMARKS
# ═══════════════════════════════════════════════════════════════════

def detect_fresh_trend_start(df, idx):
    """
    Detect if trend just started in current period
    
    Returns:
        str: '↑' for fresh uptrend, '↓' for fresh downtrend, '' for no change
    """
    if idx < 1:
        return ''
    
    current_status = df.iloc[idx]['TR_Status']
    previous_status = df.iloc[idx - 1]['TR_Status']
    
    # Define uptrend and downtrend statuses
    uptrend_statuses = ['Strong Buy', 'Buy', 'Neutral Buy']
    downtrend_statuses = ['Strong Sell', 'Sell', 'Neutral Sell']
    
    # Check if just entered uptrend
    if current_status in uptrend_statuses and previous_status not in uptrend_statuses:
        return '↑'
    
    # Check if just entered downtrend
    if current_status in downtrend_statuses and previous_status not in downtrend_statuses:
        return '↓'
    
    return ''


def check_near_buy_point(df, idx, threshold=5.0):
    """
    Check if stock is within BUY ZONE (±5% of buy point)
    AND in Stage 2 or Stage 3 uptrend
    
    CORRECTED TR LOGIC:
    - Buy Point = Recent peak (pivot high)
    - Buy Zone = Buy Point ± 5% (both above AND below)
    - Checkmark (✓) = In buy zone AND in uptrend
    
    Example:
    - Buy point (peak) = $100
    - Buy zone = $95 to $105
    - Current price = $98 (within zone)
    - TR Status = Buy (Stage 2)
    - Result: ✓ Checkmark shows!
    
    Args:
        df (pd.DataFrame): Data with Buy_Point and TR_Status
        idx (int): Current index
        threshold (float): Percentage range (default 5.0%)
    
    Returns:
        bool: True if in buy zone with uptrend
    """
    current_status = df.iloc[idx]['TR_Status']
    
    # Must be in Stage 2 or Stage 3 uptrend
    if current_status not in ['Buy', 'Strong Buy']:
        return False
    
    # Check if we have a buy point
    if 'Buy_Point' not in df.columns or pd.isna(df.iloc[idx]['Buy_Point']):
        return False
    
    buy_point = df.iloc[idx]['Buy_Point']
    current_price = df.iloc[idx]['Close']
    
    if buy_point <= 0:
        return False
    
    # Calculate distance from buy point (can be positive or negative)
    distance_pct = ((current_price - buy_point) / buy_point) * 100
    
    # Within ±5% of buy point = Buy Zone
    if -threshold <= distance_pct <= threshold:
        return True
    
    return False


def add_tr_enhancements(df):
    """
    Add arrows, checkmarks to TR status
    
    Enhancements:
    - ↑ = Fresh uptrend started
    - ↓ = Fresh downtrend started  
    - ✓ = In buy zone (±5% of buy point) AND in Stage 2/3 uptrend
    
    Args:
        df (pd.DataFrame): Data with TR_Status
    
    Returns:
        pd.DataFrame: Data with TR_Status_Enhanced
    """
    enhanced_status = []
    
    for idx in range(len(df)):
        base_status = df.iloc[idx]['TR_Status']
        
        # Start with base status
        status = base_status
        
        # Add arrow if fresh trend start
        arrow = detect_fresh_trend_start(df, idx)
        if arrow:
            status = f"{status} {arrow}"
        
        # Add checkmark if in buy zone with uptrend
        # This now correctly uses ±5% logic
        if check_near_buy_point(df, idx):
            status = f"{status} ✓"
        
        enhanced_status.append(status)
    
    df['TR_Status_Enhanced'] = enhanced_status
    
    return df


def add_signal_markers(df):
    """
    Add visual markers for buy/exit signals in TR status
    
    Args:
        df (pd.DataFrame): Data with signals
    
    Returns:
        pd.DataFrame: Data with updated TR_Status_Enhanced
    """
    enhanced_status = []
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status_Enhanced']
        
        # Add buy signal marker
        if df.iloc[i]['Buy_Signal']:
            status = f"{status} 🔵BUY"
        
        # Add exit signal marker
        if df.iloc[i]['Exit_Signal']:
            status = f"{status} 🔴EXIT"
        
        enhanced_status.append(status)
    
    df['TR_Status_Enhanced'] = enhanced_status
    
    return df


def format_tr_display(status):
    """
    Format TR status for display with colors
    
    Args:
        status (str): TR status with enhancements
    
    Returns:
        str: Formatted status
    """
    if 'Strong Buy' in status:
        emoji = '🟢🟢'
    elif 'Buy' in status:
        emoji = '🟢'
    elif 'Neutral Buy' in status:
        emoji = '🟡↗'
    elif 'Neutral Sell' in status:
        emoji = '🟡↘'
    elif 'Sell' in status:
        emoji = '🔴'
    elif 'Strong Sell' in status:
        emoji = '🔴🔴'
    else:
        emoji = '⚪'
    
    return f"{emoji} {status}"


# ═══════════════════════════════════════════════════════════════════
# SECTION 8: MAIN ANALYZER FUNCTION
# ═══════════════════════════════════════════════════════════════════

def detect_and_adjust_splits(df):
    """
    Automatically detect stock splits and adjust prices backward
    
    Detection method: Large overnight price jumps with inverse volume changes
    - Price drops >25% + Volume spikes >150% = Likely a split
    
    Args:
        df (pd.DataFrame): Stock data with OHLC
    
    Returns:
        pd.DataFrame: Split-adjusted data
    """
    if df is None or len(df) < 2:
        return df
    
    df = df.copy()
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Calculate day-over-day changes
    df['Price_Change_Pct'] = df['Close'].pct_change() * 100
    df['Volume_Change_Pct'] = df['Volume'].pct_change() * 100
    
    # Detect potential splits
    # Split signature: Price drops >25% AND volume spikes >150%
    potential_splits = df[
        (df['Price_Change_Pct'] < -25) &  # Price dropped >25%
        (df['Volume_Change_Pct'] > 150)    # Volume spiked >150%
    ].copy()
    
    if len(potential_splits) == 0:
        # No splits detected
        df = df.drop(['Price_Change_Pct', 'Volume_Change_Pct'], axis=1)
        return df
    
    print(f"\n⚠️  SPLIT DETECTED! Adjusting prices...")
    
    # Process each split (work backwards from most recent)
    for idx in potential_splits.index[::-1]:
        split_date = df.loc[idx, 'Date']
        
        # Calculate split ratio from price change
        price_before = df.loc[idx - 1, 'Close']
        price_after = df.loc[idx, 'Close']
        split_ratio = price_before / price_after
        
        print(f"   📅 Split on {split_date}")
        print(f"   📊 Ratio: {split_ratio:.2f}-for-1")
        print(f"   💰 Price: ${price_before:.2f} → ${price_after:.2f}")
        
        # Adjust all prices BEFORE the split
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in df.columns:
                df.loc[:idx-1, col] = df.loc[:idx-1, col] / split_ratio
        
        # Adjust volume BEFORE the split (multiply by ratio)
        if 'Volume' in df.columns:
            df.loc[:idx-1, 'Volume'] = df.loc[:idx-1, 'Volume'] * split_ratio
    
    print(f"   ✅ Split adjustment complete!\n")
    
    # Clean up temporary columns
    df = df.drop(['Price_Change_Pct', 'Volume_Change_Pct'], axis=1)
    
    return df


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180, market_ticker='SPY', api_source='yahoo'):
    """
    Complete TR analysis with all enhancements
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'daily' or 'weekly'
        duration_days (int): History duration
        market_ticker (str): Market index for RS calculation
        api_source (str): 'yahoo' or 'tiingo' (Note: currently uses yahoo regardless)
    
    Returns:
        pd.DataFrame: Complete TR analysis
    """
    import yfinance as yf
    from datetime import datetime, timedelta
    from tr_indicator import analyze_tr_indicator
    
    print(f"\n{'='*80}")
    print(f"🔍 COMPLETE TR ANALYSIS: {ticker}")
    print(f"📡 Data Source: YAHOO FINANCE")
    print(f"{'='*80}\n")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=duration_days)
    
    # Fetch stock data using yfinance directly
    print(f"📡 Fetching {ticker} data from Yahoo Finance...")
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if df is None or df.empty:
        print(f"❌ No data for {ticker}")
        return None
    
    # Handle multi-index columns (yfinance sometimes returns these)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # CRITICAL: yfinance returns DatetimeIndex
    # Reset to create Date column - DO NOT set back as index
    df = df.reset_index()
    if 'index' in df.columns:
        df = df.rename(columns={'index': 'Date'})
    
    # Ensure Date column exists and is datetime type
    if 'Date' not in df.columns:
        df['Date'] = df.index
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Resample to weekly if needed
    if timeframe.lower() == 'weekly':
        print(f"📊 Converting to weekly timeframe...")
        df = df.set_index('Date')
        df = df.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        # Reset index to column
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
    
    if df is None or df.empty:
        print(f"❌ No data for {ticker}")
        return None
    
    # CRITICAL: Detect and adjust for stock splits
    df = detect_and_adjust_splits(df)
    
    # Fetch market data for RS calculation
    # Try to use cache if available
    market_df = None
    if USE_UNIVERSAL_CACHE:
        try:
            from universal_cache import get_stock_data
            interval = '1d' if timeframe.lower() == 'daily' else '1wk'
            market_df_cached = get_stock_data(market_ticker, start_date, end_date, interval)
            if market_df_cached is not None and not market_df_cached.empty:
                market_df = market_df_cached
        except:
            pass
    
    # Fallback to direct fetch if cache unavailable
    if market_df is None or market_df.empty:
        print(f"📡 Fetching {market_ticker} data for RS calculation from Yahoo Finance...")
        market_df = yf.download(market_ticker, start=start_date, end=end_date, progress=False)
    
    # Handle multi-index for market data
    if market_df is not None and not market_df.empty:
        if isinstance(market_df.columns, pd.MultiIndex):
            market_df.columns = market_df.columns.get_level_values(0)
        
        # Reset index to create Date column
        market_df = market_df.reset_index()
        if 'index' in market_df.columns:
            market_df = market_df.rename(columns={'index': 'Date'})
        
        # Ensure Date exists and is datetime
        if 'Date' not in market_df.columns:
            market_df['Date'] = market_df.index
        market_df['Date'] = pd.to_datetime(market_df['Date'])
        
        # Resample market data to weekly if needed
        if timeframe.lower() == 'weekly':
            market_df = market_df.set_index('Date')
            market_df = market_df.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            market_df = market_df.reset_index()
            market_df['Date'] = pd.to_datetime(market_df['Date'])
        
        # Adjust market data for splits too
        market_df = detect_and_adjust_splits(market_df)
    
    # Run base TR analysis
    print(f"📊 Calculating TR indicators...")
    df = analyze_tr_indicator(df)
    
    # Add enhancements - CORRECTED ORDER
    print(f"✨ Adding enhancements...")
    
    # Phase 1: Peaks & Valleys (needed for buy points)
    df = add_peaks_and_valleys(df)
    
    # Phase 2: Buy Points from Peaks
    df = calculate_buy_points(df)
    
    # Phase 3: Buy Zone Indicators (±5% of buy point)
    df = add_buy_zone_indicator(df)
    
    # Phase 4: Stop Loss (8% below buy point)
    df = calculate_stop_loss(df)
    
    # Phase 5: Buy/Exit Signals
    df = identify_buy_and_exit_signals(df)
    
    # Phase 6: Arrows & Checkmarks (after buy zone calculated)
    df = add_tr_enhancements(df)
    
    # Phase 7: RS & Chaikin
    df = add_strength_indicators(df, market_df)
    df = add_star_for_strong_stocks(df)
    
    # Phase 8: Signal Markers
    df = add_signal_markers(df)
    
    print(f"✅ Complete TR analysis finished!\n")
    
    return df


# ═══════════════════════════════════════════════════════════════════
# SECTION 9: DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def display_complete_tr_summary(df, ticker):
    """
    Display complete TR summary with all enhancements
    
    Args:
        df (pd.DataFrame): Complete TR data
        ticker (str): Stock symbol
    """
    if df is None or df.empty:
        return
    
    latest = df.iloc[-1]
    
    print("="*80)
    print(f"📊 COMPLETE TR SUMMARY: {ticker}")
    print("="*80)
    
    # Current Status
    print(f"\n🎯 CURRENT STATUS:")
    print(f"   Date:           {latest['Date']}")
    print(f"   Price:          ${latest['Close']:.2f}")
    print(f"   TR Status:      {format_tr_display(latest['TR_Status_Enhanced'])}")
    
    # Buy Point Info
    if pd.notna(latest.get('Buy_Point')):
        print(f"\n📍 BUY POINT SETUP:")
        print(f"   Buy Point:      ${latest['Buy_Point']:.2f}")
        print(f"   Buy Zone:       ${latest['Buy_Zone_Lower']:.2f} - ${latest['Buy_Zone_Upper']:.2f}")
        print(f"   Stop Loss:      ${latest['Stop_Loss']:.2f}")
        print(f"   Distance:       {latest['Distance_From_BP']:+.1f}%")
        print(f"   In Buy Zone:    {'✅ YES' if latest['In_Buy_Zone'] else '❌ NO'}")
    
    # Strength Indicators
    print(f"\n💪 STRENGTH INDICATORS:")
    print(f"   Relative Strength:  {latest['RS']:.1f}%")
    print(f"   Chaikin A/D:        {latest['Chaikin_AD']:.1f}%")
    
    if latest['RS'] >= 95 and latest['Chaikin_AD'] >= 95:
        print(f"   ⭐ STRONG STOCK - Market Leader!")
    
    # Signals
    if latest.get('Buy_Signal', False):
        print(f"\n🔵 BUY SIGNAL ACTIVE!")
    
    if latest.get('Exit_Signal', False):
        print(f"\n🔴 EXIT SIGNAL ACTIVE!")
        if latest.get('Exit_Reason'):
            print(f"   Reason: {latest['Exit_Reason']}")
    
    print("="*80 + "\n")


# ═══════════════════════════════════════════════════════════════════
# SECTION 10: MULTI-STOCK ANALYZER
# ═══════════════════════════════════════════════════════════════════

def analyze_multiple_stocks(tickers, timeframe='daily', duration_days=180):
    """
    Analyze TR indicator for multiple stocks
    
    Args:
        tickers (list): List of stock symbols
        timeframe (str): 'daily' or 'weekly'
        duration_days (int): History duration
    
    Returns:
        dict: Results for all stocks
    """
    
    results = {}
    
    print("\n" + "="*80)
    print(f"🚀 ANALYZING {len(tickers)} STOCKS - TR INDICATOR")
    print("="*80)
    
    for ticker in tickers:
        result = analyze_stock_complete_tr(ticker, timeframe, duration_days)
        if result is not None:
            results[ticker] = result
    
    # Summary comparison
    print("\n" + "="*80)
    print("📊 SUMMARY - ALL STOCKS")
    print("="*80)
    print(f"{'Ticker':<10} {'Price':>10} {'TR Status':<20} {'Signal':<10}")
    print("-"*80)
    
    for ticker in tickers:
        if ticker in results:
            df = results[ticker]
            latest = df.iloc[-1]
            status = latest['TR_Status']
            price = latest['Close']
            
            status_symbol = {
                "Strong Buy": "🟢",
                "Buy": "🟢",
                "Neutral Buy": "🟡",
                "Neutral": "⚪",
                "Neutral Sell": "🟡",
                "Sell": "🔴",
                "Strong Sell": "🔴"
            }.get(status, "⚪")
            
            print(f"{ticker:<10} ${price:>9.2f} {status_symbol} {status:<18} {status_symbol}")
    
    print("="*80 + "\n")
    
    return results


def save_tr_results(result, output_folder='data'):
    """
    Save TR analysis results to CSV
    
    Args:
        result (pd.DataFrame): TR analysis results
        output_folder (str): Folder to save results
    """
    
    ticker = result.iloc[0]['Symbol']
    timeframe = result.iloc[0]['TimeFrame']
    
    # Save full data with TR status
    filename = f"{output_folder}/{ticker}_{timeframe.capitalize()}_Complete_TR.csv"
    
    # Select relevant columns
    output_columns = [
        'Symbol', 'TimeFrame', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
        'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34',
        'PPO_Line', 'PPO_Signal', 
        'PMO_Line', 'PMO_Signal',
        'TR_Status', 'TR_Status_Enhanced',
        'RS', 'Chaikin_AD',
        'Peak', 'Valley',
        'Buy_Point', 'Buy_Zone_Lower', 'Buy_Zone_Upper',
        'In_Buy_Zone', 'Distance_From_BP',
        'Stop_Loss', 'Risk_Per_Share',
        'Buy_Signal', 'Exit_Signal', 'Exit_Reason'
    ]
    
    # Only include columns that exist
    existing_columns = [col for col in output_columns if col in result.columns]
    
    df_output = result[existing_columns]
    # CRITICAL: Fix dtypes before saving to prevent apostrophe issue!
    df_output = fix_all_numeric_dtypes_before_save(df_output)
    df_output.to_csv(filename, index=False, float_format='%.6f')
    
    print(f"✅ Saved TR results to: {filename}")
    
    return filename