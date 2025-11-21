from tr_enhanced import analyze_stock_complete_tr

ticker = 'AAPL'

print("\n" + "="*80)
print(f"🧪 TESTING RS ACROSS TIMEFRAMES: {ticker}")
print("="*80 + "\n")

# Test DAILY
print("📊 DAILY TIMEFRAME:")
print("-"*80)
daily_df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=365)

if daily_df is not None:
    daily_rs = daily_df.iloc[-1]['RS']
    daily_ad = daily_df.iloc[-1]['Chaikin_AD']
    
    print(f"   Latest RS:       {daily_rs:.1f}%")
    print(f"   Latest Chaikin:  {daily_ad:.1f}%")
    print(f"   Data Points:     {len(daily_df)}")
    print(f"   Period Used:     252 days (1 year)")

print("\n" + "="*80 + "\n")

# Test WEEKLY
print("📊 WEEKLY TIMEFRAME:")
print("-"*80)
weekly_df = analyze_stock_complete_tr(ticker, timeframe='weekly', duration_days=730)

if weekly_df is not None:
    weekly_rs = weekly_df.iloc[-1]['RS']
    weekly_ad = weekly_df.iloc[-1]['Chaikin_AD']
    
    print(f"   Latest RS:       {weekly_rs:.1f}%")
    print(f"   Latest Chaikin:  {weekly_ad:.1f}%")
    print(f"   Data Points:     {len(weekly_df)}")
    print(f"   Period Used:     52 weeks (1 year)")

print("\n" + "="*80)

# Comparison
if daily_df is not None and weekly_df is not None:
    print("\n💡 COMPARISON:")
    print("-"*80)
    print(f"   Daily RS:   {daily_rs:.1f}%  {'🟢' if daily_rs >= 80 else '🟡' if daily_rs >= 50 else '🔴'}")
    print(f"   Weekly RS:  {weekly_rs:.1f}%  {'🟢' if weekly_rs >= 80 else '🟡' if weekly_rs >= 50 else '🔴'}")
    
    rs_diff = abs(daily_rs - weekly_rs)
    
    if rs_diff <= 10:
        print(f"\n   ✅ ALIGNED: Both timeframes show similar strength")
    elif rs_diff <= 20:
        print(f"\n   ⚠️  MODERATE DIVERGENCE: {rs_diff:.1f}% difference")
    else:
        print(f"\n   ❌ MAJOR DIVERGENCE: {rs_diff:.1f}% difference")
        print(f"      → Check for recent trend changes")

print("\n" + "="*80)