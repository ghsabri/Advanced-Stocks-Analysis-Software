"""
Train AI Models Using Yahoo Finance Data (No API Limits!)

This version uses yfinance for unlimited training.
Perfect for development and testing.

For production, use train_ai_models.py (Tiingo version)

Usage:
    python train_ai_models_YAHOO.py
"""

import sys
sys.path.insert(0, './src')

from ai_confidence_yahoo import AIConfidenceScorerYahoo

# Full 44 stocks - No API limits with Yahoo!
TRAINING_TICKERS = [
    # Tech
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'CRM',
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA',
    # Healthcare
    'JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'TMO',
    # Consumer
    'WMT', 'HD', 'DIS', 'NKE', 'SBUX', 'MCD',
    # Industrial
    'BA', 'CAT', 'GE', 'MMM',
    # Energy
    'XOM', 'CVX', 'COP',
    # Communication
    'T', 'VZ', 'NFLX',
    # ETFs
    'SPY', 'QQQ', 'IWM', 'DIA'
]

def main():
    """Train AI models using Yahoo Finance data"""
    
    print("="*70)
    print(" " * 15 + "AI MODEL TRAINING")
    print(" " * 10 + "Using Yahoo Finance (No API Limits!)")
    print("="*70)
    print()
    
    # Initialize Yahoo scorer
    scorer = AIConfidenceScorerYahoo(model_dir='models')
    
    print(f"📊 Training on {len(TRAINING_TICKERS)} stocks")
    print(f"📡 Data source: Yahoo Finance (unlimited)")
    print(f"⏱️  This will take 15-30 minutes...")
    print()
    
    # Collect training data
    features_df, labels_series = scorer.collect_training_data(
        tickers=TRAINING_TICKERS,
        lookback_years=3
    )
    
    if len(features_df) < 100:
        print("\n❌ Not enough training data collected!")
        print(f"   Only {len(features_df)} patterns found")
        print("   Need at least 100 patterns")
        return
    
    print(f"\n✅ Collected {len(features_df)} labeled patterns")
    print(f"   Success rate: {labels_series.mean()*100:.1f}%")
    print(f"   Failure rate: {(1-labels_series.mean())*100:.1f}%")
    
    # Train models
    results = scorer.train_models(features_df, labels_series)
    
    print("\n" + "="*70)
    print(" " * 20 + "TRAINING COMPLETE!")
    print("="*70)
    print()
    print(f"✅ Random Forest Accuracy: {results['rf_accuracy']*100:.1f}%")
    print(f"✅ Gradient Boosting Accuracy: {results['gb_accuracy']*100:.1f}%")
    print()
    print(f"📊 Cross-Validation:")
    print(f"   Random Forest: {results['rf_cv_mean']*100:.1f}%")
    print(f"   Gradient Boosting: {results['gb_cv_mean']*100:.1f}%")
    print()
    print(f"💾 Models saved to: models/")
    print()
    print("✅ AI confidence scoring is now active!")
    print("   These models work with BOTH Yahoo and Tiingo data")
    print()
    print("💡 For production with Tiingo, the models are already trained!")
    print("   No need to retrain - they work universally!")
    print()

if __name__ == '__main__':
    main()
