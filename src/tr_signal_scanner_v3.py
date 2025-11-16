"""
TR SIGNAL SCANNER - PROPER IMPLEMENTATION
==========================================
This scanner uses YOUR existing TR indicator code directly.
No duplication, no reinventing - just imports and uses your working code.

When you improve TR logic → Scanner automatically uses improved logic ✅

Author: MJ Software LLC
Date: November 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# IMPORT YOUR EXISTING TR INDICATOR CODE
# ============================================================================

USING_EXISTING_CODE = False
import_error_message = ""

try:
    # Try to import tr_enhanced (YOUR complete TR with quality markers)
    from tr_enhanced import analyze_stock_complete_tr
    print("✅ Successfully imported tr_enhanced.py (complete TR analysis)")
    
    USING_EXISTING_CODE = True
    print("✅ Using YOUR tr_enhanced.py - ONE source of truth!")
    
except ImportError as e:
    import_error_message = str(e)
    print(f"⚠️  Could not import tr_enhanced.py: {e}")
    print("   Trying fallback: tr_indicator.py...")
    
    try:
        # Fallback: Try basic TR
        import tr_calculations as tc
        from tr_indicator import analyze_tr_indicator
        print("✅ Using basic tr_indicator.py")
        USING_EXISTING_CODE = True
    except ImportError as e2:
        print(f"❌ IMPORT FAILED: {e2}")
        print("\n⚠️  Using fallback code instead.")
        USING_EXISTING_CODE = False

# ============================================================================
# FALLBACK FUNCTIONS (only used if import fails)
# ============================================================================

def fallback_analyze_stock_tr(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fallback: Basic TR analysis if your main code can't be imported
    This is a SIMPLIFIED version - the real analysis should use your code!
    """
    import yfinance as yf
    
    # Download data
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    
    if df.empty:
        return pd.DataFrame()
    
    # Handle multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Basic calculations (SIMPLIFIED!)
    df['EMA_20'] = df['Close'].ewm(span=20).mean()
    df['EMA_50'] = df['Close'].ewm(span=50).mean()
    
    # Basic TR status (VERY SIMPLIFIED!)
    df['TR_Status'] = 'Neutral'
    df.loc[df['Close'] > df['EMA_20'], 'TR_Status'] = 'Strong Buy'
    
    return df

# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def analyze_stock_tr_for_scanner(symbol: str, start_date: str, end_date: str, timeframe: str = 'Daily') -> pd.DataFrame:
    """
    Analyze stock using YOUR existing tr_enhanced.py
    
    Args:
        symbol: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: 'Daily' or 'Weekly'
    
    Returns:
        DataFrame with TR analysis from YOUR tr_enhanced.py
    """
    
    print(f"Analyzing {symbol} ({timeframe})...")
    
    if USING_EXISTING_CODE:
        try:
            # Try to use YOUR tr_enhanced.py (complete analysis)
            from tr_enhanced import analyze_stock_complete_tr
            
            # Calculate duration in days
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end_dt - start_dt).days
            
            # CALL YOUR EXISTING FUNCTION!
            result = analyze_stock_complete_tr(
                ticker=symbol,
                timeframe=timeframe.lower(),
                duration_days=duration_days
            )
            
            if result is None or result.empty:
                print(f"  ⚠️  No data returned for {symbol}")
                return pd.DataFrame()
            
            print(f"  ✅ Using YOUR tr_enhanced.py!")
            return result
            
        except Exception as e:
            print(f"  ⚠️  Error with tr_enhanced: {e}")
            print(f"  ℹ️  Trying basic tr_indicator...")
            
            # Fallback to basic TR
            try:
                import yfinance as yf
                from tr_indicator import analyze_tr_indicator
                
                # Download stock data
                if timeframe == 'Weekly':
                    df_daily = yf.download(symbol, start=start_date, end=end_date, progress=False)
                    df = df_daily.resample('W').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                else:
                    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
                
                if df.empty or len(df) < 100:
                    return pd.DataFrame()
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                result = analyze_tr_indicator(df)
                print(f"  ✅ Using basic TR indicator")
                return result
                
            except Exception as e2:
                print(f"  ❌ Error: {e2}")
                return fallback_analyze_stock_tr(symbol, start_date, end_date)
    
    else:
        print(f"  ⚠️  Using fallback (basic) analysis")
        return fallback_analyze_stock_tr(symbol, start_date, end_date)

