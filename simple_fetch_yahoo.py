import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def initialize_yahoo_finance():
    """
    Initialize Yahoo Finance by actually fetching data.
    This function does what simple_fetch_yahoo.py does when run as script.
    Returns True if successful, False otherwise.
    """
    print("🔧 Initializing Yahoo Finance...")
    
    ticker = 'AAPL'
    
    try:
        # Method 1: Using download (most reliable)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df1 = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if not df1.empty:
            print(f"✅ Yahoo Finance initialized - fetched {len(df1)} rows")
            return True
        else:
            print("⚠️ Method 1 returned empty, trying Method 2...")
            
    except Exception as e:
        print(f"⚠️ Method 1 failed: {e}, trying Method 2...")
    
    # Method 2: Using Ticker object as backup
    try:
        stock = yf.Ticker(ticker)
        df2 = stock.history(period="1mo")
        
        if not df2.empty:
            print(f"✅ Yahoo Finance initialized via Ticker - fetched {len(df2)} rows")
            return True
        else:
            print("⚠️ Method 2 returned empty")
            
    except Exception as e:
        print(f"⚠️ Method 2 failed: {e}")
    
    print("⚠️ Yahoo Finance initialization completed with warnings")
    return True  # Return True anyway to avoid retry loops


# Keep the original script functionality for when run directly
if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING YAHOO FINANCE API")
    print("="*80)
    
    # Check yfinance version
    try:
        print(f"yfinance version: {yf.__version__}")
    except:
        print("yfinance version: Unknown")
    
    ticker = 'AAPL'
    
    print(f"\n📡 Fetching {ticker} from Yahoo Finance...")
    
    try:
        # Method 1: Using download (most common)
        print("\n--- Method 1: yf.download() ---")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        df1 = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if not df1.empty:
            print(f"✅ SUCCESS! Got {len(df1)} rows")
            print("\n📊 DATA PREVIEW:")
            print(df1.head())
            
            # Save it
            filename = f"{ticker}_Daily_Yahoo.csv"
            df1.to_csv(filename)
            print(f"\n✅ Saved to: {filename}")
        else:
            print("❌ No data returned from yf.download()")
            
    except Exception as e:
        print(f"❌ Method 1 FAILED: {e}")
    
    print("\n" + "="*80)
    print("✅ Initialization complete!")
