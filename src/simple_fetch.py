import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('TIINGO_API_KEY')

print(f"API Key loaded: {api_key[:10]}..." if api_key else "❌ No API key!")

# Fetch AAPL data
ticker = 'AAPL'
url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {api_key}'
}

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

params = {
    'startDate': start_date,
    'endDate': end_date
}

print(f"📡 Fetching {ticker}...")

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Got {len(data)} rows")
    
    # Format data
    rows = []
    for day in data:
        rows.append({
            'Symbol': ticker,
            'TimeFrame': 'Daily',
            'Date': day['date'][:10],
            'Volume': int(day['volume']),
            'Open': round(day['open'], 2),
            'High': round(day['high'], 2),
            'Low': round(day['low'], 2),
            'Close': round(day['close'], 2)
        })
    
    df = pd.DataFrame(rows)
    
    # Print first few rows
    print("\n" + "="*80)
    print("📊 DATA PREVIEW:")
    print("="*80)
    print(df.head())
    
    # Save to current directory (wherever you run from)
    filename = f"data/{ticker}_Daily.csv"
    
    # Try to save
    try:
        df.to_csv(filename, index=False)
        print(f"\n✅ Saved to: {filename}")
        print(f"Full path: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"\n❌ Error saving: {e}")
        
        # Try saving to current directory instead
        filename_alt = f"{ticker}_Daily.csv"
        df.to_csv(filename_alt, index=False)
        print(f"✅ Saved to current directory: {os.path.abspath(filename_alt)}")
        
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)