# ============================================================================
# SIGNAL EXTRACTION
# ============================================================================

def extract_tr_signals(df: pd.DataFrame, symbol: str) -> List[Dict]:
    """
    Extract Strong Buy signals from TR analysis
    
    Collects signals with quality levels:
    - "Strong Buy" (basic)
    - "Strong Buy✓" (within 5% of buy point)
    - "Strong Buy*" (RS + Chaikin top 5%)
    - "Strong Buy✓*" (all criteria - BEST!)
    """
    
    signals = []
    
    # Use enhanced status if available, otherwise fall back to basic
    status_column = 'TR_Status_Enhanced' if 'TR_Status_Enhanced' in df.columns else 'TR_Status'
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Only collect Strong Buy signals (all quality levels)
        tr_status = str(row.get(status_column, 'Neutral'))
        if 'Strong Buy' not in tr_status:
            continue
        
        # Extract signal date from Date column (not row.name)
        if 'Date' in df.columns:
            signal_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        elif hasattr(row.name, 'strftime'):
            signal_date = row.name.strftime('%Y-%m-%d')
        else:
            signal_date = str(row.name)
        
        # Extract signal data
        signal = {
            'stock_symbol': symbol,
            'signal_date': signal_date,
            'tr_status': tr_status,
            'entry_price': float(row['Close']),
            
            # Quality indicators
            'has_buy_point': '✓' in tr_status,
            'has_rs_chaikin': '*' in tr_status,
            'quality_level': calculate_quality_level(tr_status),
            
            # TR Features (if available in your code)
            'ppo_value': float(row.get('PPO_Line', 0)),
            'ppo_histogram': float(row.get('PPO_Histogram', 0)),
            'pmo_value': float(row.get('PMO_Line', 0)),
            'pmo_signal': float(row.get('PMO_Signal', 0)),
            
            'ema_3': float(row.get('EMA_3', 0)),
            'ema_9': float(row.get('EMA_9', 0)),
            'ema_20': float(row.get('EMA_20', 0)),
            'ema_34': float(row.get('EMA_34', 0)),
            
            'relative_strength': float(row.get('RS_Percentile', 0)),
            'chaikin_ad': float(row.get('Chaikin_Percentile', 0)),
            
            # Buy point
            'buy_point': float(row.get('Buy_Point', 0)) if pd.notna(row.get('Buy_Point')) else None,
            
            # Targets (YOUR settings)
            'target_price': float(row['Close'] * 1.15),  # 15% target
            'stop_loss': float(row['Close'] * 0.90),     # 10% stop
            
            # Outcome (to be labeled)
            'outcome': 'PENDING',
            'days_to_target': None,
            'max_gain_pct': None,
            'max_drawdown_pct': None
        }
        
        signals.append(signal)
    
    return signals


def calculate_quality_level(tr_status: str) -> int:
    """
    Calculate signal quality level
    
    1 = Basic "Strong Buy"
    2 = "Strong Buy✓" (buy point)
    3 = "Strong Buy*" (RS + Chaikin)
    4 = "Strong Buy✓*" (all criteria - BEST!)
    """
    if tr_status == "Strong Buy":
        return 1
    elif tr_status == "Strong Buy✓":
        return 2
    elif tr_status == "Strong Buy*":
        return 3
    elif tr_status == "Strong Buy✓*" or "Strong Buy*✓" in tr_status:
        return 4
    else:
        return 1

# ============================================================================
# SIGNAL LABELING
# ============================================================================

