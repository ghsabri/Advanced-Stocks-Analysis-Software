import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()


def fetch_stock_data_tiingo(ticker, timeframe='daily', days=90):
    """
    Fetch stock data from Tiingo API
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL')
        timeframe (str): 'daily' or 'weekly'
        days (int): Number of days of history to fetch
    
    Returns:
        pandas.DataFrame: Stock data in your required format
    """
    
    # Get API key
    api_key = os.getenv('TIINGO_API_KEY')
    
    if not api_key:
        print("❌ Error: TIINGO_API_KEY not found in .env file")
        return None
    
    # Tiingo API endpoint
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {api_key}'
    }
    
    # Date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Parameters
    params = {
        'startDate': start_date,
        'endDate': end_date,
        'resampleFreq': timeframe  # 'daily' or 'weekly'
    }
    
    try:
        print(f"📡 Fetching {timeframe} data for {ticker}...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully fetched {len(data)} {timeframe} records")
            return data
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def format_for_tr_indicator(ticker, raw_data, timeframe='Daily'):
    """
    Format data into YOUR required structure for TR Indicator
    
    Columns:
    1. Symbol
    2. TimeFrame (Daily/Weekly/Monthly)
    3. Date
    4. Volume
    5. Open
    6. High
    7. Low
    8. Close
    
    Args:
        ticker (str): Stock symbol
        raw_data (list): Raw data from Tiingo
        timeframe (str): 'Daily' or 'Weekly' (capitalized for display)
    
    Returns:
        pandas.DataFrame: Formatted data ready for TR indicator
    """
    
    if not raw_data:
        return None
    
    # Create list to hold formatted rows
    formatted_rows = []
    
    for day in raw_data:
        row = {
            'Symbol': ticker.upper(),
            'TimeFrame': timeframe,
            'Date': day['date'][:10],  # Just the date part (YYYY-MM-DD)
            'Volume': int(day['volume']),
            'Open': round(day['open'], 2),
            'High': round(day['high'], 2),
            'Low': round(day['low'], 2),
            'Close': round(day['close'], 2)
        }
        formatted_rows.append(row)
    
    # Create DataFrame with exact column order
    df = pd.DataFrame(formatted_rows, columns=[
        'Symbol', 'TimeFrame', 'Date', 'Volume', 'Open', 'High', 'Low', 'Close'
    ])
    
    return df


def save_to_csv(df, ticker, timeframe='Daily'):
    """
    Save formatted data to CSV file
    
    Args:
        df (pandas.DataFrame): Formatted data
        ticker (str): Stock symbol
        timeframe (str): 'Daily' or 'Weekly'
    """
    
    if df is None or df.empty:
        print("❌ No data to save")
        return None
    
    # Create filename
    filename = f"../data/{ticker}_{timeframe}.csv"
    
    # Save to CSV
    df.to_csv(filename, index=False)
    
    print(f"✅ Saved {len(df)} rows to: {filename}")
    return filename


def display_formatted_data(df, num_rows=10):
    """
    Display formatted data nicely
    
    Args:
        df (pandas.DataFrame): Formatted data
        num_rows (int): Number of rows to display
    """
    
    if df is None or df.empty:
        print("❌ No data to display")
        return
    
    print("\n" + "=" * 100)
    print("📊 FORMATTED STOCK DATA (Ready for TR Indicator)")
    print("=" * 100)
    
    # Display column headers
    print(f"{'Symbol':<8} {'TimeFrame':<10} {'Date':<12} {'Volume':<12} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8}")
    print("-" * 100)
    
    # Display rows (last N rows - most recent)
    for _, row in df.tail(num_rows).iterrows():
        print(f"{row['Symbol']:<8} {row['TimeFrame']:<10} {row['Date']:<12} "
              f"{row['Volume']:<12,} ${row['Open']:<7.2f} ${row['High']:<7.2f} "
              f"${row['Low']:<7.2f} ${row['Close']:<7.2f}")
    
    print("-" * 100)
    print(f"Total rows: {len(df)}")
    print("=" * 100)


def get_stock_data_formatted(ticker, timeframe='daily', days=90, save=True):
    """
    Main function: Fetch, format, and optionally save stock data
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'daily' or 'weekly' (lowercase for API)
        days (int): Days of history
        save (bool): Whether to save to CSV
    
    Returns:
        pandas.DataFrame: Formatted data
    """
    
    # Fetch raw data from Tiingo
    raw_data = fetch_stock_data_tiingo(ticker, timeframe, days)
    
    if not raw_data:
        return None
    
    # Format for TR indicator (capitalize timeframe for display)
    timeframe_display = timeframe.capitalize()
    df = format_for_tr_indicator(ticker, raw_data, timeframe_display)
    
    # Display
    display_formatted_data(df)
    
    # Save to CSV if requested
    if save:
        save_to_csv(df, ticker, timeframe_display)
    
    return df


# MAIN EXECUTION
if __name__ == "__main__":
    
    print("\n🚀 STOCK DATA FORMATTER FOR TR INDICATOR")
    print("=" * 100)
    
    # Example 1: Get AAPL daily data (last 90 days)
    print("\n📈 Example 1: AAPL Daily Data")
    print("-" * 100)
    aapl_daily = get_stock_data_formatted('AAPL', timeframe='daily', days=90, save=True)
    
    # Example 2: Get MSFT weekly data
    print("\n\n📈 Example 2: MSFT Weekly Data")
    print("-" * 100)
    msft_weekly = get_stock_data_formatted('MSFT', timeframe='weekly', days=365, save=True)
    
    # Example 3: Get TSLA daily data (last 30 days only)
    print("\n\n📈 Example 3: TSLA Daily Data (30 days)")
    print("-" * 100)
    tsla_daily = get_stock_data_formatted('TSLA', timeframe='daily', days=30, save=True)
    
    print("\n\n✅ ALL DATA FORMATTED AND SAVED!")
    print("=" * 100)
    print("\n📁 Check your 'data' folder for CSV files:")
    print("   • AAPL_Daily.csv")
    print("   • MSFT_Weekly.csv")
    print("   • TSLA_Daily.csv")
    print("\n💡 These files are ready to use with your TR Indicator!")
    print("\n📋 Column Order: Symbol | TimeFrame | Date | Volume | Open | High | Low | Close")