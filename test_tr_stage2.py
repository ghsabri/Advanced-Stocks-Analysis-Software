"""
TR Indicator Diagnostic Test
Run this to see what's actually happening with Stage 2 detection
"""

import sys
import os
sys.path.append('C:/Work/Stock Analysis Project/mj-stocks-analysis/src')

import pandas as pd
from tr_enhanced import analyze_stock_complete_tr

# Test with AAPL
print("="*80)
print("🔍 DIAGNOSTIC TEST - TR STAGE 2 DETECTION")
print("="*80)

ticker = 'AAPL'
print(f"\n📊 Analyzing {ticker}...")

df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if df is not None:
    print(f"\n✅ Got {len(df)} rows of data")
    
    # Check data types IN MEMORY (before CSV save)
    print("\n" + "="*80)
    print("📋 DATA TYPES IN MEMORY:")
    print("="*80)
    
    check_cols = ['Close', 'EMA_3', 'EMA_9', 'PPO_Line', 'PMO_Line']
    for col in check_cols:
        if col in df.columns:
            dtype = str(df[col].dtype)  # Convert to string!
            sample_val = df[col].iloc[-1]
            print(f"{col:15} | dtype: {dtype:10} | sample: {sample_val}")
    
    # Check TR Status distribution
    print("\n" + "="*80)
    print("📊 TR STATUS DISTRIBUTION:")
    print("="*80)
    
    status_counts = df['TR_Status'].value_counts()
    for status, count in status_counts.items():
        pct = (count / len(df)) * 100
        print(f"{status:20} | {count:4} occurrences ({pct:5.1f}%)")
    
    # Check if "Buy" or "Sell" appear
    has_buy = 'Buy' in status_counts and status_counts['Buy'] > 0
    has_sell = 'Sell' in status_counts and status_counts['Sell'] > 0
    
    print("\n" + "="*80)
    if has_buy:
        print("✅ STAGE 2 UPTREND ('Buy') FOUND!")
    else:
        print("❌ STAGE 2 UPTREND ('Buy') NOT FOUND")
    
    if has_sell:
        print("✅ STAGE 2 DOWNTREND ('Sell') FOUND!")
    else:
        print("❌ STAGE 2 DOWNTREND ('Sell') NOT FOUND")
    print("="*80)
    
    # Check a few Strong Buy rows to see if Stage 2 conditions were met
    print("\n" + "="*80)
    print("🔍 ANALYZING STRONG BUY ROWS:")
    print("="*80)
    
    strong_buy_rows = df[df['TR_Status'] == 'Strong Buy']
    if len(strong_buy_rows) > 0:
        print(f"\nFound {len(strong_buy_rows)} Strong Buy rows")
        print("\nChecking first Strong Buy occurrence:")
        
        first_sb = strong_buy_rows.iloc[0]
        print(f"\nDate: {first_sb['Date']}")
        print(f"Close: ${first_sb['Close']:.2f}")
        
        # Check Stage 2 conditions
        print("\nStage 2 Uptrend Conditions:")
        print(f"  PPO_Line > 0:           {first_sb['PPO_Line']} > 0 = {first_sb['PPO_Line'] > 0}")
        print(f"  PPO_Rising:             {first_sb.get('PPO_Rising', 'N/A')}")
        print(f"  EMA_34_Rising:          {first_sb.get('EMA_34_Rising', 'N/A')}")
        print(f"  PPO > PPO_Signal:       {first_sb['PPO_Line']} > {first_sb['PPO_Signal']} = {first_sb['PPO_Line'] > first_sb['PPO_Signal']}")
        print(f"  EMA_9 > EMA_20:         {first_sb['EMA_9']} > {first_sb['EMA_20']} = {first_sb['EMA_9'] > first_sb['EMA_20']}")
        
        # Check Stage 3 additional conditions
        print("\nStage 3 Additional Conditions:")
        print(f"  EMA_9_Rising:           {first_sb.get('EMA_9_Rising', 'N/A')}")
        print(f"  PMO_Line > 0:           {first_sb['PMO_Line']} > 0 = {first_sb['PMO_Line'] > 0}")
        
        # Check if all Stage 2 conditions met
        stage2_met = (
            first_sb['PPO_Line'] > 0 and
            first_sb.get('PPO_Rising', False) and
            first_sb.get('EMA_34_Rising', False) and
            first_sb['PPO_Line'] > first_sb['PPO_Signal'] and
            first_sb['EMA_9'] > first_sb['EMA_20']
        )
        
        print(f"\n📊 Stage 2 conditions met: {stage2_met}")
        
        if stage2_met:
            print("   ℹ️ If Stage 2 conditions are met but showing Strong Buy,")
            print("      then Stage 3 conditions are ALSO immediately met,")
            print("      causing it to skip 'Buy' and go straight to 'Strong Buy'")
    
    print("\n" + "="*80)
    print("💡 CONCLUSION:")
    print("="*80)
    
    if not has_buy and not has_sell:
        print("Stage 2 never appears because Stage 3 conditions")
        print("are immediately satisfied when Stage 2 conditions are met.")
        print("\nThis is either:")
        print("  1. By design (Stage 2 is very brief/rare)")
        print("  2. Stage 2 conditions are too easy to meet")
        print("  3. Stage 3 conditions need to be more restrictive")
    
else:
    print("❌ Could not get data for", ticker)

print("\n" + "="*80)
