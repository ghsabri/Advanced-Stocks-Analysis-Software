import pandas as pd
import os
from stock_data_formatter import get_stock_data_formatted
from tr_enhanced import analyze_stock_complete_tr  # CHANGED: Use enhanced version!


def analyze_stock_tr(ticker, timeframe='daily', duration_days=180):
    """
    Analyze a stock's TR indicator with ENHANCED signals (arrows, checkmarks, asterisks)
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL')
        timeframe (str): 'daily' or 'weekly'
        duration_days (int): How many days of history
            - 90 days = 3 months
            - 180 days = 6 months
            - 365 days = 1 year
            - 1095 days = 3 years
            - 1825 days = 5 years
    
    Returns:
        dict: TR analysis results with enhanced signals
    """
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALYZING {ticker} - TR INDICATOR (ENHANCED)")
    print(f"{'='*80}")
    print(f"Timeframe: {timeframe.capitalize()}")
    print(f"Duration: {duration_days} days (~{duration_days//30} months)")
    print(f"{'='*80}\n")
    
    # Use the enhanced TR analysis function
    print(f"📊 Calculating ENHANCED TR indicators (with arrows, checkmarks, asterisks)...")
    df_with_tr = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe=timeframe,
        duration_days=duration_days
    )
    
    if df_with_tr is None or df_with_tr.empty:
        print(f"❌ No data available for {ticker}")
        return None
    
    # Get most recent status
    latest = df_with_tr.iloc[-1]
    
    # Use enhanced status if available, otherwise fall back to basic
    if 'TR_Status_Enhanced' in df_with_tr.columns:
        latest_status = latest['TR_Status_Enhanced']
        status_column = 'TR_Status_Enhanced'
    else:
        latest_status = latest['TR_Status']
        status_column = 'TR_Status'
    
    # Count signal occurrences in the period
    signal_counts = df_with_tr[status_column].value_counts()
    
    # Get recent signals (last 10 days)
    recent_columns = ['Date', 'Close', status_column]
    recent_signals = df_with_tr.tail(10)[recent_columns].copy()
    recent_signals = recent_signals.rename(columns={status_column: 'TR_Status'})
    
    # Create result summary
    result = {
        'ticker': ticker,
        'timeframe': timeframe,
        'latest_date': latest['Date'],
        'latest_close': latest['Close'],
        'latest_tr_status': latest_status,  # This now includes arrows/checkmarks!
        'signal_counts': signal_counts.to_dict(),
        'recent_signals': recent_signals,
        'full_data': df_with_tr
    }
    
    # Display results
    display_tr_results(result)
    
    return result


