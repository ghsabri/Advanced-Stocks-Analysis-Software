from tr_enhanced import analyze_stock_complete_tr

# Stocks to analyze
tickers = ['HOOD', 'UBER', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']

print("\n" + "="*80)
print("🔍 WEEKLY TR SCANNER - MULTIPLE STOCKS")
print("="*80 + "\n")

results = []

for ticker in tickers:
    print(f"📊 Analyzing {ticker}...")
    
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe='weekly',
        duration_days=730
    )
    
    if df is not None:
        latest = df.iloc[-1]
        
        results.append({
            'Ticker': ticker,
            'Price': latest['Close'],
            'TR_Status': latest['TR_Status'],
            'Enhanced': latest['TR_Status_Enhanced'],
            'RS': latest['RS'],
            'Chaikin': latest['Chaikin_AD']
        })
        
        # Save individual file
        filename = f"data/{ticker}_Weekly_Complete_TR.csv"
        save_cols = ['Symbol', 'TimeFrame', 'Date', 'Close', 'TR_Status', 'TR_Status_Enhanced', 'RS', 'Chaikin_AD']
        df[save_cols].to_csv(filename, index=False)
    
    print()

# Display summary
print("\n" + "="*80)
print("📊 WEEKLY SCANNER RESULTS")
print("="*80)
print(f"\n{'Ticker':<8} {'Price':>10} {'TR Status':<20} {'RS':>6} {'Chaikin':>8}")
print("-"*80)

for r in results:
    # Add emoji
    if 'Strong Buy' in r['TR_Status']:
        emoji = '🟢🟢'
    elif 'Buy' in r['TR_Status']:
        emoji = '🟢'
    elif 'Sell' in r['TR_Status']:
        emoji = '🔴'
    else:
        emoji = '⚪'
    
    # Add star if strong
    star = '*' if r['RS'] >= 95 and r['Chaikin'] >= 95 else ' '
    
    print(f"{r['Ticker']:<8} ${r['Price']:>9.2f} {emoji} {r['TR_Status']:<17} {r['RS']:>5.1f}% {r['Chaikin']:>7.1f}% {star}")

print("="*80)

# Filter for strong stocks
strong_stocks = [r for r in results if r['RS'] >= 95 and r['Chaikin'] >= 95]

if strong_stocks:
    print(f"\n⭐ MARKET LEADERS (RS & Chaikin ≥ 95%):")
    for r in strong_stocks:
        print(f"   {r['Ticker']}: {r['TR_Status']}")

# Filter for buy signals
buy_candidates = [r for r in results if 'Buy' in r['TR_Status'] and 'Sell' not in r['TR_Status']]

if buy_candidates:
    print(f"\n🟢 BUY CANDIDATES:")
    for r in buy_candidates:
        print(f"   {r['Ticker']}: ${r['Price']:.2f} - {r['TR_Status']}")

print("\n✅ WEEKLY SCAN COMPLETE!")
print("="*80)