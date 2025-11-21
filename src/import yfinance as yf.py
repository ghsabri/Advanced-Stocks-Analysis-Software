import yfinance as yf
import os

print("yfinance cache location:")
try:
    cache_dir = yf.utils.get_cache_dir()
    print(f"  {cache_dir}")
    
    # List what's in there
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        print(f"\nFiles in cache: {len(files)}")
        for f in files[:10]:  # Show first 10
            print(f"  - {f}")
    else:
        print("  Cache directory doesn't exist yet")
except Exception as e:
    print(f"  Error: {e}")