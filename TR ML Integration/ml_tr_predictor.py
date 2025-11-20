"""
TR Indicator ML Confidence Predictor
Provides ML-based confidence scores for TR indicator signals
"""

import os
import pickle
import numpy as np
from datetime import datetime

# Model directory - absolute path
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'ml_models')

# Global model cache
_models_cache = {}

def load_models():
    """Load TR ML models for both timeframes"""
    global _models_cache
    
    if _models_cache:
        return _models_cache
    
    try:
        # Check if model directory exists
        if not os.path.exists(MODEL_DIR):
            raise FileNotFoundError(f"Model directory not found: {MODEL_DIR}")
        
        # Load Daily model
        daily_models = [f for f in os.listdir(MODEL_DIR) if 'tr_daily' in f.lower() and f.endswith('.pkl')]
        if daily_models:
            daily_model_path = os.path.join(MODEL_DIR, sorted(daily_models)[-1])  # Get latest
            with open(daily_model_path, 'rb') as f:
                _models_cache['daily'] = pickle.load(f)
            print(f"✅ Daily Model Loaded: {os.path.basename(daily_model_path)}")
        else:
            print("⚠️ No Daily TR model found")
            _models_cache['daily'] = None
        
        # Load Weekly model
        weekly_models = [f for f in os.listdir(MODEL_DIR) if 'tr_weekly' in f.lower() and f.endswith('.pkl')]
        if weekly_models:
            weekly_model_path = os.path.join(MODEL_DIR, sorted(weekly_models)[-1])  # Get latest
            with open(weekly_model_path, 'rb') as f:
                _models_cache['weekly'] = pickle.load(f)
            print(f"✅ Weekly Model Loaded: {os.path.basename(weekly_model_path)}")
        else:
            print("⚠️ No Weekly TR model found")
            _models_cache['weekly'] = None
        
        return _models_cache
        
    except Exception as e:
        print(f"❌ Error loading TR models: {e}")
        return {'daily': None, 'weekly': None}


def extract_tr_features(signal_data):
    """
    Extract features from TR signal for ML prediction
    
    Parameters:
    -----------
    signal_data : dict
        Dictionary containing:
        - tr_stage: int (1-6, where 1=Strong Buy, 6=Strong Sell)
        - entry_price: float
        - ema_13: float
        - ema_30: float
        - ema_50: float (if available)
        - ema_200: float
        - rsi: float (if available)
        - volume_ratio: float (current volume / average volume)
        - atr: float (Average True Range - volatility measure)
        - distance_from_ema13: float (percentage)
        - distance_from_ema200: float (percentage)
        - trend_strength: float (0-100 score)
        - timeframe: str ('Daily' or 'Weekly')
    
    Returns:
    --------
    np.array : Feature vector for ML model
    """
    
    # Extract features
    tr_stage = signal_data.get('tr_stage', 0)
    entry_price = signal_data.get('entry_price', 0)
    ema_13 = signal_data.get('ema_13', entry_price)
    ema_30 = signal_data.get('ema_30', entry_price)
    ema_50 = signal_data.get('ema_50', entry_price)
    ema_200 = signal_data.get('ema_200', entry_price)
    rsi = signal_data.get('rsi', 50)
    volume_ratio = signal_data.get('volume_ratio', 1.0)
    atr = signal_data.get('atr', 0)
    trend_strength = signal_data.get('trend_strength', 50)
    
    # Calculate relative positions
    distance_from_ema13 = ((entry_price - ema_13) / entry_price * 100) if entry_price > 0 else 0
    distance_from_ema30 = ((entry_price - ema_30) / entry_price * 100) if entry_price > 0 else 0
    distance_from_ema200 = ((entry_price - ema_200) / entry_price * 100) if entry_price > 0 else 0
    
    # Price position relative to EMAs
    above_ema13 = 1 if entry_price > ema_13 else 0
    above_ema30 = 1 if entry_price > ema_30 else 0
    above_ema200 = 1 if entry_price > ema_200 else 0
    
    # EMA alignment (bullish when shorter EMAs > longer EMAs)
    ema_alignment = 1 if (ema_13 > ema_30 > ema_200) else 0
    
    # Volatility measure
    volatility_pct = (atr / entry_price * 100) if entry_price > 0 else 0
    
    # Signal type (buy or sell)
    is_buy_signal = 1 if tr_stage <= 3 else 0
    is_sell_signal = 1 if tr_stage >= 4 else 0
    
    # RSI zones
    rsi_oversold = 1 if rsi < 30 else 0
    rsi_overbought = 1 if rsi > 70 else 0
    
    # Volume confirmation
    high_volume = 1 if volume_ratio > 1.5 else 0
    
    # Build feature vector (MUST match training order!)
    features = np.array([
        tr_stage,                    # TR stage (1-6)
        distance_from_ema13,         # Distance from 13 EMA (%)
        distance_from_ema30,         # Distance from 30 EMA (%)
        distance_from_ema200,        # Distance from 200 EMA (%)
        above_ema13,                 # Above 13 EMA (1/0)
        above_ema30,                 # Above 30 EMA (1/0)
        above_ema200,                # Above 200 EMA (1/0)
        ema_alignment,               # EMA alignment (1/0)
        rsi,                         # RSI value
        rsi_oversold,                # RSI oversold (1/0)
        rsi_overbought,              # RSI overbought (1/0)
        volume_ratio,                # Volume ratio
        high_volume,                 # High volume (1/0)
        volatility_pct,              # Volatility (ATR %)
        trend_strength,              # Trend strength (0-100)
        is_buy_signal,               # Buy signal type (1/0)
        is_sell_signal               # Sell signal type (1/0)
    ]).reshape(1, -1)
    
    return features


