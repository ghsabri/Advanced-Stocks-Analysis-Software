"""
TR CHART MENU - Select Timeframe AND Duration
Two-step selection: 1) Timeframe (Daily/Weekly), 2) Duration
NOW WITH REAL DATA + CACHING!

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


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def draw_tr_chart_v2(ticker='AAPL', timeframe='Daily', duration='1 Year'):
    """
    Draw TR Chart with separate timeframe and duration selection
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'Daily' or 'Weekly'
        duration (str): '3 Months', '6 Months', '1 Year', '3 Years', '5 Years'
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
    else:  # Weekly
        ema_short_period = 10
        ema_long_period = 30
        ema_label_short = "10 Week EMA"
        ema_label_long = "30 Week EMA"
    
    print(f"\nTimeframe: {timeframe}")
    print(f"Duration: {duration} ({days} days)")
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
                # Call TR enhanced with correct parameters
                df = analyze_stock_complete_tr(
                    ticker=ticker,
                    timeframe=timeframe.lower(),  # 'daily' or 'weekly'
                    duration_days=days
                )
                
                if df is not None and len(df) > 0:
                    print(f"   ✅ Fetched {len(df)} rows from API")
                    # Save to cache for next time
                    cache.save_to_cache(ticker, timeframe, duration, df)
                else:
                    print(f"   ⚠️  API returned no data, using sample data")
                    df = None
                    
            except Exception as e:
                print(f"   ❌ API error: {e}")
                print(f"   ⚠️  Falling back to sample data")
                df = None
    
    # If still no data (no real data available), create sample data
    if df is None:
        print(f"   📝 Creating sample data ({days} days)...")
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        np.random.seed(42)
        
        base_price = 150
        prices = base_price + np.cumsum(np.random.randn(days) * 2)
        
        df = pd.DataFrame({
            'Date': dates,
            'Close': prices,
            'High': prices + np.random.rand(days) * 2,
            'Low': prices - np.random.rand(days) * 2,
            'TR_Status': ['Neutral Buy'] * days
        })
        
        # Add TR signals with proper stage transition logic
        # RULE: After Stage 1 Uptrend, cannot go to Stage 2/3 Downtrend without neutral first
        # RULE: After Stage 1 Downtrend, cannot go to Stage 2/3 Uptrend without neutral first
        if days >= 60:
            # Start neutral
            current_stage = 'Neutral Buy'
            
            # Phase 1: Uptrend cycle (10-40%)
            df.loc[int(days*0.1):int(days*0.25), 'TR_Status'] = 'Buy'
            df.loc[int(days*0.26):int(days*0.4), 'TR_Status'] = 'Strong Buy'
            current_stage = 'Strong Buy'
            
            # Phase 2: Return to Neutral (must go through neutral before switching to downtrend)
            df.loc[int(days*0.41):int(days*0.45), 'TR_Status'] = 'Neutral Buy'  # Exit uptrend to neutral
            current_stage = 'Neutral Buy'
            
            # Phase 3: Now can enter downtrend from neutral
            df.loc[int(days*0.46):int(days*0.5), 'TR_Status'] = 'Neutral Sell'  # First stage downtrend
            df.loc[int(days*0.51):int(days*0.6), 'TR_Status'] = 'Sell'  # Stage 2 downtrend
            df.loc[int(days*0.61):int(days*0.75), 'TR_Status'] = 'Strong Sell'  # Stage 3 downtrend
            current_stage = 'Strong Sell'
            
            # Phase 4: Return to Neutral (must go through neutral before switching to uptrend)
            df.loc[int(days*0.76):int(days*0.8), 'TR_Status'] = 'Neutral Sell'  # Exit downtrend to neutral
            current_stage = 'Neutral Sell'
            
            # Phase 5: Now can enter uptrend from neutral
            df.loc[int(days*0.81):int(days*0.85), 'TR_Status'] = 'Neutral Buy'  # First stage uptrend
            df.loc[int(days*0.86):, 'TR_Status'] = 'Buy'  # Stage 2 uptrend
    
    # Calculate EMAs
    df['EMA_Short'] = calculate_ema(df['Close'], ema_short_period)
    df['EMA_Long'] = calculate_ema(df['Close'], ema_long_period)
    
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
        'Buy': '#32CD32',          # Lime Green (more intense light green)
        'Strong Buy': '#008000',   # Green (more intense dark green)
        'Sell': '#FFFF00',         # Yellow (more intense, not light yellow)
        'Strong Sell': '#FF8C00'   # Dark Orange (instead of dark red for visibility)
    }
    
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
                      s=200, edgecolors='darkgreen', linewidths=2, zorder=10)
        elif status == 'Neutral Sell' and prev_status != 'Neutral Sell':
            ax.scatter(date, price, marker='D', color='red', 
                      s=150, edgecolors='darkred', linewidths=2, zorder=10)
    
    # Draw buy points and stop losses
    print("Drawing buy points and stop losses...")
    print("   ⚠️  Skipping buy points/stop losses for now (will add later)")
    print("✅ Buy points and stop losses drawn (skipped)")
    
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
    
    # Step 1: Select Timeframe
    print("\nSTEP 1: SELECT TIMEFRAME")
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
    
    return timeframe, duration


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
            # Generate chart (existing functionality)
            timeframe, duration = show_menu()
            
            ticker = 'AAPL'  # Default ticker
            
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
                print(f"\n❌ ERROR: {e}")
                print("Please try again.")
        
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
