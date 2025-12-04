"""
Indicator Chart Page - Dual Panel Chart
Shows selected indicator in top panel and price chart with signals in bottom panel
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cached_data import get_shared_stock_data
from ml_ichimoku_predictor import predict_ichimoku_confidence
from tr_enhanced import analyze_stock_complete_tr

st.set_page_config(
    page_title="Indicator Chart - MJ Software",
    page_icon="📈",
    layout="wide"
)

# ============================================================================
# INDICATOR CALCULATION FUNCTIONS
# ============================================================================

def calculate_rsi(df, period=14):
    """Calculate RSI indicator"""
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([None] * len(df))

def calculate_macd(df):
    """
    Calculate MACD indicator (traditional)
    MACD Line = 12 EMA - 26 EMA
    Signal Line = 9 EMA of MACD
    Histogram = MACD - Signal
    """
    try:
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram
    except:
        return pd.Series([None] * len(df)), pd.Series([None] * len(df)), pd.Series([None] * len(df))

def calculate_supertrend(df, period=10, multiplier=3.0):
    """
    Calculate SuperTrend indicator
    
    SuperTrend uses ATR (Average True Range) to identify trend direction
    - Green line (uptrend): Price above SuperTrend
    - Red line (downtrend): Price below SuperTrend
    
    Args:
        df: DataFrame with High, Low, Close prices
        period: ATR period (default: 10)
        multiplier: ATR multiplier (default: 3.0)
    
    Returns:
        supertrend: SuperTrend line values
        trend: Trend direction (1=uptrend, -1=downtrend)
    """
    try:
        # Calculate True Range
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR (Average True Range)
        atr = true_range.rolling(window=period).mean()
        
        # Calculate basic upper and lower bands
        hl_avg = (df['High'] + df['Low']) / 2
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        # Initialize
        supertrend = pd.Series(index=df.index, dtype=float)
        trend = pd.Series(index=df.index, dtype=float)
        
        # Set initial values
        supertrend.iloc[0] = lower_band.iloc[0]
        trend.iloc[0] = 1
        
        # Calculate SuperTrend
        for i in range(1, len(df)):
            if pd.notna(upper_band.iloc[i]) and pd.notna(lower_band.iloc[i]):
                
                # Determine if we're in uptrend or downtrend
                if df['Close'].iloc[i] > supertrend.iloc[i-1]:
                    # Price is above previous SuperTrend - uptrend
                    trend.iloc[i] = 1
                    supertrend.iloc[i] = lower_band.iloc[i]
                    
                    # Keep SuperTrend from dropping
                    if pd.notna(supertrend.iloc[i-1]) and trend.iloc[i-1] == 1:
                        if lower_band.iloc[i] < supertrend.iloc[i-1]:
                            supertrend.iloc[i] = supertrend.iloc[i-1]
                
                elif df['Close'].iloc[i] < supertrend.iloc[i-1]:
                    # Price is below previous SuperTrend - downtrend
                    trend.iloc[i] = -1
                    supertrend.iloc[i] = upper_band.iloc[i]
                    
                    # Keep SuperTrend from rising
                    if pd.notna(supertrend.iloc[i-1]) and trend.iloc[i-1] == -1:
                        if upper_band.iloc[i] > supertrend.iloc[i-1]:
                            supertrend.iloc[i] = supertrend.iloc[i-1]
                
                else:
                    # Price equals SuperTrend - maintain previous trend
                    trend.iloc[i] = trend.iloc[i-1]
                    if trend.iloc[i] == 1:
                        supertrend.iloc[i] = lower_band.iloc[i]
                    else:
                        supertrend.iloc[i] = upper_band.iloc[i]
        
        return supertrend, trend
    
    except Exception as e:
        print(f"Error calculating SuperTrend: {e}")
        return pd.Series([None] * len(df)), pd.Series([None] * len(df))


def calculate_ema(df, period):
    """Calculate EMA (Exponential Moving Average)"""
    try:
        ema = df['Close'].ewm(span=period, adjust=False).mean()
        return ema
    except:
        return pd.Series([None] * len(df))

def calculate_ema_crossover(df, fast_period, slow_period):
    """Calculate EMA Crossover (Fast EMA and Slow EMA)"""
    try:
        fast_ema = df['Close'].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df['Close'].ewm(span=slow_period, adjust=False).mean()
        return fast_ema, slow_ema
    except:
        return pd.Series([None] * len(df)), pd.Series([None] * len(df))

def calculate_ichimoku(df):
    """Calculate Ichimoku Cloud components"""
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

def find_supertrend_signals(df, supertrend, trend):
    """
    Find buy/sell signals for SuperTrend
    
    Buy Signal: Price crosses ABOVE SuperTrend line (trend changes to uptrend)
    Sell Signal: Price crosses BELOW SuperTrend line (trend changes to downtrend)
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect trend change
    if len(df) < 2:
        return buy_signals, sell_signals
    
    price = df['Close']
    
    for i in range(1, len(df)):
        if pd.notna(trend.iloc[i]) and pd.notna(trend.iloc[i-1]):
            
            # BUY SIGNAL: Trend changes from -1 (downtrend) to 1 (uptrend)
            # This means price crossed above SuperTrend line
            if trend.iloc[i-1] == -1 and trend.iloc[i] == 1:
                buy_signals.append(i)
            
            # SELL SIGNAL: Trend changes from 1 (uptrend) to -1 (downtrend)
            # This means price crossed below SuperTrend line
            if trend.iloc[i-1] == 1 and trend.iloc[i] == -1:
                sell_signals.append(i)
    
    return buy_signals, sell_signals


def find_ema_crossover_signals(fast_ema, slow_ema):
    """
    Find buy/sell signals for EMA Crossover strategy
    
    Buy Signal: Fast EMA crosses ABOVE Slow EMA (from below)
    Sell Signal: Fast EMA crosses BELOW Slow EMA (from above)
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect crossover
    if len(fast_ema) < 2:
        return buy_signals, sell_signals
    
    for i in range(1, len(fast_ema)):
        if pd.notna(fast_ema.iloc[i]) and pd.notna(slow_ema.iloc[i]) and \
           pd.notna(fast_ema.iloc[i-1]) and pd.notna(slow_ema.iloc[i-1]):
            
            # BUY SIGNAL: Fast EMA crosses ABOVE Slow EMA
            if fast_ema.iloc[i-1] <= slow_ema.iloc[i-1] and fast_ema.iloc[i] > slow_ema.iloc[i]:
                buy_signals.append(i)
            
            # SELL SIGNAL: Fast EMA crosses BELOW Slow EMA
            if fast_ema.iloc[i-1] >= slow_ema.iloc[i-1] and fast_ema.iloc[i] < slow_ema.iloc[i]:
                sell_signals.append(i)
    
    return buy_signals, sell_signals


def find_ema_signals(df, ema_line):
    """
    Find buy/sell signals for EMA based on price crossing EMA
    
    Buy Signal: Price crosses ABOVE EMA (from below)
    Sell Signal: Price crosses BELOW EMA (from above)
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect crossover
    if len(df) < 2:
        return buy_signals, sell_signals
    
    price = df['Close']
    
    for i in range(1, len(df)):
        if pd.notna(price.iloc[i]) and pd.notna(ema_line.iloc[i]) and \
           pd.notna(price.iloc[i-1]) and pd.notna(ema_line.iloc[i-1]):
            
            # BUY SIGNAL: Price crosses ABOVE EMA from below
            if price.iloc[i-1] <= ema_line.iloc[i-1] and price.iloc[i] > ema_line.iloc[i]:
                buy_signals.append(i)
            
            # SELL SIGNAL: Price crosses BELOW EMA from above
            if price.iloc[i-1] >= ema_line.iloc[i-1] and price.iloc[i] < ema_line.iloc[i]:
                sell_signals.append(i)
    
    return buy_signals, sell_signals


