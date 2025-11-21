from tr_enhanced import analyze_stock_complete_tr
import pandas as pd

ticker = 'hood'

print("\n🔍 DEBUGGING CHECKMARKS\n")

df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if df is not None:
    print("📊 Checking last 10 days for buy setup conditions:\n")
    print(f"{'Date':<12} {'Close':>8} {'TR':<12} {'Dist from Low':>15} {'Should Check?':>15}")
    print("-"*80)
    
    for i in range(len(df) - 10, len(df)):
        row = df.iloc[i]
        
        # Calculate distance from recent 20-day low
        lookback = 20
        start = max(0, i - lookback)
        recent_low = df.iloc[start:i+1]['Low'].min()
        
        current_price = row['Close']
        distance = ((current_price - recent_low) / recent_low) * 100 if recent_low > 0 else 0
        
        # Check if should have checkmark
        in_uptrend = row['TR_Status'] in ['Buy', 'Strong Buy']
        near_support = 0 <= distance <= 5
        should_check = in_uptrend and near_support
        
        check_symbol = "✓" if should_check else " "
        
        print(f"{row['Date']:<12} ${current_price:>7.2f} {row['TR_Status']:<12} {distance:>14.1f}% {check_symbol:>15}")
    
    print("\n💡 If 'Should Check?' shows ✓ but actual status doesn't, then function isn't working properly")

print()