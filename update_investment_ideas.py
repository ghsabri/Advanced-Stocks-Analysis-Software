"""
Investment Ideas Updater
========================
Update investment_ideas table in Supabase from CSV or Excel file.

Usage:
    python update_investment_ideas.py <filename.csv>
    python update_investment_ideas.py <filename.xlsx>

CSV/Excel Format:
-----------------
Column header = list_key (must match database)
Rows below = symbols (one per row)

Example - Single list file (weekly_picks.csv):
┌──────────────┐
│ weekly_picks │  <-- header is the list_key
├──────────────┤
│ NVDA         │
│ AAPL         │
│ GOOGL        │
│ TSLA         │
│ META         │
└──────────────┘

Example - Multiple lists in one file (all_lists.csv):
┌──────────────┬──────────┬─────────────┐
│ weekly_picks │ ai_picks │ growth_tech │
├──────────────┼──────────┼─────────────┤
│ NVDA         │ SMCI     │ IONQ        │
│ AAPL         │ AVGO     │ RGTI        │
│ GOOGL        │ AMD      │ QBTS        │
│ TSLA         │ PLTR     │ AMD         │
│ META         │ CRWD     │ NVDA        │
│ AMZN         │          │             │
└──────────────┴──────────┴─────────────┘

(Empty cells are ignored - lists can have different lengths)

Created: December 2025
"""

