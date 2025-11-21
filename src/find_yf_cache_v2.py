import os
import yfinance as yf

print("Searching for yfinance cache locations...\n")

# Common cache locations
possible_locations = [
    os.path.expanduser("~/.cache/py-yfinance"),
    os.path.expanduser("~/AppData/Local/py-yfinance"),
    os.path.expanduser("~/AppData/Local/Temp/py-yfinance"),
    os.path.join(os.getcwd(), ".cache"),
    os.path.join(os.getcwd(), "yfinance_cache"),
]

print("Checking possible locations:")
for loc in possible_locations:
    print(f"  {loc}")
    if os.path.exists(loc):
        print(f"    ✅ EXISTS!")
        try:
            files = os.listdir(loc)
            print(f"    Files: {len(files)}")
            if files:
                print(f"    Recent files:")
                for f in files[:5]:
                    print(f"      - {f}")
        except:
            print(f"    (Cannot read)")
    else:
        print(f"    ❌ Not found")
    print()

# Also check if yfinance has a __file__ attribute to find its install location
print("yfinance installation location:")
try:
    print(f"  {yf.__file__}")
    yf_dir = os.path.dirname(yf.__file__)
    cache_in_package = os.path.join(yf_dir, "cache")
    print(f"\nChecking package cache: {cache_in_package}")
    if os.path.exists(cache_in_package):
        print("  ✅ Package cache exists")
    else:
        print("  ❌ No package cache")
except:
    print("  Cannot determine")