def find_macd_signals(macd_line, signal_line):
    """
    Find buy/sell signals for MACD based on MACD and Signal line crossovers
    
    Traditional MACD signals:
    - Buy Signal: MACD line crosses ABOVE Signal line (from below)
    - Sell Signal: MACD line crosses BELOW Signal line (from above)
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect crossover
    if len(macd_line) < 2:
        return buy_signals, sell_signals
    
    for i in range(1, len(macd_line)):
        if pd.notna(macd_line.iloc[i]) and pd.notna(signal_line.iloc[i]) and \
           pd.notna(macd_line.iloc[i-1]) and pd.notna(signal_line.iloc[i-1]):
            
            # BUY SIGNAL: MACD line crosses ABOVE Signal line
            if macd_line.iloc[i-1] <= signal_line.iloc[i-1] and macd_line.iloc[i] > signal_line.iloc[i]:
                buy_signals.append(i)
            
            # SELL SIGNAL: MACD line crosses BELOW Signal line
            if macd_line.iloc[i-1] >= signal_line.iloc[i-1] and macd_line.iloc[i] < signal_line.iloc[i]:
                sell_signals.append(i)
    
    return buy_signals, sell_signals


def find_ichimoku_signals(df, tenkan, kijun, senkou_a, senkou_b, ema_13, ema_30):
    """
    Find buy/sell signals for Ichimoku + EMA crossover strategy
    
    Buy Signal: 13 EMA crosses above 30 EMA AND price is in/above cloud
    Sell Signal: 13 EMA crosses below 30 EMA AND price is in/below cloud
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
    """
    buy_signals = []
    sell_signals = []
    
    # Need at least 2 data points to detect crossover
    if len(df) < 2:
        return buy_signals, sell_signals
    
    for i in range(1, len(df)):
        if pd.notna(ema_13.iloc[i]) and pd.notna(ema_30.iloc[i]) and \
           pd.notna(ema_13.iloc[i-1]) and pd.notna(ema_30.iloc[i-1]):
            
            price = df['Close'].iloc[i]
            
            # Determine cloud boundaries (top and bottom)
            if pd.notna(senkou_a.iloc[i]) and pd.notna(senkou_b.iloc[i]):
                cloud_top = max(senkou_a.iloc[i], senkou_b.iloc[i])
                cloud_bottom = min(senkou_a.iloc[i], senkou_b.iloc[i])
                
                # Check if price is in or above cloud
                price_in_or_above_cloud = price >= cloud_bottom
                
                # Check if price is in or below cloud
                price_in_or_below_cloud = price <= cloud_top
                
                # BUY SIGNAL: 13 EMA crosses ABOVE 30 EMA from below
                if ema_13.iloc[i-1] <= ema_30.iloc[i-1] and ema_13.iloc[i] > ema_30.iloc[i]:
                    if price_in_or_above_cloud:
                        buy_signals.append(i)
                
                # SELL SIGNAL: 13 EMA crosses BELOW 30 EMA from above
                if ema_13.iloc[i-1] >= ema_30.iloc[i-1] and ema_13.iloc[i] < ema_30.iloc[i]:
                    if price_in_or_below_cloud:
                        sell_signals.append(i)
    
    return buy_signals, sell_signals


def find_enhanced_tr_signals(df, tr_data, ema_13, ema_30, senkou_a, senkou_b):
    """
    Find buy/sell signals for TR / Ichimoku Combo Strategy strategy
    
    BUY Signal (ALL conditions must be TRUE):
    1. TR Status = "Strong Buy" (3rd stage uptrend)
    2. TR has ↑ arrow (just entered this stage - fresh signal)
    3. EMA 13 > EMA 30 (momentum confirmation)
    4. Price > Ichimoku Cloud (above both Senkou Span A and B)
    
    SELL Signal (ALL conditions must be TRUE):
    1. TR Status in downtrend ("Neutral Sell", "Sell", or "Strong Sell")
    2. EMA 13 < EMA 30 (bearish momentum)
    3. Price ≤ Ichimoku Cloud (at or below cloud top)
    
    ALTERNATING SIGNALS:
    - After a BUY signal, subsequent BUY signals are ignored until a SELL signal occurs
    - After a SELL signal, subsequent SELL signals are ignored until a BUY signal occurs
    
    Args:
        df: Price DataFrame with Date, Close, etc.
        tr_data: DataFrame from analyze_stock_complete_tr with TR_Status, TR_Status_Enhanced
        ema_13: Series - 13-period EMA (for signal logic)
        ema_30: Series - 30-period EMA (for signal logic)
        senkou_a: Series - Ichimoku Senkou Span A
        senkou_b: Series - Ichimoku Senkou Span B
    
    Returns:
        buy_signals: list of indices where buy signals occur
        sell_signals: list of indices where sell signals occur
        signal_details: list of dicts with signal information
    """
    buy_signals = []
    sell_signals = []
    signal_details = []
    
    # Downtrend statuses for sell signals
    downtrend_statuses = ['Neutral Sell', 'Sell', 'Strong Sell']
    
    # Track position state for alternating signals
    # None = no position, 'BUY' = in long position (waiting for SELL), 'SELL' = out (waiting for BUY)
    last_signal = None
    
    # Need at least some data
    if len(df) < 2 or tr_data is None or tr_data.empty:
        return buy_signals, sell_signals, signal_details
    
    # Align TR data with price data by date
    tr_data_copy = tr_data.copy()
    tr_data_copy['Date'] = pd.to_datetime(tr_data_copy['Date'])
    df_copy = df.copy()
    if 'Date' in df_copy.columns:
        df_copy['Date_dt'] = pd.to_datetime(df_copy['Date'])
    else:
        df_copy['Date_dt'] = pd.to_datetime(df_copy.index)
    
    for i in range(1, len(df)):
        try:
            # Get current values
            current_date = df_copy['Date_dt'].iloc[i]
            current_price = df['Close'].iloc[i]
            
            # Find matching TR data row
            tr_match = tr_data_copy[tr_data_copy['Date'] == current_date]
            if tr_match.empty:
                # Try matching by index position if dates don't align perfectly
                if i < len(tr_data_copy):
                    tr_row = tr_data_copy.iloc[i]
                else:
                    continue
            else:
                tr_row = tr_match.iloc[0]
            
            # Get TR status
            tr_status = tr_row.get('TR_Status', '')
            tr_status_enhanced = tr_row.get('TR_Status_Enhanced', '')
            
            # Check for arrow (↑ indicates fresh entry into uptrend stage)
            has_up_arrow = '↑' in str(tr_status_enhanced)
            
            # Get EMA values
            ema13_val = ema_13.iloc[i] if pd.notna(ema_13.iloc[i]) else None
            ema30_val = ema_30.iloc[i] if pd.notna(ema_30.iloc[i]) else None
            
            # Get cloud boundaries
            span_a = senkou_a.iloc[i] if pd.notna(senkou_a.iloc[i]) else None
            span_b = senkou_b.iloc[i] if pd.notna(senkou_b.iloc[i]) else None
            
            # Skip if missing data
            if ema13_val is None or ema30_val is None or span_a is None or span_b is None:
                continue
            
            cloud_top = max(span_a, span_b)
            cloud_bottom = min(span_a, span_b)
            
            # ═══════════════════════════════════════════════════════════════
            # BUY SIGNAL CHECK
            # ═══════════════════════════════════════════════════════════════
            # Only check for BUY if last signal was not BUY (alternating)
            if last_signal != 'BUY':
                # Condition 1: TR Status = "Strong Buy"
                is_strong_buy = tr_status == 'Strong Buy'
                
                # Condition 2: Has ↑ arrow (fresh entry)
                # Condition 3: EMA 13 > EMA 30
                ema_bullish = ema13_val > ema30_val
                
                # Condition 4: Price > Cloud (above both spans)
                price_above_cloud = current_price > cloud_top
                
                if is_strong_buy and has_up_arrow and ema_bullish and price_above_cloud:
                    buy_signals.append(i)
                    signal_details.append({
                        'index': i,
                        'date': df['Date'].iloc[i] if 'Date' in df.columns else str(df.index[i]),
                        'signal': 'BUY',
                        'price': current_price,
                        'tr_status': tr_status_enhanced,
                        'ema_13': ema13_val,
                        'ema_30': ema30_val,
                        'cloud_position': 'Above'
                    })
                    last_signal = 'BUY'  # Update state - now waiting for SELL
                    continue  # Skip sell check for this bar
            
            # ═══════════════════════════════════════════════════════════════
            # SELL SIGNAL CHECK
            # ═══════════════════════════════════════════════════════════════
            # Only check for SELL if last signal was not SELL (alternating)
            if last_signal != 'SELL':
                # Condition 1: TR Status in downtrend
                is_downtrend = tr_status in downtrend_statuses
                
                # Condition 2: EMA 13 < EMA 30
                ema_bearish = ema13_val < ema30_val
                
                # Condition 3: Price ≤ Cloud top
                price_at_or_below_cloud = current_price <= cloud_top
                
                if is_downtrend and ema_bearish and price_at_or_below_cloud:
                    sell_signals.append(i)
                    
                    # Determine cloud position for display
                    if current_price < cloud_bottom:
                        cloud_pos = 'Below'
                    else:
                        cloud_pos = 'Inside'
                    
                    signal_details.append({
                        'index': i,
                        'date': df['Date'].iloc[i] if 'Date' in df.columns else str(df.index[i]),
                        'signal': 'SELL',
                        'price': current_price,
                        'tr_status': tr_status_enhanced,
                        'ema_13': ema13_val,
                        'ema_30': ema30_val,
                        'cloud_position': cloud_pos
                    })
                    last_signal = 'SELL'  # Update state - now waiting for BUY
        
        except Exception as e:
            # Skip any rows with errors
            continue
    
    return buy_signals, sell_signals, signal_details


def get_ml_confidence_for_signals(df, buy_signals, sell_signals, ema_13, ema_30, ema_200, senkou_a, senkou_b):
    """Get ML confidence scores for detected Ichimoku signals."""
    buy_predictions = []
    sell_predictions = []
    
    for idx in buy_signals:
        try:
            entry_price = float(df['Close'].iloc[idx])
            ema13_val = float(ema_13.iloc[idx])
            ema30_val = float(ema_30.iloc[idx])
            ema200_val = float(ema_200.iloc[idx])
            cloud_top = max(float(senkou_a.iloc[idx]), float(senkou_b.iloc[idx]))
            cloud_bottom = min(float(senkou_a.iloc[idx]), float(senkou_b.iloc[idx]))
            
            if entry_price > cloud_top:
                price_position = 'above'
            elif entry_price < cloud_bottom:
                price_position = 'below'
            else:
                price_position = 'inside'
            
            signal_data = {
                'entry_price': entry_price,
                'ema_13': ema13_val,
                'ema_30': ema30_val,
                'ema_200': ema200_val,
                'cloud_top': cloud_top,
                'cloud_bottom': cloud_bottom,
                'price_position': price_position,
                'timeframe': 'Daily'
            }
            
            prediction = predict_ichimoku_confidence(signal_data)
            buy_predictions.append((idx, prediction))
        except:
            continue
    
    for idx in sell_signals:
        try:
            entry_price = float(df['Close'].iloc[idx])
            ema13_val = float(ema_13.iloc[idx])
            ema30_val = float(ema_30.iloc[idx])
            ema200_val = float(ema_200.iloc[idx])
            cloud_top = max(float(senkou_a.iloc[idx]), float(senkou_b.iloc[idx]))
            cloud_bottom = min(float(senkou_a.iloc[idx]), float(senkou_b.iloc[idx]))
            
            if entry_price > cloud_top:
                price_position = 'above'
            elif entry_price < cloud_bottom:
                price_position = 'below'
            else:
                price_position = 'inside'
            
            signal_data = {
                'entry_price': entry_price,
                'ema_13': ema13_val,
                'ema_30': ema30_val,
                'ema_200': ema200_val,
                'cloud_top': cloud_top,
                'cloud_bottom': cloud_bottom,
                'price_position': price_position,
                'timeframe': 'Daily'
            }
            
            prediction = predict_ichimoku_confidence(signal_data)
            sell_predictions.append((idx, prediction))
        except:
            continue
    
    return {
        'buy_predictions': buy_predictions,
        'sell_predictions': sell_predictions
    }


# ============================================================================
# PEAK AND VALLEY DETECTION (FOR RSI ONLY)
# ============================================================================

def find_peaks_and_valleys(indicator_series, peak_range, valley_range):
    """
    Find peaks and valleys in indicator series with crossover confirmation
    
    Args:
        indicator_series: pandas Series of indicator values
        peak_range: tuple (min, max) for peak detection
        valley_range: tuple (min, max) for valley detection
    
    Returns:
        peaks: list of indices where confirmed sell signals occurred
        valleys: list of indices where confirmed buy signals occurred
        peak_threshold: average of peaks
        valley_threshold: average of valleys
    """
    peaks = []
    valleys = []
    
    # Convert to numpy for easier processing
    values = indicator_series.values
    
    # First pass: Find peaks and valleys in their respective ranges
    temp_peaks = []
    temp_valleys = []
    
    # Find peaks (in peak range, and turned back down)
    for i in range(1, len(values) - 1):
        if pd.notna(values[i]):
            # Check if in peak range
            if peak_range[0] <= values[i] <= peak_range[1]:
                # Check if it's a local maximum (turned back)
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    temp_peaks.append(i)
    
    # Find valleys (in valley range, and turned back up)
    for i in range(1, len(values) - 1):
        if pd.notna(values[i]):
            # Check if in valley range
            if valley_range[0] <= values[i] <= valley_range[1]:
                # Check if it's a local minimum (turned back)
                if values[i] < values[i-1] and values[i] < values[i+1]:
                    temp_valleys.append(i)
    
    # Calculate thresholds
    peak_threshold = np.mean([values[i] for i in temp_peaks]) if temp_peaks else peak_range[1]
    valley_threshold = np.mean([values[i] for i in temp_valleys]) if temp_valleys else valley_range[0]
    
    # Second pass: Find confirmed signals
    # BUY SIGNAL: After valley is found, wait for crossover ABOVE valley threshold from below
    for valley_idx in temp_valleys:
        # Look forward from valley to find crossover
        for i in range(valley_idx + 1, len(values) - 1):
            if pd.notna(values[i]) and pd.notna(values[i+1]):
                # Check if crossing valley threshold from below
                if values[i] <= valley_threshold < values[i+1]:
                    valleys.append(i+1)  # Signal at crossover point
                    break  # Only first crossover after valley
    
    # SELL SIGNAL: After peak is found, wait for crossover BELOW peak threshold from above
    for peak_idx in temp_peaks:
        # Look forward from peak to find crossover
        for i in range(peak_idx + 1, len(values) - 1):
            if pd.notna(values[i]) and pd.notna(values[i+1]):
                # Check if crossing peak threshold from above
                if values[i] >= peak_threshold > values[i+1]:
                    peaks.append(i+1)  # Signal at crossover point
                    break  # Only first crossover after peak
    
    return peaks, valleys, peak_threshold, valley_threshold

# ============================================================================
# CHART CREATION
# ============================================================================

def create_supertrend_chart(df, supertrend, trend, atr_period, atr_multiplier, buy_signals, sell_signals, timeframe="Daily"):
    """
    Create single-panel chart for SuperTrend with price and signals
    
    Shows:
    - Price line
    - SuperTrend line (green when uptrend, red when downtrend)
    - Buy/Sell signals (green/red diamonds)
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create single chart
    fig = go.Figure()
    
    # ========================================================================
    # PRICE LINE
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=df['Close'],
        name='Price',
        line=dict(color='black', width=2.5),
        hovertemplate='Price: $%{y:.2f}<extra></extra>'
    ))
    
    # ========================================================================
    # SUPERTREND LINE (Single continuous line with color changes)
    # ========================================================================
    
    # Build segments with proper color changes
    i = 0
    while i < len(df):
        if pd.notna(trend.iloc[i]) and pd.notna(supertrend.iloc[i]):
            # Start a new segment with current trend color
            current_trend = trend.iloc[i]
            current_color = 'green' if current_trend == 1 else 'red'
            
            segment_x = [dates[i]]
            segment_y = [supertrend.iloc[i]]
            
            # Continue segment while trend stays the same
            j = i + 1
            while j < len(df):
                if pd.notna(trend.iloc[j]) and pd.notna(supertrend.iloc[j]):
                    if trend.iloc[j] == current_trend:
                        segment_x.append(dates[j])
                        segment_y.append(supertrend.iloc[j])
                        j += 1
                    else:
                        # Trend changed - include one more point to connect segments
                        segment_x.append(dates[j])
                        segment_y.append(supertrend.iloc[j])
                        break
                else:
                    j += 1
            
            # Plot this segment
            if len(segment_x) > 1:
                fig.add_trace(go.Scatter(
                    x=segment_x,
                    y=segment_y,
                    name='SuperTrend',
                    mode='lines',
                    line=dict(color=current_color, width=2.5),
                    showlegend=(i == 0),  # Only show legend once
                    legendgroup='supertrend',
                    hovertemplate='SuperTrend: $%{y:.2f}<extra></extra>'
                ))
            
            i = j
        else:
            i += 1
    
    # ========================================================================
    # BUY/SELL SIGNALS
    # ========================================================================
    
    # Buy signals (green diamonds)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]
        
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='green',
                line=dict(color='darkgreen', width=1.5)
            ),
            hovertemplate='BUY<br>$%{y:.2f}<extra></extra>'
        ))
    
    # Sell signals (red diamonds)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]
        
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='red',
                line=dict(color='darkred', width=1.5)
            ),
            hovertemplate='SELL<br>$%{y:.2f}<extra></extra>'
        ))
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        title=dict(
            text=f'{stock_symbol} - SuperTrend ({atr_period}, {atr_multiplier}) Strategy ({timeframe})',
            font=dict(size=20, family='Arial Black'),
            x=0.5,
            xanchor='center'
        ),
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date'
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Date",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',
        tickformat='%b %d, %Y',
        tickangle=-45,
        nticks=10
    )
    
    fig.update_yaxes(
        title_text="Price ($)",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    return fig


def create_ema_crossover_chart(df, fast_ema, slow_ema, fast_period, slow_period, buy_signals, sell_signals, timeframe="Daily"):
    """
    Create single-panel chart for EMA Crossover with price and signals
    
    Shows:
    - Price line
    - Fast EMA line
    - Slow EMA line
    - Buy/Sell signals (green/red diamonds)
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create single chart
    fig = go.Figure()
    
    # ========================================================================
    # PRICE LINE
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=df['Close'],
        name='Price',
        line=dict(color='black', width=2.5),
        hovertemplate='Price: $%{y:.2f}<extra></extra>'
    ))
    
    # ========================================================================
    # FAST EMA LINE (Blue Dotted)
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=fast_ema,
        name=f'{fast_period} EMA (Fast)',
        line=dict(color='blue', width=2, dash='dot'),  # Dotted line
        hovertemplate=f'{fast_period} EMA: $%{{y:.2f}}<extra></extra>'
    ))
    
    # ========================================================================
    # SLOW EMA LINE (Red Dotted)
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=slow_ema,
        name=f'{slow_period} EMA (Slow)',
        line=dict(color='red', width=2, dash='dot'),  # Dotted line
        hovertemplate=f'{slow_period} EMA: $%{{y:.2f}}<extra></extra>'
    ))
    
    # ========================================================================
    # BUY/SELL SIGNALS
    # ========================================================================
    
    # Buy signals (green diamonds)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]
        
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='green',
                line=dict(color='darkgreen', width=1.5)
            ),
            hovertemplate='BUY<br>$%{y:.2f}<extra></extra>'
        ))
    
    # Sell signals (red diamonds)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]
        
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='red',
                line=dict(color='darkred', width=1.5)
            ),
            hovertemplate='SELL<br>$%{y:.2f}<extra></extra>'
        ))
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        title=dict(
            text=f'{stock_symbol} - EMA Crossover ({fast_period}/{slow_period}) Strategy ({timeframe})',
            font=dict(size=20, family='Arial Black'),
            x=0.5,
            xanchor='center'
        ),
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date'
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Date",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',
        tickformat='%b %d, %Y',
        tickangle=-45,
        nticks=10
    )
    
    fig.update_yaxes(
        title_text="Price ($)",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    return fig


def create_ema_chart(df, ema_line, ema_period, buy_signals, sell_signals, timeframe="Daily"):
    """
    Create single-panel chart for EMA with price and signals
    
    Shows:
    - Price line
    - EMA line
    - Buy/Sell signals (green/red diamonds)
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create single chart
    fig = go.Figure()
    
    # ========================================================================
    # PRICE LINE
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=df['Close'],
        name='Price',
        line=dict(color='black', width=2.5),
        hovertemplate='Price: $%{y:.2f}<extra></extra>'
    ))
    
    # ========================================================================
    # EMA LINE (Dotted)
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ema_line,
        name=f'{ema_period} EMA',
        line=dict(color='blue', width=2, dash='dot'),  # Dotted line
        hovertemplate=f'{ema_period} EMA: $%{{y:.2f}}<extra></extra>'
    ))
    
    # ========================================================================
    # BUY/SELL SIGNALS
    # ========================================================================
    
    # Buy signals (green diamonds)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]
        
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='green',
                line=dict(color='darkgreen', width=1.5)
            ),
            hovertemplate='BUY<br>$%{y:.2f}<extra></extra>'
        ))
    
    # Sell signals (red diamonds)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]
        
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='red',
                line=dict(color='darkred', width=1.5)
            ),
            hovertemplate='SELL<br>$%{y:.2f}<extra></extra>'
        ))
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        title=dict(
            text=f'{stock_symbol} - {ema_period} EMA Strategy ({timeframe})',
            font=dict(size=20, family='Arial Black'),
            x=0.5,
            xanchor='center'
        ),
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date'
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Date",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',
        tickformat='%b %d, %Y',
        tickangle=-45,
        nticks=10
    )
    
    fig.update_yaxes(
        title_text="Price ($)",
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    return fig


def create_macd_chart(df, macd_line, signal_line, histogram, buy_signals, sell_signals, timeframe="Daily"):
    """
    Create dual-panel chart for MACD with buy/sell signals
    
    Top Panel: MACD line, Signal line, and histogram
    Bottom Panel: Price with buy/sell signal diamonds
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.4, 0.6],
        subplot_titles=(
            f'MACD ({timeframe})',
            f'{stock_symbol} ({timeframe})'
        )
    )
    
    # ========================================================================
    # TOP PANEL: MACD INDICATOR
    # ========================================================================
    
    # MACD Line (blue)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=macd_line,
            name='MACD Line',
            line=dict(color='blue', width=2),
            hovertemplate='MACD: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Signal Line (red)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=signal_line,
            name='Signal Line',
            line=dict(color='red', width=2),
            hovertemplate='Signal: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Histogram (gray bars)
    colors = ['green' if val >= 0 else 'red' for val in histogram]
    fig.add_trace(
        go.Bar(
            x=dates,
            y=histogram,
            name='Histogram',
            marker_color=colors,
            opacity=0.3,
            hovertemplate='Histogram: %{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=1)
    
    # ========================================================================
    # BOTTOM PANEL: PRICE WITH SIGNALS
    # ========================================================================
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=df['Close'],
            name='Price',
            line=dict(color='blue', width=2),
            hovertemplate='$%{y:.2f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Buy signals (green diamonds)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]
        
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='Buy Signal',
                marker=dict(
                    symbol='diamond',
                    size=8,
                    color='green',
                    line=dict(color='darkgreen', width=1.5)
                ),
                hovertemplate='BUY<br>$%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # Sell signals (red diamonds)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]
        
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='Sell Signal',
                marker=dict(
                    symbol='diamond',
                    size=8,
                    color='red',
                    line=dict(color='darkred', width=1.5)
                ),
                hovertemplate='SELL<br>$%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date',
        xaxis2_type='date',
        font=dict(size=12)
    )
    
    # Update subplot titles
    for i, annotation in enumerate(fig.layout.annotations):
        if i == 1:
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center',
                y=annotation.y - 0.02
            )
        else:
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center'
            )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',
        tickformat='%b %d, %Y',
        tickangle=-45,
        nticks=10
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    fig.update_yaxes(title_text="MACD", row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    return fig


def create_ichimoku_chart(df, tenkan, kijun, senkou_a, senkou_b, ema_13, ema_30, buy_signals, sell_signals, timeframe="Daily", ml_results=None):
    """
    Create single-panel chart for Ichimoku Cloud with EMAs and signals
    
    Shows:
    - Price line
    - Ichimoku Cloud with proper color coding:
      * GREEN when Span A > Span B (Bullish)
      * RED when Span A < Span B (Bearish)
    - Tenkan-sen (Conversion Line)
    - Kijun-sen (Base Line)
    - 13 EMA (dotted blue)
    - 30 EMA (dotted red)
    - Buy/Sell signals (green/red diamonds)
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create single chart (no subplots)
    fig = go.Figure()
    
    # ========================================================================
    # ICHIMOKU CLOUD WITH DYNAMIC COLOR CODING
    # ========================================================================
    
    # We'll draw multiple segments with different colors
    # GREEN when Span A >= Span B (Bullish)
    # RED when Span A < Span B (Bearish)
    
    # Find continuous segments of same color
    current_color = None
    segment_start = None
    segments = []
    
    for i in range(len(dates)):
        if pd.notna(senkou_a.iloc[i]) and pd.notna(senkou_b.iloc[i]):
            # Determine color for this point
            if senkou_a.iloc[i] >= senkou_b.iloc[i]:
                point_color = 'green'  # Bullish
            else:
                point_color = 'red'    # Bearish
            
            # Start new segment if color changed or it's the first point
            if current_color != point_color:
                if segment_start is not None:
                    # Save previous segment
                    segments.append({
                        'start': segment_start,
                        'end': i,
                        'color': current_color
                    })
                segment_start = i
                current_color = point_color
    
    # Save the last segment
    if segment_start is not None:
        segments.append({
            'start': segment_start,
            'end': len(dates),
            'color': current_color
        })
    
    # Draw each colored segment
    for seg in segments:
        start_idx = seg['start']
        end_idx = seg['end']
        color = seg['color']
        
        # Determine fill color and opacity
        if color == 'green':
            fill_color = 'rgba(0, 200, 0, 0.2)'   # Green with transparency
            line_color_a = 'rgba(0, 150, 0, 0.5)'
            line_color_b = 'rgba(0, 100, 0, 0.5)'
        else:  # red
            fill_color = 'rgba(255, 0, 0, 0.2)'   # Red with transparency
            line_color_a = 'rgba(200, 0, 0, 0.5)'
            line_color_b = 'rgba(150, 0, 0, 0.5)'
        
        # Get segment data
        seg_dates = dates[start_idx:end_idx]
        seg_span_a = senkou_a.iloc[start_idx:end_idx]
        seg_span_b = senkou_b.iloc[start_idx:end_idx]
        
        # Draw Senkou Span A for this segment
        showlegend_a = (seg == segments[0])  # Only show legend for first segment
        fig.add_trace(go.Scatter(
            x=seg_dates,
            y=seg_span_a,
            name='Senkou Span A' if showlegend_a else '',
            line=dict(color=line_color_a, width=1),
            showlegend=showlegend_a,
            legendgroup='spanA',
            hovertemplate='Span A: %{y:.2f}<extra></extra>'
        ))
        
        # Draw Senkou Span B for this segment with fill
        showlegend_b = (seg == segments[0])
        fig.add_trace(go.Scatter(
            x=seg_dates,
            y=seg_span_b,
            name='Senkou Span B' if showlegend_b else '',
            line=dict(color=line_color_b, width=1),
            fill='tonexty',  # Fill to previous trace (Span A)
            fillcolor=fill_color,
            showlegend=showlegend_b,
            legendgroup='spanB',
            hovertemplate='Span B: %{y:.2f}<extra></extra>'
        ))
    
    # ========================================================================
    # EMA LINES
    # ========================================================================
    
    # 13 EMA (dotted blue)
    fig.add_trace(go.Scatter(
        x=dates,
        y=ema_13,
        name='13 EMA',
        line=dict(color='blue', width=2, dash='dot'),
        hovertemplate='13 EMA: %{y:.2f}<extra></extra>'
    ))
    
    # 30 EMA (dotted red)
    fig.add_trace(go.Scatter(
        x=dates,
        y=ema_30,
        name='30 EMA',
        line=dict(color='red', width=2, dash='dot'),
        hovertemplate='30 EMA: %{y:.2f}<extra></extra>'
    ))
    
    # ========================================================================
    # PRICE LINE (on top of everything)
    # ========================================================================
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=df['Close'],
        name='Price',
        line=dict(color='black', width=2.5),
        hovertemplate='Price: $%{y:.2f}<extra></extra>'
    ))
    
    # ========================================================================
    # BUY/SELL SIGNALS (Green and Red Diamonds)
    # ========================================================================
    
    # Buy signals (green diamonds)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]
        
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='green',
                line=dict(color='darkgreen', width=1.5)
            ),
            hovertemplate='BUY<br>$%{y:.2f}<extra></extra>'
        ))
    
    # Sell signals (red diamonds)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]
        
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell Signal',
            marker=dict(
                symbol='diamond',
                size=8,
                color='red',
                line=dict(color='darkred', width=1.5)
            ),
            hovertemplate='SELL<br>$%{y:.2f}<extra></extra>'
        ))
    
    # ========================================================================
    # ML CONFIDENCE ANNOTATIONS
    # ========================================================================
    
    if ml_results:
        # Buy signal annotations
        if ml_results.get('buy_predictions'):
            for idx, prediction in ml_results['buy_predictions']:
                if idx in buy_signals:
                    try:
                        signal_date = dates[idx]
                        signal_price = df['Close'].iloc[idx]
                        confidence = prediction['confidence_pct']
                        level = prediction['confidence_level']
                        
                        if confidence >= 75:
                            conf_color = 'darkgreen'
                        elif confidence >= 60:
                            conf_color = 'orange'
                        else:
                            conf_color = 'red'
                        
                        fig.add_annotation(
                            x=signal_date,
                            y=signal_price * 1.02,
                            text=f"🤖 {confidence:.0f}%<br>{level}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=1.5,
                            arrowcolor=conf_color,
                            ax=0,
                            ay=-30,
                            font=dict(size=10, color=conf_color),
                            bgcolor='white',
                            bordercolor=conf_color,
                            borderwidth=2,
                            borderpad=4
                        )
                    except:
                        continue
        
        # Sell signal annotations
        if ml_results.get('sell_predictions'):
            for idx, prediction in ml_results['sell_predictions']:
                if idx in sell_signals:
                    try:
                        signal_date = dates[idx]
                        signal_price = df['Close'].iloc[idx]
                        confidence = prediction['confidence_pct']
                        level = prediction['confidence_level']
                        
                        if confidence >= 75:
                            conf_color = 'darkred'
                        elif confidence >= 60:
                            conf_color = 'orange'
                        else:
                            conf_color = 'gray'
                        
                        fig.add_annotation(
                            x=signal_date,
                            y=signal_price * 0.98,
                            text=f"🤖 {confidence:.0f}%<br>{level}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=1.5,
                            arrowcolor=conf_color,
                            ax=0,
                            ay=30,
                            font=dict(size=10, color=conf_color),
                            bgcolor='white',
                            bordercolor=conf_color,
                            borderwidth=2,
                            borderpad=4
                        )
                    except:
                        continue
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        title=f'{stock_symbol} - Ichimoku Cloud with 13/30 EMA ({timeframe})',
        xaxis_title='Date',
        yaxis_title='Price',
        template='plotly_white',
        height=600,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        )
    )
    
    return fig


