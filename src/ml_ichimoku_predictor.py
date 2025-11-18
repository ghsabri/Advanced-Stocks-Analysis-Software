"""
Ichimoku ML Confidence Scoring System
Loads trained ML models and generates confidence scores for new signals
"""

import pandas as pd
import numpy as np
import pickle
import os
from typing import Dict, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# MODEL_DIR = './ml_models/' #Look in current directory
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'ml_models')

# Confidence level thresholds
CONFIDENCE_THRESHOLDS = {
    'Very High': 0.90,
    'High': 0.75,
    'Moderate': 0.60,
    'Low': 0.45,
    'Very Low': 0.0
}

# ============================================================================
# MODEL LOADER
# ============================================================================

class IchimokuMLPredictor:
    """
    Loads trained ML models and generates confidence predictions for Ichimoku signals.
    """
    
    def __init__(self, model_dir: str = MODEL_DIR):
        """
        Initialize predictor by loading trained models.
        
        Args:
            model_dir: Directory containing saved model files
        """
        self.model_dir = model_dir
        self.daily_model = None
        self.weekly_model = None
        self.daily_features = None
        self.weekly_features = None
        
        self._load_models()
    
    def _load_models(self):
        """Load the most recent trained models."""
        
        if not os.path.exists(self.model_dir):
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")
        
        # Find most recent model files
        daily_files = [f for f in os.listdir(self.model_dir) if f.startswith('ichimoku_daily_') and f.endswith('.pkl')]
        weekly_files = [f for f in os.listdir(self.model_dir) if f.startswith('ichimoku_weekly_') and f.endswith('.pkl')]
        
        if not daily_files or not weekly_files:
            raise FileNotFoundError("No trained models found. Please run ml_ichimoku_trainer.py first.")
        
        # Sort by timestamp (most recent last)
        daily_files.sort()
        weekly_files.sort()
        
        daily_path = os.path.join(self.model_dir, daily_files[-1])
        weekly_path = os.path.join(self.model_dir, weekly_files[-1])
        
        print(f"📂 Loading Daily model: {daily_files[-1]}")
        print(f"📂 Loading Weekly model: {weekly_files[-1]}")
        
        # Load models
        with open(daily_path, 'rb') as f:
            daily_dict = pickle.load(f)
            self.daily_model = daily_dict['best_model']
            self.daily_features = daily_dict['feature_cols']
            self.daily_accuracy = daily_dict['accuracy']
            self.daily_model_name = daily_dict['best_model_name']
        
        with open(weekly_path, 'rb') as f:
            weekly_dict = pickle.load(f)
            self.weekly_model = weekly_dict['best_model']
            self.weekly_features = weekly_dict['feature_cols']
            self.weekly_accuracy = weekly_dict['accuracy']
            self.weekly_model_name = weekly_dict['best_model_name']
        
        print(f"✅ Daily Model Loaded: {self.daily_model_name} ({self.daily_accuracy:.1%} accuracy)")
        print(f"✅ Weekly Model Loaded: {self.weekly_model_name} ({self.weekly_accuracy:.1%} accuracy)")
    
    def _engineer_features(self, signal_data: Dict) -> pd.DataFrame:
        """
        Engineer features from raw signal data (same as training).
        
        Args:
            signal_data: Dictionary containing signal information
            
        Returns:
            DataFrame with engineered features
        """
        # Convert to DataFrame
        df = pd.DataFrame([signal_data])
        
        # 1. PRICE POSITION FEATURES
        position_map = {'above': 1, 'inside': 0, 'below': -1}
        df['price_position_numeric'] = df['price_position'].map(position_map)
        
        # 2. CLOUD THICKNESS
        df['cloud_thickness'] = abs(df['cloud_top'] - df['cloud_bottom'])
        df['cloud_thickness_pct'] = (df['cloud_thickness'] / df['entry_price']) * 100
        
        # 3. PRICE DISTANCE FROM CLOUD
        df['distance_to_cloud_top'] = df['entry_price'] - df['cloud_top']
        df['distance_to_cloud_bottom'] = df['entry_price'] - df['cloud_bottom']
        df['distance_to_cloud_top_pct'] = (df['distance_to_cloud_top'] / df['entry_price']) * 100
        df['distance_to_cloud_bottom_pct'] = (df['distance_to_cloud_bottom'] / df['entry_price']) * 100
        
        # 4. EMA ALIGNMENT
        df['ema_alignment_bullish'] = ((df['ema_13'] > df['ema_30']) & 
                                         (df['ema_30'] > df['ema_200'])).astype(int)
        df['ema_alignment_bearish'] = ((df['ema_13'] < df['ema_30']) & 
                                         (df['ema_30'] < df['ema_200'])).astype(int)
        
        # 5. PRICE POSITION RELATIVE TO EMAS
        df['price_above_ema13'] = (df['entry_price'] > df['ema_13']).astype(int)
        df['price_above_ema30'] = (df['entry_price'] > df['ema_30']).astype(int)
        df['price_above_ema200'] = (df['entry_price'] > df['ema_200']).astype(int)
        
        # Distance to key EMAs
        df['distance_to_ema13_pct'] = ((df['entry_price'] - df['ema_13']) / df['entry_price']) * 100
        df['distance_to_ema30_pct'] = ((df['entry_price'] - df['ema_30']) / df['entry_price']) * 100
        df['distance_to_ema200_pct'] = ((df['entry_price'] - df['ema_200']) / df['entry_price']) * 100
        
        # 6. EMA SPREADS
        df['ema_13_30_spread'] = df['ema_13'] - df['ema_30']
        df['ema_30_200_spread'] = df['ema_30'] - df['ema_200']
        df['ema_13_30_spread_pct'] = (df['ema_13_30_spread'] / df['entry_price']) * 100
        df['ema_30_200_spread_pct'] = (df['ema_30_200_spread'] / df['entry_price']) * 100
        
        # 7. CLOUD POSITION RELATIVE TO PRICE
        df['cloud_as_support'] = ((df['entry_price'] > df['cloud_top']) & 
                                   (df['entry_price'] > df['cloud_bottom'])).astype(int)
        df['cloud_as_resistance'] = ((df['entry_price'] < df['cloud_top']) & 
                                      (df['entry_price'] < df['cloud_bottom'])).astype(int)
        
        # 8. TREND STRENGTH INDICATOR
        df['trend_strength'] = (
            df['ema_alignment_bullish'] * 2 +
            df['price_above_ema200'] +
            df['cloud_as_support'] +
            (df['cloud_thickness_pct'] > 2).astype(int)
        )
        
        return df
    
    def _interpret_confidence(self, confidence: float) -> str:
        """
        Convert confidence probability to human-readable level.
        
        Args:
            confidence: Probability score (0.0 to 1.0)
            
        Returns:
            Confidence level string
        """
        for level, threshold in CONFIDENCE_THRESHOLDS.items():
            if confidence >= threshold:
                return level
        return 'Very Low'
    
    def _get_confidence_factors(self, features: pd.DataFrame, model, feature_cols: list) -> list:
        """
        Identify key factors influencing the confidence score.
        
        Args:
            features: Engineered features DataFrame
            model: Trained ML model
            feature_cols: List of feature column names
            
        Returns:
            List of factor strings explaining the prediction
        """
        factors = []
        
        # Get first row (we only predict one signal at a time)
        row = features.iloc[0]
        
        # EMA Alignment
        if row.get('ema_alignment_bullish', 0) == 1:
            factors.append("✅ Strong bullish EMA alignment")
        elif row.get('ema_alignment_bearish', 0) == 1:
            factors.append("⚠️ Bearish EMA alignment")
        
        # Price vs Cloud
        if row.get('cloud_as_support', 0) == 1:
            factors.append("✅ Cloud acting as support")
        elif row.get('cloud_as_resistance', 0) == 1:
            factors.append("⚠️ Cloud acting as resistance")
        
        # Cloud Thickness
        cloud_thickness_pct = row.get('cloud_thickness_pct', 0)
        if cloud_thickness_pct > 3:
            factors.append(f"✅ Thick cloud support ({cloud_thickness_pct:.1f}%)")
        elif cloud_thickness_pct < 1:
            factors.append(f"⚠️ Thin cloud support ({cloud_thickness_pct:.1f}%)")
        
        # Distance to EMA200
        distance_200 = row.get('distance_to_ema200_pct', 0)
        if abs(distance_200) < 2:
            factors.append("✅ Near long-term trend (EMA200)")
        elif distance_200 > 10:
            factors.append("⚠️ Far above long-term trend")
        elif distance_200 < -10:
            factors.append("⚠️ Far below long-term trend")
        
        # Trend Strength
        trend_strength = row.get('trend_strength', 0)
        if trend_strength >= 4:
            factors.append(f"✅ Very strong trend (score: {int(trend_strength)})")
        elif trend_strength <= 1:
            factors.append(f"⚠️ Weak trend (score: {int(trend_strength)})")
        
        # If no factors, add generic one
        if not factors:
            factors.append("📊 Based on multiple technical indicators")
        
        return factors
    
    def predict(self, signal_data: Dict) -> Dict:
        """
        Generate ML confidence prediction for an Ichimoku signal.
        
        Args:
            signal_data: Dictionary containing:
                - entry_price: float
                - ema_13: float
                - ema_30: float
                - ema_200: float
                - cloud_top: float
                - cloud_bottom: float
                - price_position: str ('above', 'inside', 'below')
                - timeframe: str ('Daily' or 'Weekly')
                - max_gain_pct: float (optional, for display)
                - max_loss_pct: float (optional, for display)
                
        Returns:
            Dictionary containing:
                - confidence_pct: float (0-100)
                - confidence_level: str ('Very High', 'High', 'Moderate', 'Low', 'Very Low')
                - expected_outcome: str ('Success' or 'Failure')
                - model_used: str (model name)
                - model_accuracy: float (trained accuracy)
                - confidence_factors: list of strings explaining prediction
                - raw_probability: float (0-1, for advanced users)
        """
        
        # Validate required fields
        required_fields = ['entry_price', 'ema_13', 'ema_30', 'ema_200', 
                          'cloud_top', 'cloud_bottom', 'price_position', 'timeframe']
        
        missing = [f for f in required_fields if f not in signal_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Select model based on timeframe
        timeframe = signal_data['timeframe']
        if timeframe == 'Daily':
            model = self.daily_model
            feature_cols = self.daily_features
            model_name = self.daily_model_name
            model_accuracy = self.daily_accuracy
        elif timeframe == 'Weekly':
            model = self.weekly_model
            feature_cols = self.weekly_features
            model_name = self.weekly_model_name
            model_accuracy = self.weekly_accuracy
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}. Must be 'Daily' or 'Weekly'")
        
        # Add placeholder values for features that require historical data
        # (These would normally come from actual signal detection)
        if 'max_gain_pct' not in signal_data:
            signal_data['max_gain_pct'] = 0.0
        if 'max_loss_pct' not in signal_data:
            signal_data['max_loss_pct'] = 0.0
        
        # Engineer features
        features = self._engineer_features(signal_data)
        
        # Extract only the features the model was trained on
        X = features[feature_cols]
        
        # Get prediction probability
        proba = model.predict_proba(X)[0]
        confidence_raw = proba[1]  # Probability of success (class 1)
        confidence_pct = confidence_raw * 100
        
        # Interpret confidence
        confidence_level = self._interpret_confidence(confidence_raw)
        expected_outcome = 'Success' if confidence_raw >= 0.5 else 'Failure'
        
        # Get confidence factors
        confidence_factors = self._get_confidence_factors(features, model, feature_cols)
        
        # Return complete prediction
        return {
            'confidence_pct': round(confidence_pct, 1),
            'confidence_level': confidence_level,
            'expected_outcome': expected_outcome,
            'model_used': model_name,
            'model_accuracy': round(model_accuracy * 100, 1),
            'confidence_factors': confidence_factors,
            'raw_probability': round(confidence_raw, 4),
            'timeframe': timeframe
        }

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global predictor instance (initialized on first use)
_predictor = None

