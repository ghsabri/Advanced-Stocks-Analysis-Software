from tr_enhanced import analyze_stock_complete_tr
import pandas as pd
import numpy as np

ticker = 'UBER'

print("\n" + "="*80)
print(f"🎯 COMPLETE TR TRADING SYSTEM TEST: {ticker}")
print("="*80 + "\n")

df = analyze_stock_complete_tr(ticker, timeframe='daily', duration_days=180)

if df is not None:
    print("📊 LAST 15 DAYS - COMPLETE ANALYSIS:\n")
    print(f"{'Date':<12} {'Close':>8} {'Buy Pt':>8} {'Stop':>8} {'Zone':>10} {'Dist':>7} {'TR':<12} {'Signals':<20}")
    print("-"*100)
    
    for _, row in df.tail(15).iterrows():
        close = row['Close']
        buy_point = row.get('Buy_Point', np.nan)
        stop_loss = row.get('Stop_Loss', np.nan)
        in_zone = row.get('In_Buy_Zone', False)
        distance = row.get('Distance_From_BP', np.nan)
        tr_status = row['TR_Status']
        
        # Zone status with color
        if in_zone:
            zone_str = "🟢 IN ZONE"
        else:
            if pd.notna(distance):
                if distance > 5:
                    zone_str = "⬆️ Above"
                elif distance < -5:
                    zone_str = "⬇️ Below"
                else:
                    zone_str = "⚪ Near"
            else:
                zone_str = "⚪ N/A"
        
        # Distance string
        if pd.notna(distance):
            dist_str = f"{distance:+6.1f}%"
        else:
            dist_str = "N/A"
        
        # Collect signals
        signals = []
        if '✓' in row.get('TR_Status_Enhanced', ''):
            signals.append("✓Setup")
        if row.get('Buy_Signal', False):
            signals.append("🔵BUY")
        if row.get('Exit_Signal', False):
            signals.append("🔴EXIT")
            if row.get('Exit_Reason'):
                signals.append(f"({row['Exit_Reason'][:10]})")
        
        signal_str = " ".join(signals) if signals else ""
        
        # Check if at stop loss
        if pd.notna(stop_loss) and close <= stop_loss:
            signal_str = "🛑 AT STOP!" if not signal_str else signal_str + " 🛑"
        
        if pd.notna(buy_point):
            print(f"{row['Date']:<12} ${close:>7.2f} ${buy_point:>7.2f} ${stop_loss:>7.2f} {zone_str:<10} {dist_str:>7} {tr_status:<12} {signal_str:<20}")
        else:
            print(f"{row['Date']:<12} ${close:>7.2f} {'N/A':>7} {'N/A':>7} {zone_str:<10} {dist_str:>7} {tr_status:<12} {signal_str:<20}")
    
    # Risk/Reward Analysis
    print("\n" + "="*80)
    print("💰 RISK/REWARD ANALYSIS:")
    print("="*80)
    
    latest = df.iloc[-1]
    
    if pd.notna(latest['Buy_Point']) and pd.notna(latest['Stop_Loss']):
        buy_pt = latest['Buy_Point']
        stop = latest['Stop_Loss']
        current = latest['Close']
        
        risk_amount = buy_pt - stop
        risk_pct = (risk_amount / buy_pt) * 100
        
        # Calculate potential reward (assume 15% target)
        target_pct = 15.0
        target_price = buy_pt * (1 + target_pct / 100)
        reward_amount = target_price - buy_pt
        
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        print(f"\n   Buy Point:        ${buy_pt:.2f}")
        print(f"   Stop Loss:        ${stop:.2f}")
        print(f"   Current Price:    ${current:.2f}")
        print(f"   Target (15%):     ${target_price:.2f}")
        print(f"\n   Risk per share:   ${risk_amount:.2f} ({risk_pct:.1f}%)")
        print(f"   Reward per share: ${reward_amount:.2f} ({target_pct:.1f}%)")
        print(f"   Risk/Reward:      1:{risk_reward_ratio:.2f}")
        
        if risk_reward_ratio >= 2.0:
            print(f"\n   ✅ Good risk/reward (1:2 or better)")
        else:
            print(f"\n   ⚠️  Low risk/reward (less than 1:2)")
    
    # Trading Status
    print("\n" + "="*80)
    print("📍 CURRENT TRADING STATUS:")
    print("="*80)
    
    print(f"\n   Price:         ${latest['Close']:.2f}")
    if pd.notna(latest['Buy_Point']):
        print(f"   Buy Point:     ${latest['Buy_Point']:.2f}")
        print(f"   Buy Zone:      ${latest['Buy_Zone_Lower']:.2f} - ${latest['Buy_Zone_Upper']:.2f}")
        print(f"   Stop Loss:     ${latest['Stop_Loss']:.2f}")
        print(f"   Distance:      {latest['Distance_From_BP']:+.1f}%")
    else:
        print(f"   Buy Point:     Not established yet")
    
    print(f"   In Buy Zone:   {'✅ YES' if latest['In_Buy_Zone'] else '❌ NO'}")
    print(f"   TR Status:     {latest['TR_Status_Enhanced']}")
    
    # Action recommendation
    print(f"\n   📋 ACTION:")
    
    if latest.get('Buy_Signal', False):
        print(f"      🔵 BUY NOW!")
        print(f"         Entry: ${latest['Close']:.2f}")
        print(f"         Stop:  ${latest['Stop_Loss']:.2f}")
    elif latest.get('Exit_Signal', False):
        print(f"      🔴 EXIT POSITION!")
        print(f"         Reason: {latest.get('Exit_Reason', 'Exit signal triggered')}")
    elif latest['In_Buy_Zone'] and latest['TR_Status'] in ['Buy', 'Strong Buy']:
        print(f"      ✅ READY - In buy zone with uptrend")
        print(f"         Can enter at current price")
    elif latest['In_Buy_Zone']:
        print(f"      🟡 WAIT - In zone but need Stage 2/3 confirmation")
    elif latest['TR_Status'] in ['Buy', 'Strong Buy']:
        print(f"      🟡 WAIT - In uptrend but outside buy zone")
        print(f"         Wait for pullback to ${latest['Buy_Zone_Lower']:.2f}")
    else:
        print(f"      ⚪ NO SETUP - Not a buy opportunity yet")
    
    # Summary stats
    print("\n" + "="*80)
    print("📈 OVERALL STATISTICS:")
    print("="*80)
    
    buy_signal_count = df['Buy_Signal'].sum()
    exit_signal_count = df['Exit_Signal'].sum()
    days_in_zone = df['In_Buy_Zone'].sum()
    checkmark_count = (df['TR_Status_Enhanced'].str.contains('✓', na=False)).sum()
    
    print(f"\n   Total days analyzed:  {len(df)}")
    print(f"   Days in buy zone:     {days_in_zone}")
    print(f"   Checkmarks shown:     {checkmark_count}")
    print(f"   Buy signals:          {buy_signal_count}")
    print(f"   Exit signals:         {exit_signal_count}")

print("\n" + "="*80)