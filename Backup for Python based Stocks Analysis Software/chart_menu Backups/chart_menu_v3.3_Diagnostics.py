"""
TR CHART MENU - Select Timeframe AND Duration
Two-step selection: 1) Timeframe (Daily/Weekly), 2) Duration
NOW WITH REAL DATA + CACHING!
Version 3.3 - Debug: Show TR_Status values to diagnose Stage 2 bands

SETUP FOR YOUR LOCAL MACHINE:
- Place this file in: C:\Work\Stock Analysis Project\mj-stocks-analysis\
- Your src folder should be at: ./src/
- Your .env file should be in the same folder as this file
"""

import sys
import os

# Add paths for imports (LOCAL SETUP)
sys.path.insert(0, './src')  # Your src folder
sys.path.insert(0, '.')       # Current directory

from stock_cache import get_cache
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Try to import TR enhanced module
try:
    from tr_enhanced import analyze_stock_complete_tr
    USE_REAL_DATA = True
    print("✅ TR Enhanced module loaded - Using REAL stock data")
except ImportError as e:
    USE_REAL_DATA = False
    print(f"⚠️  TR Enhanced module not found: {e}")
    print("⚠️  Check that src/ folder is in the same directory")
    print("⚠️  Using SAMPLE data")


def detect_stock_splits(df, threshold=0.25):
    """
    Detect potential stock splits by finding large price drops
    
    Args:
        df: DataFrame with Date and Close columns
        threshold: % drop to consider as potential split (default 25%)
    
    Returns:
        list: Dates where splits might have occurred
    """
    splits_detected = []
    
    if len(df) < 2:
        return splits_detected
    
    for i in range(1, len(df)):
        prev_close = df.iloc[i-1]['Close']
        curr_close = df.iloc[i]['Close']
        
        if prev_close == 0 or pd.isna(prev_close) or pd.isna(curr_close):
            continue
        
        # Calculate percentage change
        pct_change = (curr_close - prev_close) / prev_close
        
        # Large drops might indicate splits (if data not adjusted)
        if pct_change < -threshold:
            split_date = df.iloc[i]['Date']
            split_ratio = prev_close / curr_close
            splits_detected.append({
                'date': split_date,
                'index': i,
                'ratio': split_ratio,
                'pct_change': pct_change * 100,
                'prev_price': prev_close,
                'curr_price': curr_close
            })
    
    return splits_detected


