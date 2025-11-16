"""
TR Chart Generator v4.0 - Main Menu
Integrated system with TR Charts, Standard Charts, and Seasonality Analysis
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

# Add paths for imports
sys.path.insert(0, './src')  # src folder
sys.path.insert(0, '.')       # Current directory

from standard_charts import StandardCharts
from seasonality import SeasonalityAnalysis
from stock_cache import StockDataCache, get_cache

# Import TR modules
try:
    from tr_enhanced import analyze_stock_complete_tr as _analyze_stock_complete_tr_original
    from stock_data_formatter import get_stock_data_formatted
    from tr_indicator import analyze_tr_indicator
    from pattern_detection import detect_patterns_for_chart
    USE_REAL_DATA = True
    print("✅ TR Enhanced module loaded")
    print("✅ Pattern Detection module loaded")
except ImportError as e:
    USE_REAL_DATA = False
    print(f"⚠️  TR Enhanced module not found: {e}")
    print("⚠️  Check that src/ folder is in the same directory")


# ============================================================================
# SPLIT DETECTION AND ADJUSTMENT FUNCTIONS (from v3.6)
# ============================================================================

def detect_stock_splits(df, threshold=0.25):
    """
    Detect potential stock splits by finding large price drops
    
    Args:
        df: DataFrame with price columns
        threshold: % drop to consider as potential split (default 25%)
    
    Returns:
        list: Dates where splits might have occurred
    """
    splits_detected = []
    
    if len(df) < 2:
        return splits_detected
    
    # Find the price column
    price_col = None
    for col in ['Close', 'close', 'adjClose', 'adj_close']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        return splits_detected
    
    for i in range(1, len(df)):
        prev_close = df.iloc[i-1][price_col]
        curr_close = df.iloc[i][price_col]
        
        if prev_close == 0 or pd.isna(prev_close) or pd.isna(curr_close):
            continue
        
        # Calculate percentage change
        pct_change = (curr_close - prev_close) / prev_close
        
        # Large drops might indicate splits
        if pct_change < -threshold:
            splits_detected.append({
                'date': df.index[i] if hasattr(df.index[i], 'strftime') else df.index[i],
                'index': i,
                'ratio': prev_close / curr_close,
                'pct_change': pct_change * 100,
                'prev_price': prev_close,
                'curr_price': curr_close
            })
    
    return splits_detected


def adjust_for_splits(df, splits, price_col='Close'):
    """
    Manually adjust historical prices for splits
    
    Args:
        df: DataFrame with OHLCV data
        splits: List of detected splits
        price_col: Name of the main price column
    
    Returns:
        DataFrame: Split-adjusted data
    """
    if not splits:
        return df
    
    df = df.copy()
    
    print(f"\n🔧 Adjusting data for {len(splits)} split(s)...")
    
    # Process splits from oldest to newest
    for split in sorted(splits, key=lambda x: x['index']):
        split_idx = split['index']
        split_ratio = split['ratio']
        split_date = split['date']
        
        print(f"   • Adjusting pre-{split_date} data by factor of {split_ratio:.2f}")
        
        # Adjust all price columns BEFORE the split
        price_columns = []
        for col in ['Open', 'High', 'Low', 'Close', 'open', 'high', 'low', 'close']:
            if col in df.columns:
                price_columns.append(col)
        
        for col in price_columns:
            df.loc[:split_idx-1, col] = df.loc[:split_idx-1, col] / split_ratio
        
        # Adjust volume if exists
        for vol_col in ['Volume', 'volume']:
            if vol_col in df.columns:
                df.loc[:split_idx-1, vol_col] = df.loc[:split_idx-1, vol_col] * split_ratio
    
    print(f"   ✅ Split adjustment complete!\n")
    
    return df


def check_and_adjust_splits(df, ticker):
    """
    Check for splits and automatically adjust the data
    
    Args:
        df: DataFrame with stock data
        ticker: Stock symbol
    
    Returns:
        DataFrame: Split-adjusted data
    """
    splits = detect_stock_splits(df, threshold=0.20)
    
    if splits:
        print(f"\n⚠️  CRITICAL: Detected {len(splits)} unadjusted split(s) in {ticker}!")
        for split in splits:
            ratio = split['ratio']
            date = split['date']
            print(f"   • {date}: ~{ratio:.1f}-for-1 split")
            print(f"     ${split['prev_price']:.2f} → ${split['curr_price']:.2f} ({split['pct_change']:.1f}% drop)")
        
        print(f"\n   ⚠️  Tiingo data is NOT properly adjusted!")
        print(f"   🔧 Automatically adjusting historical prices...")
        
        # Find price column for adjustment
        price_col = None
        for col in ['Close', 'close', 'adjClose', 'adj_close']:
            if col in df.columns:
                price_col = col
                break
        
        # Adjust the data
        df = adjust_for_splits(df, splits, price_col)
        
        # Verify
        verification_splits = detect_stock_splits(df, threshold=0.20)
        if len(verification_splits) == 0:
            print(f"   ✅ Verification: All splits corrected! Data is now continuous.\n")
        else:
            print(f"   ⚠️  Warning: {len(verification_splits)} potential issues remain\n")
    else:
        print(f"   ✅ No splits detected - data looks clean!\n")
    
    return df


def analyze_stock_complete_tr_with_split_adjustment(ticker, timeframe='daily', duration_days=180):
    """
    Complete TR analysis with split adjustment BEFORE calculations
    This is the v3.6 approach that works correctly
    """
    print(f"\n{'='*80}")
    print(f"🔍 COMPLETE TR ANALYSIS: {ticker} (with split adjustment)")
    print(f"{'='*80}\n")
    
    # Fetch raw data
    print(f"📡 Fetching {ticker} data...")
    df = get_stock_data_formatted(ticker, timeframe=timeframe, days=duration_days, save=False)
    
    if df is None or df.empty:
        print(f"❌ No data for {ticker}")
        return None
    
    print(f"   ✅ Fetched {len(df)} rows from API")
    
    # CRITICAL: Adjust for splits BEFORE TR calculations
    print(f"\n🔍 Checking for stock splits...")
    df = check_and_adjust_splits(df, ticker)
    
    # Now run TR analysis on split-adjusted data
    print(f"\n📊 Calculating TR indicators on adjusted data...")
    df = analyze_tr_indicator(df)
    
    # Add enhancements (creates Buy_Point and Stop_Loss columns)
    print(f"✨ Adding TR enhancements...")
    
    try:
        # Import only the functions that exist in tr_enhanced.py
        from tr_enhanced import (
            add_peaks_and_valleys,
            calculate_buy_points,
            calculate_stop_loss
        )
        
        print(f"   ✅ Enhancement functions imported")
        
        # Add peaks and calculate buy points (creates Buy_Point column)
        print(f"   → Adding peaks and valleys...")
        df = add_peaks_and_valleys(df)
        
        print(f"   → Calculating buy points...")
        df = calculate_buy_points(df)
        
        print(f"   → Calculating stop losses...")
        df = calculate_stop_loss(df)
        
        # Verify columns were created
        if 'Buy_Point' in df.columns and 'Stop_Loss' in df.columns:
            print(f"   ✅ Buy_Point and Stop_Loss columns created successfully!")
        else:
            print(f"   ⚠️  WARNING: Missing columns")
            if 'Buy_Point' not in df.columns:
                print(f"      ❌ Buy_Point missing")
            if 'Stop_Loss' not in df.columns:
                print(f"      ❌ Stop_Loss missing")
        
        print(f"   ✅ Enhancements complete")
        
    except ImportError as e:
        print(f"   ❌ ERROR: Could not import enhancement functions!")
        print(f"   ❌ Error: {e}")
        print(f"   ⚠️  Buy_Point and Stop_Loss will NOT be available")
    except Exception as e:
        print(f"   ❌ ERROR during enhancements: {e}")
        import traceback
        traceback.print_exc()
    
    # The analyze_tr_indicator should add TR_Status and other columns
    print(f"✅ TR analysis complete!\n")
    
    # Add display EMAs (50/200 for daily, 10/30 for weekly) for chart visualization
    # These are separate from TR indicator EMAs (3, 9, 20, 34)
    print(f"📊 Adding display EMAs for chart...")
    
    # Find the price column (could be adjClose, adj_close, close, Close)
    price_col = None
    for col in ['adjClose', 'adj_close', 'close', 'Close']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        print(f"   ⚠️  Could not find price column for EMAs")
        return df
    
    if timeframe.lower() == 'daily':
        df['ema_50'] = df[price_col].ewm(span=50, adjust=False).mean()
        df['ema_200'] = df[price_col].ewm(span=200, adjust=False).mean()
        print(f"   ✅ Added 50-day and 200-day EMAs")
    else:  # weekly or monthly
        df['ema_10'] = df[price_col].ewm(span=10, adjust=False).mean()
        df['ema_30'] = df[price_col].ewm(span=30, adjust=False).mean()
        print(f"   ✅ Added 10-week and 30-week EMAs")
    
    return df


# ============================================================================
# TR CHART GENERATION FUNCTIONS
# ============================================================================

def draw_tr_chart_v2(ticker='AAPL', timeframe='Daily', duration='1 Year', show_chart=True, show_patterns=True):
    """
    Draw TR Chart with separate timeframe and duration selection
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'Daily' or 'Weekly'
        duration (str): '3M', '6M', '1Y', '3Y', '5Y'
        show_chart (bool): Display chart window
        show_patterns (bool): Show pattern detection on chart
    """
    duration_map = {
        '3M': 90, '3 Months': 90,
        '6M': 180, '6 Months': 180,
        '1Y': 365, '1 Year': 365,
        '3Y': 1095, '3 Years': 1095,
        '5Y': 1825, '5 Years': 1825
    }
    
    duration_days = duration_map.get(duration, 365)
    
    # Run TR analysis WITH SPLIT ADJUSTMENT (v3.6 approach)
    df = analyze_stock_complete_tr_with_split_adjustment(
        ticker, 
        timeframe=timeframe.lower(),
        duration_days=duration_days
    )
    
    if df is None or len(df) == 0:
        print(f"❌ No data returned for {ticker}")
        return None
    
    # Convert Date column to datetime index for proper x-axis display
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        print(f"✅ Date column converted to datetime index")
    
    print(f"✅ TR analysis complete! {len(df)} data points")
    print(f"📊 Available columns: {list(df.columns)}")
    
    # Find the price column (could be adjClose, adj_close, close, etc.)
    price_col = None
    for col in ['adjClose', 'adj_close', 'close', 'Close']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        print(f"❌ No price column found in DataFrame!")
        print(f"   Available columns: {list(df.columns)}")
        return None
    
    print(f"✅ Using price column: {price_col}")
    
    # Generate chart
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Define stage colors
    stage_colors = {
        'Buy': '#32CD32',          # Lime Green - Stage 2 Uptrend
        'Strong Buy': '#008000',   # Dark Green - Stage 3 Uptrend
        'Sell': '#FFFF00',         # Yellow - Stage 2 Downtrend
        'Strong Sell': '#FF8C00'   # Dark Orange - Stage 3 Downtrend
    }
    
    # Draw colored background for TR stages using TR_Status column
    if 'TR_Status' in df.columns:
        print("✅ TR_Status column found - drawing colored backgrounds")
        
        # Debug: show unique statuses
        unique_statuses = df['TR_Status'].unique()
        print(f"   TR Status values: {[s for s in unique_statuses if pd.notna(s)]}")
        
        current_status = None
        band_start = None
        
        for i in range(len(df)):
            status = df.iloc[i]['TR_Status']
            
            # Skip nan/None values
            if pd.isna(status):
                if current_status is not None:
                    band_end = i - 1
                    if band_end >= band_start:
                        x_start = df.index[band_start]
                        x_end = df.index[band_end]
                        ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
                    current_status = None
                    band_start = None
                continue
            
            if status in stage_colors:
                if current_status != status:
                    # End previous band if exists
                    if current_status is not None:
                        band_end = i - 1
                        if band_end >= band_start:
                            x_start = df.index[band_start]
                            x_end = df.index[band_end]
                            ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
                    
                    # Start new band
                    current_status = status
                    band_start = i
            else:
                # Status is not in stage_colors (Neutral, etc.)
                if current_status is not None:
                    band_end = i - 1
                    if band_end >= band_start:
                        x_start = df.index[band_start]
                        x_end = df.index[band_end]
                        ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
                    current_status = None
                    band_start = None
        
        # Draw final band if we're still in one
        if current_status is not None and band_start is not None:
            x_start = df.index[band_start]
            x_end = df.index[-1]
            ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
    else:
        print("⚠️  Note: TR_Status not found, skipping colored background")
    
    # Plot price
    ax.plot(df.index, df[price_col], color='black', linewidth=2, label='Price', zorder=3)
    
    # Plot EMAs - Different for Daily vs Weekly/Monthly (v3.6 logic)
    # EMAs are DOTTED lines, not solid
    if timeframe.lower() == 'daily':
        # Daily charts: 50 and 200 day EMAs
        if 'ema_50' in df.columns and df['ema_50'].notna().any():
            ax.plot(df.index, df['ema_50'], color='blue', linewidth=1.5, 
                   linestyle=':', label='50-Day EMA', alpha=0.8, zorder=4)
            print(f"   ✅ Drew 50-Day EMA (blue dotted line)")
        
        if 'ema_200' in df.columns and df['ema_200'].notna().any():
            ax.plot(df.index, df['ema_200'], color='red', linewidth=1.5, 
                   linestyle=':', label='200-Day EMA', alpha=0.8, zorder=4)
            print(f"   ✅ Drew 200-Day EMA (red dotted line)")
    else:
        # Weekly/Monthly charts: 10 and 30 period EMAs
        if 'ema_10' in df.columns and df['ema_10'].notna().any():
            ax.plot(df.index, df['ema_10'], color='blue', linewidth=1.5, 
                   linestyle=':', label='10-Week EMA', alpha=0.8, zorder=4)
            print(f"   ✅ Drew 10-Week EMA (blue dotted line)")
        
        if 'ema_30' in df.columns and df['ema_30'].notna().any():
            ax.plot(df.index, df['ema_30'], color='red', linewidth=1.5, 
                   linestyle=':', label='30-Week EMA', alpha=0.8, zorder=4)
            print(f"   ✅ Drew 30-Week EMA (red dotted line)")
    
    # ===================================================================
    # STAGE 1 MARKERS (Green triangles for Neutral Buy, Red diamonds for Neutral Sell)
    # ===================================================================
    if 'TR_Status' in df.columns:
        print("   Drawing Stage 1 markers...")
        prev_status = None
        for i in range(len(df)):
            status = df.iloc[i]['TR_Status']
            date = df.index[i]
            price = df.iloc[i][price_col]
            
            if i > 0:
                prev_status = df.iloc[i-1]['TR_Status']
            
            # Green triangle for Neutral Buy (Stage 1 Uptrend)
            if status == 'Neutral Buy' and prev_status != 'Neutral Buy':
                ax.scatter(date, price, marker='^', color='lightgreen',
                          s=60, edgecolors='darkgreen', linewidths=1.2, zorder=10,
                          label='Stage 1 Uptrend' if i == 0 else '')
            
            # Red diamond for Neutral Sell (Stage 1 Downtrend)  
            elif status == 'Neutral Sell' and prev_status != 'Neutral Sell':
                ax.scatter(date, price, marker='D', color='red',
                          s=40, edgecolors='darkred', linewidths=1.2, zorder=10,
                          label='Stage 1 Downtrend' if i == 0 else '')
    
    # ===================================================================
    # BUY POINTS AND STOP LOSSES (Black and Red dashed lines)
    # ===================================================================
    if 'Buy_Point' in df.columns and 'Stop_Loss' in df.columns:
        print("   Drawing buy points and stop losses...")
        
        # Get rows where Buy_Point changes (new peaks detected)
        df['Buy_Point_Changed'] = df['Buy_Point'].ne(df['Buy_Point'].shift())
        peak_changes = df[df['Buy_Point_Changed'] & df['Buy_Point'].notna()]
        
        if len(peak_changes) > 0:
            print(f"   Found {len(peak_changes)} buy point levels")
            
            from datetime import timedelta
            
            for idx in peak_changes.index:
                try:
                    start_date = idx
                    buy_point = df.loc[idx, 'Buy_Point']
                    stop_loss = df.loc[idx, 'Stop_Loss']
                    
                    if pd.isna(buy_point) or pd.isna(stop_loss):
                        continue
                    
                    # Find where this buy point ends
                    next_changes = peak_changes[peak_changes.index > idx]
                    if len(next_changes) > 0:
                        end_idx = next_changes.index[0]
                    else:
                        end_idx = df.index[-1]
                    
                    end_date = end_idx
                    
                    # Draw buy point line (black dashed - 5 dashes)
                    ax.plot([start_date, end_date], [buy_point, buy_point],
                           color='black', linewidth=1.5, 
                           dashes=[10, 8],  # Simple: 10pt dash, 8pt gap
                           zorder=6, alpha=0.9,
                           label='Buy Point' if idx == peak_changes.index[0] else '')
                    
                    # Draw stop loss line (red dashed - shorter, first 33%)
                    try:
                        start_idx_pos = df.index.get_loc(start_date)
                        end_idx_pos = df.index.get_loc(end_date)
                        
                        # Calculate stop end as 33% of distance
                        stop_distance = max(1, int((end_idx_pos - start_idx_pos) * 0.33))
                        stop_end_idx = min(start_idx_pos + stop_distance, len(df.index) - 1)
                        stop_end_date = df.index[stop_end_idx]
                        
                        # Draw simple dashed line
                        ax.plot([start_date, stop_end_date], [stop_loss, stop_loss],
                               color='red', linewidth=1.5,
                               dashes=[10, 8],  # Same pattern as buy point
                               zorder=6, alpha=0.9,
                               label='Stop Loss (8% rule)' if idx == peak_changes.index[0] else '')
                    except Exception as e:
                        # Silent fail
                        pass
                
                except Exception as e:
                    print(f"   ⚠️  Error drawing level at index {idx}: {e}")
                    continue
            
            print(f"   ✅ Drew buy points and stop losses")
        else:
            print("   ⚠️  No buy point changes detected")
    else:
        print("   ⚠️  Buy_Point/Stop_Loss columns not found")
    
    # Labels and formatting
    timeframe_label = timeframe.title()
    ax.set_title(f'{ticker} - {timeframe_label} {duration} TR Chart', fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis dates nicely
    import matplotlib.dates as mdates
    from matplotlib.ticker import AutoMinorLocator
    
    if timeframe.lower() == 'daily':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())  # Minor ticks every week
    elif timeframe.lower() == 'weekly':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())  # Minor ticks every month
    else:  # monthly
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))  # Minor ticks every 3 months
    
    # Add minor ticks to Y-axis (price)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    
    # Enable minor grid lines (lighter than major grid)
    ax.grid(which='major', alpha=0.3, linewidth=1.0)
    ax.grid(which='minor', alpha=0.15, linewidth=0.5, linestyle=':')
    
    # Rotate date labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # ===================================================================
    # PATTERN DETECTION AND VISUALIZATION
    # ===================================================================
    if show_patterns:
        try:
            print("🔍 Detecting chart patterns...")
            patterns = detect_patterns_for_chart(df, price_col)
            
            if len(patterns) > 0:
                print(f"📊 Drawing {len(patterns)} patterns on chart...")
                
                # Draw each pattern with outline instead of box
                for pattern in patterns:
                    start_date = pattern['start_date']
                    end_date = pattern['end_date']
                    start_idx = pattern['start_idx']
                    end_idx = pattern['end_idx']
                    pattern_type = pattern['type']
                    confidence = pattern['confidence']
                    direction = pattern['direction']
                    
                    # Choose color based on direction
                    if direction == 'bullish':
                        outline_color = 'green'
                        text_color = 'darkgreen'
                    elif direction == 'bearish':
                        outline_color = 'red'
                        text_color = 'darkred'
                    else:
                        outline_color = 'gray'
                        text_color = 'black'
                    
                    # Get price data within pattern range
                    pattern_prices = df[price_col].iloc[start_idx:end_idx+1]
                    pattern_dates = df.index[start_idx:end_idx+1]
                    
                    # Calculate rectangle boundaries
                    pattern_high = max(pattern_prices)
                    pattern_low = min(pattern_prices)
                    
                    # Add 2% padding above and below for visibility
                    padding = (pattern_high - pattern_low) * 0.02
                    rect_top = pattern_high + padding
                    rect_bottom = pattern_low - padding
                    
                    # Draw dotted rectangle frame around pattern
                    # Top horizontal line
                    ax.plot([start_date, end_date], [rect_top, rect_top],
                           color=outline_color, linestyle=':', linewidth=2,
                           alpha=0.8, zorder=8)
                    
                    # Bottom horizontal line
                    ax.plot([start_date, end_date], [rect_bottom, rect_bottom],
                           color=outline_color, linestyle=':', linewidth=2,
                           alpha=0.8, zorder=8)
                    
                    # Left vertical line
                    ax.plot([start_date, start_date], [rect_bottom, rect_top],
                           color=outline_color, linestyle=':', linewidth=2,
                           alpha=0.8, zorder=8)
                    
                    # Right vertical line
                    ax.plot([end_date, end_date], [rect_bottom, rect_top],
                           color=outline_color, linestyle=':', linewidth=2,
                           alpha=0.8, zorder=8)
                    
                    # ===================================================================
                    # SPECIAL: Draw Cup Shape for Cup & Handle Patterns
                    # ===================================================================
                    if pattern_type == 'Cup & Handle' and 'cup_left_idx' in pattern:
                        # Get cup structure indices
                        cup_left_idx = pattern['cup_left_idx']
                        cup_bottom_idx = pattern['cup_bottom_idx']
                        cup_right_idx = pattern['cup_right_idx']
                        handle_start_idx = pattern['handle_start_idx']
                        
                        # Get cup prices
                        cup_left_price = pattern['cup_left_price']
                        cup_bottom_price = pattern['cup_bottom_price']
                        cup_right_price = pattern['cup_right_price']
                        
                        # Get dates
                        cup_left_date = df.index[cup_left_idx]
                        cup_bottom_date = df.index[cup_bottom_idx]
                        cup_right_date = df.index[cup_right_idx]
                        handle_start_date = df.index[handle_start_idx]
                        
                        # Draw the cup outline in THICK GREEN
                        # Left rim to bottom
                        left_cup_segment = df[price_col].iloc[cup_left_idx:cup_bottom_idx+1]
                        left_cup_dates = df.index[cup_left_idx:cup_bottom_idx+1]
                        ax.plot(left_cup_dates, left_cup_segment,
                               color='lime', linewidth=3, linestyle='-',
                               alpha=0.9, zorder=10, label='Cup' if start_idx == pattern['start_idx'] else '')
                        
                        # Bottom to right rim
                        right_cup_segment = df[price_col].iloc[cup_bottom_idx:cup_right_idx+1]
                        right_cup_dates = df.index[cup_bottom_idx:cup_right_idx+1]
                        ax.plot(right_cup_dates, right_cup_segment,
                               color='lime', linewidth=3, linestyle='-',
                               alpha=0.9, zorder=10)
                        
                        # Draw the handle in ORANGE
                        handle_segment = df[price_col].iloc[cup_right_idx:handle_start_idx+1]
                        handle_dates = df.index[cup_right_idx:handle_start_idx+1]
                        ax.plot(handle_dates, handle_segment,
                               color='orange', linewidth=3, linestyle='-',
                               alpha=0.9, zorder=10, label='Handle' if start_idx == pattern['start_idx'] else '')
                        
                        # Add markers at key points
                        # Left rim (cup start)
                        ax.plot(cup_left_date, cup_left_price, 'o',
                               color='lime', markersize=8, markeredgecolor='darkgreen',
                               markeredgewidth=2, zorder=12)
                        ax.text(cup_left_date, cup_left_price * 1.03, 'Cup Start',
                               fontsize=8, color='darkgreen', fontweight='bold',
                               ha='center', va='bottom',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                       edgecolor='lime', linewidth=1.5, alpha=0.9),
                               zorder=15)
                        
                        # Bottom (lowest point)
                        ax.plot(cup_bottom_date, cup_bottom_price, 'o',
                               color='lime', markersize=10, markeredgecolor='darkgreen',
                               markeredgewidth=2, zorder=12)
                        ax.text(cup_bottom_date, cup_bottom_price * 0.97, 'Cup Bottom',
                               fontsize=8, color='darkgreen', fontweight='bold',
                               ha='center', va='top',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                       edgecolor='lime', linewidth=1.5, alpha=0.9),
                               zorder=15)
                        
                        # Right rim (cup recovery)
                        ax.plot(cup_right_date, cup_right_price, 'o',
                               color='lime', markersize=8, markeredgecolor='darkgreen',
                               markeredgewidth=2, zorder=12)
                        ax.text(cup_right_date, cup_right_price * 1.03, 'Cup End',
                               fontsize=8, color='darkgreen', fontweight='bold',
                               ha='center', va='bottom',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                       edgecolor='lime', linewidth=1.5, alpha=0.9),
                               zorder=15)
                        
                        # Handle start marker
                        ax.plot(handle_start_date, df[price_col].iloc[handle_start_idx], 's',
                               color='orange', markersize=8, markeredgecolor='darkorange',
                               markeredgewidth=2, zorder=12)
                    
                    # ===================================================================
                    # END Cup Visualization
                    # ===================================================================
                    
                    # Add pattern label near the pattern (not at top)
                    # Find highest/lowest point in pattern for label placement
                    if direction == 'bearish':
                        # Place label above pattern
                        label_y = max(pattern_prices) * 1.02
                        va_align = 'bottom'
                    else:
                        # Place label below pattern  
                        label_y = min(pattern_prices) * 0.98
                        va_align = 'top'
                    
                    # Calculate middle date for label placement
                    if hasattr(start_date, 'to_pydatetime') and hasattr(end_date, 'to_pydatetime'):
                        start_dt = start_date.to_pydatetime() if hasattr(start_date, 'to_pydatetime') else start_date
                        end_dt = end_date.to_pydatetime() if hasattr(end_date, 'to_pydatetime') else end_date
                        mid_date = start_dt + (end_dt - start_dt) / 2
                    else:
                        mid_date = start_date
                    
                    # Add text label
                    label_text = f"{pattern_type} ({confidence}%)"
                    ax.text(mid_date, label_y, label_text,
                           fontsize=9, fontweight='bold',
                           ha='center', va=va_align,
                           color=text_color,
                           bbox=dict(boxstyle='round,pad=0.4', 
                                    facecolor='white', 
                                    edgecolor=outline_color,
                                    linewidth=1.5,
                                    alpha=0.9),
                           zorder=15)
                    
                    # Add target price line if available
                    if 'target_price' in pattern:
                        target = pattern['target_price']
                        
                        # Draw target line only across the pattern width
                        ax.plot([start_date, end_date], [target, target],
                               color=outline_color, linestyle='--', 
                               linewidth=1.5, alpha=0.6, zorder=6)
                        
                        # Add target label near the end of pattern
                        ax.text(end_date, target, f' ${target:.2f}',
                               fontsize=8, color=text_color, fontweight='bold',
                               va='center', ha='left',
                               bbox=dict(boxstyle='round,pad=0.3',
                                       facecolor='white',
                                       edgecolor=outline_color,
                                       linewidth=1,
                                       alpha=0.85),
                               zorder=15)
                
                print(f"✅ Drew {len(patterns)} patterns on chart")
            else:
                print("   No patterns detected")
        
        except Exception as e:
            print(f"⚠️  Pattern detection error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   Pattern detection: OFF")
    
    # Save chart
    filename = f"{ticker}_{timeframe_label}_{duration.replace(' ', '_')}_TR_Chart.png"
    filepath = os.path.join('charts', filename)
    os.makedirs('charts', exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved: {filepath}")
    
    if show_chart:
        plt.show()
    else:
        plt.close()
    
    return filepath


# ============================================================================
# MAIN MENU CLASS
# ============================================================================

class ChartGeneratorMenu:
    """Main menu system for TR Chart Generator v4.0"""
    
    def __init__(self):
        """Initialize all modules"""
        print("🚀 Initializing TR Chart Generator v4.0...")
        
        self.standard_charts = StandardCharts(output_dir='charts')
        self.seasonality = SeasonalityAnalysis(output_dir='charts')
        self.cache = get_cache()  # Use the function to get cache instance
        
        print("✅ All modules loaded!\n")
    
    def display_main_menu(self):
        """Display the main menu"""
        print(f"\n{'='*70}")
        print(" " * 15 + "TR CHART GENERATOR v4.0")
        print(" " * 7 + "AI-Powered Stock Analysis with Pattern Detection")
        print(f"{'='*70}")
        print()
        print("📊 CHART GENERATION:")
        print("  1. TR Indicator Chart (Stages + Signals + Patterns)")
        print("  2. Standard Charts (Line/Candlestick/OHLC)")
        print("  3. Seasonality Analysis (Monthly Patterns)")
        print("  4. Generate All (Complete Package)")
        print()
        print("🔧 UTILITIES:")
        print("  5. View Cache Status")
        print("  6. Clear Cache")
        print()
        print("  0. Exit")
        print(f"{'='*70}")
    
    def handle_tr_chart(self):
        """Handle TR indicator chart generation"""
        print(f"\n{'='*70}")
        print("TR INDICATOR CHART GENERATOR")
        print(f"{'='*70}")
        
        # Get symbol
        ticker = input("\nEnter stock symbol (e.g., AAPL): ").strip().upper()
        if not ticker:
            print("❌ Invalid symbol")
            return
        
        # Get timeframe
        print("\nSelect timeframe:")
        print("1. Daily   (50/200 Day EMAs)")
        print("2. Weekly  (10/30 Week EMAs)")
        timeframe_choice = input("Enter choice: ").strip()
        
        if timeframe_choice == '1':
            timeframe = 'daily'
        elif timeframe_choice == '2':
            timeframe = 'weekly'
        else:
            print("❌ Invalid choice")
            return
        
        # Get duration
        print("\nSelect duration:")
        print("1. 3 Months")
        print("2. 6 Months")
        print("3. 1 Year")
        print("4. 3 Years")
        print("5. 5 Years")
        duration_choice = input("Enter choice: ").strip()
        
        duration_map = {
            '1': ('3M', 90),
            '2': ('6M', 180),
            '3': ('1Y', 365),
            '4': ('3Y', 1095),
            '5': ('5Y', 1825)
        }
        
        if duration_choice not in duration_map:
            print("❌ Invalid choice")
            return
        
        duration_label, duration_days = duration_map[duration_choice]
        
        # Ask about pattern detection
        print("\nPattern Detection:")
        print("1. Show patterns on chart (Head & Shoulders, Triangles, etc.)")
        print("2. TR Chart only (no patterns)")
        pattern_choice = input("Enter choice (default=1): ").strip() or '1'
        
        show_patterns = (pattern_choice == '1')
        
        # Generate chart
        print(f"\n⏳ Generating TR chart for {ticker}...")
        print(f"   Timeframe: {timeframe.title()}")
        print(f"   Duration: {duration_label}")
        print(f"   Patterns: {'ON' if show_patterns else 'OFF'}")
        
        try:
            chart_path = draw_tr_chart_v2(
                ticker=ticker,
                timeframe=timeframe,
                duration=duration_label,
                show_chart=True,
                show_patterns=show_patterns
            )
            
            print(f"\n✅ Chart generated successfully!")
            print(f"📁 Saved to: {chart_path}")
            
        except Exception as e:
            print(f"\n❌ Error generating chart: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def handle_standard_charts(self):
        """Handle standard charts generation"""
        print(f"\n{'='*70}")
        print("STANDARD CHARTS GENERATOR")
        print(f"{'='*70}")
        
        # Get symbol
        ticker = input("\nEnter stock symbol (e.g., AAPL): ").strip().upper()
        if not ticker:
            print("❌ Invalid symbol")
            return
        
        # Get chart type
        print("\nSelect chart type:")
        print("1. Line Chart")
        print("2. Candlestick Chart")
        print("3. OHLC Chart")
        print("4. All Charts")
        chart_choice = input("Enter choice: ").strip()
        
        if chart_choice not in ['1', '2', '3', '4']:
            print("❌ Invalid choice")
            return
        
        # Get interval
        print("\nSelect interval:")
        print("1. Daily (D)")
        print("2. Weekly (W)")
        print("3. Monthly (M)")
        interval_choice = input("Enter choice (default: Daily): ").strip() or '1'
        
        interval_map = {'1': 'D', '2': 'W', '3': 'M'}
        interval = interval_map.get(interval_choice, 'D')
        
        # Generate charts
        print(f"\n⏳ Generating chart(s) for {ticker}...")
        
        try:
            if chart_choice == '1':
                self.standard_charts.generate_line_chart(ticker, interval)
            elif chart_choice == '2':
                self.standard_charts.generate_candlestick_chart(ticker, interval)
            elif chart_choice == '3':
                self.standard_charts.generate_ohlc_chart(ticker, interval)
            elif chart_choice == '4':
                self.standard_charts.generate_all_charts(ticker, interval, open_browser=True)
            
            print(f"\n✅ Chart(s) generated and opened in browser!")
            print(f"📁 Saved to: charts/")
            
        except Exception as e:
            print(f"\n❌ Error generating charts: {str(e)}")
    
    def handle_seasonality(self):
        """Handle seasonality analysis"""
        print(f"\n{'='*70}")
        print("SEASONALITY ANALYSIS")
        print(f"{'='*70}")
        
        # Get symbol
        ticker = input("\nEnter stock symbol (e.g., AAPL): ").strip().upper()
        if not ticker:
            print("❌ Invalid symbol")
            return
        
        # Get periods
        print("\nSelect period(s) to analyze:")
        print("1. 1 Year")
        print("2. 3 Years")
        print("3. 5 Years")
        print("4. 10 Years")
        print("5. 15 Years")
        print("6. 20 Years")
        print("7. All Periods (1Y, 3Y, 5Y, 10Y, 15Y, 20Y)")
        period_choice = input("Enter choice: ").strip()
        
        period_map = {
            '1': [1],
            '2': [3],
            '3': [5],
            '4': [10],
            '5': [15],
            '6': [20],
            '7': [1, 3, 5, 10, 15, 20]
        }
        
        if period_choice not in period_map:
            print("❌ Invalid choice")
            return
        
        periods = period_map[period_choice]
        
        # Generate analysis
        print(f"\n⏳ Analyzing seasonality for {ticker}...")
        
        try:
            charts = self.seasonality.generate_complete_analysis(
                ticker, 
                periods=periods,
                open_charts=True
            )
            
            print(f"\n✅ Analysis complete! {len(charts)} charts generated.")
            print(f"📁 Saved to: charts/")
            
        except Exception as e:
            print(f"\n❌ Error during analysis: {str(e)}")
    
    def handle_generate_all(self):
        """Generate complete analysis package"""
        print(f"\n{'='*70}")
        print("GENERATE COMPLETE ANALYSIS PACKAGE")
        print(f"{'='*70}")
        
        # Get symbol
        ticker = input("\nEnter stock symbol (e.g., AAPL): ").strip().upper()
        if not ticker:
            print("❌ Invalid symbol")
            return
        
        print(f"\n🚀 Generating COMPLETE analysis package for {ticker}...")
        print("This will create:")
        print("  • 1 TR Indicator chart")
        print("  • 3 Standard charts (Line, Candlestick, OHLC)")
        print("  • 12 Seasonality charts (1Y, 3Y, 5Y, 10Y, 15Y, 20Y × 2 types)")
        print("  Total: 16 charts\n")
        
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
        
        start_time = time.time()
        charts_generated = 0
        
        try:
            # 1. TR Chart
            print(f"\n{'─'*70}")
            print("📊 Step 1/3: Generating TR Indicator Chart...")
            print(f"{'─'*70}")
            tr_chart = draw_tr_chart_v2(ticker, 'daily', '1Y', show_chart=False)
            charts_generated += 1
            print(f"✅ TR chart complete!")
            
            # 2. Standard Charts
            print(f"\n{'─'*70}")
            print("📈 Step 2/3: Generating Standard Charts...")
            print(f"{'─'*70}")
            standard_charts = self.standard_charts.generate_all_charts(
                ticker, interval='D', open_browser=False
            )
            charts_generated += len(standard_charts)
            print(f"✅ Standard charts complete!")
            
            # 3. Seasonality
            print(f"\n{'─'*70}")
            print("🌙 Step 3/3: Generating Seasonality Analysis...")
            print(f"{'─'*70}")
            season_charts = self.seasonality.generate_complete_analysis(
                ticker, periods=[1, 3, 5, 10, 15, 20], open_charts=False
            )
            charts_generated += len(season_charts)
            print(f"✅ Seasonality analysis complete!")
            
            elapsed = time.time() - start_time
            
            # Summary
            print(f"\n{'='*70}")
            print("🎉 COMPLETE PACKAGE GENERATED!")
            print(f"{'='*70}")
            print(f"✅ Charts created: {charts_generated}")
            print(f"⏱️  Time taken: {elapsed:.1f} seconds")
            print(f"📁 Location: charts/")
            print(f"{'='*70}")
            
        except Exception as e:
            print(f"\n❌ Error generating complete package: {str(e)}")
    
    def handle_cache_status(self):
        """Display cache status"""
        print(f"\n{'='*70}")
        print("CACHE STATUS")
        print(f"{'='*70}")
        
        # Use the cache's built-in method
        self.cache.print_cache_summary()
        
        print(f"{'='*70}")
    
    def handle_clear_cache(self):
        """Clear the cache"""
        print(f"\n{'='*70}")
        print("CLEAR CACHE")
        print(f"{'='*70}")
        
        # Get cache info first
        cache_info = self.cache.get_cache_info()
        
        if not cache_info:
            print("📭 Cache is already empty")
            return
        
        print(f"⚠️  This will delete cache for {len(cache_info)} file(s)")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm == 'y':
            self.cache.clear_cache()  # Clear all
            print("✅ Cache cleared!")
        else:
            print("❌ Cancelled")
    
    def run(self):
        """Main menu loop"""
        print("\n" + "="*70)
        print(" " * 20 + "Welcome to")
        print(" " * 10 + "TR CHART GENERATOR v4.0")
        print(" " * 8 + "AI-Powered Stock Analysis Platform")
        print("="*70)
        
        while True:
            try:
                self.display_main_menu()
                choice = input("Enter your choice: ").strip()
                
                if choice == '0':
                    print("\n👋 Thank you for using TR Chart Generator v4.0!")
                    print("📧 Contact: support@analyzestocks.net\n")
                    break
                
                elif choice == '1':
                    self.handle_tr_chart()
                
                elif choice == '2':
                    self.handle_standard_charts()
                
                elif choice == '3':
                    self.handle_seasonality()
                
                elif choice == '4':
                    self.handle_generate_all()
                
                elif choice == '5':
                    self.handle_cache_status()
                
                elif choice == '6':
                    self.handle_clear_cache()
                
                else:
                    print("\n❌ Invalid choice. Please try again.")
                
                # Pause before showing menu again
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    try:
        menu = ChartGeneratorMenu()
        menu.run()
    except Exception as e:
        print(f"\n❌ Failed to start: {str(e)}")
        print("Please check your .env file and dependencies.")


if __name__ == "__main__":
    main()
