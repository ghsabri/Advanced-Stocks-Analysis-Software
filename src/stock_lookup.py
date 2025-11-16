"""
Stock Lookup Module - Hybrid Smart Cache System
Combines local StocksList CSV with Yahoo Finance API fallback
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import yfinance as yf


class StockLookup:
    """
    Hybrid stock information lookup system
    
    Priority:
    1. Local StocksList CSV (5,738 stocks) - INSTANT
    2. API Cache (30-day expiry) - FAST
    3. Yahoo Finance API - SLOW but always current
    """
    
    def __init__(self, csv_path='stocks_list.csv'):
        """Initialize with StocksList CSV"""
        self.csv_path = csv_path
        self.stocks_df = None
        self.api_cache = {}  # In-memory cache
        self.cache_expiry_days = 30
        
        # Load StocksList CSV
        self._load_stocks_list()
    
    def _load_stocks_list(self):
        """Load the StocksList CSV into memory"""
        try:
            if os.path.exists(self.csv_path):
                self.stocks_df = pd.read_csv(self.csv_path)
                self.stocks_df['Symbol'] = self.stocks_df['Symbol'].str.upper()
                print(f"✅ Loaded {len(self.stocks_df)} stocks from StocksList")
            else:
                print(f"⚠️ StocksList not found: {self.csv_path}")
                self.stocks_df = pd.DataFrame()
        except Exception as e:
            print(f"❌ Error loading StocksList: {e}")
            self.stocks_df = pd.DataFrame()
    
    def get_stock_info(self, ticker):
        """
        Get stock information using hybrid lookup
        
        Args:
            ticker (str): Stock symbol
        
        Returns:
            dict: Stock information including sector, industry, exchange, etc.
        """
        ticker = ticker.upper().strip()
        
        # PRIORITY 1: Check StocksList (INSTANT)
        if not self.stocks_df.empty:
            stock_row = self.stocks_df[self.stocks_df['Symbol'] == ticker]
            if not stock_row.empty:
                return self._format_stock_info(stock_row.iloc[0], source='StocksList')
        
        # PRIORITY 2: Check API Cache (FAST)
        if ticker in self.api_cache:
            cached_data = self.api_cache[ticker]
            # Check if cache is still valid (30 days)
            if datetime.now() - cached_data['timestamp'] < timedelta(days=self.cache_expiry_days):
                print(f"✅ Using cached data for {ticker}")
                return cached_data['info']
        
        # PRIORITY 3: Fetch from Yahoo Finance (SLOW)
        print(f"🔄 Fetching {ticker} from Yahoo Finance...")
        yahoo_info = self._fetch_from_yahoo(ticker)
        
        if yahoo_info:
            # Cache the result
            self.api_cache[ticker] = {
                'info': yahoo_info,
                'timestamp': datetime.now()
            }
            return yahoo_info
        
        return None
    
    def _format_stock_info(self, row, source='StocksList'):
        """Format stock information from StocksList row"""
        return {
            'symbol': row['Symbol'],
            'name': row['Name'],
            'exchange': row['Exchange'],
            'sector': row['Sector'],
            'sector_etf': row['Sector'],  # XLK, XLV, etc.
            'industry': row['Industry'],
            'sp500': row['S&P 500'] if 'S&P 500' in row else False,
            'source': source
        }
    
    def _fetch_from_yahoo(self, ticker):
        """Fetch stock information from Yahoo Finance API"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or 'symbol' not in info:
                return None
            
            # Map Yahoo sector to ETF (best effort)
            sector_map = {
                'Technology': 'XLK',
                'Healthcare': 'XLV',
                'Financial Services': 'XLF',
                'Consumer Cyclical': 'XLY',
                'Industrials': 'XLI',
                'Consumer Defensive': 'XLP',
                'Energy': 'XLE',
                'Basic Materials': 'XLB',
                'Real Estate': 'XLRE',
                'Utilities': 'XLU',
                'Communication Services': 'XLC'
            }
            
            sector = info.get('sector', 'Unknown')
            sector_etf = sector_map.get(sector, 'SPY')
            
            return {
                'symbol': ticker,
                'name': info.get('longName', ticker),
                'exchange': info.get('exchange', 'Unknown'),
                'sector': sector,
                'sector_etf': sector_etf,
                'industry': info.get('industry', 'Unknown'),
                'sp500': False,  # Cannot determine from Yahoo
                'source': 'Yahoo Finance API'
            }
            
        except Exception as e:
            print(f"❌ Error fetching {ticker} from Yahoo: {e}")
            return None
    
    def get_sector_etf(self, ticker):
        """Get the sector ETF for a given stock"""
        info = self.get_stock_info(ticker)
        if info:
            return info.get('sector_etf', 'SPY')
        return 'SPY'
    
    def is_sp500(self, ticker):
        """Check if stock is in S&P 500"""
        info = self.get_stock_info(ticker)
        if info:
            return info.get('sp500', False)
        return False
    
    def search_stocks(self, query, limit=10):
        """
        Search for stocks by symbol or name
        
        Args:
            query (str): Search query
            limit (int): Max results
        
        Returns:
            list: Matching stocks
        """
        query = query.upper().strip()
        
        if self.stocks_df.empty:
            return []
        
        # Search by symbol or name
        matches = self.stocks_df[
            self.stocks_df['Symbol'].str.contains(query, na=False) |
            self.stocks_df['Name'].str.upper().str.contains(query, na=False)
        ]
        
        results = []
        for _, row in matches.head(limit).iterrows():
            results.append({
                'symbol': row['Symbol'],
                'name': row['Name'],
                'exchange': row['Exchange'],
                'sector': row['Sector'],
                'industry': row['Industry']
            })
        
        return results
    
    def clear_cache(self):
        """Clear the API cache"""
        self.api_cache.clear()
        print("🗑️ API cache cleared")
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'stocks_list_size': len(self.stocks_df) if not self.stocks_df.empty else 0,
            'api_cache_size': len(self.api_cache),
            'cache_expiry_days': self.cache_expiry_days
        }