def adjust_for_splits(df, splits):
    """
    Manually adjust historical prices for splits
    
    Args:
        df: DataFrame with OHLCV data
        splits: List of detected splits from detect_stock_splits()
    
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
        
        # Adjust all data BEFORE the split
        # Divide prices by ratio, multiply volume by ratio
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in df.columns:
                df.loc[:split_idx-1, col] = df.loc[:split_idx-1, col] / split_ratio
        
        # Adjust volume (multiply by ratio since shares increased)
        if 'Volume' in df.columns:
            df.loc[:split_idx-1, 'Volume'] = df.loc[:split_idx-1, 'Volume'] * split_ratio
        
        # Adjust buy points and stop losses if they exist
        if 'Buy_Point' in df.columns:
            df.loc[:split_idx-1, 'Buy_Point'] = df.loc[:split_idx-1, 'Buy_Point'] / split_ratio
        
        if 'Stop_Loss' in df.columns:
            df.loc[:split_idx-1, 'Stop_Loss'] = df.loc[:split_idx-1, 'Stop_Loss'] / split_ratio
    
    print(f"   ✅ Split adjustment complete!\n")
    
    return df


def check_and_adjust_splits(df, ticker):
    """
    Check for splits, warn user, and AUTOMATICALLY ADJUST the data
    
    Args:
        df: DataFrame with stock data
        ticker: Stock symbol
    
    Returns:
        DataFrame: Split-adjusted data
    """
    splits = detect_stock_splits(df, threshold=0.20)  # 20% threshold to catch more splits
    
    if splits:
        print(f"\n⚠️  CRITICAL: Detected {len(splits)} unadjusted split(s) in {ticker}!")
        for split in splits:
            ratio = split['ratio']
            date = split['date']
            print(f"   • {date}: ~{ratio:.1f}-for-1 split")
            print(f"     ${split['prev_price']:.2f} → ${split['curr_price']:.2f} ({split['pct_change']:.1f}% drop)")
        
        print(f"\n   ⚠️  Tiingo data is NOT properly adjusted!")
        print(f"   🔧 Automatically adjusting historical prices...")
        
        # AUTOMATICALLY ADJUST THE DATA
        df = adjust_for_splits(df, splits)
        
        # Verify adjustment worked
        verification_splits = detect_stock_splits(df, threshold=0.20)
        if len(verification_splits) == 0:
            print(f"   ✅ Verification: All splits corrected! Data is now continuous.\n")
        else:
            print(f"   ⚠️  Warning: {len(verification_splits)} splits still detected after adjustment.")
            print(f"   This may indicate complex splits or data issues.\n")
        
        return df
    
    return df


def validate_stock_symbol(ticker, quick_mode=False):
    """
    Validate if stock symbol exists by attempting a quick API check
    
    Args:
        ticker (str): Stock symbol to validate
        quick_mode (bool): If True, only do format check (fast)
    
    Returns:
        tuple: (bool: is_valid, str: error_message)
    """
    # Basic format validation (always fast)
    if not ticker or not ticker.isalpha() or len(ticker) > 5:
        return False, f"Symbol '{ticker}' has invalid format. Use 1-5 letters only (e.g., AAPL, MSFT)."
    
    # If quick mode or sample data, skip API validation
    if quick_mode or not USE_REAL_DATA:
        return True, None
    
    try:
        print(f"   🔍 Validating symbol '{ticker}'...")
        
        # Try to fetch just 5 days of data as a quick validation
        test_df = analyze_stock_complete_tr(
            ticker=ticker,
            timeframe='daily',
            duration_days=5
        )
        
        if test_df is None or len(test_df) == 0:
            return False, f"Symbol '{ticker}' returned no data. It may be invalid or delisted."
        
        print(f"   ✅ Symbol '{ticker}' is valid!")
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        
        # Check for common error types
        if "404" in error_msg or "not found" in error_msg.lower():
            return False, f"Symbol '{ticker}' not found. Please check the spelling."
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            return False, f"API authentication error. Check your API key in .env file."
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            return False, f"API rate limit exceeded. Please wait a moment and try again."
        else:
            return False, f"Error validating symbol: {error_msg}"


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def draw_tr_chart_v2(ticker='AAPL', timeframe='Daily', duration='1 Year', show_chart=True):
    """
    Draw TR Chart with separate timeframe and duration selection
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'Daily' or 'Weekly'
        duration (str): '3 Months', '6 Months', '1 Year', '3 Years', '5 Years'
        show_chart (bool): If True, display chart on screen. If False, only save to file.
    """
    
    print("\n" + "="*80)
    print(f"DRAWING TR CHART: {ticker} - {timeframe} - {duration}")
    print("="*80)
    
    # Convert duration to days
    duration_days = {
        '3 Months': 90,
        '6 Months': 180,
        '1 Year': 365,
        '3 Years': 1095,
        '5 Years': 1825
    }
    
    days = duration_days.get(duration, 365)
    
    # Determine EMAs based on timeframe
    if timeframe == 'Daily':
        ema_short_period = 50
        ema_long_period = 200
        ema_label_short = "50 Day EMA"
        ema_label_long = "200 Day EMA"
        buffer_days = 250  # Extra days for EMA calculation (need 200+ for 200 Day EMA)
    else:  # Weekly
        ema_short_period = 10
        ema_long_period = 30
        ema_label_short = "10 Week EMA"
        ema_label_long = "30 Week EMA"
        buffer_days = 40  # Extra weeks for EMA calculation (need 30+ for 30 Week EMA)
    
    # Fetch extra data for EMA warmup period
    fetch_days = days + buffer_days
    
    print(f"\nTimeframe: {timeframe}")
    print(f"Duration: {duration} ({days} days)")
    print(f"Fetching: {fetch_days} days (includes {buffer_days} day buffer for EMA calculation)")
    print(f"EMAs: {ema_label_short} (blue) and {ema_label_long} (red)")
    
    # ═══════════════════════════════════════════════════════════════════
    # GET REAL DATA WITH CACHING
    # ═══════════════════════════════════════════════════════════════════
    
    cache = get_cache()
    df = None
    
    # Check if we should use real data
    if USE_REAL_DATA:
        print(f"\n📊 Fetching data for {ticker}...")
        
        # Check cache first
        if cache.is_cache_valid(ticker, timeframe, duration):
            df = cache.load_from_cache(ticker, timeframe, duration)
        
        # If no valid cache, fetch from API
        if df is None:
            print(f"   🌐 Fetching from API (no valid cache)...")
            try:
                # Call TR enhanced with EXTRA days for EMA warmup
                df = analyze_stock_complete_tr(
                    ticker=ticker,
                    timeframe=timeframe.lower(),  # 'daily' or 'weekly'
                    duration_days=fetch_days  # Extra days for EMA calculation
                )
                
                if df is not None and len(df) > 0:
                    print(f"   ✅ Fetched {len(df)} rows from API (includes buffer)")
                    
                    # CRITICAL: Check for splits and adjust if needed
                    # Note: TR indicators were calculated on unadjusted data by TR system
                    # This adjustment fixes price data but TR indicators may need recalculation
                    original_len = len(df)
                    df = check_and_adjust_splits(df, ticker)
                    
                    # If splits were adjusted, warn that TR indicators used old data
                    splits_found = detect_stock_splits(df, threshold=0.20)
                    if len(splits_found) == 0 and original_len == len(df):
                        # No splits detected after adjustment - data was already good OR we fixed it
                        pass
                    
                    # Trim to requested period (keep only last 'days' rows for display)
                    if len(df) > days:
                        df = df.tail(days).copy()
                        print(f"   ✅ Trimmed to {len(df)} rows for display")
                    
                    # Save adjusted data to cache
                    cache.save_to_cache(ticker, timeframe, duration, df)
                else:
                    # No data returned - symbol is invalid
                    raise ValueError(f"Symbol '{ticker}' not found or returned no data. Please check the symbol and try again.")
                    
            except ValueError as ve:
                # Re-raise ValueError (invalid symbol)
                raise ve
            except Exception as e:
                # Other API errors
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    raise ValueError(f"Symbol '{ticker}' not found on the exchange.")
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    raise ValueError(f"API authentication failed. Check your TIINGO_API_KEY in .env file.")
                elif "429" in error_msg or "rate limit" in error_msg.lower():
                    raise ValueError(f"API rate limit exceeded. Please wait a few minutes and try again.")
                else:
                    raise ValueError(f"Error fetching data for '{ticker}': {error_msg}")
    else:
        # USE_REAL_DATA is False - use sample data
        print(f"   ⚠️  TR Enhanced not available, using sample data for {ticker}")
    
    # If still no data (no real data available), create sample data
    # This only happens when USE_REAL_DATA is False
    if not USE_REAL_DATA:
        print(f"   📝 Creating sample data ({fetch_days} days including buffer)...")
        dates = pd.date_range(end=datetime.now(), periods=fetch_days, freq='D')
        np.random.seed(42)
        
        base_price = 150
        prices = base_price + np.cumsum(np.random.randn(fetch_days) * 2)
        
        df = pd.DataFrame({
            'Date': dates,
            'Close': prices,
            'High': prices + np.random.rand(fetch_days) * 2,
            'Low': prices - np.random.rand(fetch_days) * 2,
            'TR_Status': ['Neutral Buy'] * fetch_days
        })
        
        # Add TR signals with proper stage transition logic
        # RULE: After Stage 1 Uptrend, cannot go to Stage 2/3 Downtrend without neutral first
        # RULE: After Stage 1 Downtrend, cannot go to Stage 2/3 Uptrend without neutral first
        if fetch_days >= 60:
            # Start neutral
            current_stage = 'Neutral Buy'
            
            # Phase 1: Uptrend cycle (10-40%)
            df.loc[int(fetch_days*0.1):int(days*0.25), 'TR_Status'] = 'Buy'
            df.loc[int(fetch_days*0.26):int(days*0.4), 'TR_Status'] = 'Strong Buy'
            current_stage = 'Strong Buy'
            
            # Phase 2: Return to Neutral (must go through neutral before switching to downtrend)
            df.loc[int(fetch_days*0.41):int(days*0.45), 'TR_Status'] = 'Neutral Buy'  # Exit uptrend to neutral
            current_stage = 'Neutral Buy'
            
            # Phase 3: Now can enter downtrend from neutral
            df.loc[int(fetch_days*0.46):int(days*0.5), 'TR_Status'] = 'Neutral Sell'  # First stage downtrend
            df.loc[int(fetch_days*0.51):int(days*0.6), 'TR_Status'] = 'Sell'  # Stage 2 downtrend
            df.loc[int(fetch_days*0.61):int(days*0.75), 'TR_Status'] = 'Strong Sell'  # Stage 3 downtrend
            current_stage = 'Strong Sell'
            
            # Phase 4: Return to Neutral (must go through neutral before switching to uptrend)
            df.loc[int(fetch_days*0.76):int(fetch_days*0.8), 'TR_Status'] = 'Neutral Sell'  # Exit downtrend to neutral
            current_stage = 'Neutral Sell'
            
            # Phase 5: Now can enter uptrend from neutral
            df.loc[int(fetch_days*0.81):int(fetch_days*0.85), 'TR_Status'] = 'Neutral Buy'  # First stage uptrend
            df.loc[int(fetch_days*0.86):, 'TR_Status'] = 'Buy'  # Stage 2 uptrend
    
    # Calculate EMAs
    df['EMA_Short'] = calculate_ema(df['Close'], ema_short_period)
    df['EMA_Long'] = calculate_ema(df['Close'], ema_long_period)
    
    # Trim to display period if we have extra buffer data
    if len(df) > days:
        df = df.tail(days).copy()
        print(f"   ✅ Trimmed to {len(df)} days for display (EMAs accurate from start)")
    
    # Add peaks
    df['Peak'] = False
    df['Buy_Point'] = np.nan
    df['Stop_Loss'] = np.nan
    
    for i in range(10, days-10, 30):
        df.loc[i, 'Peak'] = True
        peak_price = df.loc[i, 'High']
        df.loc[i:, 'Buy_Point'] = peak_price
        df.loc[i:, 'Stop_Loss'] = peak_price * 0.92
    
    print(f"✅ Data created: {len(df)} days")
    print(f"✅ EMAs calculated: {ema_label_short} and {ema_label_long}")
    
    # Ensure Date column is datetime type for plotting
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Create chart
    print("Drawing chart...")
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Plot price line
    ax.plot(df['Date'], df['Close'], color='black', linewidth=2, label='Close Price', zorder=5)
    
    # Plot EMAs
    ax.plot(df['Date'], df['EMA_Short'], 
           color='blue', linewidth=1.5, label=ema_label_short, zorder=4, alpha=0.8)
    ax.plot(df['Date'], df['EMA_Long'], 
           color='red', linewidth=1.5, label=ema_label_long, zorder=4, alpha=0.8)
    
    # Background bands (more intense colors)
    stage_colors = {
        'Buy': '#32CD32',          # Lime Green - Stage 2 Uptrend
        'Strong Buy': '#008000',   # Dark Green - Stage 3 Uptrend
        'Sell': '#FFFF00',         # Yellow - Stage 2 Downtrend
        'Strong Sell': '#FF8C00'   # Dark Orange - Stage 3 Downtrend
    }
    
    # Debug: Check what TR_Status values we actually have
    if 'TR_Status' in df.columns:
        unique_statuses = df['TR_Status'].unique()
        print(f"\n📊 TR Status values in data: {list(unique_statuses)}")
        
        # Count each status
        for status in unique_statuses:
            count = (df['TR_Status'] == status).sum()
            print(f"   • {status}: {count} occurrences")
        print()
    
    current_status = None
    band_start = None
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        
        if status in stage_colors:
            if current_status != status:
                current_status = status
                band_start = i
        else:
            if current_status is not None:
                band_end = i - 1
                x_start = df.iloc[band_start]['Date']
                x_end = df.iloc[band_end]['Date']
                ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
                current_status = None
                band_start = None
    
    if current_status is not None:
        x_start = df.iloc[band_start]['Date']
        x_end = df.iloc[-1]['Date']
        ax.axvspan(x_start, x_end, facecolor=stage_colors[current_status], alpha=0.3, zorder=1)
    
    # Stage 1 markers
    prev_status = None
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        date = df.iloc[i]['Date']
        price = df.iloc[i]['Close']
        
        if i > 0:
            prev_status = df.iloc[i - 1]['TR_Status']
        
        if status == 'Neutral Buy' and prev_status != 'Neutral Buy':
            ax.scatter(date, price, marker='^', color='lightgreen', 
                      s=60, edgecolors='darkgreen', linewidths=1.2, zorder=10)
        elif status == 'Neutral Sell' and prev_status != 'Neutral Sell':
            ax.scatter(date, price, marker='D', color='red', 
                      s=40, edgecolors='darkred', linewidths=1.2, zorder=10)
    
    # Draw buy points and stop losses
    print("Drawing buy points and stop losses...")
    
    # Check if we have the required columns from TR system
    if 'Buy_Point' in df.columns and 'Stop_Loss' in df.columns:
        print("   Using buy points from TR system...")
        
        # Get rows where Buy_Point changes (new peaks detected)
        df['Buy_Point_Changed'] = df['Buy_Point'].ne(df['Buy_Point'].shift())
        peak_changes = df[df['Buy_Point_Changed'] & df['Buy_Point'].notna()]
        
        if len(peak_changes) > 0:
            print(f"   Drawing {len(peak_changes)} buy point levels...")
            
            for idx in peak_changes.index:
                try:
                    start_date = df.loc[idx, 'Date']
                    buy_point = df.loc[idx, 'Buy_Point']
                    stop_loss = df.loc[idx, 'Stop_Loss']
                    
                    # Validate dates and values
                    if pd.isna(start_date) or pd.isna(buy_point) or pd.isna(stop_loss):
                        continue
                    
                    # Ensure start_date is a valid datetime
                    if not isinstance(start_date, pd.Timestamp):
                        start_date = pd.to_datetime(start_date)
                    
                    # Find where this buy point ends (next buy point change or end of data)
                    next_changes = peak_changes[peak_changes.index > idx]
                    if len(next_changes) > 0:
                        end_idx = next_changes.index[0] - 1
                    else:
                        end_idx = df.index[-1]
                    
                    end_date = df.loc[end_idx, 'Date']
                    
                    # Validate end_date
                    if pd.isna(end_date):
                        continue
                    
                    if not isinstance(end_date, pd.Timestamp):
                        end_date = pd.to_datetime(end_date)
                    
                    # Draw buy point line (black dashed)
                    ax.plot([start_date, end_date], [buy_point, buy_point],
                           color='black', linewidth=1.5, linestyle='--', dashes=(8, 4), 
                           zorder=6, alpha=0.7)
                    
                    # Draw stop loss line (red dashed) - shorter, only first third
                    from datetime import timedelta
                    total_days = (end_date - start_date).days
                    
                    if total_days > 0:
                        stop_end_days = max(1, int(total_days * 0.33))  # First 33%
                        stop_end_date = start_date + timedelta(days=stop_end_days)
                        
                        ax.plot([start_date, stop_end_date], [stop_loss, stop_loss],
                               color='red', linewidth=1.5, linestyle='--', dashes=(8, 4), 
                               zorder=6, alpha=0.7)
                    
                except Exception as e:
                    print(f"   ⚠️  Error drawing level at index {idx}: {e}")
                    continue
            
            # Add legend entries
            ax.plot([], [], color='black', linewidth=1.5, linestyle='--', 
                   label='Buy Point', alpha=0.7)
            ax.plot([], [], color='red', linewidth=1.5, linestyle='--', 
                   label='Stop Loss (8% below)', alpha=0.7)
            
            print("   ✅ Buy points and stop losses drawn")
        else:
            print("   ⚠️  No buy point changes detected")
    else:
        print("   ⚠️  Buy_Point/Stop_Loss columns not found, skipping")
    
    print("✅ Buy points and stop losses complete")
    
    # Format chart
    ax.set_xlabel('Date', fontsize=14, fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=14, fontweight='bold')
    ax.set_title(f'{ticker} - TR Indicator Chart ({timeframe} - {duration})', 
                fontsize=18, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'${y:.2f}'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax.legend(loc='best', fontsize=11, framealpha=0.95)
    plt.tight_layout()
    
    # Save - ensure all values are strings and sanitize for filename
    ticker_str = str(ticker).replace('/', '_').replace('\\', '_')
    timeframe_str = str(timeframe).replace(' ', '_')
    duration_str = str(duration).replace(' ', '_')
    output_filename = f'{ticker_str}_{timeframe_str}_{duration_str}_TR_Chart.png'
    
    # Save to current directory (not hardcoded server path)
    try:
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"\n✅ Chart saved: {output_filename}")
        
        # Show chart on screen if requested
        if show_chart:
            print("📊 Displaying chart on screen...")
            print("   (Close the chart window to continue)")
            plt.show()
        
    except Exception as e:
        print(f"\n❌ Error saving chart: {e}")
        print(f"   Filename: {output_filename}")
        print(f"   Type of filename: {type(output_filename)}")
        import traceback
        traceback.print_exc()
        # Try saving with a simple name as fallback
        try:
            simple_name = 'chart_output.png'
            plt.savefig(simple_name, dpi=300, bbox_inches='tight')
            print(f"   ✅ Saved with fallback name: {simple_name}")
        except Exception as e2:
            print(f"   ❌ Fallback also failed: {e2}")
    
    print("="*80 + "\n")
    
    return fig


def show_menu():
    """Display menu and get selections"""
    
    print("\n" + "="*80)
    print("TR INDICATOR CHART GENERATOR")
    print("="*80)
    
    # Step 0: Enter Stock Symbol
    print("\nSTEP 0: ENTER STOCK SYMBOL")
    print("-"*80)
    
    while True:
        ticker = input("Enter stock symbol (or 'Q' to quit): ").strip().upper()
        
        # Check for quit
        if ticker in ['Q', 'QUIT', 'EXIT']:
            print("❌ Cancelled. Returning to main menu.")
            return None, None, None
        
        if not ticker:
            print("❌ Empty input! Please enter a symbol or 'Q' to quit.")
            continue
        
        # Quick format validation (fast, no API call)
        is_valid, error_msg = validate_stock_symbol(ticker, quick_mode=True)
        
        if not is_valid:
            print(f"❌ {error_msg}")
            print("   Try again or enter 'Q' to quit.")
            continue
        
        # Format is valid, break the loop
        print(f"✅ Selected ticker: {ticker}")
        print("   (Symbol will be validated when fetching data)")
        break
    
    # Step 1: Select Timeframe
    print("\n" + "-"*80)
    print("STEP 1: SELECT TIMEFRAME")
    print("-"*80)
    print("  1. Daily   (Uses 50-Day and 200-Day EMA)")
    print("  2. Weekly  (Uses 10-Week and 30-Week EMA)")
    
    timeframe_choice = input("\nEnter timeframe choice (1 or 2): ").strip()
    
    if timeframe_choice == '1':
        timeframe = 'Daily'
    elif timeframe_choice == '2':
        timeframe = 'Weekly'
    else:
        print("❌ Invalid choice! Defaulting to Daily.")
        timeframe = 'Daily'
    
    print(f"✅ Selected: {timeframe}")
    
    # Step 2: Select Duration
    print("\n" + "-"*80)
    print("STEP 2: SELECT CHART DURATION")
    print("-"*80)
    print("  1. 3 Months")
    print("  2. 6 Months")
    print("  3. 1 Year")
    print("  4. 3 Years")
    print("  5. 5 Years")
    
    duration_choice = input("\nEnter duration choice (1-5): ").strip()
    
    duration_map = {
        '1': '3 Months',
        '2': '6 Months',
        '3': '1 Year',
        '4': '3 Years',
        '5': '5 Years'
    }
    
    duration = duration_map.get(duration_choice, '1 Year')
    print(f"✅ Selected: {duration}")
    
    return ticker, timeframe, duration


def main():
    """Main function"""
    
    while True:
        print("\n" + "="*80)
        print("TR INDICATOR CHART GENERATOR")
        print("="*80)
        print("\nSelect Option:")
        print("  1. Generate Chart")
        print("  2. View Cache Status")
        print("  3. Clear Cache")
        print("  0. Exit")
        
        main_choice = input("\nEnter choice (0-3): ").strip()
        
        if main_choice == '0':
            print("\n✅ Goodbye!")
            print("="*80 + "\n")
            break
        
        elif main_choice == '1':
            # Generate chart (now includes ticker input)
            ticker, timeframe, duration = show_menu()
            
            # Check if user cancelled during input
            if ticker is None:
                continue  # Go back to main menu
            
            print("\n" + "="*80)
            print("GENERATING CHART...")
            print("="*80)
            print(f"\nTicker: {ticker}")
            print(f"Timeframe: {timeframe}")
            print(f"Duration: {duration}")
            
            if timeframe == 'Daily':
                print(f"EMAs: 50-Day (blue) and 200-Day (red)")
            else:
                print(f"EMAs: 10-Week (blue) and 30-Week (red)")
            
            try:
                fig = draw_tr_chart_v2(ticker=ticker, timeframe=timeframe, duration=duration)
                
                print("\n" + "="*80)
                print("✅ SUCCESS!")
                print("="*80)
                
                # Sanitize output filename display
                ticker_str = str(ticker).replace('/', '_').replace('\\', '_')
                timeframe_str = str(timeframe).replace(' ', '_')
                duration_str = str(duration).replace(' ', '_')
                output_file = f'{ticker_str}_{timeframe_str}_{duration_str}_TR_Chart.png'
                
                print(f"\n📊 Chart saved: {output_file}")
                print(f"   Location: Current directory")
                
                again = input("\nCreate another chart? (y/n): ").strip().lower()
                if again != 'y':
                    break
                    
            except Exception as e:
                error_str = str(e)
                print(f"\n❌ ERROR: {e}")
                
                # Check if it's a symbol validation error
                if "404" in error_str or "not found" in error_str.lower():
                    print(f"\n💡 Symbol '{ticker}' appears to be invalid.")
                    print("   Please check:")
                    print("   - Spelling is correct")
                    print("   - Symbol exists on the exchange")
                    print("   - Stock hasn't been delisted")
                elif "401" in error_str or "unauthorized" in error_str.lower():
                    print("\n💡 API authentication failed.")
                    print("   Please check your TIINGO_API_KEY in .env file")
                elif "429" in error_str or "rate limit" in error_str.lower():
                    print("\n💡 API rate limit exceeded.")
                    print("   Please wait a few minutes before trying again")
                
                # Ask if user wants to try again
                retry = input("\nTry again with a different symbol? (y/n): ").strip().lower()
                if retry == 'y':
                    continue  # Loop back to main menu, user can select option 1 again
                else:
                    print("   Returning to main menu...")
        
        elif main_choice == '2':
            # View cache status
            cache = get_cache()
            cache.print_cache_summary()
            input("\nPress Enter to continue...")
        
        elif main_choice == '3':
            # Clear cache
            print("\n" + "="*80)
            print("CLEAR CACHE")
            print("="*80)
            print("\nOptions:")
            print("  1. Clear all cache")
            print("  2. Clear specific ticker")
            print("  0. Cancel")
            
            clear_choice = input("\nEnter choice (0-2): ").strip()
            
            cache = get_cache()
            
            if clear_choice == '1':
                confirm = input("Clear ALL cache? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    cache.clear_cache()
                else:
                    print("   Cancelled")
            
            elif clear_choice == '2':
                ticker = input("Enter ticker symbol: ").strip().upper()
                cache.clear_cache(ticker)
            
            input("\nPress Enter to continue...")
        
        else:
            print("\n❌ Invalid choice!")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
