"""
AI Confidence Scoring System for Pattern Detection
Uses Machine Learning to predict pattern success probability

Features:
- Collects historical pattern data
- Labels outcomes (success/failure)
- Trains Random Forest & XGBoost models
- Generates confidence scores for predictions
"""

import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


class AIConfidenceScorer:
    """ML-based confidence scoring for pattern predictions"""
    
    def __init__(self, model_dir='models'):
        """
        Initialize AI confidence scorer
        
        Args:
            model_dir (str): Directory to save/load trained models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        self.models = {}
        self.feature_names = []
        
        # Load existing models if available
        self._load_models()
    
    def extract_features(self, pattern, df, price_col='Close'):
        """
        Extract features from a pattern for ML prediction
        
        Args:
            pattern (dict): Pattern dictionary
            df (pd.DataFrame): Price data
            price_col (str): Price column name
        
        Returns:
            dict: Feature dictionary
        """
        features = {}
        
        # Basic pattern info
        features['pattern_type'] = pattern['type']
        features['confidence'] = pattern['confidence']
        features['direction'] = pattern['direction']
        
        # Price characteristics
        start_idx = pattern['start_idx']
        end_idx = pattern['end_idx']
        pattern_prices = df[price_col].iloc[start_idx:end_idx+1]
        
        features['pattern_length'] = end_idx - start_idx
        features['price_range'] = pattern_prices.max() - pattern_prices.min()
        features['price_range_pct'] = (pattern_prices.max() - pattern_prices.min()) / pattern_prices.mean()
        features['volatility'] = pattern_prices.std() / pattern_prices.mean()
        
        # Volume characteristics (if available)
        if 'Volume' in df.columns:
            pattern_volume = df['Volume'].iloc[start_idx:end_idx+1]
            features['avg_volume'] = pattern_volume.mean()
            features['volume_trend'] = np.polyfit(range(len(pattern_volume)), pattern_volume.values, 1)[0]
        else:
            features['avg_volume'] = 0
            features['volume_trend'] = 0
        
        # Pattern-specific features
        if 'neckline' in pattern:
            features['neckline'] = pattern['neckline']
        else:
            features['neckline'] = 0
        
        if 'target_price' in pattern:
            current_price = df[price_col].iloc[end_idx]
            features['target_distance'] = abs(pattern['target_price'] - current_price) / current_price
        else:
            features['target_distance'] = 0
        
        # Market context
        features['current_price'] = df[price_col].iloc[end_idx]
        
        # Trend strength
        if end_idx >= 20:
            recent_prices = df[price_col].iloc[end_idx-20:end_idx+1]
            features['trend_strength'] = np.polyfit(range(len(recent_prices)), recent_prices.values, 1)[0]
        else:
            features['trend_strength'] = 0
        
        return features
    
    def label_pattern_outcome(self, pattern, df, price_col='Close', lookforward_days=30):
        """
        Label whether a pattern succeeded or failed
        
        Args:
            pattern (dict): Pattern dictionary
            df (pd.DataFrame): Complete price data (including future)
            price_col (str): Price column name
            lookforward_days (int): Days to look forward for outcome
        
        Returns:
            int: 1 if success, 0 if failure, -1 if unknown
        """
        end_idx = pattern['end_idx']
        
        # Check if we have enough future data
        if end_idx + lookforward_days >= len(df):
            return -1  # Unknown (not enough future data)
        
        current_price = df[price_col].iloc[end_idx]
        future_prices = df[price_col].iloc[end_idx+1:end_idx+lookforward_days+1]
        
        # Get target price
        if 'target_price' not in pattern:
            return -1  # No target to evaluate
        
        target_price = pattern['target_price']
        direction = pattern['direction']
        
        # Check if target was reached
        if direction == 'bullish':
            # Success if price reached or exceeded target
            if future_prices.max() >= target_price:
                return 1  # Success
            # Failure if price dropped significantly (more than 10%)
            elif future_prices.min() < current_price * 0.90:
                return 0  # Failure
            else:
                return -1  # Unclear
        
        elif direction == 'bearish':
            # Success if price reached or went below target
            if future_prices.min() <= target_price:
                return 1  # Success
            # Failure if price rose significantly (more than 10%)
            elif future_prices.max() > current_price * 1.10:
                return 0  # Failure
            else:
                return -1  # Unclear
        
        else:  # neutral
            # For neutral patterns, check if significant move happened
            max_move = max(
                abs(future_prices.max() - current_price) / current_price,
                abs(future_prices.min() - current_price) / current_price
            )
            if max_move > 0.05:  # 5% move
                return 1  # Success (breakout occurred)
            else:
                return 0  # Failure (no significant move)
    
    def collect_training_data(self, tickers, lookback_years=3):
        """
        Collect historical patterns for training
        
        Args:
            tickers (list): List of stock tickers to analyze
            lookback_years (int): Years of historical data
        
        Returns:
            tuple: (features_df, labels_series)
        """
        print(f"📊 Collecting training data from {len(tickers)} stocks...")
        
        from pattern_detection import detect_patterns_for_chart
        from stock_data_formatter import get_stock_data_formatted
        
        all_features = []
        all_labels = []
        
        for ticker in tickers:
            try:
                print(f"   Analyzing {ticker}...")
                
                # Get historical data using Tiingo (your existing source)
                df = get_stock_data_formatted(
                    ticker=ticker,
                    timeframe='weekly',
                    days=lookback_years * 365
                )
                
                if df is None or len(df) < 50:
                    print(f"   ⚠️  Not enough data for {ticker}")
                    continue
                
                # Find the correct price column name
                price_col = None
                for col in ['adjClose', 'adj_close', 'Close', 'close']:
                    if col in df.columns:
                        price_col = col
                        break
                
                if price_col is None:
                    print(f"   ⚠️  No price column found for {ticker}")
                    continue
                
                # Detect patterns
                patterns = detect_patterns_for_chart(df, price_col)
                
                print(f"   Found {len(patterns)} patterns")
                
                # Extract features and labels for each pattern
                for pattern in patterns:
                    # Skip patterns too close to present (need future data for labeling)
                    if pattern['end_idx'] + 30 >= len(df):
                        continue
                    
                    # Extract features
                    features = self.extract_features(pattern, df, price_col)
                    
                    # Label outcome
                    label = self.label_pattern_outcome(pattern, df, price_col)
                    
                    if label != -1:  # Only include if we have a clear label
                        all_features.append(features)
                        all_labels.append(label)
                
            except Exception as e:
                print(f"   ⚠️  Error with {ticker}: {e}")
                continue
        
        print(f"\n✅ Collected {len(all_features)} labeled patterns")
        
        # Convert to DataFrame
        features_df = pd.DataFrame(all_features)
        labels_series = pd.Series(all_labels)
        
        return features_df, labels_series
    
    def train_models(self, features_df, labels_series):
        """
        Train ML models on collected data
        
        Args:
            features_df (pd.DataFrame): Feature matrix
            labels_series (pd.Series): Labels (0/1)
        """
        print("\n🤖 Training AI models...")
        
        # Prepare data
        # Convert categorical features to numeric
        X = pd.get_dummies(features_df, columns=['pattern_type', 'direction'])
        y = labels_series
        
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"   Training set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        print(f"   Success rate: {y.mean()*100:.1f}%")
        
        # Train Random Forest
        print("\n   Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        rf_accuracy = accuracy_score(y_test, rf_model.predict(X_test))
        print(f"   ✅ Random Forest accuracy: {rf_accuracy*100:.1f}%")
        
        # Train Gradient Boosting
        print("\n   Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        gb_accuracy = accuracy_score(y_test, gb_model.predict(X_test))
        print(f"   ✅ Gradient Boosting accuracy: {gb_accuracy*100:.1f}%")
        
        # Cross-validation
        print("\n   Running cross-validation...")
        rf_cv_scores = cross_val_score(rf_model, X, y, cv=5)
        gb_cv_scores = cross_val_score(gb_model, X, y, cv=5)
        
        print(f"   Random Forest CV: {rf_cv_scores.mean()*100:.1f}% (+/- {rf_cv_scores.std()*200:.1f}%)")
        print(f"   Gradient Boosting CV: {gb_cv_scores.mean()*100:.1f}% (+/- {gb_cv_scores.std()*200:.1f}%)")
        
        # Store models
        self.models['random_forest'] = rf_model
        self.models['gradient_boosting'] = gb_model
        
        # Save models
        self._save_models()
        
        print("\n✅ Models trained and saved!")
        
        return {
            'rf_accuracy': rf_accuracy,
            'gb_accuracy': gb_accuracy,
            'rf_cv_mean': rf_cv_scores.mean(),
            'gb_cv_mean': gb_cv_scores.mean()
        }
    
    def predict_confidence(self, pattern, df, price_col='Close'):
        """
        Predict success confidence for a pattern
        
        Args:
            pattern (dict): Pattern dictionary
            df (pd.DataFrame): Price data
            price_col (str): Price column name
        
        Returns:
            dict: Prediction results
        """
        if not self.models:
            return {
                'ai_confidence': pattern['confidence'],  # Fallback to geometry confidence
                'success_probability': None,
                'model_used': 'geometry_only'
            }
        
        # Extract features
        features = self.extract_features(pattern, df, price_col)
        
        # Convert to DataFrame and encode
        features_df = pd.DataFrame([features])
        X = pd.get_dummies(features_df, columns=['pattern_type', 'direction'])
        
        # Ensure all training features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0
        
        # Reorder columns to match training
        X = X[self.feature_names]
        
        # Get predictions from both models
        rf_prob = self.models['random_forest'].predict_proba(X)[0][1]
        gb_prob = self.models['gradient_boosting'].predict_proba(X)[0][1]
        
        # Average the probabilities
        avg_prob = (rf_prob + gb_prob) / 2
        
        return {
            'ai_confidence': int(avg_prob * 100),
            'success_probability': avg_prob,
            'rf_probability': rf_prob,
            'gb_probability': gb_prob,
            'model_used': 'ensemble'
        }
    
    def _save_models(self):
        """Save trained models to disk"""
        for name, model in self.models.items():
            filepath = os.path.join(self.model_dir, f'{name}.pkl')
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
        
        # Save feature names
        features_path = os.path.join(self.model_dir, 'feature_names.pkl')
        with open(features_path, 'wb') as f:
            pickle.dump(self.feature_names, f)
    
    def _load_models(self):
        """Load trained models from disk"""
        try:
            # Load Random Forest
            rf_path = os.path.join(self.model_dir, 'random_forest.pkl')
            if os.path.exists(rf_path):
                with open(rf_path, 'rb') as f:
                    self.models['random_forest'] = pickle.load(f)
            
            # Load Gradient Boosting
            gb_path = os.path.join(self.model_dir, 'gradient_boosting.pkl')
            if os.path.exists(gb_path):
                with open(gb_path, 'rb') as f:
                    self.models['gradient_boosting'] = pickle.load(f)
            
            # Load feature names
            features_path = os.path.join(self.model_dir, 'feature_names.pkl')
            if os.path.exists(features_path):
                with open(features_path, 'rb') as f:
                    self.feature_names = pickle.load(f)
            
            if self.models:
                print(f"✅ Loaded {len(self.models)} trained models")
        
        except Exception as e:
            print(f"⚠️  Could not load models: {e}")


# Convenience function
def get_ai_scorer():
    """Get or create AI confidence scorer instance"""
    return AIConfidenceScorer()
