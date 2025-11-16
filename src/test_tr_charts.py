"""
Test TR Indicator Chart Plotter
Generates sample charts to demonstrate TR visualization
"""

import sys
import os
import matplotlib.pyplot as plt

# Add src directory to path if needed
sys.path.append('src')

from tr_chart_plotter import (
    plot_tr_indicator_chart,
    plot_tr_with_buy_zones,
    quick_tr_chart
)


def test_basic_tr_chart():
    """Test basic TR indicator chart with bands and markers"""
    print("\n" + "="*80)
    print("🎨 TEST 1: BASIC TR INDICATOR CHART")
    print("="*80)
    
    ticker = 'AAPL'
    print(f"\n📊 Generating basic TR chart for {ticker}...")
    
    # This will fetch data and create chart
    fig = quick_tr_chart(
        ticker=ticker,
        timeframe='daily',
        duration_days=180,
        chart_type='basic'
    )
    
    if fig:
        print("✅ Basic chart created successfully!")
    else:
        print("❌ Failed to create chart")


def test_enhanced_tr_chart():
    """Test enhanced TR chart with buy zones and signals"""
    print("\n" + "="*80)
    print("🎨 TEST 2: ENHANCED TR CHART (with Buy Zones)")
    print("="*80)
    
    ticker = 'MSFT'
    print(f"\n📊 Generating enhanced TR chart for {ticker}...")
    
    fig = quick_tr_chart(
        ticker=ticker,
        timeframe='daily',
        duration_days=180,
        chart_type='enhanced'
    )
    
    if fig:
        print("✅ Enhanced chart created successfully!")
    else:
        print("❌ Failed to create chart")


def test_weekly_chart():
    """Test weekly timeframe chart"""
    print("\n" + "="*80)
    print("🎨 TEST 3: WEEKLY TR CHART")
    print("="*80)
    
    ticker = 'TSLA'
    print(f"\n📊 Generating weekly TR chart for {ticker}...")
    
    fig = quick_tr_chart(
        ticker=ticker,
        timeframe='weekly',
        duration_days=730,  # 2 years
        chart_type='enhanced'
    )
    
    if fig:
        print("✅ Weekly chart created successfully!")
    else:
        print("❌ Failed to create chart")


def test_multiple_stocks():
    """Test charting multiple stocks"""
    print("\n" + "="*80)
    print("🎨 TEST 4: MULTIPLE STOCKS COMPARISON")
    print("="*80)
    
    tickers = ['NVDA', 'META', 'GOOGL']
    
    for ticker in tickers:
        print(f"\n📊 Creating chart for {ticker}...")
        
        fig = quick_tr_chart(
            ticker=ticker,
            timeframe='daily',
            duration_days=90,  # 3 months
            chart_type='basic'
        )
        
        if fig:
            print(f"   ✅ {ticker} chart complete")
        else:
            print(f"   ❌ {ticker} chart failed")


def test_custom_chart():
    """Test creating chart with custom data"""
    print("\n" + "="*80)
    print("🎨 TEST 5: CUSTOM CHART FROM EXISTING DATA")
    print("="*80)
    
    # Import required modules
    from tr_enhanced import analyze_stock_complete_tr
    
    ticker = 'AAPL'
    print(f"\n📊 Fetching data for {ticker}...")
    
    # Get TR data
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe='daily',
        duration_days=180
    )
    
    if df is not None:
        print(f"✅ Data fetched: {len(df)} rows")
        
        # Create custom chart
        print("\n🎨 Creating custom chart...")
        
        fig = plot_tr_with_buy_zones(
            df=df,
            ticker=ticker,
            timeframe='Daily',
            save_path=f'charts/{ticker}_Custom_TR_Chart.png',
            figsize=(20, 12)
        )
        
        print("✅ Custom chart created!")
        plt.show()
    else:
        print("❌ Could not fetch data")


def run_all_tests():
    """Run all chart tests"""
    print("\n" + "="*80)
    print("🎨 TR INDICATOR CHART PLOTTER - COMPREHENSIVE TEST")
    print("="*80)
    
    # Create charts directory if it doesn't exist
    os.makedirs('charts', exist_ok=True)
    print("✅ Charts directory ready")
    
    # Run tests
    tests = [
        ("Basic TR Chart", test_basic_tr_chart),
        ("Enhanced TR Chart", test_enhanced_tr_chart),
        ("Weekly Chart", test_weekly_chart),
        ("Multiple Stocks", test_multiple_stocks),
        ("Custom Chart", test_custom_chart)
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED!")
    print("="*80)
    print("\n📁 Check the 'charts/' directory for saved images")


if __name__ == "__main__":
    # You can run individual tests or all tests
    
    # Option 1: Run all tests
    run_all_tests()
    
    # Option 2: Run individual test (uncomment to use)
    # test_basic_tr_chart()
    # test_enhanced_tr_chart()
    # test_weekly_chart()
    # test_custom_chart()
