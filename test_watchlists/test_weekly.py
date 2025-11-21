from tr_enhanced import analyze_stock_complete_tr, display_complete_tr_summary

# Analyze AAPL with WEEKLY timeframe
ticker = 'AAPL'
timeframe = 'weekly'  # ← KEY: Change to 'weekly'
duration_days = 730    # 2 years of data (104 weeks)

print(f"\n{'='*80}")
print(f"📊 WEEKLY TR ANALYSIS: {ticker}")
print(f"{'='*80}\n")

df = analyze_stock_complete_tr(
    ticker=ticker,
    timeframe=timeframe,      # 'weekly' instead of 'daily'
    duration_days=duration_days,
    market_ticker='SPY'
)

if df is not None:
    # Display summary
    display_complete_tr_summary(df, ticker)
    
    # Save to CSV
    filename = f"data/{ticker}_Weekly_Complete_TR.csv"
    
    save_columns = [
        'Symbol', 'TimeFrame', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
        'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34',
        'TR_Status', 'TR_Status_Enhanced',
        'RS', 'Chaikin_AD',
        'Peak', 'Valley',
        'Buy_Point', 'Stop_Loss',
        'Buy_Signal', 'Exit_Signal'
    ]
    
    df[save_columns].to_csv(filename, index=False)
    print(f"\n✅ Saved weekly TR data to: {filename}")
    
    # Show last 10 weeks
    print(f"\n📅 LAST 10 WEEKS:")
    print("-"*80)
    recent = df.tail(10)[['Date', 'Close', 'TR_Status_Enhanced']]
    for _, row in recent.iterrows():
        print(f"{row['Date']}: ${row['Close']:>7.2f} - {row['TR_Status_Enhanced']}")

print("\n✅ WEEKLY ANALYSIS COMPLETE!")