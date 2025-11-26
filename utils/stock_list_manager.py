"""
Stock List Manager - Hybrid Storage System
MJ Software LLC - AI-Powered Stock Analysis Platform

This module provides fast access to stock list data with 3-tier caching:
1. Local pickle cache (fastest - instant)
2. Supabase database (fast - network call)
3. Bundled CSV file (fallback - always available)

Usage:
    from utils.stock_list_manager import (
        get_sector_stocks,
        get_sp500_stocks,
        get_all_sectors,
        get_stocks_by_sector_etf
    )
    
    # Get all Technology stocks
    tech_stocks = get_sector_stocks('Technology')
    
    # Get all S&P 500 stocks
    sp500 = get_sp500_stocks()
    
    # Get stocks for heat map (by sector ETF)
    xlk_stocks = get_stocks_by_sector_etf('XLK')
"""

import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================

# Cache settings
CACHE_DIR = '.stock_cache'
CACHE_FILE = os.path.join(CACHE_DIR, 'stock_list.pkl')
CACHE_TTL = 86400  # 24 hours in seconds

# CSV file locations to check (in order)
CSV_PATHS = [
    'stocks_list.csv',           # Project root
    'data/stocks_list.csv',      # Data folder
    '../stocks_list.csv',        # Parent directory
    'src/stocks_list.csv',       # Src folder
]

# Sector to ETF mapping
SECTOR_ETF_MAP = {
    'Technology': 'XLK',
    'Information Technology': 'XLK',
    'Health Care': 'XLV',
    'Healthcare': 'XLV',
    'Financials': 'XLF',
    'Financial': 'XLF',
    'Energy': 'XLE',
    'Consumer Discretionary': 'XLY',
    'Communication Services': 'XLC',
    'Communications': 'XLC',
    'Industrials': 'XLI',
    'Industrial': 'XLI',
    'Materials': 'XLB',
    'Basic Materials': 'XLB',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Consumer Staples': 'XLP',
    'Consumer Defensive': 'XLP',
}

# ETF to Sector mapping (reverse)
ETF_SECTOR_MAP = {
    'XLK': 'Technology',
    'XLV': 'Health Care',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLY': 'Consumer Discretionary',
    'XLC': 'Communication Services',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLU': 'Utilities',
    'XLRE': 'Real Estate',
    'XLP': 'Consumer Staples',
}

# All sector ETFs in order
ALL_SECTOR_ETFS = ['XLK', 'XLV', 'XLF', 'XLE', 'XLY', 'XLC', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLP']


# ============================================================
# CACHE FUNCTIONS
# ============================================================

def _cache_valid() -> bool:
    """Check if local cache exists and is still valid (within TTL)"""
    if not os.path.exists(CACHE_FILE):
        return False
    
    file_time = os.path.getmtime(CACHE_FILE)
    age = datetime.now().timestamp() - file_time
    return age < CACHE_TTL


def _load_from_cache() -> Optional[pd.DataFrame]:
    """Load stock list from local pickle cache"""
    try:
        if _cache_valid():
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"⚠️ Cache load error: {e}")
    return None


def _save_to_cache(df: pd.DataFrame) -> None:
    """Save stock list to local pickle cache"""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(df, f)
    except Exception as e:
        print(f"⚠️ Cache save error: {e}")


