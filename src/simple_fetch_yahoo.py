import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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

# Method 2: Using Ticker object
try:
    print("\n--- Method 2: yf.Ticker() ---")
    stock = yf.Ticker(ticker)
    
    # Get history
    df2 = stock.history(period="1mo")
    
    if not df2.empty:
        print(f"✅ SUCCESS! Got {len(df2)} rows")
        print("\n📊 DATA PREVIEW:")
        print(df2.head())
        
        # Format like your app expects
        df2_formatted = df2.reset_index()
        df2_formatted['Symbol'] = ticker
        df2_formatted['TimeFrame'] = 'Daily'
        
        # Rename columns to match your format
        df2_formatted = df2_formatted.rename(columns={'index': 'Date'})
        
        # Ensure Date is formatted correctly
        df2_formatted['Date'] = pd.to_datetime(df2_formatted['Date']).dt.date
        
        # Reorder columns
        columns = ['Symbol', 'TimeFrame', 'Date', 'Volume', 'Open', 'High', 'Low', 'Close']
        existing_cols = [col for col in columns if col in df2_formatted.columns]
        df2_formatted = df2_formatted[existing_cols]
        
        print("\n📊 FORMATTED DATA:")
        print(df2_formatted.head())
        
        # Save it
        filename2 = f"{ticker}_Daily_Yahoo_Formatted.csv"
        df2_formatted.to_csv(filename2, index=False)
        print(f"\n✅ Saved to: {filename2}")
        
    else:
        print("❌ No data returned from Ticker.history()")
        
except Exception as e:
    print(f"❌ Method 2 FAILED: {e}")

print("\n" + "="*80)

# Method 3: Check if ticker info is accessible
try:
    print("\n--- Method 3: Ticker Info Check ---")
    stock = yf.Ticker(ticker)
    info = stock.info
    
    if info and 'shortName' in info:
        print(f"✅ Ticker info accessible")
        print(f"   Company: {info.get('shortName', 'N/A')}")
        print(f"   Current Price: ${info.get('currentPrice', 'N/A')}")
        print(f"   Market Cap: ${info.get('marketCap', 'N/A'):,}")
    else:
        print("⚠️ Ticker info returned but incomplete")
        
except Exception as e:
    print(f"❌ Method 3 FAILED: {e}")

print("\n" + "="*80)
print("🎯 CONCLUSION:")
print("="*80)

# Summary
if 'df1' in locals() and not df1.empty:
    print("✅ Yahoo Finance is WORKING (Method 1 succeeded)")
elif 'df2' in locals() and not df2.empty:
    print("✅ Yahoo Finance is WORKING (Method 2 succeeded)")
else:
    print("❌ Yahoo Finance is NOT WORKING")
    print("\n💡 SOLUTIONS:")
    print("   1. Upgrade yfinance: pip install --upgrade yfinance")
    print("   2. Use Tiingo API instead (already working for you)")
    print("   3. Check your internet connection")

print("="*80)
