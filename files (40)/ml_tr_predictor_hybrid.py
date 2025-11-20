"""
TR ML CONFIDENCE PREDICTOR - For Hybrid Models
===============================================

This predictor works with the hybrid TR models and shows:
- ML confidence score
- Quality tier (Basic, Buy Point, Uptrend, ELITE)
- Confidence factors
- Elite badge when applicable
"""

import pandas as pd
import numpy as np
import pickle
import os
import glob
from datetime import datetime

def load_latest_models():
    """Load the most recent TR models"""
    
    models_dir = 'ml_models'
    
    # Find latest models
    daily_models = glob.glob(f'{models_dir}/tr_daily_*.pkl')
    weekly_models = glob.glob(f'{models_dir}/tr_weekly_*.pkl')
    
    if not daily_models or not weekly_models:
        raise FileNotFoundError("TR models not found. Please train models first.")
    
    # Sort by timestamp (filename) and get latest
    daily_model_path = sorted(daily_models)[-1]
    weekly_model_path = sorted(weekly_models)[-1]
    
    # Load models
    with open(daily_model_path, 'rb') as f:
        daily_data = pickle.load(f)
    
    with open(weekly_model_path, 'rb') as f:
        weekly_data = pickle.load(f)
    
    print(f"✅ Daily Model Loaded: {os.path.basename(daily_model_path)}")
    print(f"✅ Weekly Model Loaded: {os.path.basename(weekly_model_path)}")
    
    return daily_data, weekly_data