def label_signal_outcome(symbol: str, signal_date: str, entry_price: float, 
                         target_price: float, stop_loss: float, timeframe: str = 'Daily',
                         max_days: int = 180) -> Dict:
    """
    Label signal as SUCCESS or FAILURE based on future price action
    
    SUCCESS: Price reaches target (+15%) BEFORE any failure condition
    
    FAILURE: Whichever happens first:
      - Price hits -10% stop loss
      - Daily: Price closes below 200-day EMA
      - Weekly: Price closes below 30-week EMA
    
    Args:
        symbol: Stock symbol
        signal_date: Signal date
        entry_price: Entry price
        target_price: Target price (+15%)
        stop_loss: Stop loss price (-10%)
        timeframe: 'Daily' or 'Weekly'
        max_days: Max days to check (default 180)
    
    Returns:
        Dict with outcome and metrics
    """
    import yfinance as yf
    
    try:
        signal_dt = datetime.strptime(signal_date, '%Y-%m-%d')
        end_dt = signal_dt + timedelta(days=max_days)
        
        # Download future data (need more history for EMA calculation)
        # Start earlier to calculate EMA properly
        history_start = signal_dt - timedelta(days=250)  # Extra for 200 EMA
        
        full_df = yf.download(symbol, 
                             start=history_start.strftime('%Y-%m-%d'),
                             end=end_dt.strftime('%Y-%m-%d'), 
                             progress=False)
        
        if full_df.empty:
            return {
                'outcome': 'INSUFFICIENT_DATA',
                'days_to_target': None,
                'max_gain_pct': None,
                'max_drawdown_pct': None
            }
        
        # Handle multi-index
        if isinstance(full_df.columns, pd.MultiIndex):
            full_df.columns = full_df.columns.get_level_values(0)
        
        # Resample to weekly if needed
        if timeframe == 'Weekly':
            full_df = full_df.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        
        # Calculate EMA
        if timeframe == 'Daily':
            full_df['EMA'] = full_df['Close'].ewm(span=200, adjust=False).mean()
            ema_label = '200-day EMA'
        else:  # Weekly
            full_df['EMA'] = full_df['Close'].ewm(span=30, adjust=False).mean()
            ema_label = '30-week EMA'
        
        # Get data AFTER signal date
        future_df = full_df[full_df.index > signal_dt]
        
        if len(future_df) < 2:
            return {
                'outcome': 'INSUFFICIENT_DATA',
                'days_to_target': None,
                'max_gain_pct': None,
                'max_drawdown_pct': None
            }
        
        # Calculate metrics
        max_price = float(future_df['High'].max())
        min_price = float(future_df['Low'].min())
        
        max_gain_pct = ((max_price - entry_price) / entry_price) * 100
        max_drawdown_pct = ((min_price - entry_price) / entry_price) * 100
        
        # Find FIRST occurrence of:
        # 1. Target reached (SUCCESS)
        # 2. Stop loss hit (FAILURE)
        # 3. Close below EMA (FAILURE)
        
        target_reached_series = future_df['High'] >= target_price
        stop_hit_series = future_df['Low'] <= stop_loss
        ema_breach_series = future_df['Close'] < future_df['EMA']
        
        target_reached = target_reached_series.any()
        stop_hit = stop_hit_series.any()
        ema_breached = ema_breach_series.any()
        
        # Collect all events with their dates
        events = []
        
        if target_reached:
            target_day = future_df.index[target_reached_series][0]
            events.append(('TARGET', target_day))
        
        if stop_hit:
            stop_day = future_df.index[stop_hit_series][0]
            events.append(('STOP', stop_day))
        
        if ema_breached:
            ema_day = future_df.index[ema_breach_series][0]
            events.append(('EMA', ema_day))
        
        if not events:
            # Nothing happened
            return {
                'outcome': 'PENDING',
                'reason': f'NO_EVENT_WITHIN_{max_days}_DAYS',
                'days_to_target': None,
                'max_gain_pct': float(max_gain_pct),
                'max_drawdown_pct': float(max_drawdown_pct)
            }
        
        # Sort by date to find what happened FIRST
        events.sort(key=lambda x: x[1])
        first_event, first_date = events[0]
        
        days_elapsed = (first_date - signal_dt).days
        
        if first_event == 'TARGET':
            # Target reached first = SUCCESS
            return {
                'outcome': 'SUCCESS',
                'days_to_target': int(days_elapsed),
                'max_gain_pct': float(max_gain_pct),
                'max_drawdown_pct': float(max_drawdown_pct),
                'win_reason': 'TARGET_REACHED_FIRST'
            }
        
        elif first_event == 'STOP':
            # Stop loss hit first = FAILURE
            return {
                'outcome': 'FAILURE',
                'reason': 'STOP_LOSS_HIT_FIRST',
                'days_to_failure': int(days_elapsed),
                'days_to_target': None,
                'max_gain_pct': float(max_gain_pct),
                'max_drawdown_pct': float(max_drawdown_pct)
            }
        
        else:  # first_event == 'EMA'
            # Closed below EMA first = FAILURE
            ema_value = float(future_df.loc[first_date, 'EMA'])
            close_value = float(future_df.loc[first_date, 'Close'])
            
            return {
                'outcome': 'FAILURE',
                'reason': f'CLOSED_BELOW_{ema_label.upper().replace("-", "_").replace(" ", "_")}',
                'days_to_failure': int(days_elapsed),
                'days_to_target': None,
                'max_gain_pct': float(max_gain_pct),
                'max_drawdown_pct': float(max_drawdown_pct),
                'ema_breach_price': float(close_value),
                'ema_value': float(ema_value)
            }
    
    except Exception as e:
        print(f"  ⚠️  Error labeling signal: {str(e)[:100]}")
        return {'outcome': 'ERROR', 'days_to_target': None, 
               'max_gain_pct': None, 'max_drawdown_pct': None}

