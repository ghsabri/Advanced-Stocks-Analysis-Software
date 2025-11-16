from tr_enhanced import analyze_stock_complete_tr

ticker = 'IBM'

print("\n" + "="*80)
print(f"🔍 TESTING ARROWS & CHECKMARKS: {ticker}")
print("="*80 + "\n")

# Analyze with full TR
df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if df is not None:
    print(f"📊 DATA LOADED: {len(df)} days")
    print(f"\n{'='*80}")
    print("CHECKING LAST 20 DAYS FOR ARROWS & CHECKMARKS:")
    print("="*80)
    print(f"\n{'Date':<12} {'Close':>8} {'TR_Status':<20} {'Enhanced':<30}")
    print("-"*80)
    
    for _, row in df.tail(20).iterrows():
        base_status = row['TR_Status']
        enhanced_status = row['TR_Status_Enhanced']
        
        # Check for symbols
        has_arrow_up = '↑' in enhanced_status
        has_arrow_down = '↓' in enhanced_status
        has_check = '✓' in enhanced_status
        has_star = '*' in enhanced_status
        
        indicators = []
        if has_arrow_up:
            indicators.append("↑")
        if has_arrow_down:
            indicators.append("↓")
        if has_check:
            indicators.append("✓")
        if has_star:
            indicators.append("*")
        
        indicator_str = " ".join(indicators) if indicators else "none"
        
        print(f"{row['Date']:<12} ${row['Close']:>7.2f} {base_status:<20} {indicator_str:<10} {enhanced_status}")
    
    print("\n" + "="*80)
    
    # Count occurrences
    arrow_up_count = (df['TR_Status_Enhanced'].str.contains('↑', na=False)).sum()
    arrow_down_count = (df['TR_Status_Enhanced'].str.contains('↓', na=False)).sum()
    check_count = (df['TR_Status_Enhanced'].str.contains('✓', na=False)).sum()
    star_count = (df['TR_Status_Enhanced'].str.contains('\*', regex=True, na=False)).sum()
    
    print("\n📈 SYMBOL COUNTS (in entire dataset):")
    print(f"   ↑ Arrows Up:    {arrow_up_count}")
    print(f"   ↓ Arrows Down:  {arrow_down_count}")
    print(f"   ✓ Checkmarks:   {check_count}")
    print(f"   * Stars:        {star_count}")
    
    if arrow_up_count == 0 and arrow_down_count == 0:
        print(f"\n   ❌ NO ARROWS FOUND - Function may not be working!")
    else:
        print(f"\n   ✅ Arrows are working!")
    
    if check_count == 0:
        print(f"   ❌ NO CHECKMARKS FOUND - Function may not be working!")
    else:
        print(f"   ✅ Checkmarks are working!")
    
    # Debug: Check if enhancement function is being called
    print(f"\n🔧 DEBUG INFO:")
    print(f"   'TR_Status_Enhanced' column exists: {'TR_Status_Enhanced' in df.columns}")
    print(f"   Sample enhanced status: {df.iloc[-1]['TR_Status_Enhanced']}")
    
    # Check if base TR_Status is different from enhanced
    different = df['TR_Status'] != df['TR_Status_Enhanced']
    diff_count = different.sum()
    print(f"   Rows where enhanced differs from base: {diff_count}/{len(df)}")
    
    if diff_count == 0:
        print(f"\n   ⚠️  WARNING: TR_Status_Enhanced is identical to TR_Status!")
        print(f"   Enhancement functions may not be running!")

print("\n" + "="*80)