# Create global instance
_stock_lookup = None

def get_stock_lookup():
    """Get or create global StockLookup instance"""
    global _stock_lookup
    if _stock_lookup is None:
        # Get the directory where this module is located
        module_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try to find stocks_list.csv in multiple locations
        possible_paths = [
            'stocks_list.csv',  # Current working directory
            os.path.join(module_dir, 'stocks_list.csv'),  # Same dir as module
            os.path.join(module_dir, '..', 'stocks_list.csv'),  # Parent dir (project root)
            os.path.join(module_dir, '..', '..', 'stocks_list.csv'),  # Two levels up
            os.path.join(module_dir, '..', 'data', 'stocks_list.csv'),  # data folder
        ]
        
        csv_path = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                csv_path = abs_path
                print(f"✅ Found StocksList at: {abs_path}")
                break
        
        if csv_path:
            _stock_lookup = StockLookup(csv_path)
        else:
            print("⚠️ StocksList CSV not found in any of these locations:")
            for path in possible_paths:
                print(f"  - {os.path.abspath(path)}")
            print("Using API-only mode")
            _stock_lookup = StockLookup()
    
    return _stock_lookup


# Convenience functions
def get_stock_info(ticker):
    """Get stock information"""
    return get_stock_lookup().get_stock_info(ticker)


def get_sector_etf(ticker):
    """Get sector ETF for stock"""
    return get_stock_lookup().get_sector_etf(ticker)


def is_sp500(ticker):
    """Check if stock is in S&P 500"""
    return get_stock_lookup().is_sp500(ticker)


def search_stocks(query, limit=10):
    """Search for stocks"""
    return get_stock_lookup().search_stocks(query, limit)


# Test function
if __name__ == "__main__":
    print("Testing Stock Lookup System...")
    
    # Test with known stocks
    test_tickers = ['AAPL', 'GOOGL', 'TSLA', 'NEWIPO']
    
    for ticker in test_tickers:
        print(f"\n{'='*50}")
        print(f"Looking up: {ticker}")
        info = get_stock_info(ticker)
        
        if info:
            print(f"✅ Found!")
            print(f"  Name: {info['name']}")
            print(f"  Sector: {info['sector']}")
            print(f"  Sector ETF: {info['sector_etf']}")
            print(f"  Industry: {info['industry']}")
            print(f"  S&P 500: {info['sp500']}")
            print(f"  Source: {info['source']}")
        else:
            print(f"❌ Not found")
    
    # Test search
    print(f"\n{'='*50}")
    print("Testing search: 'Apple'")
    results = search_stocks('Apple', limit=5)
    for r in results:
        print(f"  {r['symbol']}: {r['name']}")
    
    # Cache stats
    print(f"\n{'='*50}")
    print("Cache Statistics:")
    stats = get_stock_lookup().get_cache_stats()
    print(f"  StocksList: {stats['stocks_list_size']} stocks")
    print(f"  API Cache: {stats['api_cache_size']} entries")
    print(f"  Cache Expiry: {stats['cache_expiry_days']} days")