import os
import sys
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ============================================================================
# CONFIGURATION - Reads from .env file (same as your database.py)
# ============================================================================

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_supabase_client() -> Client:
    """Create Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
        print("   Make sure your .env file exists and contains:")
        print("     SUPABASE_URL=https://your-project.supabase.co")
        print("     SUPABASE_KEY=your-anon-key")
        print("\n   The .env file should be in the same folder as this script")
        print("   or in your project root folder.")
        sys.exit(1)
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================================
# FILE READING
# ============================================================================

def read_file(filename: str) -> dict:
    """
    Read CSV or Excel file and return dict of {list_key: [symbols]}
    
    Each column is a list:
    - Header = list_key
    - Rows = symbols
    """
    if not os.path.exists(filename):
        print(f"❌ ERROR: File not found: {filename}")
        sys.exit(1)
    
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.csv':
            df = pd.read_csv(filename)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filename)
        else:
            print(f"❌ ERROR: Unsupported file type: {ext}")
            print("   Supported formats: .csv, .xlsx, .xls")
            sys.exit(1)
        
        # Convert columns to dict of lists
        lists = {}
        for column in df.columns:
            list_key = str(column).strip()
            
            # Get non-empty values from column
            symbols = df[column].dropna().astype(str).str.strip().str.upper().tolist()
            
            # Remove empty strings
            symbols = [s for s in symbols if s and s != 'NAN']
            
            if symbols:
                lists[list_key] = symbols
        
        print(f"✅ Read {len(lists)} list(s) from {filename}")
        return lists
        
    except Exception as e:
        print(f"❌ ERROR reading file: {e}")
        sys.exit(1)


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_existing_lists(supabase: Client) -> dict:
    """Fetch existing lists from database"""
    try:
        response = supabase.table('investment_ideas').select('*').execute()
        
        if response.data:
            return {item['list_key']: item for item in response.data}
        return {}
        
    except Exception as e:
        print(f"❌ ERROR fetching existing lists: {e}")
        sys.exit(1)


def update_list(supabase: Client, list_key: str, symbols: list) -> bool:
    """Update symbols for a list in database"""
    try:
        data = {
            'symbols': symbols,
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('investment_ideas') \
            .update(data) \
            .eq('list_key', list_key) \
            .execute()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR updating {list_key}: {e}")
        return False


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def preview_changes(new_lists: dict, existing_lists: dict):
    """Show preview of changes"""
    print("\n" + "=" * 60)
    print("📋 PREVIEW OF CHANGES")
    print("=" * 60)
    
    updates = []
    errors = []
    
    for list_key, new_symbols in new_lists.items():
        if list_key in existing_lists:
            old_symbols = existing_lists[list_key].get('symbols', [])
            
            added = set(new_symbols) - set(old_symbols)
            removed = set(old_symbols) - set(new_symbols)
            
            updates.append({
                'list_key': list_key,
                'old_symbols': old_symbols,
                'new_symbols': new_symbols,
                'added': added,
                'removed': removed
            })
        else:
            errors.append(f"List '{list_key}' not found in database")
    
    if errors:
        print(f"\n⚠️  ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
    
    if updates:
        print(f"\n🔄 UPDATES ({len(updates)}):")
        for item in updates:
            print(f"\n   📌 {item['list_key']}:")
            print(f"      Symbols: {len(item['old_symbols'])} → {len(item['new_symbols'])}")
            
            if item['added']:
                print(f"      ✅ Added ({len(item['added'])}): {', '.join(sorted(item['added']))}")
            if item['removed']:
                print(f"      ❌ Removed ({len(item['removed'])}): {', '.join(sorted(item['removed']))}")
            if not item['added'] and not item['removed']:
                print(f"      (no changes)")
            
            print(f"      New list: {', '.join(item['new_symbols'])}")
    
    print("\n" + "=" * 60)
    
    return updates, errors


def apply_changes(supabase: Client, updates: list) -> tuple:
    """Apply changes to database"""
    success_count = 0
    fail_count = 0
    
    print("\n🚀 Applying changes...")
    
    for item in updates:
        list_key = item['list_key']
        new_symbols = item['new_symbols']
        
        # Skip if no actual changes
        if not item['added'] and not item['removed']:
            print(f"   ⏭️  Skipped: {list_key} (no changes)")
            continue
        
        if update_list(supabase, list_key, new_symbols):
            print(f"   ✅ Updated: {list_key}")
            success_count += 1
        else:
            print(f"   ❌ Failed: {list_key}")
            fail_count += 1
    
    return success_count, fail_count


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    print("\n" + "=" * 60)
    print("📊 INVESTMENT IDEAS UPDATER")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\n❌ Usage: python update_investment_ideas.py <filename.csv>")
        print("         python update_investment_ideas.py <filename.xlsx>")
        print("\n📝 CSV Format:")
        print("   Column header = list_key (e.g., weekly_picks)")
        print("   Rows below = symbols (one per row)")
        print("\n   Example (single list):")
        print("   ┌──────────────┐")
        print("   │ weekly_picks │")
        print("   ├──────────────┤")
        print("   │ NVDA         │")
        print("   │ AAPL         │")
        print("   │ GOOGL        │")
        print("   │ TSLA         │")
        print("   └──────────────┘")
        print("\n   Example (multiple lists):")
        print("   ┌──────────────┬──────────┐")
        print("   │ weekly_picks │ ai_picks │")
        print("   ├──────────────┼──────────┤")
        print("   │ NVDA         │ SMCI     │")
        print("   │ AAPL         │ AVGO     │")
        print("   │ GOOGL        │ AMD      │")
        print("   │ TSLA         │ PLTR     │")
        print("   └──────────────┴──────────┘")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Connect to Supabase
    print("\n🔌 Connecting to Supabase...")
    supabase = get_supabase_client()
    print("   ✅ Connected")
    
    # Fetch existing lists
    print("\n📥 Fetching existing lists from database...")
    existing_lists = get_existing_lists(supabase)
    print(f"   Found {len(existing_lists)} lists: {', '.join(existing_lists.keys())}")
    
    # Read input file
    print(f"\n📂 Reading {filename}...")
    new_lists = read_file(filename)
    
    for list_key, symbols in new_lists.items():
        print(f"   • {list_key}: {len(symbols)} symbols")
    
    # Preview changes
    updates, errors = preview_changes(new_lists, existing_lists)
    
    # Check if there are changes to apply
    changes_to_apply = [u for u in updates if u['added'] or u['removed']]
    
    if not changes_to_apply:
        print("\n✅ No changes to apply. Exiting.")
        sys.exit(0)
    
    # Confirm before applying
    print("\n" + "-" * 60)
    response = input("🤔 Apply these changes? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Cancelled. No changes applied.")
        sys.exit(0)
    
    # Apply changes
    success, fail = apply_changes(supabase, updates)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"   ✅ Successful: {success}")
    print(f"   ❌ Failed: {fail}")
    print(f"   ⚠️  Errors: {len(errors)}")
    print("=" * 60)
    
    if fail == 0 and len(errors) == 0:
        print("\n🎉 All updates applied successfully!")
    else:
        print("\n⚠️  Some issues occurred. Please review the output above.")


if __name__ == "__main__":
    main()