def predict_tr_confidence(signal_data):
    """
    Predict confidence score for a TR indicator signal
    
    Parameters:
    -----------
    signal_data : dict
        TR signal data (see extract_tr_features for required fields)
    
    Returns:
    --------
    dict : Prediction results containing:
        - confidence_pct: float (0-100)
        - confidence_level: str ('Very High', 'High', 'Moderate', 'Low', 'Very Low')
        - expected_outcome: str ('Success' or 'Failure')
        - model_used: str ('RandomForest' or 'XGBoost')
        - timeframe: str ('Daily' or 'Weekly')
        - raw_probability: float (0-1)
    """
    
    try:
        # Load models
        models = load_models()
        
        # Get timeframe
        timeframe = signal_data.get('timeframe', 'Daily')
        model_key = 'daily' if timeframe == 'Daily' else 'weekly'
        
        # Get model
        model = models.get(model_key)
        
        if model is None:
            # Return default prediction if model not available
            return {
                'confidence_pct': 50.0,
                'confidence_level': 'Moderate',
                'expected_outcome': 'Unknown',
                'model_used': 'None',
                'timeframe': timeframe,
                'raw_probability': 0.5,
                'confidence_factors': []
            }
        
        # Extract features
        features = extract_tr_features(signal_data)
        
        # Make prediction
        probability = model.predict_proba(features)[0][1]  # Probability of success
        confidence_pct = probability * 100
        
        # Determine confidence level
        if confidence_pct >= 85:
            confidence_level = 'Very High'
        elif confidence_pct >= 75:
            confidence_level = 'High'
        elif confidence_pct >= 60:
            confidence_level = 'Moderate'
        elif confidence_pct >= 45:
            confidence_level = 'Low'
        else:
            confidence_level = 'Very Low'
        
        # Expected outcome
        expected_outcome = 'Success' if confidence_pct >= 60 else 'Failure'
        
        # Determine model type
        model_type = type(model).__name__
        if 'RandomForest' in model_type:
            model_used = 'RandomForest'
        elif 'XGBoost' in model_type or 'XGB' in model_type:
            model_used = 'XGBoost'
        else:
            model_used = model_type
        
        # Analyze confidence factors
        confidence_factors = analyze_confidence_factors(signal_data, confidence_pct)
        
        return {
            'confidence_pct': round(confidence_pct, 1),
            'confidence_level': confidence_level,
            'expected_outcome': expected_outcome,
            'model_used': model_used,
            'timeframe': timeframe,
            'raw_probability': round(probability, 3),
            'confidence_factors': confidence_factors
        }
        
    except Exception as e:
        print(f"❌ TR prediction error: {e}")
        # Return safe default
        return {
            'confidence_pct': 50.0,
            'confidence_level': 'Moderate',
            'expected_outcome': 'Unknown',
            'model_used': 'Error',
            'timeframe': signal_data.get('timeframe', 'Daily'),
            'raw_probability': 0.5,
            'confidence_factors': [f"⚠️ Error: {str(e)}"]
        }


