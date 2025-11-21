from tr_enhanced import analyze_stock_complete_tr, display_complete_tr_summary

ticker = 'AAPL'

print("\n" + "="*80)
print(f"📊 TIMEFRAME COMPARISON: {ticker}")
print("="*80 + "\n")

# DAILY Analysis
print("📈 DAILY TIMEFRAME (6 months):")
print("-"*80)
daily_df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if daily_df is not None:
    daily_latest = daily_df.iloc[-1]
    print(f"\n   Latest Daily TR: {daily_latest['TR_Status_Enhanced']}")
    print(f"   RS: {daily_latest['RS']:.1f}% | Chaikin: {daily_latest['Chaikin_AD']:.1f}%")
    
    # Count signals
    daily_buy_count = daily_df['Buy_Signal'].sum()
    daily_exit_count = daily_df['Exit_Signal'].sum()
    print(f"   Buy Signals: {daily_buy_count} | Exit Signals: {daily_exit_count}")

print("\n" + "="*80 + "\n")

# WEEKLY Analysis
print("📈 WEEKLY TIMEFRAME (2 years):")
print("-"*80)
weekly_df = analyze_stock_complete_tr(ticker, timeframe='weekly', duration_days=730)

if weekly_df is not None:
    weekly_latest = weekly_df.iloc[-1]
    print(f"\n   Latest Weekly TR: {weekly_latest['TR_Status_Enhanced']}")
    print(f"   RS: {weekly_latest['RS']:.1f}% | Chaikin: {weekly_latest['Chaikin_AD']:.1f}%")
    
    # Count signals
    weekly_buy_count = weekly_df['Buy_Signal'].sum()
    weekly_exit_count = weekly_df['Exit_Signal'].sum()
    print(f"   Buy Signals: {weekly_buy_count} | Exit Signals: {weekly_exit_count}")

print("\n" + "="*80)

# Comparison
print("\n💡 TIMEFRAME INSIGHTS:")
print("-"*80)

if daily_df is not None and weekly_df is not None:
    print(f"\n   DAILY:  {daily_latest['TR_Status']}")
    print(f"   WEEKLY: {weekly_latest['TR_Status']}")
    
    if daily_latest['TR_Status'] == weekly_latest['TR_Status']:
        print(f"\n   ✅ ALIGNED: Both timeframes show {daily_latest['TR_Status']}")
        print(f"   → Strong confirmation!")
    else:
        print(f"\n   ⚠️  DIVERGENCE: Different signals on different timeframes")
        print(f"   → Weekly trend = Primary direction")
        print(f"   → Daily trend = Entry/exit timing")

print("\n" + "="*80)