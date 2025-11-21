"""
Database Module - Supabase Integration
Handles all database operations for watchlists
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ═══════════════════════════════════════════════════════════════════
# WATCHLIST OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def create_watchlist(name: str, user_id: str = 'default_user') -> Optional[Dict]:
    """
    Create a new watchlist in database
    
    Args:
        name: Watchlist name
        user_id: User identifier (default: 'default_user')
    
    Returns:
        Dictionary with watchlist data including id, or None if error
    """
    try:
        response = supabase.table('watchlists').insert({
            'name': name,
            'user_id': user_id
        }).execute()
        
        if response.data:
            print(f"✅ Created watchlist: {name} (ID: {response.data[0]['id']})")
            return response.data[0]
        return None
        
    except Exception as e:
        print(f"❌ Error creating watchlist: {e}")
        return None


def get_all_watchlists(user_id: str = 'default_user') -> List[Dict]:
    """
    Get all watchlists for a user
    
    Args:
        user_id: User identifier
    
    Returns:
        List of watchlist dictionaries
    """
    try:
        response = supabase.table('watchlists')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=False)\
            .execute()
        
        if response.data:
            print(f"📋 Loaded {len(response.data)} watchlists from database")
            return response.data
        return []
        
    except Exception as e:
        print(f"❌ Error loading watchlists: {e}")
        return []


def update_watchlist_name(watchlist_id: int, new_name: str) -> bool:
    """
    Update watchlist name
    
    Args:
        watchlist_id: Database ID of watchlist
        new_name: New name for watchlist
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = supabase.table('watchlists')\
            .update({
                'name': new_name,
                'updated_at': datetime.utcnow().isoformat()
            })\
            .eq('id', watchlist_id)\
            .execute()
        
        if response.data:
            print(f"✅ Renamed watchlist {watchlist_id} to: {new_name}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error renaming watchlist: {e}")
        return False


