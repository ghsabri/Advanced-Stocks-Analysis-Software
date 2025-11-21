import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

print("Testing Supabase connection...\n")

# Get credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"URL: {url}")
print(f"Key: {key[:20]}..." if key else "Key: NOT FOUND")
print()

if not url or not key:
    print("❌ Missing credentials in .env file!")
    print("Please check your .env file has:")
    print("  SUPABASE_URL=https://xxxxx.supabase.co")
    print("  SUPABASE_KEY=eyJhbGc...")
    exit()

try:
    # Create Supabase client
    supabase: Client = create_client(url, key)
    print("✅ Supabase client created successfully!")
    
    # Try a simple query to test connection
    # This will fail if tables don't exist yet, but that's ok
    response = supabase.table('watchlists').select("*").limit(1).execute()
    print("✅ Connection works! Database is accessible.")
    print(f"   Tables exist and can be queried.")
    
except Exception as e:
    error_str = str(e)
    
    if "relation" in error_str and "does not exist" in error_str:
        print("✅ Connection works!")
        print("⚠️  Tables don't exist yet (expected - we'll create them next)")
    elif "Invalid API key" in error_str or "JWT" in error_str:
        print("❌ Invalid credentials!")
        print("   Your Supabase project may have been paused/deleted.")
        print("   You'll need to:")
        print("   1. Go to https://supabase.com/dashboard")
        print("   2. Check if project exists and is active")
        print("   3. If paused, restore it")
        print("   4. Get new credentials and update .env")
    else:
        print(f"❌ Connection error: {error_str}")

print("\n" + "="*60)