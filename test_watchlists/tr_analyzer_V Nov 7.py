import pandas as pd
import os
from stock_data_formatter import get_stock_data_formatted
from tr_indicator import analyze_tr_indicator


def analyze_stock_tr(ticker, timeframe='daily', duration_days=180):
    """
    Analyze a stock's TR indicator
    
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
        dict: TR analysis results
    """
    
    print(f"\n{'='*80}")
    print(f"🔍 ANALYZING {ticker} - TR INDICATOR")
    print(f"{'='*80}")
    print(f"Timeframe: {timeframe.capitalize()}")
    print(f"Duration: {duration_days} days (~{duration_days//30} months)")
    print(f"{'='*80}\n")
    
    # Fetch stock data
    df = get_stock_data_formatted(ticker, timeframe=timeframe, days=duration_days, save=False)
    
    if df is None or df.empty:
        print(f"❌ No data available for {ticker}")
        return None
    
    # Run TR analysis
    print(f"📊 Calculating TR indicators...")
    df_with_tr = analyze_tr_indicator(df)
    
    # Get most recent status
    latest = df_with_tr.iloc[-1]
    
    # Count signal occurrences in the period
    signal_counts = df_with_tr['TR_Status'].value_counts()
    
    # Get recent signals (last 10 days)
    recent_signals = df_with_tr.tail(10)[['Date', 'Close', 'TR_Status']]
    
    # Create result summary
    result = {
        'ticker': ticker,
        'timeframe': timeframe,
        'latest_date': latest['Date'],
        'latest_close': latest['Close'],
        'latest_tr_status': latest['TR_Status'],
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
    
    # Color-code the status
    status = result['latest_tr_status']
    if status == "Strong Buy":
        print(f"   Status: 🟢 {status} (Stage 3 Uptrend)")
    elif status == "Buy":
        print(f"   Status: 🟢 {status} (Stage 2 Uptrend)")
    elif status == "Neutral Buy":
        print(f"   Status: 🟡 {status} (Stage 1 Uptrend)")
    elif status == "Neutral Sell":
        print(f"   Status: 🟡 {status} (Stage 1 Downtrend)")
    elif status == "Sell":
        print(f"   Status: 🔴 {status} (Stage 2 Downtrend)")
    elif status == "Strong Sell":
        print(f"   Status: 🔴 {status} (Stage 3 Downtrend)")
    else:
        print(f"   Status: ⚪ {status}")
    
    # Signal distribution
    print(f"\n📈 SIGNAL DISTRIBUTION (Last {len(result['full_data'])} days):")
    print("-"*80)
    
    signal_order = ["Strong Buy", "Buy", "Neutral Buy", "Neutral", "Neutral Sell", "Sell", "Strong Sell"]
    counts = result['signal_counts']
    
    for signal in signal_order:
        count = counts.get(signal, 0)
        if count > 0:
            percentage = (count / len(result['full_data'])) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {signal:<15} │ {count:>3} days ({percentage:>5.1f}%) {bar}")
    
    # Recent signals
    print(f"\n📅 RECENT SIGNALS (Last 10 days):")
    print("-"*80)
    print(f"{'Date':<12} {'Close':>10} {'TR Status':<20}")
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
        }.get(row['TR_Status'], "⚪")
        
        print(f"{row['Date']:<12} ${row['Close']:>9.2f} {status_symbol} {row['TR_Status']:<20}")
    
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
    print(f"🚀 ANALYZING {len(tickers)} STOCKS - TR INDICATOR")
    print("="*80)
    
    for ticker in tickers:
        result = analyze_stock_tr(ticker, timeframe, duration_days)
        if result:
            results[ticker] = result
    
    # Summary comparison
    print("\n" + "="*80)
    print("📊 SUMMARY - ALL STOCKS")
    print("="*80)
    print(f"{'Ticker':<10} {'Price':>10} {'TR Status':<20} {'Signal':<10}")
    print("-"*80)
    
    for ticker, result in results.items():
        status = result['latest_tr_status']
        price = result['latest_close']
        
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
    filename = f"{output_folder}/{ticker}_{timeframe.capitalize()}_TR.csv"
    
    df = result['full_data']
    
    # Select relevant columns
    output_columns = [
        'Symbol', 'TimeFrame', 'Date', 'Close', 
        'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34',
        'PPO_Line', 'PPO_Signal', 
        'PMO_Line', 'PMO_Signal',
        'TR_Status'
    ]
    
    df_output = df[output_columns]
    df_output.to_csv(filename, index=False)
    
    print(f"✅ Saved TR results to: {filename}")
    
    return filename


# MAIN EXECUTION FOR TESTING
if __name__ == "__main__":
    
    print("\n🚀 TR INDICATOR ANALYZER - TEST")
    print("="*80)
    
    # Test 1: Analyze single stock
    print("\n📈 TEST 1: Analyze AAPL (6 months, Daily)")
    print("-"*80)
    aapl_result = analyze_stock_tr('AAPL', timeframe='daily', duration_days=180)
    
    if aapl_result:
        # Save results
        save_tr_results(aapl_result)
    
    # Test 2: Analyze multiple stocks
    print("\n\n📈 TEST 2: Analyze Multiple Stocks")
    print("-"*80)
    
    tickers = ['AAPL', 'MSFT', 'TSLA']
    results = analyze_multiple_stocks(tickers, timeframe='daily', duration_days=180)
    
    # Save all results
    for ticker, result in results.items():
        save_tr_results(result)
    
    print("\n✅ TR INDICATOR TESTING COMPLETE!")
    print("="*80)
    print("\n💡 Check your '../data' folder (parent directory) for TR results CSV files!")