def create_enhanced_tr_chart(df, ema_display_1, ema_display_2, ema_period_1, ema_period_2,
                              buy_signals, sell_signals, signal_details, timeframe='Daily', ml_results=None):
    """
    Create TR / Ichimoku Combo Strategy chart
    
    Display:
    - Candlestick price chart
    - EMA lines (50/200 for Daily, 10/30 for Weekly) - for visual trend context
    - Buy signals (green triangles)
    - Sell signals (red triangles)
    - ML confidence annotations (if available)
    
    Note: Ichimoku cloud is NOT plotted (used only for signal calculation)
    
    Args:
        df: Price DataFrame
        ema_display_1: First EMA to display (50 for Daily, 10 for Weekly)
        ema_display_2: Second EMA to display (200 for Daily, 30 for Weekly)
        ema_period_1: Period label for first EMA
        ema_period_2: Period label for second EMA
        buy_signals: List of indices for buy signals
        sell_signals: List of indices for sell signals
        signal_details: List of dicts with signal information
        timeframe: 'Daily' or 'Weekly'
        ml_results: Dict with 'buy_predictions' and 'sell_predictions' from ML model
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Get dates and stock symbol
    dates = df.index
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create figure
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=dates,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # Add EMA lines (display EMAs - not the signal EMAs)
    fig.add_trace(go.Scatter(
        x=dates,
        y=ema_display_1,
        mode='lines',
        name=f'EMA {ema_period_1}',
        line=dict(color='#2196F3', width=1.5),  # Blue
        opacity=0.8,
        hovertemplate=f'EMA {ema_period_1}: $%{{y:.2f}}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=ema_display_2,
        mode='lines',
        name=f'EMA {ema_period_2}',
        line=dict(color='#FF9800', width=1.5),  # Orange
        opacity=0.8,
        hovertemplate=f'EMA {ema_period_2}: $%{{y:.2f}}<extra></extra>'
    ))
    
    # Add BUY signals (green diamond)
    if buy_signals:
        buy_dates = [dates[i] for i in buy_signals]
        buy_prices = [df['Close'].iloc[i] for i in buy_signals]  # At close price
        buy_hover = []
        
        for i in buy_signals:
            # Find signal detail
            detail = next((d for d in signal_details if d['index'] == i), None)
            if detail:
                hover_text = (
                    f"<b>🟢 BUY SIGNAL</b><br>"
                    f"Date: {detail['date']}<br>"
                    f"Price: ${detail['price']:.2f}<br>"
                    f"TR Status: {detail['tr_status']}<br>"
                    f"EMA 13: ${detail['ema_13']:.2f}<br>"
                    f"EMA 30: ${detail['ema_30']:.2f}<br>"
                    f"Cloud: {detail['cloud_position']}"
                )
            else:
                hover_text = f"BUY @ ${df['Close'].iloc[i]:.2f}"
            buy_hover.append(hover_text)
        
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='BUY Signal',
            marker=dict(
                symbol='diamond',
                size=10,
                color='green',
                line=dict(color='darkgreen', width=1.5)
            ),
            hovertext=buy_hover,
            hoverinfo='text'
        ))
    
    # Add SELL signals (red diamond)
    if sell_signals:
        sell_dates = [dates[i] for i in sell_signals]
        sell_prices = [df['Close'].iloc[i] for i in sell_signals]  # At close price
        sell_hover = []
        
        for i in sell_signals:
            # Find signal detail
            detail = next((d for d in signal_details if d['index'] == i), None)
            if detail:
                hover_text = (
                    f"<b>🔴 SELL SIGNAL</b><br>"
                    f"Date: {detail['date']}<br>"
                    f"Price: ${detail['price']:.2f}<br>"
                    f"TR Status: {detail['tr_status']}<br>"
                    f"EMA 13: ${detail['ema_13']:.2f}<br>"
                    f"EMA 30: ${detail['ema_30']:.2f}<br>"
                    f"Cloud: {detail['cloud_position']}"
                )
            else:
                hover_text = f"SELL @ ${df['Close'].iloc[i]:.2f}"
            sell_hover.append(hover_text)
        
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='SELL Signal',
            marker=dict(
                symbol='diamond',
                size=10,
                color='red',
                line=dict(color='darkred', width=1.5)
            ),
            hovertext=sell_hover,
            hoverinfo='text'
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'📊 {stock_symbol} - TR / Ichimoku Combo Strategy ({timeframe})',
            font=dict(size=18)
        ),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date'
        ),
        height=650,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    # Add signal count annotation
    buy_count = len(buy_signals)
    sell_count = len(sell_signals)
    
    fig.add_annotation(
        text=f"Signals: 🟢 {buy_count} BUY | 🔴 {sell_count} SELL",
        xref="paper", yref="paper",
        x=0, y=1.08,
        showarrow=False,
        font=dict(size=12),
        align="left"
    )
    
    # Add ML confidence annotations
    if ml_results:
        # Add ML confidence for BUY signals
        if ml_results.get('buy_predictions'):
            for idx, prediction in ml_results['buy_predictions']:
                if idx < len(dates):
                    try:
                        confidence = prediction['confidence_pct']
                        level = prediction['confidence_level']
                        
                        # Color based on confidence
                        if confidence >= 75:
                            color = '#00C853'  # Green
                        elif confidence >= 60:
                            color = '#FFD600'  # Yellow
                        else:
                            color = '#FF6D00'  # Orange
                        
                        fig.add_annotation(
                            x=dates[idx],
                            y=df['High'].iloc[idx] * 1.02,
                            text=f"🤖 {confidence:.0f}%<br>{level}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=1,
                            arrowcolor=color,
                            font=dict(size=9, color=color),
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor=color,
                            borderwidth=1,
                            borderpad=2,
                            ax=0,
                            ay=-40
                        )
                    except:
                        pass
        
        # Add ML confidence for SELL signals
        if ml_results.get('sell_predictions'):
            for idx, prediction in ml_results['sell_predictions']:
                if idx < len(dates):
                    try:
                        confidence = prediction['confidence_pct']
                        level = prediction['confidence_level']
                        
                        # Color based on confidence
                        if confidence >= 75:
                            color = '#D50000'  # Red
                        elif confidence >= 60:
                            color = '#FF6D00'  # Orange
                        else:
                            color = '#FFD600'  # Yellow
                        
                        fig.add_annotation(
                            x=dates[idx],
                            y=df['Low'].iloc[idx] * 0.98,
                            text=f"🤖 {confidence:.0f}%<br>{level}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=1,
                            arrowcolor=color,
                            font=dict(size=9, color=color),
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor=color,
                            borderwidth=1,
                            borderpad=2,
                            ax=0,
                            ay=40
                        )
                    except:
                        pass
    
    return fig


def create_simple_indicator_chart(df, indicator_name, indicator_data, timeframe="Daily"):
    """
    Create dual-panel chart WITHOUT buy/sell signals
    Used for indicators that don't have signal logic defined yet
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Handle different indicator types
    if isinstance(indicator_data, tuple):
        main_indicator = indicator_data[0]
        additional_lines = indicator_data[1:]
    else:
        main_indicator = indicator_data
        additional_lines = []
    
    # Get stock name
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.4, 0.6],
        subplot_titles=(
            f'{indicator_name} ({timeframe})',
            f'{stock_symbol} ({timeframe})'
        )
    )
    
    # Get dates
    dates = df.index
    
    # TOP PANEL: INDICATOR
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=main_indicator,
            name=indicator_name,
            line=dict(color='blue', width=2),
            hovertemplate='%{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add additional lines if any
    colors = ['red', 'green', 'purple', 'orange']
    line_names = ['Signal', 'Line 3', 'Line 4', 'Line 5']
    for i, line in enumerate(additional_lines):
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=line,
                name=line_names[i] if i < len(line_names) else f'Line {i+2}',
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # BOTTOM PANEL: PRICE
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=df['Close'],
            name='Price',
            line=dict(color='blue', width=2),
            hovertemplate='$%{y:.2f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # LAYOUT
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date',
        xaxis2_type='date',
        font=dict(size=12)
    )
    
    # Update subplot titles
    for i, annotation in enumerate(fig.layout.annotations):
        if i == 1:
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center',
                y=annotation.y - 0.02
            )
        else:
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center'
            )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',
        tickformat='%b %d, %Y',
        tickangle=-45,
        nticks=10
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    fig.update_yaxes(title_text=indicator_name, row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    return fig


def create_indicator_chart(df, indicator_name, indicator_data, peak_range, valley_range, timeframe="Daily"):
    """
    Create dual-panel chart with indicator on top and price on bottom
    
    Args:
        df: DataFrame with OHLCV data
        indicator_name: Name of the indicator
        indicator_data: Series or tuple of indicator values
        peak_range: tuple (min, max) for peak detection
        valley_range: tuple (min, max) for valley detection
        timeframe: "Daily" or "Weekly" (default: "Daily")
    """
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        else:
            df.index = pd.to_datetime(df.index)
    
    # Handle different indicator types
    if isinstance(indicator_data, tuple):
        # Multiple lines (e.g., MACD with signal and histogram)
        main_indicator = indicator_data[0]
        additional_lines = indicator_data[1:]
    else:
        main_indicator = indicator_data
        additional_lines = []
    
    # Find peaks and valleys
    peaks, valleys, peak_threshold, valley_threshold = find_peaks_and_valleys(
        main_indicator, peak_range, valley_range
    )
    
    # Create subplots with 2 rows
    # Top panel (indicator) should be 40% height, bottom (price) 60%
    
    # Get stock name from dataframe
    stock_symbol = df["Symbol"].iloc[0] if "Symbol" in df.columns else "Stock"
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,  # Increased from 0.03 to 0.08 for more space
        row_heights=[0.4, 0.6],
        subplot_titles=(
            f'{indicator_name} ({timeframe})',  # Top chart: "RSI (Weekly)"
            f'{stock_symbol} ({timeframe})'     # Bottom chart: "GOOGL (Weekly)"
        )
    )
    
    # ========================================================================
    # TOP PANEL: INDICATOR
    # ========================================================================
    
    # Get dates from dataframe index
    dates = df.index
    
    # Main indicator line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=main_indicator,
            name=indicator_name,
            line=dict(color='blue', width=2),
            hovertemplate='%{y:.2f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Additional lines (e.g., MACD signal line)
    colors = ['red', 'green', 'purple']
    for i, line in enumerate(additional_lines):
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=line,
                name=f'{indicator_name} Signal',
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate='%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Peak threshold line (green) with label
    fig.add_trace(
        go.Scatter(
            x=[dates[0], dates[-1]],
            y=[peak_threshold, peak_threshold],
            name='Peak Threshold',
            line=dict(color='green', width=2, dash='solid'),
            hoverinfo='skip',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add peak threshold value annotation (top left)
    fig.add_annotation(
        x=dates[0],
        y=peak_threshold,
        text=f"{peak_threshold:.2f}",
        showarrow=False,
        xanchor='left',
        yanchor='bottom',
        font=dict(size=12, color='green', family='Arial Black'),
        bgcolor='white',
        bordercolor='green',
        borderwidth=1,
        row=1, col=1
    )
    
    # Valley threshold line (red) with label
    fig.add_trace(
        go.Scatter(
            x=[dates[0], dates[-1]],
            y=[valley_threshold, valley_threshold],
            name='Valley Threshold',
            line=dict(color='red', width=2, dash='solid'),
            hoverinfo='skip',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Add valley threshold value annotation (top left)
    fig.add_annotation(
        x=dates[0],
        y=valley_threshold,
        text=f"{valley_threshold:.2f}",
        showarrow=False,
        xanchor='left',
        yanchor='top',
        font=dict(size=12, color='red', family='Arial Black'),
        bgcolor='white',
        bordercolor='red',
        borderwidth=1,
        row=1, col=1
    )
    
    # ========================================================================
    # BOTTOM PANEL: PRICE CHART
    # ========================================================================
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=df['Close'],
            name='Price',
            line=dict(color='blue', width=2),
            hovertemplate='$%{y:.2f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add green diamonds at valley points (buy signals)
    if valleys:
        valley_dates = [dates[i] for i in valleys]
        valley_prices = [df['Close'].iloc[i] for i in valleys]
        
        fig.add_trace(
            go.Scatter(
                x=valley_dates,
                y=valley_prices,
                mode='markers',
                name='Buy Signal',
                marker=dict(
                    symbol='diamond',
                    size=8,
                    color='green',
                    line=dict(color='darkgreen', width=1.5)
                ),
                hovertemplate='Buy Signal<br>$%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # Add red diamonds at peak points (sell signals)
    if peaks:
        peak_dates = [dates[i] for i in peaks]
        peak_prices = [df['Close'].iloc[i] for i in peaks]
        
        fig.add_trace(
            go.Scatter(
                x=peak_dates,
                y=peak_prices,
                mode='markers',
                name='Sell Signal',
                marker=dict(
                    symbol='diamond',
                    size=8,
                    color='red',
                    line=dict(color='darkred', width=1.5)
                ),
                hovertemplate='Sell Signal<br>$%{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # ========================================================================
    # LAYOUT
    # ========================================================================
    
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_type='date',  # Force date type on x-axis
        xaxis2_type='date',  # Force date type on second x-axis
        font=dict(size=12)
    )
    
    # Update subplot titles to be larger and centered
    for i, annotation in enumerate(fig.layout.annotations):
        if i == 1:  # Bottom chart title (second annotation)
            # Move it down more
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center',
                y=annotation.y - 0.02  # Move down by 2%
            )
        else:  # Top chart title
            annotation.update(
                font=dict(size=16, family='Arial Black'),
                xanchor='center'
            )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black',
        type='date',  # Explicitly set as date type
        tickformat='%b %d, %Y',  # Format as "Jan 15, 2024"
        tickangle=-45,  # Angle the dates for better readability
        nticks=10  # Number of tick marks
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        showline=True,
        linecolor='black'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text=indicator_name, row=1, col=1)
    fig.update_yaxes(title_text="Price ($)", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    return fig

# ============================================================================
# MAIN PAGE
# ============================================================================

st.title("📈 Indicator Chart")
st.markdown("**Dual-panel chart showing indicator signals and price action**")
st.markdown("---")

# ============================================================================
# SYNC FROM STOCKS ANALYSIS
# ============================================================================

synced_symbol = ""
synced_indicator = ""
synced_indicator_idx = 0
synced_tf = "daily"
synced_tf_idx = 0
should_auto_analyze = False

indicator_options = ["RSI", "MACD", "EMA", "EMA Crossover", "Ichimoku Cloud", "SuperTrend", "TR / Ichimoku Combo Strategy"]

if st.session_state.get('auto_sync_enabled', False) and st.session_state.get('sync_indicator_chart', False):
    if st.session_state.get('synced_symbol', ''):
        synced_symbol = st.session_state.get('synced_symbol', '')
        synced_indicator = st.session_state.get('sync_indicator_type', 'RSI')
        synced_tf = st.session_state.get('synced_timeframe', 'daily')
        synced_tf_idx = 0 if synced_tf == 'daily' else 1
        
        # Get index for indicator dropdown
        if synced_indicator in indicator_options:
            synced_indicator_idx = indicator_options.index(synced_indicator)
        
        # Check if this is a NEW sync (symbol or indicator or timeframe changed)
        last_synced = st.session_state.get('ic_last_synced', '')
        current_sync_key = f"{synced_symbol}_{synced_indicator}_{synced_tf}"
        
        if current_sync_key != last_synced:
            st.session_state['ic_last_synced'] = current_sync_key
            should_auto_analyze = True

# Determine defaults for inputs
if synced_symbol:
    default_symbol = synced_symbol
    default_indicator_idx = synced_indicator_idx
    default_tf_idx = synced_tf_idx
elif 'ic_last_analyzed_symbol' in st.session_state:
    default_symbol = st.session_state['ic_last_analyzed_symbol']
    last_indicator = st.session_state.get('ic_last_analyzed_indicator', 'RSI')
    default_indicator_idx = indicator_options.index(last_indicator) if last_indicator in indicator_options else 0
    last_tf = st.session_state.get('ic_last_analyzed_timeframe', 'Daily')
    default_tf_idx = 0 if last_tf == 'Daily' else 1
else:
    default_symbol = "GOOGL"
    default_indicator_idx = 0
    default_tf_idx = 0

# ============================================================================
# CONTROLS
# ============================================================================

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    indicator_choice = st.selectbox(
        "Indicator:",
        indicator_options,
        index=default_indicator_idx,
        help="Select technical indicator to display"
    )

with col2:
    symbol = st.text_input(
        "Symbol:",
        value=default_symbol,
        help="Enter stock ticker symbol"
    ).upper()

with col3:
    duration_choice = st.selectbox(
        "Chart Duration:",
        ["1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years"],
        index=4,  # Default to 3 Years
        help="Select data duration"
    )

# Show sync indicator if synced
if synced_symbol:
    st.caption(f"🔗 Synced from Stocks Analysis ({synced_symbol}, {synced_indicator}, {synced_tf.capitalize()})")

# Duration mapping
duration_map = {
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365,
    "3 Years": 1095,
    "5 Years": 1825
}
duration_days = duration_map[duration_choice]

# Indicator-specific parameters
st.markdown("### Indicator Parameters")

if indicator_choice == "EMA":
    col_ema_param, col_spacer = st.columns([1, 3])  # Make input box narrower
    with col_ema_param:
        ema_period = st.number_input(
            "EMA Period:",
            min_value=3,
            max_value=250,
            value=20,
            step=1,
            help="Enter EMA period (3-250)"
        )
elif indicator_choice == "EMA Crossover":
    col_ema1, col_ema2 = st.columns(2)
    with col_ema1:
        fast_ema = st.number_input(
            "Fast EMA:",
            min_value=3,
            max_value=250,
            value=12,
            step=1,
            help="Fast EMA period (must be less than Slow EMA)"
        )
    with col_ema2:
        slow_ema = st.number_input(
            "Slow EMA:",
            min_value=3,
            max_value=250,
            value=26,
            step=1,
            help="Slow EMA period (must be greater than Fast EMA)"
        )
    
    # Validation
    if fast_ema >= slow_ema:
        st.error("⚠️ Fast EMA must be less than Slow EMA!")
        st.stop()

elif indicator_choice == "SuperTrend":
    col_st1, col_st2, col_spacer = st.columns([1, 1, 2])
    with col_st1:
        atr_period = st.number_input(
            "ATR Period:",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            help="Period for ATR calculation (default: 10)"
        )
    with col_st2:
        atr_multiplier = st.number_input(
            "ATR Multiplier:",
            min_value=0.5,
            max_value=10.0,
            value=3.0,
            step=0.5,
            help="Multiplier for ATR (default: 3.0)"
        )

# Timeframe selection
col4, col5, col6 = st.columns([1, 1, 3])

with col4:
    timeframe = st.radio(
        "Chart Timeframe:",
        ["Daily", "Weekly"],
        index=default_tf_idx,
        horizontal=True
    )

with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    update_button = st.button("🔄 Update", type="primary", use_container_width=True)

# Auto-analyze if:
# 1. New sync from Stocks Analysis, OR
# 2. Returning to page with previously analyzed symbol/indicator/timeframe (re-run from cache)
if should_auto_analyze and symbol:
    update_button = True
elif not update_button:
    last_symbol = st.session_state.get('ic_last_analyzed_symbol', '')
    last_indicator = st.session_state.get('ic_last_analyzed_indicator', '')
    last_tf = st.session_state.get('ic_last_analyzed_timeframe', '')
    if last_symbol and last_symbol.upper() == symbol.upper() and last_indicator == indicator_choice and last_tf == timeframe:
        update_button = True

st.markdown("---")

# ============================================================================
# INDICATOR-SPECIFIC PARAMETERS
# ============================================================================

# Define peak and valley ranges for RSI (only RSI has this logic for now)
indicator_params = {
    "RSI": {
        "peak_range": (70, 100),
        "valley_range": (21, 39),
        "period": 14,
        "has_signals": True  # RSI logic is complete
    },
    "MACD": {
        "has_signals": True  # SMA crossover signals implemented
    },
    "EMA": {
        "has_signals": True  # Price crossover signals implemented
    },
    "EMA Crossover": {
        "has_signals": True  # EMA crossover signals implemented
    },
    "Ichimoku Cloud": {
        "has_signals": True  # Now has signal logic!
    },
    "SuperTrend": {
        "has_signals": True  # Price/SuperTrend crossover signals
    },
    "TR / Ichimoku Combo Strategy": {
        "has_signals": True  # TR + Ichimoku + EMA combined strategy
    }
}

# ============================================================================
# INFORMATION BOX
# ============================================================================

if indicator_choice == "RSI":
    st.info(f"""
**How to read this chart:**

**Top Panel:** {indicator_choice} indicator with calculated thresholds
- **Green line:** Peak threshold (average of all peaks in peak range)
- **Red line:** Valley threshold (average of all valleys in valley range)

**Bottom Panel:** Stock price with buy/sell signals

**🟢 BUY SIGNAL (Green Diamond):**
1. RSI encounters a valley in the valley range (top chart)
2. Then RSI crosses the red line (valley threshold) from below going up
3. Buy signal appears at the crossover point on the price chart

**🔴 SELL SIGNAL (Red Diamond):**
1. RSI encounters a peak in the peak range (top chart)
2. Then RSI crosses the green line (peak threshold) from above going down
3. Sell signal appears at the crossover point on the price chart

**Note:** Indicator and price charts use the same timeframe ({'Daily' if timeframe == 'Daily' else 'Weekly'})
""")
elif indicator_choice == "MACD":
    st.info(f"""
**How to read this chart:**

**Top Panel:** MACD Indicator
- **Blue line:** MACD Line (12 EMA - 26 EMA)
- **Red line:** Signal Line (9 EMA of MACD)
- **Gray bars:** Histogram (MACD - Signal)
  - Green bars: MACD above Signal (bullish)
  - Red bars: MACD below Signal (bearish)

**Bottom Panel:** Stock price with buy/sell signals

**🟢 BUY SIGNAL (Green Diamond):**
1. MACD line crosses ABOVE Signal line (from below)
2. Indicates bullish momentum shift
3. Green diamond marks the entry point on price chart

**🔴 SELL SIGNAL (Red Diamond):**
1. MACD line crosses BELOW Signal line (from above)
2. Indicates bearish momentum shift
3. Red diamond marks the exit point on price chart

**Trading Logic:**
- Traditional MACD crossover system
- Buy when faster MACD crosses above slower Signal line
- Sell when faster MACD crosses below slower Signal line
- Histogram shows the strength of the trend

**Note:** Using standard MACD settings (12, 26, 9)
""")
elif indicator_choice == "EMA":
    st.info(f"""
**How to read this chart:**

**Single Chart Display:** Price with EMA overlay

**Components:**
- **Black line:** Price
- **Blue line:** {ema_period}-period EMA (Exponential Moving Average)

**🟢 BUY SIGNAL (Green Diamond):**
1. Price crosses ABOVE the EMA line (from below)
2. Indicates bullish momentum
3. Price breaking above moving average support
4. Green diamond marks the entry point

**🔴 SELL SIGNAL (Red Diamond):**
1. Price crosses BELOW the EMA line (from above)
2. Indicates bearish momentum
3. Price breaking below moving average resistance
4. Red diamond marks the exit point

**Trading Logic:**
- EMA acts as dynamic support/resistance
- Buy when price breaks above EMA (trend turning bullish)
- Sell when price breaks below EMA (trend turning bearish)
- Longer EMA periods = smoother line, fewer signals
- Shorter EMA periods = more responsive, more signals

**Current EMA Period:** {ema_period} days
- Lower values (5-20): More signals, more sensitive
- Medium values (20-50): Balanced approach
- Higher values (50-200): Fewer signals, major trends only
""")
elif indicator_choice == "EMA Crossover":
    st.info(f"""
**How to read this chart:**

**Single Chart Display:** Price with dual EMA overlay

**Components:**
- **Black line:** Price
- **Blue line:** {fast_ema}-period Fast EMA
- **Red line:** {slow_ema}-period Slow EMA

**🟢 BUY SIGNAL (Green Diamond):**
1. Fast EMA ({fast_ema}) crosses ABOVE Slow EMA ({slow_ema}) from below
2. Indicates bullish momentum shift
3. Faster moving average breaking above slower one
4. Classic "Golden Cross" when using longer periods (e.g., 50/200)
5. Green diamond marks the entry point

**🔴 SELL SIGNAL (Red Diamond):**
1. Fast EMA ({fast_ema}) crosses BELOW Slow EMA ({slow_ema}) from above
2. Indicates bearish momentum shift
3. Faster moving average breaking below slower one
4. Classic "Death Cross" when using longer periods (e.g., 50/200)
5. Red diamond marks the exit point

**Trading Logic:**
- Dual EMA crossover strategy (classic trend-following system)
- Buy when fast EMA crosses above slow EMA (momentum turning bullish)
- Sell when fast EMA crosses below slow EMA (momentum turning bearish)
- Fast EMA reacts quicker to price changes
- Slow EMA provides trend confirmation
- Crossover = significant momentum shift

**Popular EMA Combinations:**
- **12/26:** MACD default (short-term trading)
- **20/50:** Swing trading favorite
- **50/200:** Long-term investing (Golden/Death Cross)
- **Your selection:** {fast_ema}/{slow_ema}

**Note:** Longer periods = fewer signals but stronger trends
""")
elif indicator_choice == "Ichimoku Cloud":
    st.info(f"""
**How to read this chart:**

**Single Chart Display:** Price with Ichimoku Cloud + EMA Strategy

**Components:**
- **Black line:** Price
- **Green/Red Cloud:** Ichimoku Cloud (Senkou Span A & B only)
  - Cloud boundaries show support/resistance zones
  - Price above cloud = bullish
  - Price below cloud = bearish
  - Price in cloud = neutral/transition
- **Blue dotted line:** 13-period EMA (fast)
- **Red dotted line:** 30-period EMA (slow)

**🟢 BUY SIGNAL (Green Diamond):**
1. 13 EMA crosses ABOVE 30 EMA (bullish EMA crossover)
2. AND price is inside the cloud OR above the cloud
3. Green diamond marks the entry point

**🔴 SELL SIGNAL (Red Diamond):**
1. 13 EMA crosses BELOW 30 EMA (bearish EMA crossover)
2. AND price is inside the cloud OR below the cloud
3. Red diamond marks the exit point

**Trading Logic:**
- Buy when fast EMA (13) crosses slow EMA (30) upward + price strength confirmed by cloud position
- Sell when fast EMA (13) crosses slow EMA (30) downward + price weakness confirmed by cloud position
- Cloud acts as dynamic support/resistance zone
""")

elif indicator_choice == "SuperTrend":
    st.info(f"""
**How to read this chart:**

**Single Chart Display:** Price with SuperTrend overlay

**Components:**
- **Black line:** Price
- **Green line:** SuperTrend in uptrend (price above SuperTrend)
- **Red line:** SuperTrend in downtrend (price below SuperTrend)

**SuperTrend Parameters:**
- **ATR Period:** {atr_period} (measures volatility)
- **ATR Multiplier:** {atr_multiplier} (sensitivity adjustment)

**🟢 BUY SIGNAL (Green Diamond):**
1. Price closes ABOVE the SuperTrend line
2. SuperTrend line turns GREEN (uptrend confirmed)
3. Indicates potential uptrend beginning
4. Green diamond marks the entry point

**🔴 SELL SIGNAL (Red Diamond):**
1. Price falls BELOW the SuperTrend line
2. SuperTrend line turns RED (downtrend confirmed)
3. Indicates potential downtrend beginning
4. Red diamond marks the exit point

**How SuperTrend Works:**
- Uses ATR (Average True Range) to measure volatility
- Creates dynamic support/resistance based on volatility
- Green line = Price in uptrend, SuperTrend acts as support
- Red line = Price in downtrend, SuperTrend acts as resistance
- Line color changes when trend changes

**Trading Logic:**
- Strong trend-following indicator
- Buy when price breaks above SuperTrend (trend turning bullish)
- Sell when price breaks below SuperTrend (trend turning bearish)
- Works best in trending markets
- Reduces whipsaws compared to simple moving averages

**Adjusting Parameters:**
- **Lower ATR Period (5-7):** More sensitive, more signals
- **Higher ATR Period (14-20):** Less sensitive, fewer signals
- **Lower Multiplier (1-2):** Tighter stops, more signals
- **Higher Multiplier (3-5):** Wider stops, fewer signals
- **Current: {atr_period} period, {atr_multiplier}x multiplier**
""")

elif indicator_choice == "TR / Ichimoku Combo Strategy":
    st.info("""
**TR / Ichimoku Combo Strategy** - A conservative, high-quality signal system that combines multiple technical indicators to identify strong trend entries and exits.

**Chart:** Candlesticks with EMA 50/200 (Daily) or 10/30 (Weekly) | Green ◆ = BUY | Red ◆ = SELL

*Signals alternate (BUY→SELL→BUY) - fewer signals but higher confidence.*
""")

# ============================================================================
# GENERATE CHART
# ============================================================================

if update_button:
    
    st.session_state['indicator_chart_symbol'] = symbol
    st.session_state['indicator_chart_indicator'] = indicator_choice
    st.session_state['indicator_chart_duration'] = duration_choice
    st.session_state['indicator_chart_timeframe'] = timeframe
    
    with st.spinner(f"📊 Loading {duration_choice} of {timeframe.lower()} data for {symbol}..."):
        
        try:
            # Fetch data
            df = get_shared_stock_data(
                ticker=symbol,
                duration_days=duration_days,
                timeframe=timeframe.lower(),
                api_source='yahoo'
            )
            
            if df is None or df.empty:
                st.error(f"❌ Could not retrieve data for {symbol}")
                st.stop()
            
            # Add symbol to dataframe
            df['Symbol'] = symbol
            
            # Calculate selected indicator
            params = indicator_params[indicator_choice]
            
            if indicator_choice == "RSI":
                indicator_data = calculate_rsi(df, params['period'])
                
            elif indicator_choice == "MACD":
                macd, signal, histogram = calculate_macd(df)
                indicator_data = (macd, signal, histogram)  # Include histogram!
                
            elif indicator_choice == "EMA":
                ema = calculate_ema(df, ema_period)
                indicator_data = ema
                
            elif indicator_choice == "EMA Crossover":
                fast_ema_line, slow_ema_line = calculate_ema_crossover(df, fast_ema, slow_ema)
                indicator_data = (fast_ema_line, slow_ema_line)
                
            elif indicator_choice == "Ichimoku Cloud":
                tenkan, kijun, senkou_a, senkou_b, chikou = calculate_ichimoku(df)
                # Also calculate 13 and 30 EMAs for this strategy
                ema_13 = calculate_ema(df, 13)
                ema_30 = calculate_ema(df, 30)
                indicator_data = (tenkan, kijun, senkou_a, senkou_b, chikou, ema_13, ema_30)
            
            elif indicator_choice == "SuperTrend":
                supertrend, trend = calculate_supertrend(df, atr_period, atr_multiplier)
                indicator_data = (supertrend, trend)
            
            # Create chart based on indicator type
            if indicator_choice == "SuperTrend":
                # SuperTrend with price crossover signals
                supertrend, trend = indicator_data
                
                # Find buy/sell signals
                buy_signals, sell_signals = find_supertrend_signals(df, supertrend, trend)
                
                # Create SuperTrend chart (single panel)
                fig = create_supertrend_chart(
                    df=df,
                    supertrend=supertrend,
                    trend=trend,
                    atr_period=atr_period,
                    atr_multiplier=atr_multiplier,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    timeframe=timeframe
                )
                
            elif indicator_choice == "EMA Crossover":
                # EMA Crossover with dual EMA signals
                fast_ema_line, slow_ema_line = indicator_data
                
                # Find buy/sell signals
                buy_signals, sell_signals = find_ema_crossover_signals(fast_ema_line, slow_ema_line)
                
                # Create EMA Crossover chart (single panel)
                fig = create_ema_crossover_chart(
                    df=df,
                    fast_ema=fast_ema_line,
                    slow_ema=slow_ema_line,
                    fast_period=fast_ema,
                    slow_period=slow_ema,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    timeframe=timeframe
                )
                
            elif indicator_choice == "EMA":
                # EMA with price crossover signals
                ema_line = indicator_data
                
                # Find buy/sell signals
                buy_signals, sell_signals = find_ema_signals(df, ema_line)
                
                # Create EMA chart (single panel)
                fig = create_ema_chart(
                    df=df,
                    ema_line=ema_line,
                    ema_period=ema_period,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    timeframe=timeframe
                )
                
            elif indicator_choice == "MACD":
                # MACD with crossover signals
                macd_line, signal_line, histogram = indicator_data
                
                # Find buy/sell signals
                buy_signals, sell_signals = find_macd_signals(macd_line, signal_line)
                
                # Create MACD chart (dual panel)
                fig = create_macd_chart(
                    df=df,
                    macd_line=macd_line,
                    signal_line=signal_line,
                    histogram=histogram,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    timeframe=timeframe
                )
                
            elif indicator_choice == "Ichimoku Cloud":
                # Special handling for Ichimoku - single panel with all components
                tenkan, kijun, senkou_a, senkou_b, chikou, ema_13, ema_30 = indicator_data
                
                # Find buy/sell signals
                buy_signals, sell_signals = find_ichimoku_signals(
                    df, tenkan, kijun, senkou_a, senkou_b, ema_13, ema_30
                )
                
                # Get ML confidence scores for signals
                try:
                    ema_200 = calculate_ema(df, 200)
                    ml_results = get_ml_confidence_for_signals(
                        df, buy_signals, sell_signals, 
                        ema_13, ema_30, ema_200,
                        senkou_a, senkou_b
                    )
                    # Store ML results for metrics display
                    st.session_state['ichimoku_ml_results'] = ml_results

                except Exception as e:
                    st.warning(f"⚠️ ML predictions unavailable: {str(e)}")
                    ml_results = {'buy_predictions': [], 'sell_predictions': []}
                    st.session_state['ichimoku_ml_results'] = ml_results
                
                # Create Ichimoku chart (single panel)
                fig = create_ichimoku_chart(
                    df=df,
                    tenkan=tenkan,
                    kijun=kijun,
                    senkou_a=senkou_a,
                    senkou_b=senkou_b,
                    ema_13=ema_13,
                    ema_30=ema_30,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    timeframe=timeframe,
                    ml_results=ml_results
                )
            
            elif indicator_choice == "TR / Ichimoku Combo Strategy":
                # TR / Ichimoku Combo Strategy Strategy
                # Combines: TR Indicator + Ichimoku Cloud + EMA Crossover
                
                # Ensure minimum 1 year of data for TR analysis
                actual_duration = max(365, duration_days)
                
                # Fetch TR analysis data
                try:
                    with st.spinner("🔄 Calculating TR Indicator..."):
                        tr_data = analyze_stock_complete_tr(
                            ticker=symbol,
                            timeframe=timeframe.lower(),
                            duration_days=actual_duration
                        )
                except Exception as e:
                    st.error(f"❌ Error calculating TR Indicator: {str(e)}")
                    st.stop()
                
                if tr_data is None or tr_data.empty:
                    st.error(f"❌ Could not calculate TR Indicator for {symbol}")
                    st.stop()
                
                # Calculate Ichimoku components (for signal logic, not display)
                tenkan, kijun, senkou_a, senkou_b, chikou = calculate_ichimoku(df)
                
                # Calculate signal EMAs (13/30 - for signal detection)
                ema_13 = calculate_ema(df, 13)
                ema_30 = calculate_ema(df, 30)
                
                # Calculate display EMAs based on timeframe
                if timeframe == 'Daily':
                    ema_display_1 = calculate_ema(df, 50)
                    ema_display_2 = calculate_ema(df, 200)
                    ema_period_1 = 50
                    ema_period_2 = 200
                else:  # Weekly
                    ema_display_1 = calculate_ema(df, 10)
                    ema_display_2 = calculate_ema(df, 30)
                    ema_period_1 = 10
                    ema_period_2 = 30
                
                # Find Enhanced TR signals
                buy_signals, sell_signals, signal_details = find_enhanced_tr_signals(
                    df, tr_data, ema_13, ema_30, senkou_a, senkou_b
                )
                
                # Get ML confidence scores for Combo signals (using Ichimoku ML)
                try:
                    ema_200 = calculate_ema(df, 200)
                    combo_ml_results = get_ml_confidence_for_signals(
                        df, buy_signals, sell_signals,
                        ema_13, ema_30, ema_200,
                        senkou_a, senkou_b
                    )
                    # Store ML results for metrics display
                    st.session_state['combo_ml_results'] = combo_ml_results
                except Exception as e:
                    st.warning(f"⚠️ ML predictions unavailable: {str(e)}")
                    combo_ml_results = {'buy_predictions': [], 'sell_predictions': []}
                    st.session_state['combo_ml_results'] = combo_ml_results
                
                # Create chart
                fig = create_enhanced_tr_chart(
                    df=df,
                    ema_display_1=ema_display_1,
                    ema_display_2=ema_display_2,
                    ema_period_1=ema_period_1,
                    ema_period_2=ema_period_2,
                    buy_signals=buy_signals,
                    sell_signals=sell_signals,
                    signal_details=signal_details,
                    timeframe=timeframe,
                    ml_results=combo_ml_results
                )
                
                # Store signal details for table display
                st.session_state['enhanced_tr_signals'] = signal_details
                
            elif params.get('has_signals', False):
                # RSI - has buy/sell signals
                fig = create_indicator_chart(
                    df=df,
                    indicator_name=indicator_choice,
                    indicator_data=indicator_data,
                    peak_range=params['peak_range'],
                    valley_range=params['valley_range'],
                    timeframe=timeframe
                )
            else:
                # For indicators without signal logic yet (MACD, EMA, EMA Crossover)
                fig = create_simple_indicator_chart(
                    df=df,
                    indicator_name=indicator_choice,
                    indicator_data=indicator_data,
                    timeframe=timeframe
                )
            
            # Store in session state
            st.session_state['indicator_chart_fig'] = fig
            st.session_state['indicator_chart_data'] = {
                'df': df,
                'indicator': indicator_choice,
                'timeframe': timeframe
            }
            
            st.success(f"✅ Chart generated for {symbol} ({duration_choice}, {timeframe})")
            
            # Store what was analyzed (for re-display on return)
            st.session_state['ic_last_analyzed_symbol'] = symbol
            st.session_state['ic_last_analyzed_indicator'] = indicator_choice
            st.session_state['ic_last_analyzed_timeframe'] = timeframe
            
        except Exception as e:
            st.error(f"❌ Error generating chart: {str(e)}")
            with st.expander("Show error details"):
                st.exception(e)

# Display chart if it exists in session state
if 'indicator_chart_fig' in st.session_state:
    st.plotly_chart(st.session_state['indicator_chart_fig'], use_container_width=True)
    
    # Display Ichimoku ML Performance Metrics if available
    if 'indicator_chart_data' in st.session_state:
        if st.session_state['indicator_chart_data'].get('indicator') == 'Ichimoku Cloud':
            if 'ichimoku_ml_results' in st.session_state:
                ml_results = st.session_state['ichimoku_ml_results']
                
                # Get metrics from the first prediction (they're the same for all signals of same timeframe)
                if ml_results.get('buy_predictions') or ml_results.get('sell_predictions'):
                    # Try to get metrics from first available prediction
                    first_pred = None
                    if ml_results.get('buy_predictions'):
                        first_pred = ml_results['buy_predictions'][0][1]
                    elif ml_results.get('sell_predictions'):
                        first_pred = ml_results['sell_predictions'][0][1]
                    
                    if first_pred and first_pred.get('performance_metrics'):
                        metrics = first_pred['performance_metrics']
                        
                        st.markdown("### 📈 Ichimoku Strategy Performance Metrics")
                        mcol1, mcol2, mcol3 = st.columns(3)
                        
                        with mcol1:
                            pf = metrics['profit_factor']
                            st.metric(
                                f"{pf['emoji']} Profit Factor", 
                                pf['display'],
                                pf['rating'],
                                help=pf['help']
                            )
                        with mcol2:
                            exp = metrics['expectancy']
                            st.metric(
                                f"{exp['emoji']} Expectancy", 
                                exp['display'],
                                exp['rating'],
                                help=exp['help']
                            )
                        with mcol3:
                            ar = metrics['annual_return']
                            st.metric(
                                f"{ar['emoji']} Annual Return", 
                                ar['display'],
                                ar['rating'],
                                help=ar['help']
                            )
                        
                        # Show data source note
                        if metrics.get('data_source') == 'estimated':
                            st.caption(f"📊 Based on {metrics['total_trades']:,} training samples | Win Rate: {metrics['win_rate']}% | *Estimated metrics*")
                        else:
                            st.caption(f"📊 Based on {metrics['total_trades']:,} historical trades | Win Rate: {metrics['win_rate']}%")
    
    # Display TR / Ichimoku Combo Strategy ML metrics and table
    if 'indicator_chart_data' in st.session_state:
        if st.session_state['indicator_chart_data'].get('indicator') == 'TR / Ichimoku Combo Strategy':
            # Display ML Performance Metrics for Combo Strategy
            if 'combo_ml_results' in st.session_state:
                ml_results = st.session_state['combo_ml_results']
                
                # Get metrics from the first prediction
                if ml_results.get('buy_predictions') or ml_results.get('sell_predictions'):
                    first_pred = None
                    if ml_results.get('buy_predictions'):
                        first_pred = ml_results['buy_predictions'][0][1]
                    elif ml_results.get('sell_predictions'):
                        first_pred = ml_results['sell_predictions'][0][1]
                    
                    if first_pred:
                        # ML Confidence Summary Section (like TR Indicator)
                        st.markdown("### 🤖 ML Confidence Score")
                        
                        # Calculate average confidence from all predictions
                        all_confidences = []
                        if ml_results.get('buy_predictions'):
                            for _, pred in ml_results['buy_predictions']:
                                all_confidences.append(pred['confidence_pct'])
                        if ml_results.get('sell_predictions'):
                            for _, pred in ml_results['sell_predictions']:
                                all_confidences.append(pred['confidence_pct'])
                        
                        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
                        
                        # Determine confidence level
                        if avg_confidence >= 75:
                            conf_level = 'Very High'
                        elif avg_confidence >= 65:
                            conf_level = 'High'
                        elif avg_confidence >= 55:
                            conf_level = 'Moderate'
                        elif avg_confidence >= 45:
                            conf_level = 'Low'
                        else:
                            conf_level = 'Very Low'
                        
                        conf_emoji = "🔥" if avg_confidence >= 70 else "✅" if avg_confidence >= 60 else "⚠️" if avg_confidence >= 50 else "❌"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                f"{conf_emoji} Avg ML Confidence", 
                                f"{avg_confidence:.1f}%", 
                                conf_level
                            )
                        with col2:
                            timeframe = st.session_state['indicator_chart_data'].get('timeframe', 'Daily')
                            target = "5%" if timeframe == 'Daily' else "8%"
                            st.metric("🎯 Target", target, timeframe)
                        with col3:
                            model_accuracy = first_pred.get('model_accuracy', 91.5)
                            st.metric("📊 Model Accuracy", f"{model_accuracy}%", "Ichimoku ML")
                        
                        st.markdown("---")
                        
                        # Performance Metrics Section
                        if first_pred.get('performance_metrics'):
                            metrics = first_pred['performance_metrics']
                            
                            st.markdown("### 📈 Strategy Performance Metrics")
                            mcol1, mcol2, mcol3 = st.columns(3)
                            
                            with mcol1:
                                pf = metrics['profit_factor']
                                st.metric(
                                    f"{pf['emoji']} Profit Factor", 
                                    pf['display'],
                                    pf['rating'],
                                    help=pf['help']
                                )
                            with mcol2:
                                exp = metrics['expectancy']
                                st.metric(
                                    f"{exp['emoji']} Expectancy", 
                                    exp['display'],
                                    exp['rating'],
                                    help=exp['help']
                                )
                            with mcol3:
                                ar = metrics['annual_return']
                                st.metric(
                                    f"{ar['emoji']} Annual Return", 
                                    ar['display'],
                                    ar['rating'],
                                    help=ar['help']
                                )
                            
                            # Show data source note
                            if metrics.get('data_source') == 'estimated':
                                st.caption(f"📊 Based on {metrics['total_trades']:,} training samples | Win Rate: {metrics['win_rate']}% | *Estimated metrics (using Ichimoku ML)*")
                            else:
                                st.caption(f"📊 Based on {metrics['total_trades']:,} historical trades | Win Rate: {metrics['win_rate']}% | *Using Ichimoku ML model*")
            
            # Display signals table
            if 'enhanced_tr_signals' in st.session_state and st.session_state['enhanced_tr_signals']:
                st.markdown("### 📋 Recent Signals (Last 20)")
                
                # Get last 20 signals
                signals = st.session_state['enhanced_tr_signals'][-20:]
                
                if signals:
                    # Create DataFrame for display - only Date, Signal, Price
                    signal_df = pd.DataFrame(signals)
                    signal_df = signal_df[['date', 'signal', 'price']]
                    signal_df.columns = ['Date', 'Signal', 'Price']
                    
                    # Format price column
                    signal_df['Price'] = signal_df['Price'].apply(lambda x: f"${x:.2f}")
                    
                    # Color code signals
                    def highlight_signal(row):
                        if row['Signal'] == 'BUY':
                            return ['background-color: rgba(0, 200, 83, 0.3)'] * len(row)
                        else:
                            return ['background-color: rgba(255, 23, 68, 0.3)'] * len(row)
                    
                    styled_df = signal_df.style.apply(highlight_signal, axis=1)
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    # Summary
                    all_signals = st.session_state['enhanced_tr_signals']
                    buy_count = len([s for s in all_signals if s['signal'] == 'BUY'])
                    sell_count = len([s for s in all_signals if s['signal'] == 'SELL'])
                    st.caption(f"Total signals in period: {len(all_signals)} (🟢 {buy_count} BUY, 🔴 {sell_count} SELL) | Showing last {len(signals)}")
                else:
                    st.info("No signals found in this period. This strategy is conservative and signals are rare.")
            else:
                st.info("ℹ️ No Enhanced TR signals found. This is a conservative strategy - signals are rare but high quality.")
else:
    st.info("👆 Click 'Update' button to generate the indicator chart")

# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
