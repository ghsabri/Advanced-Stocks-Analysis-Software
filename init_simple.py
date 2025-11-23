import requests
print("🔧 Testing simple network initialization...")
try:
    r = requests.get("https://api.tiingo.com", timeout=10)
    print(f"✅ Network request successful (Status: {r.status_code})")
except Exception as e:
    print(f"⚠️ Request failed: {e}")
print("Done.")