def predict_confidence(signal_data, timeframe='Daily'):
    """
    Predict confidence for a TR signal
    
    Parameters:
    -----------
    signal_data : dict
        Signal features including:
        - tr_stage: 1-6
        - entry_price, ema_3, ema_9, ema_20, ema_34
        - ppo_value, ppo_histogram, pmo_value
        - has_buy_point: 0/1
        - has_uptrend: 0/1
        - has_rs_chaikin: 0/1 (ELITE marker)
        - quality_level: 0-3
    
    timeframe : str
        'Daily' or 'Weekly'
    
    Returns:
    --------
    dict with:
        - confidence: float (0-100)
        - confidence_level: str ('Very Low', 'Low', 'Moderate', 'High', 'Very High')
        - expected_outcome: str ('Failure', 'Success')
        - is_elite: bool
        - quality_tier: str
        - factors: list of contributing factors
    """
    
    # Load models
    daily_data, weekly_data = load_latest_models()
    
    # Select appropriate model
    if timeframe == 'Daily':
        model_data = daily_data
        target = 5.0
    else:
        model_data = weekly_data
        target = 8.0
    
    model = model_data['model']
    features = model_data['features']
    
    # Calculate derived features
    entry_price = signal_data['entry_price']
    
    # EMA distances
    distance_from_ema3 = (entry_price - signal_data['ema_3']) / entry_price * 100
    distance_from_ema9 = (entry_price - signal_data['ema_9']) / entry_price * 100
    distance_from_ema20 = (entry_price - signal_data['ema_20']) / entry_price * 100
    distance_from_ema34 = (entry_price - signal_data['ema_34']) / entry_price * 100
    
    # Above EMA indicators
    above_ema3 = 1 if entry_price > signal_data['ema_3'] else 0
    above_ema9 = 1 if entry_price > signal_data['ema_9'] else 0
    above_ema20 = 1 if entry_price > signal_data['ema_20'] else 0
    above_ema34 = 1 if entry_price > signal_data['ema_34'] else 0
    
    # EMA alignment
    ema_alignment = 1 if (signal_data['ema_3'] > signal_data['ema_9'] > 
                          signal_data['ema_20'] > signal_data['ema_34']) else 0
    
    # PPO indicators
    ppo_positive = 1 if signal_data['ppo_value'] > 0 else 0
    ppo_strong = 1 if abs(signal_data['ppo_value']) > 1.5 else 0
    
    # Quality indicator
    has_quality = 1 if signal_data['quality_level'] > 0 else 0
    
    # Build feature array
    feature_values = {
        'tr_stage': signal_data['tr_stage'],
        'distance_from_ema3': distance_from_ema3,
        'distance_from_ema9': distance_from_ema9,
        'distance_from_ema20': distance_from_ema20,
        'distance_from_ema34': distance_from_ema34,
        'above_ema3': above_ema3,
        'above_ema9': above_ema9,
        'above_ema20': above_ema20,
        'above_ema34': above_ema34,
        'ema_alignment': ema_alignment,
        'ppo_value': signal_data['ppo_value'],
        'ppo_histogram': signal_data['ppo_histogram'],
        'ppo_positive': ppo_positive,
        'ppo_strong': ppo_strong,
        'pmo_value': signal_data['pmo_value'],
        'has_quality': has_quality,
        'has_buy_point': signal_data['has_buy_point'],
        'has_uptrend': signal_data['has_uptrend'],
        'has_rs_chaikin': signal_data['has_rs_chaikin']
    }
    
    # Create feature vector in correct order
    X = np.array([[feature_values[f] for f in features]])
    
    # Predict
    proba = model.predict_proba(X)[0]
    confidence = proba[1] * 100  # Probability of success
    
    # Determine confidence level
    if confidence >= 75:
        confidence_level = 'Very High'
    elif confidence >= 65:
        confidence_level = 'High'
    elif confidence >= 55:
        confidence_level = 'Moderate'
    elif confidence >= 45:
        confidence_level = 'Low'
    else:
        confidence_level = 'Very Low'
    
    # Expected outcome
    expected_outcome = 'Success' if confidence >= 50 else 'Failure'
    
    # Determine quality tier
    is_elite = signal_data['has_rs_chaikin'] == 1
    has_buy_point = signal_data['has_buy_point'] == 1
    has_uptrend = signal_data['has_uptrend'] == 1
    
    if is_elite and has_buy_point and has_uptrend:
        quality_tier = 'ELITE (↑ + 🔵BUY + *)'
    elif has_uptrend and has_buy_point:
        quality_tier = 'Premium (↑ + 🔵BUY)'
    elif has_buy_point:
        quality_tier = 'Good (🔵BUY)'
    else:
        quality_tier = 'Basic'
    
    # Identify contributing factors
    factors = []
    
    # TR Stage
    if signal_data['tr_stage'] == 1:
        factors.append('✅ Strong Buy signal (Stage 1)')
    elif signal_data['tr_stage'] == 2:
        factors.append('✅ Buy signal (Stage 2)')
    
    # EMA Alignment
    if ema_alignment:
        factors.append('✅ Strong bullish EMA alignment')
    elif above_ema20:
        factors.append('✅ Price above key EMAs')
    
    # Momentum
    if signal_data['ppo_value'] > 2:
        factors.append('✅ Strong positive momentum (PPO)')
    elif signal_data['ppo_value'] > 0:
        factors.append('✅ Positive momentum (PPO)')
    
    if signal_data['pmo_value'] > 2:
        factors.append('✅ Very strong PMO signal')
    elif signal_data['pmo_value'] > 0:
        factors.append('✅ Positive PMO signal')
    
    # Quality features
    if has_buy_point:
        factors.append('✅ Buy point identified (🔵BUY)')
    
    if has_uptrend:
        factors.append('✅ Uptrend confirmed (↑)')
    
    if is_elite:
        factors.append('⭐ ELITE: Relative Strength + Chaikin A/D confirmed (*)')
    
    if signal_data['quality_level'] >= 2:
        factors.append('✅ High-quality setup')
    
    return {
        'confidence': round(confidence, 1),
        'confidence_level': confidence_level,
        'expected_outcome': expected_outcome,
        'is_elite': is_elite,
        'quality_tier': quality_tier,
        'target': target,
        'timeframe': timeframe,
        'factors': factors,
        'model_info': {
            'algorithm': 'RandomForest',
            'training_samples': model_data['training_samples'],
            'accuracy': round(model_data['accuracy'] * 100, 1),
            'success_rate': round(model_data['success_rate'] * 100, 1)
        }
    }

