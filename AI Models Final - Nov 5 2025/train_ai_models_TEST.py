"""
TEST AI Model Training - Uses Only 2 Stocks
For testing purposes to avoid API rate limits

Usage:
    python train_ai_models_TEST.py
"""

import sys
sys.path.insert(0, './src')

from ai_confidence import AIConfidenceScorer

# TEST with only 2 stocks to avoid API limits
TEST_TICKERS = [
    'AAPL',
    'MSFT'
]

def main():
    """Train AI models on minimal data for testing"""
    
    print("="*70)
    print(" " * 15 + "AI MODEL TRAINING - TEST")
    print(" " * 10 + "Using ONLY 2 stocks to test for errors")
    print("="*70)
    print()
    
    # Initialize scorer
    scorer = AIConfidenceScorer(model_dir='models')
    
    print(f"📊 Training on {len(TEST_TICKERS)} stocks (TEST MODE)")
    print(f"⏱️  This will take 2-3 minutes...")
    print()
    
    # Collect training data
    features_df, labels_series = scorer.collect_training_data(
        tickers=TEST_TICKERS,
        lookback_years=3
    )
    
    if len(features_df) < 10:
        print("\n⚠️  Warning: Not enough training data for accurate models!")
        print(f"   Only {len(features_df)} patterns found")
        print("   Need at least 100 patterns for production")
        print("\n   This is just a TEST to check for errors.")
        
        if len(features_df) < 5:
            print("\n❌ Too few patterns to train models")
            return
    
    print(f"\n✅ Collected {len(features_df)} labeled patterns (test data)")
    print(f"   Success rate: {labels_series.mean()*100:.1f}%")
    print(f"   Failure rate: {(1-labels_series.mean())*100:.1f}%")
    
    # Train models (even with small data, just to test)
    print("\n⚠️  Training with limited data (test only)...")
    results = scorer.train_models(features_df, labels_series)
    
    print("\n" + "="*70)
    print(" " * 20 + "TEST COMPLETE!")
    print("="*70)
    print()
    print(f"✅ Code works! No errors detected!")
    print()
    print(f"📊 Test Results:")
    print(f"   Random Forest: {results['rf_accuracy']*100:.1f}%")
    print(f"   Gradient Boosting: {results['gb_accuracy']*100:.1f}%")
    print()
    print(f"⚠️  Note: Accuracy is low because we only used 2 stocks")
    print(f"   For production, run train_ai_models.py with 20-45 stocks")
    print()
    print(f"💾 Test models saved to: models/")
    print()

if __name__ == '__main__':
    main()
