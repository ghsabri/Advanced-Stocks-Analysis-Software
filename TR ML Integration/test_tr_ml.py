# TR ML PREDICTOR TEST SCRIPT

"""
Quick test to verify ml_tr_predictor.py works correctly
Run this BEFORE integrating into main app
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'C:\\Work\\Stock Analysis Project\\mj-stocks-analysis\\src')

from ml_tr_predictor import predict_tr_confidence, load_models

print("="*80)
print("TR ML PREDICTOR - VERIFICATION TEST")
print("="*80)
print()

# Test 1: Load Models
print("TEST 1: Loading ML Models...")
print("-" * 80)
try:
    models = load_models()
    if models.get('daily'):
        print("✅ Daily model loaded successfully")
    else:
        print("⚠️ Daily model not found")
    
    if models.get('weekly'):
        print("✅ Weekly model loaded successfully")
    else:
        print("⚠️ Weekly model not found")
    print()
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    print()

# Test 2: Strong Buy Signal (TR Stage 1)
print("TEST 2: Strong Buy Signal (TR Stage 1)")
print("-" * 80)
signal_buy = {
    'tr_stage': 1,
    'entry_price': 150.50,
    'ema_13': 148.20,
    'ema_30': 145.80,
    'ema_50': 144.00,
    'ema_200': 140.00,
    'rsi': 35.5,
    'volume_ratio': 1.8,
    'atr': 3.5,
    'trend_strength': 75,
    'timeframe': 'Daily'
}

try:
    prediction = predict_tr_confidence(signal_buy)
    print(f"✅ Prediction successful!")
    print(f"   Confidence: {prediction['confidence_pct']}%")
    print(f"   Level: {prediction['confidence_level']}")
    print(f"   Expected: {prediction['expected_outcome']}")
    print(f"   Model: {prediction['model_used']}")
    print()
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    print()

# Test 3: Strong Sell Signal (TR Stage 6)
print("TEST 3: Strong Sell Signal (TR Stage 6)")
print("-" * 80)
signal_sell = {
    'tr_stage': 6,
    'entry_price': 150.50,
    'ema_13': 152.80,
    'ema_30': 155.20,
    'ema_50': 157.00,
    'ema_200': 160.00,
    'rsi': 72.5,
    'volume_ratio': 2.1,
    'atr': 4.2,
    'trend_strength': 80,
    'timeframe': 'Daily'
}

try:
    prediction = predict_tr_confidence(signal_sell)
    print(f"✅ Prediction successful!")
    print(f"   Confidence: {prediction['confidence_pct']}%")
    print(f"   Level: {prediction['confidence_level']}")
    print(f"   Expected: {prediction['expected_outcome']}")
    print(f"   Model: {prediction['model_used']}")
    print()
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    print()

# Test 4: Neutral Signal (TR Stage 3)
print("TEST 4: Neutral Signal (TR Stage 3)")
print("-" * 80)
signal_neutral = {
    'tr_stage': 3,
    'entry_price': 150.50,
    'ema_13': 150.00,
    'ema_30': 149.50,
    'ema_50': 148.00,
    'ema_200': 145.00,
    'rsi': 52.0,
    'volume_ratio': 0.9,
    'atr': 2.8,
    'trend_strength': 45,
    'timeframe': 'Daily'
}

try:
    prediction = predict_tr_confidence(signal_neutral)
    print(f"✅ Prediction successful!")
    print(f"   Confidence: {prediction['confidence_pct']}%")
    print(f"   Level: {prediction['confidence_level']}")
    print(f"   Expected: {prediction['expected_outcome']}")
    print(f"   Model: {prediction['model_used']}")
    print()
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    print()

# Test 5: Weekly Timeframe
print("TEST 5: Weekly Timeframe Signal")
print("-" * 80)
signal_weekly = {
    'tr_stage': 2,
    'entry_price': 150.50,
    'ema_13': 147.20,
    'ema_30': 144.80,
    'ema_50': 142.00,
    'ema_200': 135.00,
    'rsi': 42.5,
    'volume_ratio': 1.3,
    'atr': 5.5,
    'trend_strength': 65,
    'timeframe': 'Weekly'
}

try:
    prediction = predict_tr_confidence(signal_weekly)
    print(f"✅ Prediction successful!")
    print(f"   Confidence: {prediction['confidence_pct']}%")
    print(f"   Level: {prediction['confidence_level']}")
    print(f"   Expected: {prediction['expected_outcome']}")
    print(f"   Model: {prediction['model_used']}")
    print(f"   Timeframe: {prediction['timeframe']}")
    print()
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    print()

# Test 6: Confidence Factors
print("TEST 6: Confidence Factors Analysis")
print("-" * 80)
try:
    prediction = predict_tr_confidence(signal_buy)
    print(f"Confidence Factors for Strong Buy Signal:")
    print()
    for factor in prediction['confidence_factors']:
        print(f"  {factor}")
    print()
except Exception as e:
    print(f"❌ Factors analysis failed: {e}")
    print()

# Final Summary
print("="*80)
print("TEST SUMMARY")
print("="*80)
print()
print("If all tests show ✅, the ML predictor is ready!")
print()
print("If you see ⚠️ 'model not found':")
print("  - Make sure TR model .pkl files are in src/ml_models/ folder")
print("  - Model files should be named: tr_daily_*.pkl and tr_weekly_*.pkl")
print()
print("If you see ❌ errors:")
print("  - Copy the error message")
print("  - Share with Claude tomorrow for debugging")
print()
print("Next steps:")
print("  1. If tests pass ✅ → Ready to integrate into app!")
print("  2. Come back to chat tomorrow")
print("  3. Say: 'Ready for TR ML integration!'")
print()
print("="*80)