def format_prediction_output(prediction):
    """Format prediction for display"""
    
    print()
    print("="*80)
    print("PREDICTION RESULTS")
    print("="*80)
    print()
    
    # Main confidence
    confidence = prediction['confidence']
    level = prediction['confidence_level']
    
    # Color code by confidence level
    if confidence >= 70:
        icon = '🔥'
    elif confidence >= 60:
        icon = '✅'
    elif confidence >= 50:
        icon = '⚠️'
    else:
        icon = '❌'
    
    print(f"{icon} Confidence Score: {confidence}%")
    print(f"📊 Confidence Level: {level}")
    print(f"🎯 Expected Outcome: {prediction['expected_outcome']}")
    print(f"📈 Target: {prediction['target']}% gain ({prediction['timeframe']})")
    print()
    
    # Quality tier
    print(f"🏆 Quality Tier: {prediction['quality_tier']}")
    
    if prediction['is_elite']:
        print()
        print("⭐" * 20)
        print("ELITE SETUP DETECTED!")
        print("⭐" * 20)
        print()
        print("This signal has BOTH Relative Strength (vs SPY) and")
        print("Chaikin Accumulation/Distribution in the top 5% of their ranges.")
        print()
        print("Note: Elite signals are high-volatility, high-reward setups.")
        print("      Consider wider targets (10-15%) for these signals.")
        print()
    
    # Contributing factors
    if prediction['factors']:
        print("📋 Confidence Factors:")
        for factor in prediction['factors']:
            print(f"  {factor}")
        print()
    
    # Model info
    print("🔧 Model Info:")
    info = prediction['model_info']
    print(f"  Algorithm: {info['algorithm']}")
    print(f"  Timeframe: {prediction['timeframe']}")
    print(f"  Training Samples: {info['training_samples']:,}")
    print(f"  Model Accuracy: {info['accuracy']}%")
    print(f"  Historical Success Rate: {info['success_rate']}%")
    print()
    
    print("="*80)
    print()

# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == '__main__':
    print("="*80)
    print("TR ML CONFIDENCE PREDICTOR - DEMO")
    print("="*80)
    print()
    
    # Test signal data
    test_signals = [
        {
            'name': 'Basic Strong Buy',
            'data': {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.1,
                'ppo_histogram': 0.5,
                'pmo_value': 3.2,
                'quality_level': 1,
                'has_buy_point': 0,
                'has_uptrend': 0,
                'has_rs_chaikin': 0
            }
        },
        {
            'name': 'Strong Buy + Buy Point',
            'data': {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.1,
                'ppo_histogram': 0.5,
                'pmo_value': 3.2,
                'quality_level': 2,
                'has_buy_point': 1,  # Has buy point
                'has_uptrend': 0,
                'has_rs_chaikin': 0
            }
        },
        {
            'name': 'Premium (Uptrend + Buy Point)',
            'data': {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.5,
                'ppo_histogram': 0.7,
                'pmo_value': 3.5,
                'quality_level': 2,
                'has_buy_point': 1,
                'has_uptrend': 1,  # Has uptrend
                'has_rs_chaikin': 0
            }
        },
        {
            'name': 'ELITE Setup (*)',
            'data': {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 3.0,
                'ppo_histogram': 1.0,
                'pmo_value': 4.0,
                'quality_level': 3,
                'has_buy_point': 1,
                'has_uptrend': 1,
                'has_rs_chaikin': 1  # ELITE!
            }
        }
    ]
    
    # Test each signal
    for test in test_signals:
        print(f"Testing: {test['name']}")
        print("-" * 80)
        
        prediction = predict_confidence(test['data'], timeframe='Daily')
        format_prediction_output(prediction)
        
        input("Press Enter to continue to next test...")
        print()
