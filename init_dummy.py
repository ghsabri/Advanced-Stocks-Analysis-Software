import requests
import pandas as pd
print("🔧 Initializing Python environment...")
try:
    response = requests.get("https://www.google.com", timeout=5)
    print(f"✅ Network initialized (status: {response.status_code})")
except Exception as e:
    print(f"⚠️ Warning: {e}")