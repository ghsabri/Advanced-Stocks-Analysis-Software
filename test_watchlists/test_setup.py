import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import requests

# Load API keys from .env file
load_dotenv()

print("=" * 50)
print("TESTING YOUR SETUP")
print("=" * 50)

# Test 1: Check Python packages
print("\n✓ Pandas version:", pd.__version__)
print("✓ NumPy version:", np.__version__)
print("✓ Requests package: OK")

# Test 2: Check API keys are loaded
tiingo_key = os.getenv('TIINGO_API_KEY')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if tiingo_key:
    print("✓ Tiingo API key: Loaded")
else:
    print("✗ Tiingo API key: NOT FOUND - check .env file")

if supabase_url:
    print("✓ Supabase URL: Loaded")
else:
    print("✗ Supabase URL: NOT FOUND - check .env file")

if supabase_key:
    print("✓ Supabase Key: Loaded")
else:
    print("✗ Supabase Key: NOT FOUND - check .env file")

# Test 3: Test Tiingo API connection
print("\n" + "=" * 50)
print("TESTING TIINGO API CONNECTION")
print("=" * 50)

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {tiingo_key}'
}

try:
    response = requests.get('https://api.tiingo.com/api/test', headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✓ Tiingo API: Connected successfully!")
        print("  Message:", data.get('message', 'OK'))
    else:
        print("✗ Tiingo API: Connection failed")
        print("  Status code:", response.status_code)
except Exception as e:
    print("✗ Tiingo API: Error -", str(e))

print("\n" + "=" * 50)
print("SETUP TEST COMPLETE!")
print("=" * 50)