def get_predictor() -> IchimokuMLPredictor:
    """
    Get or initialize the global predictor instance.
    
    Returns:
        IchimokuMLPredictor instance
    """
    global _predictor
    if _predictor is None:
        _predictor = IchimokuMLPredictor()
    return _predictor

def predict_ichimoku_confidence(signal_data: Dict) -> Dict:
    """
    Convenience function to get confidence prediction.
    
    Args:
        signal_data: Signal information dictionary
        
    Returns:
        Prediction results dictionary
    """
    predictor = get_predictor()
    return predictor.predict(signal_data)

# ============================================================================
# TESTING / DEMO
# ============================================================================

def demo():
    """Demonstration of the prediction system."""
    
    print("=" * 80)
    print("ICHIMOKU ML CONFIDENCE PREDICTOR - DEMO")
    print("=" * 80)
    
    # Example signal data (AAPL bullish setup)
    test_signal = {
        'entry_price': 225.50,
        'ema_13': 220.15,
        'ema_30': 218.40,
        'ema_200': 210.00,
        'cloud_top': 222.00,
        'cloud_bottom': 219.00,
        'price_position': 'above',
        'timeframe': 'Daily'
    }
    
    print("\n📊 Test Signal Data:")
    for key, value in test_signal.items():
        print(f"   {key}: {value}")
    
    # Get prediction
    print("\n🤖 Generating ML Prediction...")
    result = predict_ichimoku_confidence(test_signal)
    
    # Display results
    print("\n" + "=" * 80)
    print("PREDICTION RESULTS")
    print("=" * 80)
    print(f"\n🎯 Confidence Score: {result['confidence_pct']}%")
    print(f"📊 Confidence Level: {result['confidence_level']}")
    print(f"✅ Expected Outcome: {result['expected_outcome']}")
    print(f"\n🤖 Model Info:")
    print(f"   Algorithm: {result['model_used']}")
    print(f"   Timeframe: {result['timeframe']}")
    print(f"   Trained Accuracy: {result['model_accuracy']}%")
    print(f"   Raw Probability: {result['raw_probability']}")
    
    print(f"\n💡 Confidence Factors:")
    for factor in result['confidence_factors']:
        print(f"   {factor}")
    
    print("\n" + "=" * 80)
    print("✅ PREDICTION SYSTEM READY FOR PRODUCTION")
    print("=" * 80)

if __name__ == '__main__':
    demo()
