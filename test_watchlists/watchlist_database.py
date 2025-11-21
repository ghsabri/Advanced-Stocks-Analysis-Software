"""
Watchlist Database Functions
Supabase integration for persistent watchlist storage
"""

from supabase import create_client, Client
from datetime import datetime
from typing import List, Dict, Optional
import os

# ============================================================================
# SUPABASE CONFIGURATION
# ============================================================================

def get_supabase_client() -> Client:
    """Initialize Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment variables")
    
    return create_client(url, key)

# ============================================================================
# WATCHLIST OPERATIONS
# ============================================================================

def create_watchlist_db(user_id: str, name: str) -> Optional[int]:
    """
    Create a new watchlist in database
    
    Args:
        user_id: User ID
        name: Watchlist name
    
    Returns:
        Watchlist ID if successful, None otherwise
    """
    try:
        supabase = get_supabase_client()
        
        data = {
            'user_id': user_id,
            'name': name,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('watchlists').insert(data).execute()
        
        if result.data:
            return result.data[0]['id']
        return None
    
    except Exception as e:
        print(f"Error creating watchlist: {e}")
        return None

def get_user_watchlists_db(user_id: str) -> List[Dict]:
    """
    Get all watchlists for a user
    
    Args:
        user_id: User ID
    
    Returns:
        List of watchlist dictionaries
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('watchlists')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        print(f"Error fetching watchlists: {e}")
        return []

def delete_watchlist_db(watchlist_id: int) -> bool:
    """
    Delete a watchlist and all its stocks
    
    Args:
        watchlist_id: Watchlist ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        # Delete all stocks in the watchlist first
        supabase.table('watchlist_stocks')\
            .delete()\
            .eq('watchlist_id', watchlist_id)\
            .execute()
        
        # Delete the watchlist
        supabase.table('watchlists')\
            .delete()\
            .eq('id', watchlist_id)\
            .execute()
        
        return True
    
    except Exception as e:
        print(f"Error deleting watchlist: {e}")
        return False

def rename_watchlist_db(watchlist_id: int, new_name: str) -> bool:
    """
    Rename a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        new_name: New name for the watchlist
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        supabase.table('watchlists')\
            .update({'name': new_name})\
            .eq('id', watchlist_id)\
            .execute()
        
        return True
    
    except Exception as e:
        print(f"Error renaming watchlist: {e}")
        return False

# ============================================================================
# WATCHLIST STOCK OPERATIONS
# ============================================================================

def add_stock_to_watchlist_db(watchlist_id: int, symbol: str) -> bool:
    """
    Add a stock to a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        symbol: Stock symbol
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        # Check if stock already exists in watchlist
        existing = supabase.table('watchlist_stocks')\
            .select('id')\
            .eq('watchlist_id', watchlist_id)\
            .eq('symbol', symbol)\
            .execute()
        
        if existing.data:
            return False  # Stock already in watchlist
        
        # Add stock
        data = {
            'watchlist_id': watchlist_id,
            'symbol': symbol,
            'added_at': datetime.now().isoformat()
        }
        
        supabase.table('watchlist_stocks').insert(data).execute()
        return True
    
    except Exception as e:
        print(f"Error adding stock to watchlist: {e}")
        return False

def remove_stock_from_watchlist_db(watchlist_id: int, symbol: str) -> bool:
    """
    Remove a stock from a watchlist
    
    Args:
        watchlist_id: Watchlist ID
        symbol: Stock symbol
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        
        supabase.table('watchlist_stocks')\
            .delete()\
            .eq('watchlist_id', watchlist_id)\
            .eq('symbol', symbol)\
            .execute()
        
        return True
    
    except Exception as e:
        print(f"Error removing stock from watchlist: {e}")
        return False

def get_watchlist_stocks_db(watchlist_id: int) -> List[str]:
    """
    Get all stocks in a watchlist
    
    Args:
        watchlist_id: Watchlist ID
    
    Returns:
        List of stock symbols
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('watchlist_stocks')\
            .select('symbol')\
            .eq('watchlist_id', watchlist_id)\
            .order('added_at', desc=False)\
            .execute()
        
        if result.data:
            return [item['symbol'] for item in result.data]
        return []
    
    except Exception as e:
        print(f"Error fetching watchlist stocks: {e}")
        return []

def get_watchlist_stock_count_db(watchlist_id: int) -> int:
    """
    Get count of stocks in a watchlist
    
    Args:
        watchlist_id: Watchlist ID
    
    Returns:
        Number of stocks in the watchlist
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('watchlist_stocks')\
            .select('id', count='exact')\
            .eq('watchlist_id', watchlist_id)\
            .execute()
        
        return result.count if result.count else 0
    
    except Exception as e:
        print(f"Error counting watchlist stocks: {e}")
        return 0

# ============================================================================
# DATABASE SCHEMA (SQL)
# ============================================================================

"""
-- Watchlists Table
CREATE TABLE watchlists (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster user lookups
CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);

-- Watchlist Stocks Table
CREATE TABLE watchlist_stocks (
    id BIGSERIAL PRIMARY KEY,
    watchlist_id BIGINT NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster watchlist lookups
CREATE INDEX idx_watchlist_stocks_watchlist_id ON watchlist_stocks(watchlist_id);

-- Unique constraint to prevent duplicate stocks in same watchlist
CREATE UNIQUE INDEX idx_watchlist_stocks_unique ON watchlist_stocks(watchlist_id, symbol);

-- Row Level Security (RLS) Policies
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist_stocks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own watchlists
CREATE POLICY "Users can view own watchlists" ON watchlists
    FOR SELECT
    USING (auth.uid()::text = user_id);

-- Policy: Users can insert their own watchlists
CREATE POLICY "Users can insert own watchlists" ON watchlists
    FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- Policy: Users can update their own watchlists
CREATE POLICY "Users can update own watchlists" ON watchlists
    FOR UPDATE
    USING (auth.uid()::text = user_id);

-- Policy: Users can delete their own watchlists
CREATE POLICY "Users can delete own watchlists" ON watchlists
    FOR DELETE
    USING (auth.uid()::text = user_id);

-- Policy: Users can view stocks in their watchlists
CREATE POLICY "Users can view own watchlist stocks" ON watchlist_stocks
    FOR SELECT
    USING (
        watchlist_id IN (
            SELECT id FROM watchlists WHERE user_id = auth.uid()::text
        )
    );

-- Policy: Users can add stocks to their watchlists
CREATE POLICY "Users can add stocks to own watchlists" ON watchlist_stocks
    FOR INSERT
    WITH CHECK (
        watchlist_id IN (
            SELECT id FROM watchlists WHERE user_id = auth.uid()::text
        )
    );

-- Policy: Users can remove stocks from their watchlists
CREATE POLICY "Users can remove stocks from own watchlists" ON watchlist_stocks
    FOR DELETE
    USING (
        watchlist_id IN (
            SELECT id FROM watchlists WHERE user_id = auth.uid()::text
        )
    );

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for watchlists table
CREATE TRIGGER update_watchlists_updated_at BEFORE UPDATE ON watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