def display_tr_results(result):
    """
    Display TR analysis results in a nice format
    
    Args:
        result (dict): TR analysis results
    """
    
    print("\n" + "="*80)
    print(f"📊 TR ANALYSIS RESULTS - {result['ticker']}")
    print("="*80)
    
    # Latest status
    print(f"\n🎯 CURRENT TR STATUS:")
    print(f"   Date:   {result['latest_date']}")
    print(f"   Price:  ${result['latest_close']:.2f}")
    
    # Display enhanced status with color coding
    status = result['latest_tr_status']
    if "Strong Buy" in status:
        print(f"   Status: 🟢 {status} (Stage 3 Uptrend)")
    elif "Buy" in status and "Strong" not in status:
        print(f"   Status: 🟢 {status} (Stage 2 Uptrend)")
    elif "Neutral Buy" in status:
        print(f"   Status: 🟡 {status} (Stage 1 Uptrend)")
    elif "Neutral Sell" in status:
        print(f"   Status: 🟡 {status} (Stage 1 Downtrend)")
    elif "Sell" in status and "Strong" not in status:
        print(f"   Status: 🔴 {status} (Stage 2 Downtrend)")
    elif "Strong Sell" in status:
        print(f"   Status: 🔴 {status} (Stage 3 Downtrend)")
    else:
        print(f"   Status: ⚪ {status}")
    
    # Signal distribution
    print(f"\n📈 SIGNAL DISTRIBUTION (Last {len(result['full_data'])} days):")
    print("-"*80)
    
    counts = result['signal_counts']
    total_days = len(result['full_data'])
    
    # Sort by count descending
    for signal, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_days) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {signal:<25} │ {count:>3} days ({percentage:>5.1f}%) {bar}")
    
    # Recent signals
    print(f"\n📅 RECENT SIGNALS (Last 10 days):")
    print("-"*80)
    print(f"{'Date':<12} {'Close':>10} {'TR Status':<30}")
    print("-"*80)
    
    for _, row in result['recent_signals'].iterrows():
        status_symbol = {
            "Strong Buy": "🟢",
            "Buy": "🟢",
            "Neutral Buy": "🟡",
            "Neutral": "⚪",
            "Neutral Sell": "🟡",
            "Sell": "🔴",
            "Strong Sell": "🔴"
        }
        
        # Get symbol based on base status (without arrows/checkmarks)
        base_status = row['TR_Status'].split()[0:2]  # Get first two words
        base_status_str = ' '.join(base_status)
        symbol = status_symbol.get(base_status_str, "⚪")
        
        # Handle cases where status might have more words
        for key in status_symbol.keys():
            if key in row['TR_Status']:
                symbol = status_symbol[key]
                break
        
        print(f"{row['Date']:<12} ${row['Close']:>9.2f} {symbol} {row['TR_Status']:<30}")
    
    print("="*80 + "\n")


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
    print(f"🚀 ANALYZING {len(tickers)} STOCKS - TR INDICATOR (ENHANCED)")
    print("="*80)
    
    for ticker in tickers:
        result = analyze_stock_tr(ticker, timeframe, duration_days)
        if result:
            results[ticker] = result
    
    # Summary comparison
    print("\n" + "="*80)
    print("📊 SUMMARY - ALL STOCKS")
    print("="*80)
    print(f"{'Ticker':<10} {'Price':>10} {'TR Status':<35}")
    print("-"*80)
    
    for ticker, result in results.items():
        status = result['latest_tr_status']
        price = result['latest_close']
        
        status_symbol = "⚪"
        if "Strong Buy" in status:
            status_symbol = "🟢"
        elif "Buy" in status:
            status_symbol = "🟢"
        elif "Neutral Buy" in status:
            status_symbol = "🟡"
        elif "Neutral Sell" in status:
            status_symbol = "🟡"
        elif "Sell" in status:
            status_symbol = "🔴"
        
        print(f"{ticker:<10} ${price:>9.2f} {status_symbol} {status:<33}")
    
    print("="*80 + "\n")
    
    return results


def save_tr_results(result, output_folder='../data'):
    """
    Save TR analysis results to CSV
    
    Args:
        result (dict): TR analysis results
        output_folder (str): Folder to save results (default: '../data' - parent directory)
    """
    
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created output folder: {output_folder}")
    
    ticker = result['ticker']
    timeframe = result['timeframe']
    
    # Save full data with TR status
    filename = f"{output_folder}/{ticker}_{timeframe.capitalize()}_TR_Enhanced.csv"
    
    df = result['full_data']
    
    # Save all columns
    df.to_csv(filename, index=False)
    
    print(f"✅ Saved ENHANCED TR results to: {filename}")
    
    return filename


# MAIN EXECUTION FOR TESTING
if __name__ == "__main__":
    
    print("\n🚀 TR INDICATOR ANALYZER (ENHANCED) - TEST")
    print("="*80)
    
    # Test: Analyze single stock with enhanced signals
    print("\n📈 TEST: Analyze AAPL with Enhanced TR Signals")
    print("-"*80)
    aapl_result = analyze_stock_tr('AAPL', timeframe='daily', duration_days=180)
    
    if aapl_result:
        # Save results
        save_tr_results(aapl_result)
        
        print("\n✨ Enhanced features included:")
        print("   ↑ Up arrows for bullish signals")
        print("   ↓ Down arrows for bearish signals")
        print("   ✓ Checkmarks for good setups")
        print("   ✗ X marks for bad setups")
        print("   * Asterisks for special conditions")
    
    print("\n✅ ENHANCED TR INDICATOR TESTING COMPLETE!")
    print("="*80)
    print("\n💡 Check your '../data' folder for TR results with enhanced signals!")
