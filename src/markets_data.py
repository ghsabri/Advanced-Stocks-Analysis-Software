"""
Markets Data Fetcher
Fetches major market indices data in batch from Yahoo Finance
Uses ACTUAL INDEX SYMBOLS for correct values
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# Market indices configuration - ACTUAL INDEX SYMBOLS
MARKETS = {
    'S&P 500': '^GSPC',
    'Nasdaq Composite': '^IXIC',  # Updated from "Nasdaq Comp"
    'Nasdaq 100': '^NDX',
    'Dow Jones Industrial': '^DJI',  # Updated from "Dow Jones Ind"
    'Russell 2000 (Small Stocks)': 'IWM',  # Updated from "Russell 2000 - ETF"
    'VIX': '^VIX',  # Updated from "CBOE VIX"
    'Gold': 'GLD',
    'USO (United States Oil)': 'USO'
}


def fetch_markets_data_simple():
    """
    Fetch market data using actual index symbols
    Returns current prices without dollar signs
    """
    symbols = list(MARKETS.values())
    
    try:
        # Download current data for all symbols
        data = yf.download(symbols, period='2d', progress=False)
        
        results = []
        
        for market_name, symbol in MARKETS.items():
            try:
                # Get latest and previous close
                if len(symbols) == 1:
                    current = data['Close'].iloc[-1]
                    previous = data['Close'].iloc[-2]
                else:
                    current = data['Close'][symbol].iloc[-1]
                    previous = data['Close'][symbol].iloc[-2]
                
                # Calculate change
                change_value = current - previous
                change_percent = (change_value / previous) * 100
                
                # Determine direction
                if change_value > 0:
                    direction = 'up'
                    arrow = '▲'
                elif change_value < 0:
                    direction = 'down'
                    arrow = '▼'
                else:
                    direction = 'neutral'
                    arrow = '━'
                
                results.append({
                    'market': market_name,
                    'symbol': symbol,
                    'price': float(current),
                    'change': float(change_value),
                    'change_percent': float(change_percent),
                    'direction': direction,
                    'arrow': arrow
                })
                
            except Exception as e:
                print(f"Error processing {market_name}: {e}")
                results.append({
                    'market': market_name,
                    'symbol': symbol,
                    'price': 0,
                    'change': 0,
                    'change_percent': 0,
                    'direction': 'neutral',
                    'arrow': '━'
                })
        
        return results
        
    except Exception as e:
        print(f"Error fetching markets data: {e}")
        return []


# Test function
if __name__ == "__main__":
    print("Fetching markets data...")
    
    markets = fetch_markets_data_simple()
    
    if markets:
        print("\nMarkets Data (NO DOLLAR SIGNS):")
        for m in markets:
            print(f"{m['market']:25} {m['price']:>10,.2f}  {m['arrow']} {m['change']:>8.2f} ({m['change_percent']:>6.2f}%)")
    else:
        print("Failed to fetch markets data")