def clear_cache() -> None:
    """Clear the local cache (force refresh from source)"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("✅ Cache cleared")


# ============================================================
# DATA SOURCE FUNCTIONS
# ============================================================

def _load_from_supabase() -> Optional[pd.DataFrame]:
    """Load stock list from Supabase database"""
    try:
        # Try to import Supabase client from your config
        # Adjust this import based on your project structure
        try:
            from config import SUPABASE_URL, SUPABASE_KEY
        except ImportError:
            # Try streamlit secrets
            if hasattr(st, 'secrets') and 'SUPABASE_URL' in st.secrets:
                SUPABASE_URL = st.secrets['SUPABASE_URL']
                SUPABASE_KEY = st.secrets['SUPABASE_KEY']
            else:
                return None
        
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('stock_list').select('*').eq('is_active', True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            print(f"✅ Loaded {len(df)} stocks from Supabase")
            return df
            
    except Exception as e:
        print(f"⚠️ Supabase load error: {e}")
    
    return None


def _load_from_csv() -> Optional[pd.DataFrame]:
    """Load stock list from bundled CSV file"""
    # Try each possible CSV location
    for csv_path in CSV_PATHS:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                
                # Standardize column names
                df.columns = df.columns.str.strip()
                
                # Ensure symbol column exists and is clean
                if 'Symbol' in df.columns:
                    df['symbol'] = df['Symbol'].str.strip().str.upper()
                elif 'symbol' in df.columns:
                    df['symbol'] = df['symbol'].str.strip().str.upper()
                
                # Map common column names
                column_mapping = {
                    'Symbol': 'symbol',
                    'Name': 'name',
                    'Sector': 'sector',
                    'Sector Name': 'sector_etf',
                    'Industry': 'industry',
                    'Exchange': 'exchange',
                    'S&P 500': 'is_sp500',
                }
                
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns and new_col not in df.columns:
                        df[new_col] = df[old_col]
                
                # Handle boolean columns
                if 'is_sp500' in df.columns:
                    df['is_sp500'] = df['is_sp500'].apply(
                        lambda x: x == True or str(x).upper() in ['TRUE', 'YES', '1']
                    )
                
                # Add sector_etf if missing
                if 'sector_etf' not in df.columns and 'sector' in df.columns:
                    df['sector_etf'] = df['sector'].map(SECTOR_ETF_MAP)
                
                print(f"✅ Loaded {len(df)} stocks from CSV: {csv_path}")
                return df
                
            except Exception as e:
                print(f"⚠️ CSV load error ({csv_path}): {e}")
                continue
    
    return None


# ============================================================
# MAIN DATA ACCESS FUNCTION
# ============================================================

@st.cache_data(ttl=3600)  # Streamlit cache for 1 hour
def get_stock_list() -> pd.DataFrame:
    """
    Get the full stock list with 3-tier fallback:
    1. Local pickle cache (fastest)
    2. Supabase database
    3. Bundled CSV file
    
    Returns:
        pd.DataFrame: Stock list with columns: symbol, name, sector, sector_etf, etc.
    """
    # Tier 1: Check local pickle cache
    df = _load_from_cache()
    if df is not None:
        return df
    
    # Tier 2: Try Supabase
    df = _load_from_supabase()
    if df is not None:
        _save_to_cache(df)
        return df
    
    # Tier 3: Fallback to CSV
    df = _load_from_csv()
    if df is not None:
        _save_to_cache(df)
        return df
    
    # If all fails, return empty DataFrame
    print("❌ Could not load stock list from any source!")
    return pd.DataFrame()


# ============================================================
# QUERY FUNCTIONS
# ============================================================

def get_sector_stocks(sector: str) -> List[str]:
    """
    Get all stock symbols in a specific sector.
    
    Args:
        sector: Sector name (e.g., 'Technology', 'Health Care')
    
    Returns:
        List of stock symbols
    """
    df = get_stock_list()
    if df.empty:
        return []
    
    # Handle sector column name variations
    sector_col = 'sector' if 'sector' in df.columns else 'Sector'
    
    return df[df[sector_col].str.lower() == sector.lower()]['symbol'].tolist()


def get_stocks_by_sector_etf(sector_etf: str) -> List[str]:
    """
    Get all stock symbols for a sector ETF (XLK, XLV, etc.)
    
    Args:
        sector_etf: Sector ETF symbol (e.g., 'XLK', 'XLV')
    
    Returns:
        List of stock symbols
    """
    df = get_stock_list()
    if df.empty:
        return []
    
    # Check for sector_etf or "Sector Name" column (handle both formats)
    sector_col = None
    for col in ['sector_etf', 'Sector Name', 'sector_name', 'SectorETF']:
        if col in df.columns:
            sector_col = col
            break
    
    if sector_col:
        # Handle NULL values - fill with empty string, then compare
        df_filtered = df[df[sector_col].fillna('').astype(str).str.upper() == sector_etf.upper()]
        if 'symbol' in df_filtered.columns:
            return df_filtered['symbol'].tolist()
        elif 'Symbol' in df_filtered.columns:
            return df_filtered['Symbol'].tolist()
    
    # Fallback: map ETF to sector name
    sector_name = ETF_SECTOR_MAP.get(sector_etf.upper())
    if sector_name:
        return get_sector_stocks(sector_name)
    
    return []


def get_sp500_stocks() -> List[str]:
    """Get all S&P 500 stock symbols"""
    df = get_stock_list()
    if df.empty:
        return []
    
    # Handle column name variations
    if 'is_sp500' in df.columns:
        return df[df['is_sp500'] == True]['symbol'].tolist()
    elif 'S&P 500' in df.columns:
        return df[df['S&P 500'].apply(
            lambda x: x == True or str(x).upper() in ['TRUE', 'YES', '1']
        )]['symbol'].tolist()
    
    return []


def get_nasdaq100_stocks() -> List[str]:
    """Get all NASDAQ 100 stock symbols"""
    df = get_stock_list()
    if df.empty:
        return []
    
    if 'is_nasdaq100' in df.columns:
        return df[df['is_nasdaq100'] == True]['symbol'].tolist()
    
    return []


def get_dow30_stocks() -> List[str]:
    """Get all DOW 30 stock symbols"""
    df = get_stock_list()
    if df.empty:
        return []
    
    if 'is_dow30' in df.columns:
        return df[df['is_dow30'] == True]['symbol'].tolist()
    
    return []


def get_all_sectors() -> List[str]:
    """Get list of all unique sectors"""
    df = get_stock_list()
    if df.empty:
        return list(SECTOR_ETF_MAP.keys())
    
    sector_col = 'sector' if 'sector' in df.columns else 'Sector'
    return df[sector_col].dropna().unique().tolist()


def get_all_sector_etfs() -> List[str]:
    """Get list of all sector ETFs"""
    return ALL_SECTOR_ETFS.copy()


def get_stocks_by_industry(industry: str) -> List[str]:
    """Get stocks by industry"""
    df = get_stock_list()
    if df.empty:
        return []
    
    industry_col = 'industry' if 'industry' in df.columns else 'Industry'
    
    if industry_col in df.columns:
        return df[df[industry_col].str.lower() == industry.lower()]['symbol'].tolist()
    
    return []


def get_stock_info(symbol: str) -> Optional[Dict]:
    """
    Get detailed info for a single stock.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        Dictionary with stock info or None if not found
    """
    df = get_stock_list()
    if df.empty:
        return None
    
    symbol = symbol.upper().strip()
    stock = df[df['symbol'] == symbol]
    
    if stock.empty:
        return None
    
    row = stock.iloc[0]
    return {
        'symbol': row.get('symbol', symbol),
        'name': row.get('name', row.get('Name', '')),
        'sector': row.get('sector', row.get('Sector', '')),
        'sector_etf': row.get('sector_etf', row.get('Sector Name', '')),
        'industry': row.get('industry', row.get('Industry', '')),
        'exchange': row.get('exchange', row.get('Exchange', '')),
        'is_sp500': row.get('is_sp500', row.get('S&P 500', False)),
    }


def search_stocks(query: str, limit: int = 20) -> List[Dict]:
    """
    Search stocks by symbol or name.
    
    Args:
        query: Search query
        limit: Maximum results to return
    
    Returns:
        List of matching stock dictionaries
    """
    df = get_stock_list()
    if df.empty:
        return []
    
    query = query.upper().strip()
    
    # Search in symbol and name
    mask = (
        df['symbol'].str.contains(query, case=False, na=False) |
        df.get('name', df.get('Name', pd.Series())).str.contains(query, case=False, na=False)
    )
    
    results = df[mask].head(limit)
    
    return [
        {
            'symbol': row.get('symbol', ''),
            'name': row.get('name', row.get('Name', '')),
            'sector': row.get('sector', row.get('Sector', '')),
        }
        for _, row in results.iterrows()
    ]


def get_sector_stock_count() -> Dict[str, int]:
    """Get count of stocks in each sector"""
    df = get_stock_list()
    if df.empty:
        return {}
    
    sector_col = 'sector' if 'sector' in df.columns else 'Sector'
    return df[sector_col].value_counts().to_dict()


def get_sector_etf_for_stock(symbol: str) -> Optional[str]:
    """Get the sector ETF for a specific stock"""
    info = get_stock_info(symbol)
    if info:
        return info.get('sector_etf')
    return None


# ============================================================
# ADMIN / UTILITY FUNCTIONS
# ============================================================

def get_data_source_info() -> Dict:
    """Get information about the current data source"""
    df = get_stock_list()
    
    return {
        'total_stocks': len(df),
        'sectors': len(get_all_sectors()),
        'sp500_count': len(get_sp500_stocks()),
        'cache_valid': _cache_valid(),
        'cache_file': CACHE_FILE if os.path.exists(CACHE_FILE) else None,
    }


# ============================================================
# TEST / DEBUG
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("STOCK LIST MANAGER - TEST")
    print("=" * 60)
    
    # Test loading
    df = get_stock_list()
    print(f"\n📊 Total stocks loaded: {len(df)}")
    
    # Test sector query
    tech_stocks = get_sector_stocks('Technology')
    print(f"\n🔧 Technology stocks: {len(tech_stocks)}")
    print(f"   Sample: {tech_stocks[:5]}")
    
    # Test S&P 500
    sp500 = get_sp500_stocks()
    print(f"\n📈 S&P 500 stocks: {len(sp500)}")
    
    # Test sector ETF
    xlk_stocks = get_stocks_by_sector_etf('XLK')
    print(f"\n💻 XLK (Technology) stocks: {len(xlk_stocks)}")
    
    # Test stock info
    info = get_stock_info('AAPL')
    print(f"\n🍎 AAPL Info: {info}")
    
    # Test search
    results = search_stocks('Apple', limit=5)
    print(f"\n🔍 Search 'Apple': {results}")
    
    # Data source info
    source_info = get_data_source_info()
    print(f"\n📦 Data Source Info: {source_info}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
