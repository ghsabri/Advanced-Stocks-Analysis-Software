import requests
print("🔧 Initializing network for Yahoo Finance...")
try:
    # Make a simple request to Yahoo Finance domain
    r = requests.get("https://query1.finance.yahoo.com", timeout=10)
    print(f"✅ Yahoo Finance network initialized (Status: {r.status_code})")
except Exception as e:
    print(f"⚠️ Request warning: {e}")
    print("   (This is OK, initialization should still work)")
print("Done.")