def analyze_confidence_factors(signal_data, confidence_pct):
    """
    Analyze what factors are contributing to the confidence score
    
    Returns list of human-readable factors
    """
    factors = []
    
    tr_stage = signal_data.get('tr_stage', 0)
    entry_price = signal_data.get('entry_price', 0)
    ema_13 = signal_data.get('ema_13', entry_price)
    ema_30 = signal_data.get('ema_30', entry_price)
    ema_200 = signal_data.get('ema_200', entry_price)
    rsi = signal_data.get('rsi', 50)
    volume_ratio = signal_data.get('volume_ratio', 1.0)
    trend_strength = signal_data.get('trend_strength', 50)
    
    # TR Stage assessment
    if tr_stage in [1, 6]:
        factors.append("✅ Strong TR signal (Stage 1 or 6)")
    elif tr_stage in [2, 5]:
        factors.append("✅ Clear TR signal")
    else:
        factors.append("⚠️ Neutral TR zone")
    
    # EMA alignment
    if tr_stage <= 3:  # Buy signals
        if entry_price > ema_13 > ema_30 > ema_200:
            factors.append("✅ Strong bullish EMA alignment")
        elif entry_price > ema_200:
            factors.append("✅ Above long-term trend (EMA200)")
        else:
            factors.append("⚠️ Below long-term trend")
    else:  # Sell signals
        if entry_price < ema_13 < ema_30 < ema_200:
            factors.append("✅ Strong bearish EMA alignment")
        elif entry_price < ema_200:
            factors.append("✅ Below long-term trend (EMA200)")
        else:
            factors.append("⚠️ Above long-term trend")
    
    # RSI confirmation
    if tr_stage <= 3:  # Buy signals
        if rsi < 40:
            factors.append("✅ RSI shows oversold (good buy opportunity)")
        elif rsi > 70:
            factors.append("⚠️ RSI overbought (risky buy)")
    else:  # Sell signals
        if rsi > 60:
            factors.append("✅ RSI shows overbought (good sell signal)")
        elif rsi < 30:
            factors.append("⚠️ RSI oversold (risky sell)")
    
    # Volume confirmation
    if volume_ratio > 1.5:
        factors.append("✅ High volume confirmation")
    elif volume_ratio < 0.7:
        factors.append("⚠️ Low volume (weak signal)")
    
    # Trend strength
    if trend_strength > 70:
        factors.append("✅ Very strong trend")
    elif trend_strength > 50:
        factors.append("✅ Moderate trend strength")
    else:
        factors.append("⚠️ Weak trend")
    
    return factors


# Demo/Test function
if __name__ == "__main__":
    print("="*80)
    print("TR ML CONFIDENCE PREDICTOR - DEMO")
    print("="*80)
    print()
    
    # Test signal data (example)
    test_signal = {
        'tr_stage': 1,           # Strong Buy
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
    
    print("📊 Test Signal Data:")
    for key, value in test_signal.items():
        print(f"  {key}: {value}")
    print()
    
    print("🤖 Generating ML Prediction...")
    print()
    
    # Get prediction
    prediction = predict_tr_confidence(test_signal)
    
    print("="*80)
    print("PREDICTION RESULTS")
    print("="*80)
    print()
    print(f"🎯 Confidence Score: {prediction['confidence_pct']}%")
    print(f"📊 Confidence Level: {prediction['confidence_level']}")
    print(f"✅ Expected Outcome: {prediction['expected_outcome']}")
    print()
    print(f"🔧 Model Info:")
    print(f"  Algorithm: {prediction['model_used']}")
    print(f"  Timeframe: {prediction['timeframe']}")
    print(f"  Raw Probability: {prediction['raw_probability']}")
    print()
    print(f"📋 Confidence Factors:")
    for factor in prediction['confidence_factors']:
        print(f"  {factor}")
    print()
    print("="*80)