def delete_watchlist(watchlist_id: int) -> bool:
    """
    Delete a watchlist (CASCADE will auto-delete associated stocks)
    
    Args:
        watchlist_id: Database ID of watchlist to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = supabase.table('watchlists')\
            .delete()\
            .eq('id', watchlist_id)\
            .execute()
        
        print(f"🗑️ Deleted watchlist {watchlist_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting watchlist: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# STOCK OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def add_stock_to_watchlist(watchlist_id: int, symbol: str) -> bool:
    """
    Add a stock to a watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
        symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        True if successful, False if already exists or error
    """
    try:
        response = supabase.table('watchlist_stocks').insert({
            'watchlist_id': watchlist_id,
            'symbol': symbol.upper()
        }).execute()
        
        if response.data:
            print(f"✅ Added {symbol} to watchlist {watchlist_id}")
            return True
        return False
        
    except Exception as e:
        error_str = str(e)
        if 'duplicate key' in error_str.lower() or 'unique' in error_str.lower():
            print(f"ℹ️ {symbol} already in watchlist {watchlist_id}")
            return False
        print(f"❌ Error adding stock: {e}")
        return False


def get_watchlist_stocks(watchlist_id: int) -> List[str]:
    """
    Get all stocks in a watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
    
    Returns:
        List of stock symbols
    """
    try:
        response = supabase.table('watchlist_stocks')\
            .select('symbol')\
            .eq('watchlist_id', watchlist_id)\
            .order('added_at', desc=False)\
            .execute()
        
        if response.data:
            symbols = [row['symbol'] for row in response.data]
            print(f"📊 Loaded {len(symbols)} stocks from watchlist {watchlist_id}")
            return symbols
        return []
        
    except Exception as e:
        print(f"❌ Error loading stocks: {e}")
        return []


def remove_stock_from_watchlist(watchlist_id: int, symbol: str) -> bool:
    """
    Remove a stock from a watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
        symbol: Stock symbol to remove
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = supabase.table('watchlist_stocks')\
            .delete()\
            .eq('watchlist_id', watchlist_id)\
            .eq('symbol', symbol.upper())\
            .execute()
        
        print(f"🗑️ Removed {symbol} from watchlist {watchlist_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error removing stock: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_watchlist_summary(watchlist_id: int) -> Optional[Dict]:
    """
    Get watchlist with stock count
    
    Args:
        watchlist_id: Database ID of watchlist
    
    Returns:
        Dictionary with watchlist info and stock_count
    """
    try:
        # Get watchlist
        watchlist_response = supabase.table('watchlists')\
            .select('*')\
            .eq('id', watchlist_id)\
            .single()\
            .execute()
        
        if not watchlist_response.data:
            return None
        
        # Get stock count
        stocks_response = supabase.table('watchlist_stocks')\
            .select('symbol', count='exact')\
            .eq('watchlist_id', watchlist_id)\
            .execute()
        
        watchlist = watchlist_response.data
        watchlist['stock_count'] = stocks_response.count if stocks_response.count else 0
        
        return watchlist
        
    except Exception as e:
        print(f"❌ Error getting watchlist summary: {e}")
        return None


def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection works, False otherwise
    """
    try:
        response = supabase.table('watchlists').select('id').limit(1).execute()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# BULK OPERATIONS
# ═══════════════════════════════════════════════════════════════════

def add_multiple_stocks(watchlist_id: int, symbols: List[str]) -> Dict[str, List[str]]:
    """
    Add multiple stocks to a watchlist at once
    
    Args:
        watchlist_id: Database ID of watchlist
        symbols: List of stock symbols
    
    Returns:
        Dictionary with 'added' and 'failed' lists
    """
    added = []
    failed = []
    
    for symbol in symbols:
        if add_stock_to_watchlist(watchlist_id, symbol):
            added.append(symbol)
        else:
            failed.append(symbol)
    
    return {'added': added, 'failed': failed}


def clear_watchlist(watchlist_id: int) -> bool:
    """
    Remove all stocks from a watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = supabase.table('watchlist_stocks')\
            .delete()\
            .eq('watchlist_id', watchlist_id)\
            .execute()
        
        print(f"🗑️ Cleared all stocks from watchlist {watchlist_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing watchlist: {e}")
        return False



# ═══════════════════════════════════════════════════════════════════
# USER PREFERENCES (CUSTOM VIEWS & SETTINGS)
# ═══════════════════════════════════════════════════════════════════

def save_custom_view(view_name: str, columns: List[str], user_id: str = 'default_user') -> bool:
    """
    Save a custom view configuration to database
    
    Args:
        view_name: Name of the custom view
        columns: List of column names to display
        user_id: User identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Upsert with onConflict specified
        response = supabase.table('user_preferences').upsert({
            'user_id': user_id,
            'preference_type': 'custom_view',
            'preference_key': view_name,
            'preference_value': {'columns': columns}
        }, on_conflict='user_id,preference_type,preference_key').execute()
        
        if response.data:
            print(f"✅ Saved custom view: {view_name}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error saving custom view: {e}")
        return False


def get_all_custom_views(user_id: str = 'default_user') -> Dict[str, List[str]]:
    """
    Get all custom views for a user
    
    Args:
        user_id: User identifier
    
    Returns:
        Dictionary mapping view names to column lists
    """
    try:
        response = supabase.table('user_preferences')\
            .select('preference_key, preference_value')\
            .eq('user_id', user_id)\
            .eq('preference_type', 'custom_view')\
            .execute()
        
        if response.data:
            custom_views = {}
            for item in response.data:
                view_name = item['preference_key']
                columns = item['preference_value'].get('columns', [])
                custom_views[view_name] = columns
            
            print(f"📋 Loaded {len(custom_views)} custom views")
            return custom_views
        return {}
        
    except Exception as e:
        print(f"❌ Error loading custom views: {e}")
        return {}


def delete_custom_view(view_name: str, user_id: str = 'default_user') -> bool:
    """
    Delete a custom view
    
    Args:
        view_name: Name of the view to delete
        user_id: User identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        response = supabase.table('user_preferences')\
            .delete()\
            .eq('user_id', user_id)\
            .eq('preference_type', 'custom_view')\
            .eq('preference_key', view_name)\
            .execute()
        
        print(f"🗑️ Deleted custom view: {view_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting custom view: {e}")
        return False


def save_watchlist_view_preference(watchlist_id: int, view_name: str, user_id: str = 'default_user') -> bool:
    """
    Save which view is selected for a specific watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
        view_name: Name of the selected view
        user_id: User identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use upsert with onConflict to handle updates properly
        response = supabase.table('user_preferences').upsert({
            'user_id': user_id,
            'preference_type': 'watchlist_view_pref',
            'preference_key': str(watchlist_id),
            'preference_value': {'view': view_name}
        }, on_conflict='user_id,preference_type,preference_key').execute()
        
        if response.data:
            print(f"✅ Saved view preference for watchlist {watchlist_id}: {view_name}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error saving view preference: {e}")
        return False


def get_watchlist_view_preference(watchlist_id: int, user_id: str = 'default_user') -> Optional[str]:
    """
    Get the selected view for a specific watchlist
    
    Args:
        watchlist_id: Database ID of watchlist
        user_id: User identifier
    
    Returns:
        View name if found, None otherwise
    """
    try:
        response = supabase.table('user_preferences')\
            .select('preference_value')\
            .eq('user_id', user_id)\
            .eq('preference_type', 'watchlist_view_pref')\
            .eq('preference_key', str(watchlist_id))\
            .single()\
            .execute()
        
        if response.data:
            return response.data['preference_value'].get('view')
        return None
        
    except Exception as e:
        # Not an error if not found, just means no preference saved yet
        return None


# ═══════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Test database functions"""
    print("\n" + "="*60)
    print("DATABASE MODULE TEST")
    print("="*60 + "\n")
    
    # Test connection
    print("1. Testing connection...")
    test_connection()
    
    # Create test watchlist
    print("\n2. Creating test watchlist...")
    watchlist = create_watchlist("Test Watchlist")
    
    if watchlist:
        watchlist_id = watchlist['id']
        
        # Add stocks
        print("\n3. Adding stocks...")
        add_stock_to_watchlist(watchlist_id, "AAPL")
        add_stock_to_watchlist(watchlist_id, "MSFT")
        add_stock_to_watchlist(watchlist_id, "GOOGL")
        
        # Get stocks
        print("\n4. Getting stocks...")
        stocks = get_watchlist_stocks(watchlist_id)
        print(f"   Stocks: {stocks}")
        
        # Get all watchlists
        print("\n5. Getting all watchlists...")
        all_watchlists = get_all_watchlists()
        for wl in all_watchlists:
            print(f"   - {wl['name']} (ID: {wl['id']})")
        
        # Clean up test data
        print("\n6. Cleaning up test data...")
        delete_watchlist(watchlist_id)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
