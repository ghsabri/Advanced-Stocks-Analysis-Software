"""
Stock Data Cache Manager
Saves API calls by caching stock data locally
"""

import os
import pandas as pd
import json
from datetime import datetime, timedelta
import pickle


class StockDataCache:
    """
    Cache manager for stock data
    - Stores data locally to avoid repeated API calls
    - Auto-refreshes after expiry time
    - Saves both raw data and TR analysis results
    """
    
    def __init__(self, cache_dir='cache'):
        """
        Initialize cache manager
        
        Args:
            cache_dir (str): Directory to store cache files
        """
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache settings
        self.cache_expiry_hours = 24  # Refresh daily data after 24 hours
        
    def get_cache_filename(self, ticker, timeframe, duration):
        """Generate cache filename"""
        # Sanitize inputs to ensure they're strings and valid for filenames
        ticker_clean = str(ticker).replace('/', '_').replace('\\', '_')
        timeframe_clean = str(timeframe).replace(' ', '_')
        duration_clean = str(duration).replace(' ', '_')
        return f"{self.cache_dir}/{ticker_clean}_{timeframe_clean}_{duration_clean}_cache.pkl"
    
    def get_metadata_filename(self, ticker, timeframe, duration):
        """Generate metadata filename"""
        # Sanitize inputs to ensure they're strings and valid for filenames
        ticker_clean = str(ticker).replace('/', '_').replace('\\', '_')
        timeframe_clean = str(timeframe).replace(' ', '_')
        duration_clean = str(duration).replace(' ', '_')
        return f"{self.cache_dir}/{ticker_clean}_{timeframe_clean}_{duration_clean}_meta.json"
    
    def is_cache_valid(self, ticker, timeframe, duration):
        """
        Check if cached data exists and is still valid
        
        Returns:
            bool: True if cache is valid, False otherwise
        """
        meta_file = self.get_metadata_filename(ticker, timeframe, duration)
        
        if not os.path.exists(meta_file):
            return False
        
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if cache has expired
            cached_time = datetime.fromisoformat(metadata['cached_at'])
            expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)
            
            if datetime.now() > expiry_time:
                print(f"   ⚠️  Cache expired (older than {self.cache_expiry_hours} hours)")
                return False
            
            print(f"   ✅ Using cached data from {cached_time.strftime('%Y-%m-%d %H:%M')}")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Cache validation error: {e}")
            return False
    
    def save_to_cache(self, ticker, timeframe, duration, dataframe):
        """
        Save dataframe to cache
        
        Args:
            ticker (str): Stock symbol
            timeframe (str): Daily or Weekly
            duration (str): Duration string
            dataframe (pd.DataFrame): Data to cache
        """
        cache_file = self.get_cache_filename(ticker, timeframe, duration)
        meta_file = self.get_metadata_filename(ticker, timeframe, duration)
        
        try:
            # Save dataframe
            with open(cache_file, 'wb') as f:
                pickle.dump(dataframe, f)
            
            # Save metadata - convert dates to strings for JSON serialization
            date_min = str(dataframe['Date'].min()) if 'Date' in dataframe.columns else 'N/A'
            date_max = str(dataframe['Date'].max()) if 'Date' in dataframe.columns else 'N/A'
            
            metadata = {
                'ticker': str(ticker),
                'timeframe': str(timeframe),
                'duration': str(duration),
                'cached_at': datetime.now().isoformat(),
                'rows': int(len(dataframe)),
                'date_range': {
                    'start': date_min,
                    'end': date_max
                }
            }
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"   💾 Data cached: {len(dataframe)} rows")
            
        except Exception as e:
            print(f"   ⚠️  Failed to save cache: {e}")
            import traceback
            traceback.print_exc()
    
    def load_from_cache(self, ticker, timeframe, duration):
        """
        Load dataframe from cache
        
        Returns:
            pd.DataFrame or None: Cached dataframe if exists, None otherwise
        """
        cache_file = self.get_cache_filename(ticker, timeframe, duration)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                dataframe = pickle.load(f)
            
            print(f"   📂 Loaded from cache: {len(dataframe)} rows")
            return dataframe
            
        except Exception as e:
            print(f"   ⚠️  Failed to load cache: {e}")
            return None
    
    def clear_cache(self, ticker=None):
        """
        Clear cache files
        
        Args:
            ticker (str, optional): Clear only this ticker's cache. If None, clear all.
        """
        if ticker:
            # Clear specific ticker
            pattern = f"{ticker}_*"
            print(f"   🗑️  Clearing cache for {ticker}...")
        else:
            # Clear all
            pattern = "*"
            print(f"   🗑️  Clearing all cache...")
        
        import glob
        
        files = glob.glob(f"{self.cache_dir}/{pattern}")
        count = 0
        
        for file in files:
            try:
                os.remove(file)
                count += 1
            except Exception as e:
                print(f"   ⚠️  Failed to delete {file}: {e}")
        
        print(f"   ✅ Cleared {count} cache files")
    
    def get_cache_info(self):
        """
        Get information about all cached data
        
        Returns:
            list: List of cache information dictionaries
        """
        import glob
        
        meta_files = glob.glob(f"{self.cache_dir}/*_meta.json")
        cache_info = []
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if expired
                cached_time = datetime.fromisoformat(metadata['cached_at'])
                expiry_time = cached_time + timedelta(hours=self.cache_expiry_hours)
                is_expired = datetime.now() > expiry_time
                
                metadata['is_expired'] = is_expired
                metadata['expiry_time'] = expiry_time.isoformat()
                
                cache_info.append(metadata)
                
            except Exception as e:
                print(f"   ⚠️  Error reading {meta_file}: {e}")
        
        return cache_info
    
    def print_cache_summary(self):
        """Print summary of cached data"""
        cache_info = self.get_cache_info()
        
        if not cache_info:
            print("\n📁 Cache is empty")
            return
        
        print("\n" + "="*80)
        print("📁 CACHE SUMMARY")
        print("="*80)
        
        print(f"\nTotal cached items: {len(cache_info)}")
        print(f"Cache directory: {self.cache_dir}/")
        print(f"Cache expiry: {self.cache_expiry_hours} hours")
        
        print("\n" + "-"*80)
        print(f"{'Ticker':<8} {'Timeframe':<10} {'Duration':<12} {'Rows':<8} {'Status':<10} {'Cached At':<20}")
        print("-"*80)
        
        for info in cache_info:
            ticker = info['ticker']
            timeframe = info['timeframe']
            duration = info['duration']
            rows = info['rows']
            status = '⚠️ Expired' if info['is_expired'] else '✅ Valid'
            cached_at = datetime.fromisoformat(info['cached_at']).strftime('%Y-%m-%d %H:%M')
            
            print(f"{ticker:<8} {timeframe:<10} {duration:<12} {rows:<8} {status:<10} {cached_at:<20}")
        
        print("="*80 + "\n")


# Global cache instance
_cache_instance = None

def get_cache():
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = StockDataCache()
    return _cache_instance


if __name__ == "__main__":
    # Test the cache system
    cache = StockDataCache()
    
    print("\n" + "="*80)
    print("CACHE SYSTEM TEST")
    print("="*80)
    
    # Create test data
    test_df = pd.DataFrame({
        'Date': pd.date_range(end=datetime.now(), periods=100),
        'Close': [150 + i for i in range(100)]
    })
    
    # Save to cache
    print("\n1. Saving test data to cache...")
    cache.save_to_cache('TEST', 'Daily', '1 Year', test_df)
    
    # Check if valid
    print("\n2. Checking cache validity...")
    is_valid = cache.is_cache_valid('TEST', 'Daily', '1 Year')
    print(f"   Cache valid: {is_valid}")
    
    # Load from cache
    print("\n3. Loading from cache...")
    loaded_df = cache.load_from_cache('TEST', 'Daily', '1 Year')
    print(f"   Loaded {len(loaded_df)} rows")
    
    # Show cache summary
    cache.print_cache_summary()
    
    # Clear test cache
    print("\n4. Clearing test cache...")
    cache.clear_cache('TEST')
    
    print("\n✅ Cache system test complete!")
    print("="*80)