# ============================================================================
# BATCH SCANNER
# ============================================================================

def scan_multiple_stocks(stock_list: List[str], 
                         start_date: str, 
                         end_date: str,
                         scan_both_timeframes: bool = True,
                         output_file: str = 'tr_signals_labeled.csv') -> pd.DataFrame:
    """
    Scan multiple stocks for TR signals using YOUR existing TR code
    
    Args:
        stock_list: List of stock symbols
        start_date: Start date
        end_date: End date
        scan_both_timeframes: If True, scans BOTH Daily and Weekly (default True)
        output_file: Output CSV filename
    
    Returns:
        DataFrame with all signals (Daily + Weekly combined)
    """
    
    all_signals = []
    
    print(f"\n{'='*80}")
    print(f"TR SIGNAL SCANNER - Using YOUR TR Indicator Code")
    print(f"{'='*80}")
    print(f"Stocks: {len(stock_list)}")
    print(f"Period: {start_date} to {end_date}")
    
    if scan_both_timeframes:
        print(f"Timeframes: Daily AND Weekly ✅")
    else:
        print(f"Timeframe: Daily only")
    
    if USING_EXISTING_CODE:
        print(f"✅ Using YOUR existing tr_enhanced.py")
    else:
        print(f"⚠️  Using fallback code")
    print(f"{'='*80}\n")
    
    # Determine which timeframes to scan
    timeframes_to_scan = ['Daily', 'Weekly'] if scan_both_timeframes else ['Daily']
    
    for timeframe in timeframes_to_scan:
        print(f"\n{'='*80}")
        print(f"SCANNING {timeframe.upper()} TIMEFRAME")
        print(f"{'='*80}\n")
        
        for idx, symbol in enumerate(stock_list, 1):
            print(f"[{idx}/{len(stock_list)}] Processing {symbol} ({timeframe})...")
            
            try:
                # Use YOUR TR indicator code!
                df = analyze_stock_tr_for_scanner(symbol, start_date, end_date, timeframe=timeframe)
                
                if df.empty:
                    print(f"  ⚠️  Skipping {symbol} - no data")
                    continue
                
                # Extract Strong Buy signals
                signals = extract_tr_signals(df, symbol)
                
                # Add timeframe to each signal
                for signal in signals:
                    signal['timeframe'] = timeframe
                
                print(f"  ✅ Found {len(signals)} Strong Buy signals")
                
                # Label each signal
                labeled_count = 0
                for signal in signals:
                    outcome = label_signal_outcome(
                        symbol,
                        signal['signal_date'],
                        signal['entry_price'],
                        signal['target_price'],
                        signal['stop_loss'],
                        timeframe=timeframe  # Pass timeframe for EMA check
                    )
                    
                    signal.update(outcome)
                    
                    if outcome['outcome'] in ['SUCCESS', 'FAILURE']:
                        labeled_count += 1
                
                print(f"  ✅ Labeled {labeled_count} signals")
                all_signals.extend(signals)
                
            except Exception as e:
                print(f"  ❌ Error with {symbol}: {str(e)[:100]}")
                continue
            
            print()
    
    # Convert to DataFrame
    df_signals = pd.DataFrame(all_signals)
    
    if len(df_signals) == 0:
        print("\n⚠️  No signals collected!")
        return df_signals
    
    # Save to CSV
    df_signals.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE!")
    print(f"{'='*80}")
    print(f"Total signals found: {len(all_signals)}")
    
    # Show breakdown by timeframe
    if 'timeframe' in df_signals.columns:
        print(f"\nBy Timeframe:")
        for tf in ['Daily', 'Weekly']:
            count = (df_signals['timeframe'] == tf).sum()
            if count > 0:
                print(f"  {tf}: {count} signals")
    
    # Show breakdown by quality level
    if 'quality_level' in df_signals.columns:
        print(f"\nBy Quality Level:")
        for level in [4, 3, 2, 1]:
            count = (df_signals['quality_level'] == level).sum()
            if count > 0:
                level_name = {
                    4: "Level 4 (Strong Buy✓* - BEST)",
                    3: "Level 3 (Strong Buy*)",
                    2: "Level 2 (Strong Buy✓)",
                    1: "Level 1 (Strong Buy)"
                }[level]
                print(f"  {level_name}: {count}")
    
    # Show success/failure
    success_count = (df_signals['outcome'] == 'SUCCESS').sum()
    failure_count = (df_signals['outcome'] == 'FAILURE').sum()
    other_count = (~df_signals['outcome'].isin(['SUCCESS', 'FAILURE'])).sum()
    
    print(f"\nOutcomes:")
    print(f"  SUCCESS: {success_count}")
    print(f"  FAILURE: {failure_count}")
    print(f"  OTHER: {other_count}")
    
    if success_count + failure_count > 0:
        success_rate = (success_count / (success_count + failure_count)) * 100
        print(f"\n✅ Overall Success Rate: {success_rate:.1f}%")
        
        # Success rate by timeframe
        if 'timeframe' in df_signals.columns:
            print(f"\nSuccess Rate by Timeframe:")
            for tf in ['Daily', 'Weekly']:
                tf_df = df_signals[df_signals['timeframe'] == tf]
                tf_success = (tf_df['outcome'] == 'SUCCESS').sum()
                tf_failure = (tf_df['outcome'] == 'FAILURE').sum()
                if tf_success + tf_failure > 0:
                    tf_rate = (tf_success / (tf_success + tf_failure)) * 100
                    print(f"  {tf}: {tf_rate:.1f}%")
        
        # Success rate by quality level
        if 'quality_level' in df_signals.columns:
            print(f"\nSuccess Rate by Quality Level:")
            for level in [4, 3, 2, 1]:
                level_df = df_signals[df_signals['quality_level'] == level]
                level_success = (level_df['outcome'] == 'SUCCESS').sum()
                level_failure = (level_df['outcome'] == 'FAILURE').sum()
                if level_success + level_failure > 0:
                    level_rate = (level_success / (level_success + level_failure)) * 100
                    level_name = {4: "✓*", 3: "*", 2: "✓", 1: "Basic"}[level]
                    print(f"  Level {level} ({level_name}): {level_rate:.1f}%")
    
    print(f"\nSaved to: {output_file}")
    print(f"{'='*80}\n")
    
    return df_signals


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Test
    print("TR Signal Scanner")
    print("=" * 80)
    print("\nThis scanner uses YOUR existing TR indicator code.")
    print("Make sure tr_indicator.py is in the same folder!\n")
