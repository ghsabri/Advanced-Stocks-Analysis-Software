from tr_enhanced import analyze_stock_complete_tr, display_complete_tr_summary

print("\n🚀 TESTING COMPLETE TR INDICATOR")
print("="*80)

# Test on AAPL
ticker = 'AAPL'
print(f"\n📈 Analyzing {ticker}...")

df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if df is not None:
    # Display summary
    display_complete_tr_summary(df, ticker)
    
    # Save to CSV
    filename = f"data/{ticker}_Complete_TR.csv"
    
    # Select columns to save
    save_columns = [
        'Symbol', 'TimeFrame', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
        'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34',
        'PPO_Line', 'PPO_Signal', 'PMO_Line', 'PMO_Signal',
        'TR_Status', 'TR_Status_Enhanced',
        'RS', 'Chaikin_AD',
        'Peak', 'Valley',
        'Buy_Point', 'Stop_Loss',
        'Buy_Signal', 'Exit_Signal'
    ]
    
    df[save_columns].to_csv(filename, index=False)
    print(f"✅ Saved complete TR data to: {filename}")
    
    # Show last 10 days with enhanced status
    print(f"\n📅 LAST 10 DAYS:")
    print("-"*80)
    recent = df.tail(10)[['Date', 'Close', 'TR_Status_Enhanced', 'Buy_Signal', 'Exit_Signal']]
    for _, row in recent.iterrows():
        signals = ""
        if row['Buy_Signal']:
            signals += " 🔵"
        if row['Exit_Signal']:
            signals += " 🔴"
        print(f"{row['Date']}: ${row['Close']:.2f} - {row['TR_Status_Enhanced']}{signals}")

print("\n✅ COMPLETE TR TESTING FINISHED!")
print("="*80)