"""
Watchlists Page V3 - Enhanced with Custom View Creator
FIXED VERSION - November 20, 2025

FIXES APPLIED:
✅ Fixed duplicate watchlist creation bug
✅ Fixed include_tr parameter error in get_shared_stock_data
✅ Fixed watchlist ID assignment to prevent conflicts
✅ Improved session state initialization

Features:
✅ 32 Available Fields
✅ Custom View Creator - Select any fields you want
✅ Save/Load/Delete Custom Templates
✅ 7 Built-in Preset Views + Unlimited Custom Views
✅ Bulk Stock Addition (comma-separated)
✅ Fixed TR Status and TR Value
✅ Fixed EMA calculations
✅ Progress indicators
✅ Smart caching
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from stock_lookup import get_stock_info
from cached_data import get_shared_stock_data

# Import database module
try:
    from database import (
        create_watchlist as db_create_watchlist,
        get_all_watchlists as db_get_all_watchlists,
        update_watchlist_name as db_update_watchlist_name,
        delete_watchlist as db_delete_watchlist,
        add_stock_to_watchlist as db_add_stock,
        get_watchlist_stocks as db_get_stocks,
        remove_stock_from_watchlist as db_remove_stock
    )
    DATABASE_ENABLED = True
    print("✅ Database module loaded successfully")
except Exception as e:
    DATABASE_ENABLED = False
    print(f"⚠️ Database not available: {e}")
    print("   Watchlists will work in session-only mode")

st.set_page_config(
    page_title="Watchlists - MJ Software",
    page_icon="📋",
    layout="wide"
)

# CSS for styling
st.markdown("""
<style>
    .stButton > button {
        height: 38px !important;
        padding: 6px 16px !important;
        font-size: 14px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .stDownloadButton > button {
        height: 38px !important;
        padding: 6px 16px !important;
        font-size: 14px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        min-width: 120px !important;
    }
    
    .tr-strong-buy {
        background-color: #00CC00;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .tr-buy {
        background-color: #66CC66;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .tr-neutral {
        background-color: #FFCC00;
        color: black;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .tr-sell {
        background-color: #FF6666;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .tr-strong-sell {
        background-color: #CC0000;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    .tr-loading {
        background-color: #999999;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# COLUMN CONFIGURATION - 32 FIELDS AVAILABLE
# ============================================================================

AVAILABLE_COLUMNS = {
    # Basic Fields (4)
    'symbol': {'name': 'Symbol', 'width': 1.5, 'category': 'Basic'},
    'current_price': {'name': 'Price', 'width': 1.5, 'category': 'Basic'},
    'price_change_pct': {'name': 'Change %', 'width': 1.5, 'category': 'Basic'},
    'volume': {'name': 'Volume', 'width': 1.5, 'category': 'Basic'},
    
    # TR Indicators (2)
    'tr_status': {'name': 'TR Status', 'width': 2, 'category': 'TR Indicator'},
    'tr_value': {'name': 'TR Value', 'width': 1.5, 'category': 'TR Indicator'},
    
    # Technical Indicators (2)
    'rsi': {'name': 'RSI', 'width': 1, 'category': 'Technical'},
    'macd': {'name': 'MACD', 'width': 1.5, 'category': 'Technical'},
    
    # TR Trading Levels (3)
    'buy_point': {'name': 'Buy Point', 'width': 1.5, 'category': 'TR Levels'},
    'stop_loss': {'name': 'Stop Loss', 'width': 1.5, 'category': 'TR Levels'},
    'risk_pct': {'name': 'Risk %', 'width': 1.5, 'category': 'TR Levels'},
    
    # Moving Averages (7)
    'ema_6': {'name': 'EMA 6', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_10': {'name': 'EMA 10', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_13': {'name': 'EMA 13', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_20': {'name': 'EMA 20', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_30': {'name': 'EMA 30', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_50': {'name': 'EMA 50', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_200': {'name': 'EMA 200', 'width': 1.5, 'category': 'Moving Averages'},
    
    # 52 Week Stats (2)
    'high_52w': {'name': '52W High', 'width': 1.5, 'category': '52 Week Stats'},
    'low_52w': {'name': '52W Low', 'width': 1.5, 'category': '52 Week Stats'},
    
    # Fundamentals (3)
    'beta': {'name': 'Beta', 'width': 1.2, 'category': 'Fundamentals'},
    'pe_ratio': {'name': 'P/E', 'width': 1.2, 'category': 'Fundamentals'},
    'market_cap': {'name': 'Market Cap', 'width': 1.8, 'category': 'Fundamentals'},
    
    # Performance (7)
    'perf_1m': {'name': '1M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_3m': {'name': '3M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_6m': {'name': '6M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_ytd': {'name': 'YTD Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_1y': {'name': '1Y Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_3y': {'name': '3Y Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_5y': {'name': '5Y Perf%', 'width': 1.5, 'category': 'Performance'},
}

# Built-in preset views
PRESET_VIEWS = {
    'Compact': ['symbol', 'current_price', 'price_change_pct', 'tr_status'],
    'Standard': ['symbol', 'current_price', 'price_change_pct', 'volume', 'rsi', 'tr_status'],
    'Detailed': ['symbol', 'current_price', 'price_change_pct', 'tr_status', 'tr_value', 'buy_point', 'stop_loss', 'risk_pct'],
    'Trading': ['symbol', 'current_price', 'price_change_pct', 'tr_status', 'buy_point', 'stop_loss', 'ema_13', 'ema_30'],
    'Technical': ['symbol', 'current_price', 'volume', 'rsi', 'tr_status', 'tr_value', 'ema_13', 'ema_30'],
    'Long Term': ['symbol', 'current_price', 'price_change_pct', 'beta', 'pe_ratio', 'market_cap', 'ema_50', 'ema_200', 'perf_ytd'],
    'Performance': ['symbol', 'current_price', 'price_change_pct', 'perf_1m', 'perf_3m', 'perf_ytd', 'high_52w', 'low_52w'],
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state for watchlists - WITH DATABASE INTEGRATION"""
    
    # First-time initialization flag
    if 'watchlists_loaded' not in st.session_state:
        st.session_state.watchlists_loaded = False
    
    if 'watchlists' not in st.session_state:
        st.session_state.watchlists = {}
    
    # Load from database on first run
    if DATABASE_ENABLED and not st.session_state.watchlists_loaded:
        try:
            print("📂 Loading watchlists from database...")
            db_watchlists = db_get_all_watchlists()
            
            if db_watchlists:
                # Convert database format to session state format
                for db_wl in db_watchlists:
                    wl_id = db_wl['id']
                    
                    # Get stocks for this watchlist
                    stocks = db_get_stocks(wl_id)
                    
                    # Add to session state
                    st.session_state.watchlists[wl_id] = {
                        'name': db_wl['name'],
                        'created_at': datetime.fromisoformat(db_wl['created_at'].replace('Z', '+00:00')),
                        'stocks': stocks,
                        'db_id': wl_id  # Store database ID
                    }
                
                print(f"✅ Loaded {len(db_watchlists)} watchlists from database")
            else:
                print("ℹ️ No watchlists found in database")
                
            st.session_state.watchlists_loaded = True
            
        except Exception as e:
            print(f"⚠️ Could not load from database: {e}")
            st.session_state.watchlists_loaded = True  # Don't keep trying
    
    # Calculate next_watchlist_id based on existing watchlists
    if 'next_watchlist_id' not in st.session_state:
        if st.session_state.watchlists:
            # Get the maximum existing ID and add 1
            max_id = max(st.session_state.watchlists.keys())
            st.session_state.next_watchlist_id = max_id + 1
        else:
            st.session_state.next_watchlist_id = 1
    
    if 'active_watchlist' not in st.session_state:
        if st.session_state.watchlists:
            st.session_state.active_watchlist = list(st.session_state.watchlists.keys())[0]
        else:
            st.session_state.active_watchlist = None
    
    if 'stock_tr_cache' not in st.session_state:
        st.session_state.stock_tr_cache = {}
    
    # Custom views storage
    if 'custom_views' not in st.session_state:
        st.session_state.custom_views = {}
    
    # View preference per watchlist
    if 'watchlist_view_prefs' not in st.session_state:
        st.session_state.watchlist_view_prefs = {}
    
    # Sorting state per watchlist
    if 'watchlist_sort' not in st.session_state:
        st.session_state.watchlist_sort = {}


# ============================================================================
# WATCHLIST MANAGEMENT FUNCTIONS
# ============================================================================

def create_watchlist(name):
    """Create a new watchlist - WITH DATABASE INTEGRATION"""
    
    # Create in database first
    if DATABASE_ENABLED:
        try:
            db_watchlist = db_create_watchlist(name)
            if db_watchlist:
                watchlist_id = db_watchlist['id']
                print(f"✅ Created watchlist in database (ID: {watchlist_id})")
            else:
                print("⚠️ Database creation failed, using session only")
                watchlist_id = st.session_state.next_watchlist_id if st.session_state.watchlists else 1
                st.session_state.next_watchlist_id = watchlist_id + 1
        except Exception as e:
            print(f"⚠️ Database error: {e}, using session only")
            watchlist_id = st.session_state.next_watchlist_id if st.session_state.watchlists else 1
            st.session_state.next_watchlist_id = watchlist_id + 1
    else:
        # No database, calculate ID based on existing watchlists
        if st.session_state.watchlists:
            watchlist_id = max(st.session_state.watchlists.keys()) + 1
        else:
            watchlist_id = 1
        st.session_state.next_watchlist_id = watchlist_id + 1
    
    # Add to session state
    st.session_state.watchlists[watchlist_id] = {
        'name': name,
        'created_at': datetime.now(),
        'stocks': [],
        'db_id': watchlist_id
    }
    
    st.session_state.active_watchlist = watchlist_id
    st.session_state.watchlist_view_prefs[watchlist_id] = 'Standard'
    
    return watchlist_id

def delete_watchlist(watchlist_id):
    """Delete a watchlist - WITH DATABASE INTEGRATION"""
    if watchlist_id in st.session_state.watchlists:
        # Delete from database
        if DATABASE_ENABLED:
            try:
                db_delete_watchlist(watchlist_id)
            except Exception as e:
                print(f"⚠️ Database deletion failed: {e}")
        
        # Delete from session state
        del st.session_state.watchlists[watchlist_id]
        if watchlist_id in st.session_state.watchlist_view_prefs:
            del st.session_state.watchlist_view_prefs[watchlist_id]
        
        # Update active watchlist
        if st.session_state.active_watchlist == watchlist_id:
            if st.session_state.watchlists:
                st.session_state.active_watchlist = list(st.session_state.watchlists.keys())[0]
            else:
                st.session_state.active_watchlist = None

def rename_watchlist(watchlist_id, new_name):
    """Rename a watchlist - WITH DATABASE INTEGRATION"""
    if watchlist_id in st.session_state.watchlists:
        # Update in database
        if DATABASE_ENABLED:
            try:
                db_update_watchlist_name(watchlist_id, new_name)
            except Exception as e:
                print(f"⚠️ Database update failed: {e}")
        
        # Update session state
        st.session_state.watchlists[watchlist_id]['name'] = new_name

def add_stock_to_watchlist(watchlist_id, symbol):
    """Add a stock to a watchlist - WITH DATABASE INTEGRATION"""
    if watchlist_id in st.session_state.watchlists:
        stocks = st.session_state.watchlists[watchlist_id]['stocks']
        if symbol not in stocks:
            # Add to database
            if DATABASE_ENABLED:
                try:
                    db_add_stock(watchlist_id, symbol)
                except Exception as e:
                    print(f"⚠️ Database add failed: {e}")
            
            # Add to session state
            stocks.append(symbol)
            return True
    return False

def remove_stock_from_watchlist(watchlist_id, symbol):
    """Remove a stock from a watchlist - WITH DATABASE INTEGRATION"""
    if watchlist_id in st.session_state.watchlists:
        stocks = st.session_state.watchlists[watchlist_id]['stocks']
        if symbol in stocks:
            # Remove from database
            if DATABASE_ENABLED:
                try:
                    db_remove_stock(watchlist_id, symbol)
                except Exception as e:
                    print(f"⚠️ Database removal failed: {e}")
            
            # Remove from session state
            stocks.remove(symbol)
            return True
    return False

def get_watchlist_summary(watchlist_id):
    """Get summary stats for a watchlist"""
    if watchlist_id not in st.session_state.watchlists:
        return None
    
    watchlist = st.session_state.watchlists[watchlist_id]
    return {
        'name': watchlist['name'],
        'stock_count': len(watchlist['stocks']),
        'created_at': watchlist['created_at']
    }

# ============================================================================
# CUSTOM VIEWS MANAGEMENT
# ============================================================================

def save_custom_view(view_name, fields):
    """Save a custom view"""
    st.session_state.custom_views[view_name] = fields

def delete_custom_view(view_name):
    """Delete a custom view"""
    if view_name in st.session_state.custom_views:
        del st.session_state.custom_views[view_name]

def get_all_views():
    """Get all views (preset + custom)"""
    all_views = PRESET_VIEWS.copy()
    all_views.update(st.session_state.custom_views)
    return all_views

# ============================================================================
# TECHNICAL INDICATORS
# ============================================================================

def calculate_rsi(df, period=14):
    """Calculate RSI"""
    if len(df) < period + 1:
        return None
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1]

def calculate_macd(df):
    """Calculate MACD"""
    if len(df) < 26:
        return None
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    
    return macd.iloc[-1]

def get_fundamentals(symbol):
    """Get fundamental data (Beta, P/E, Market Cap)"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            'beta': info.get('beta'),
            'pe_ratio': info.get('trailingPE'),
            'market_cap': info.get('marketCap')
        }
    except:
        return {'beta': None, 'pe_ratio': None, 'market_cap': None}

# ============================================================================
# STOCK DATA ANALYSIS
# ============================================================================

def format_tr_status_html(tr_status):
    """Format TR status with colored badge"""
    status_map = {
        'Strong Buy': 'tr-strong-buy',
        'Buy': 'tr-buy',
        'Neutral': 'tr-neutral',
        'Neutral Buy': 'tr-neutral',
        'Neutral Sell': 'tr-neutral',
        'Sell': 'tr-sell',
        'Strong Sell': 'tr-strong-sell'
    }
    
    css_class = status_map.get(tr_status, 'tr-loading')
    return f'<span class="{css_class}">{tr_status}</span>'

def analyze_stock_enhanced(symbol, data_source='yahoo', needed_fields=None):
    """
    Enhanced analysis with ALL 32 fields - FIXED VERSION
    
    FIXES:
    - Removed invalid include_tr parameter
    - TR is always calculated by get_shared_stock_data
    - Added comprehensive error handling for API failures
    
    Args:
        symbol: Stock ticker symbol
        data_source: 'yahoo' or 'tiingo' (default: 'yahoo')
        needed_fields: List of field IDs that are actually needed (for future optimization)
    """
    # Check cache first
    cache_key = f"{symbol}_{data_source}"
    if cache_key in st.session_state.stock_tr_cache:
        cached_time = st.session_state.stock_tr_cache[cache_key].get('timestamp')
        if cached_time and (datetime.now() - cached_time).total_seconds() < 300:  # 5 minute cache
            return st.session_state.stock_tr_cache[cache_key]
    
    try:
        # FIXED: Removed include_tr parameter - TR is always calculated
        df = get_shared_stock_data(
            ticker=symbol,
            duration_days=1825,  # 5 years
            timeframe='daily',
            api_source=data_source
        )
        
        if df is None or df.empty:
            # API failed - don't cache this failure
            return None
        
        latest = df.iloc[-1]
        
        # ============= TR VALUE & STATUS =============
        tr_value = None
        possible_tr_names = ['TR', 'TR Indicator', 'TR_Value', 'tr', 'TR_Indicator', 'TR Value']
        
        for col_name in possible_tr_names:
            if col_name in df.columns:
                tr_value = latest.get(col_name, None)
                if tr_value is not None and not pd.isna(tr_value):
                    break
        
        # Calculate TR from EMAs if not found
        if tr_value is None or pd.isna(tr_value):
            close = latest['Close']
            ema_13 = df['Close'].ewm(span=13, adjust=False).mean().iloc[-1] if len(df) >= 13 else None
            ema_30 = df['Close'].ewm(span=30, adjust=False).mean().iloc[-1] if len(df) >= 30 else None
            
            if ema_13 and ema_30:
                if close > ema_13 and ema_13 > ema_30:
                    spread = ((close - ema_30) / ema_30) * 100
                    tr_value = 2.0 if spread > 5 else 1.5
                elif close > ema_13:
                    tr_value = 1.0
                elif close < ema_13 and ema_13 < ema_30:
                    spread = ((ema_30 - close) / ema_30) * 100
                    tr_value = -2.0 if spread > 5 else -1.5
                elif close < ema_13:
                    tr_value = -1.0
                else:
                    tr_value = 0.0
        
        # TR Status
        if tr_value is None or pd.isna(tr_value):
            tr_status = "N/A"
        else:
            if tr_value >= 2:
                tr_status = "Strong Buy"
            elif tr_value >= 1:
                tr_status = "Buy"
            elif tr_value >= -1:
                tr_status = "Neutral"
            elif tr_value >= -2:
                tr_status = "Sell"
            else:
                tr_status = "Strong Sell"
        
        # ============= PRICE CHANGE =============
        if len(df) > 1:
            prev_close = df.iloc[-2]['Close']
            price_change = latest['Close'] - prev_close
            price_change_pct = (price_change / prev_close) * 100
        else:
            price_change = 0
            price_change_pct = 0
        
        # ============= TECHNICAL INDICATORS =============
        rsi = calculate_rsi(df)
        macd = calculate_macd(df)
        
        # ============= MOVING AVERAGES =============
        ema_6 = df['Close'].ewm(span=6, adjust=False).mean().iloc[-1] if len(df) >= 6 else None
        ema_10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1] if len(df) >= 10 else None
        ema_13 = df['Close'].ewm(span=13, adjust=False).mean().iloc[-1] if len(df) >= 13 else None
        ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1] if len(df) >= 20 else None
        ema_30 = df['Close'].ewm(span=30, adjust=False).mean().iloc[-1] if len(df) >= 30 else None
        ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(df) >= 50 else None
        ema_200 = df['Close'].ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else None
        
        # ============= 52 WEEK HIGH/LOW =============
        high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
        low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()
        
        # ============= FUNDAMENTALS =============
        fundamentals = get_fundamentals(symbol)
        
        # ============= PERFORMANCE =============
        current_price = latest['Close']
        
        # 1 Month Performance
        if len(df) >= 21:
            price_1m_ago = df.iloc[-21]['Close']
            perf_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
        else:
            perf_1m = None
        
        # 3 Month Performance
        if len(df) >= 63:
            price_3m_ago = df.iloc[-63]['Close']
            perf_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        else:
            perf_3m = None
        
        # 6 Month Performance
        if len(df) >= 126:
            price_6m_ago = df.iloc[-126]['Close']
            perf_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            perf_6m = None
        
        # YTD Performance - FIXED
        perf_ytd = None
        try:
            year_start = datetime(datetime.now().year, 1, 1)
            
            # Convert df.index to datetime if needed
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'Date' in df.columns:
                    df_temp = df.copy()
                    df_temp['Date'] = pd.to_datetime(df_temp['Date'])
                    df_temp = df_temp.set_index('Date')
                else:
                    df_temp = df.copy()
                    df_temp.index = pd.to_datetime(df_temp.index)
            else:
                df_temp = df
            
            # Handle timezone
            if hasattr(df_temp.index, 'tz') and df_temp.index.tz is not None:
                import pytz
                year_start = year_start.replace(tzinfo=pytz.UTC)
            
            df_ytd = df_temp[df_temp.index >= year_start]
            if len(df_ytd) > 0:
                price_ytd_start = df_ytd.iloc[0]['Close']
                perf_ytd = ((current_price - price_ytd_start) / price_ytd_start) * 100
        except Exception as e:
            # Fallback: use trading days estimate
            days_this_year = (datetime.now() - datetime(datetime.now().year, 1, 1)).days
            trading_days_ytd = int(days_this_year * 0.69)
            if len(df) >= trading_days_ytd and trading_days_ytd > 0:
                price_ytd_start = df.iloc[-trading_days_ytd]['Close']
                perf_ytd = ((current_price - price_ytd_start) / price_ytd_start) * 100
        
        # 1 Year Performance
        if len(df) >= 252:
            price_1y_ago = df.iloc[-252]['Close']
            perf_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        else:
            perf_1y = None
        
        # 3 Year Performance
        if len(df) >= 756:
            price_3y_ago = df.iloc[-756]['Close']
            perf_3y = ((current_price - price_3y_ago) / price_3y_ago) * 100
        else:
            perf_3y = None
        
        # 5 Year Performance
        perf_5y = None
        if len(df) >= 1260:
            try:
                price_5y_ago = df.iloc[-1260]['Close']
                perf_5y = ((current_price - price_5y_ago) / price_5y_ago) * 100
            except:
                perf_5y = None
        elif len(df) >= 1000:
            try:
                price_earliest = df.iloc[0]['Close']
                perf_5y = ((current_price - price_earliest) / price_earliest) * 100
            except:
                perf_5y = None
        
        # ============= TR LEVELS =============
        buy_point = None
        stop_loss = None
        buy_names = ['Buy Point', 'buy_point', 'BuyPoint', 'Entry', 'Buy_Point']
        stop_names = ['Stop Loss', 'stop_loss', 'StopLoss', 'Stop', 'Stop_Loss']
        
        for col_name in buy_names:
            if col_name in df.columns:
                buy_point = latest.get(col_name, None)
                if buy_point is not None and not pd.isna(buy_point):
                    break
        
        for col_name in stop_names:
            if col_name in df.columns:
                stop_loss = latest.get(col_name, None)
                if stop_loss is not None and not pd.isna(stop_loss):
                    break
        
        risk_pct = None
        if buy_point and stop_loss and buy_point > 0:
            risk_pct = ((buy_point - stop_loss) / buy_point) * 100
        
        # ============= BUILD COMPLETE RESULT =============
        result = {
            # Basic
            'symbol': symbol,
            'current_price': latest['Close'],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': latest.get('Volume', None),
            
            # TR Indicators
            'tr_status': tr_status,
            'tr_value': tr_value,
            
            # Technical
            'rsi': rsi,
            'macd': macd,
            
            # TR Levels
            'buy_point': buy_point,
            'stop_loss': stop_loss,
            'risk_pct': risk_pct,
            
            # Moving Averages
            'ema_6': ema_6,
            'ema_10': ema_10,
            'ema_13': ema_13,
            'ema_20': ema_20,
            'ema_30': ema_30,
            'ema_50': ema_50,
            'ema_200': ema_200,
            
            # 52 Week Stats
            'high_52w': high_52w,
            'low_52w': low_52w,
            
            # Fundamentals
            'beta': fundamentals['beta'],
            'pe_ratio': fundamentals['pe_ratio'],
            'market_cap': fundamentals['market_cap'],
            
            # Performance
            'perf_1m': perf_1m,
            'perf_3m': perf_3m,
            'perf_6m': perf_6m,
            'perf_ytd': perf_ytd,
            'perf_1y': perf_1y,
            'perf_3y': perf_3y,
            'perf_5y': perf_5y,
            
            # Metadata
            'timestamp': datetime.now(),
            'price': latest['Close']
        }
        
        # Cache the result
        st.session_state.stock_tr_cache[cache_key] = result
        
        return result
        
    except Exception as e:
        # Log error but don't crash the app
        print(f"❌ Error analyzing {symbol} with {data_source}: {str(e)[:200]}")
        # Return None so the stock shows as not analyzed
        return None

def format_column_value(stock_data, column_id):
    """Format column value for display"""
    value = stock_data.get(column_id, None)
    
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    
    # Format based on column type
    if column_id in ['current_price', 'buy_point', 'stop_loss', 'ema_6', 'ema_10', 'ema_13', 'ema_20', 'ema_30', 'ema_50', 'ema_200', 'high_52w', 'low_52w']:
        return f"${value:.2f}"
    
    elif column_id in ['price_change_pct', 'risk_pct', 'perf_1m', 'perf_3m', 'perf_6m', 'perf_ytd', 'perf_1y', 'perf_3y', 'perf_5y']:
        color = "green" if value >= 0 else "red"
        sign = "+" if value >= 0 else ""
        return f'<span style="color:{color}; font-weight:bold;">{sign}{value:.2f}%</span>'
    
    elif column_id == 'volume':
        if value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:,.0f}"
    
    elif column_id == 'tr_status':
        return format_tr_status_html(value)
    
    elif column_id == 'tr_value':
        return f"{value:.2f}"
    
    elif column_id in ['rsi', 'macd']:
        return f"{value:.2f}"
    
    elif column_id == 'beta':
        return f"{value:.2f}"
    
    elif column_id == 'pe_ratio':
        return f"{value:.2f}"
    
    elif column_id == 'market_cap':
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        else:
            return f"${value:,.0f}"
    
    return str(value)

# ============================================================================
# SIDEBAR - WATCHLIST SELECTOR
# ============================================================================

def show_watchlist_selector():
    """Show watchlist selector in sidebar"""
    st.sidebar.title("📋 Your Watchlists")
    
    if not st.session_state.watchlists:
        st.sidebar.info("No watchlists yet. Create one below!")
        return
    
    for wl_id, watchlist in st.session_state.watchlists.items():
        col1, col2 = st.sidebar.columns([4, 1])
        
        with col1:
            is_active = (st.session_state.active_watchlist == wl_id)
            button_type = "primary" if is_active else "secondary"
            
            stock_count = len(watchlist['stocks'])
            
            if st.sidebar.button(
                f"📊 {watchlist['name']} ({stock_count})",
                key=f"select_wl_{wl_id}",
                type=button_type,
                use_container_width=True
            ):
                st.session_state.active_watchlist = wl_id
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_wl_{wl_id}"):
                delete_watchlist(wl_id)
                st.rerun()
    
    st.sidebar.divider()

def show_create_watchlist_form():
    """Show form to create a new watchlist - SAFE VERSION"""
    st.sidebar.subheader("➕ Create New Watchlist")
    
    # Use a unique key that changes each time
    new_name = st.sidebar.text_input(
        "Watchlist Name", 
        placeholder="e.g., Tech Stocks",
        key="new_watchlist_input"
    )
    
    if st.sidebar.button("Create Watchlist", key="create_btn"):
        if new_name and new_name.strip():
            # Only create if name is not empty
            wl_id = create_watchlist(new_name.strip())
            st.sidebar.success(f"✅ Created: {new_name}")
            # Don't call st.rerun() here - let natural rerun happen
        else:
            st.sidebar.error("Please enter a name")

def show_add_stock_form(watchlist_id):
    """Show form to add stocks - supports bulk addition"""
    st.subheader("➕ Add Stock(s) to Watchlist")
    st.caption("💡 Tip: Add multiple stocks at once (e.g., AAPL, MSFT, GOOGL)")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_symbols = st.text_input(
            "Enter Stock Symbol(s)",
            placeholder="e.g., AAPL or AAPL, MSFT, GOOGL",
            key=f"add_stock_input_{watchlist_id}",
            help="Enter one or more stock symbols separated by commas"
        )
    
    with col2:
        st.write("")
        st.write("")
        add_button = st.button("Add Stock(s)", key=f"add_stock_btn_{watchlist_id}")
    
    if add_button and new_symbols:
        symbols_list = [s.strip().upper() for s in new_symbols.split(',') if s.strip()]
        
        if not symbols_list:
            st.error("❌ Please enter at least one stock symbol")
            return
        
        added = []
        already_exists = []
        invalid = []
        
        if len(symbols_list) > 1:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for idx, symbol in enumerate(symbols_list):
            if len(symbols_list) > 1:
                progress = (idx + 1) / len(symbols_list)
                progress_bar.progress(progress)
                status_text.text(f"Processing {symbol}... ({idx + 1}/{len(symbols_list)})")
            
            # First, verify stock exists
            stock_info = get_stock_info(symbol)
            
            if not stock_info:
                invalid.append(symbol)
                continue
            
            # Check if already in watchlist BEFORE trying to fetch data
            watchlist = st.session_state.watchlists.get(watchlist_id)
            if watchlist and symbol in watchlist.get('stocks', []):
                already_exists.append(symbol)
                continue
            
            # Try to fetch stock data to verify it's accessible
            try:
                data_source = watchlist.get('data_source', 'yahoo')
                test_data = get_shared_stock_data(
                    ticker=symbol,
                    duration_days=30,  # Just test with 30 days
                    timeframe='daily',
                    api_source=data_source
                )
                
                if test_data is None or test_data.empty:
                    invalid.append(f"{symbol} (no data available)")
                    continue
                
                # Data is good, now add to watchlist
                success = add_stock_to_watchlist(watchlist_id, symbol)
                if success:
                    added.append(f"{symbol} - {stock_info.get('name', '')}")
                else:
                    already_exists.append(symbol)
                    
            except Exception as e:
                invalid.append(f"{symbol} (error: {str(e)[:50]})")
                continue
        
        if len(symbols_list) > 1:
            progress_bar.empty()
            status_text.empty()
        
        if added:
            st.success(f"✅ Added {len(added)} stock(s):")
            for stock in added:
                st.write(f"  • {stock}")
        
        if already_exists:
            st.warning(f"⚠️ Already in watchlist ({len(already_exists)}): {', '.join(already_exists)}")
        
        if invalid:
            st.error(f"❌ Could not add ({len(invalid)}): {', '.join(invalid)}")
        
        # Don't call st.rerun() - Streamlit will rerun naturally after button click
    
    st.divider()

def show_custom_view_manager(watchlist_id):
    """Show custom view creator and manager"""
    
    # Save Watchlist As
    st.markdown("**💾 Save Watchlist As:**")
    
    col1, col2 = st.columns([6, 2])
    
    with col1:
        new_watchlist_name = st.text_input(
            "Watchlist Name",
            placeholder="Enter new watchlist name",
            key=f"save_watchlist_as_{watchlist_id}",
            label_visibility="collapsed"
        )
    
    with col2:
        save_watchlist_btn = st.button("Save", key=f"save_watchlist_btn_{watchlist_id}", type="primary", use_container_width=True)
    
    if save_watchlist_btn:
        if new_watchlist_name:
            watchlists = st.session_state.watchlists
            current_watchlist = watchlists.get(watchlist_id, {})
            
            # Create new watchlist with same stocks
            new_id = create_watchlist(new_watchlist_name)
            st.session_state.watchlists[new_id]['stocks'] = current_watchlist.get('stocks', []).copy()
            
            st.success(f"✅ Watchlist saved as: {new_watchlist_name}")
            st.rerun()
        else:
            st.error("Please enter a watchlist name")
    
    st.markdown("")
    
    with st.expander("⚙️ Customize Columns & Manage Views", expanded=False):
        st.subheader("📊 Create Custom View")
        st.caption("Select fields manually to create a custom view from scratch")
        
        # Get current view
        all_views = get_all_views()
        current_view_name = st.session_state.watchlist_view_prefs.get(watchlist_id, 'Standard')
        current_columns = all_views.get(current_view_name, PRESET_VIEWS['Standard'])
        
        with st.form(key=f"save_view_form_{watchlist_id}"):
            # Group fields by category
            categories = {}
            for field_id, field_info in AVAILABLE_COLUMNS.items():
                category = field_info.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append((field_id, field_info['name']))
            
            st.write("**Select Fields to Display:**")
            
            selected_fields = []
            
            # Show checkboxes by category
            for category, fields in sorted(categories.items()):
                st.markdown(f"**{category}:**")
                cols = st.columns(3)
                for idx, (field_id, field_name) in enumerate(fields):
                    with cols[idx % 3]:
                        if st.checkbox(field_name, key=f"field_{field_id}_{watchlist_id}"):
                            selected_fields.append(field_id)
            
            st.divider()
            
            # Save button
            st.markdown("**Save View:**")
            col1, col2 = st.columns([6, 2])
            with col1:
                view_name = st.text_input(
                    "name", 
                    placeholder="e.g., My Day Trading View",
                    key=f"view_name_input_{watchlist_id}",
                    label_visibility="collapsed"
                )
            with col2:
                save_view_btn = st.form_submit_button("Save", type="primary", use_container_width=True)
            
            if save_view_btn:
                if view_name and selected_fields:
                    if 'symbol' not in selected_fields:
                        selected_fields.insert(0, 'symbol')
                    save_custom_view(view_name, selected_fields)
                    st.session_state.watchlist_view_prefs[watchlist_id] = view_name
                    st.success(f"✅ Saved view: {view_name}")
                    st.rerun()
                elif not view_name:
                    st.error("Please enter a view name")
                elif not selected_fields:
                    st.error("Please select at least one field")
        
        # Manage existing custom views
        if st.session_state.custom_views:
            st.divider()
            st.subheader("🗂️ Manage Custom Views")
            
            for view_name in list(st.session_state.custom_views.keys()):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📌 {view_name}")
                with col2:
                    if st.button("🗑️", key=f"delete_view_{view_name}"):
                        delete_custom_view(view_name)
                        st.rerun()

def show_watchlist_stocks_enhanced(watchlist_id):
    """Display watchlist stocks with enhanced features"""
    
    watchlist = st.session_state.watchlists.get(watchlist_id)
    if not watchlist:
        st.error("Watchlist not found")
        return
    
    stocks = watchlist.get('stocks', [])
    
    if not stocks:
        st.info("📭 No stocks in this watchlist yet. Add some stocks to get started!")
        return
    
    # View selector and custom view creator
    col1, col2 = st.columns([2, 1])
    
    with col1:
        all_views = get_all_views()
        current_view = st.session_state.watchlist_view_prefs.get(watchlist_id, 'Standard')
        
        view_options = list(all_views.keys())
        current_index = view_options.index(current_view) if current_view in view_options else 0
        
        selected_view = st.selectbox(
            "Select View",
            options=view_options,
            index=current_index,
            key=f"view_selector_{watchlist_id}"
        )
        
        if selected_view != current_view:
            st.session_state.watchlist_view_prefs[watchlist_id] = selected_view
            st.rerun()
    
    with col2:
        st.write("")
        st.write("")
    
    show_custom_view_manager(watchlist_id)
    
    st.divider()
    
    # Get columns to show
    columns_to_show = all_views.get(selected_view, PRESET_VIEWS['Standard'])
    
    # Analyze All button
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        data_source = watchlist.get('data_source', 'yahoo')
        if st.button(f"🔄 Analyze All ({len(stocks)} stocks)", key=f"analyze_all_{watchlist_id}", type="primary"):
            st.session_state[f"analyzing_{watchlist_id}"] = True
            st.rerun()
    
    # Bulk delete functionality
    bulk_delete_key = f"bulk_delete_selection_{watchlist_id}"
    if bulk_delete_key not in st.session_state:
        st.session_state[bulk_delete_key] = set()
    
    with col2:
        selected_count = len(st.session_state[bulk_delete_key])
        if selected_count > 0:
            if st.button(f"🗑️ Remove Selected ({selected_count})", key=f"bulk_delete_{watchlist_id}", type="secondary"):
                for symbol in list(st.session_state[bulk_delete_key]):
                    remove_stock_from_watchlist(watchlist_id, symbol)
                st.session_state[bulk_delete_key].clear()
                st.rerun()
    
    # Export column placeholder (will be filled later after data is loaded)
    export_col = col3
    
    # Analyze stocks if requested
    if st.session_state.get(f"analyzing_{watchlist_id}", False):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # CRITICAL: Get fresh watchlist data from session state before analyzing
        fresh_watchlist = st.session_state.watchlists.get(watchlist_id)
        if not fresh_watchlist:
            st.error("Watchlist not found")
            st.session_state[f"analyzing_{watchlist_id}"] = False
            return
        
        # Read data source fresh from watchlist
        current_data_source = fresh_watchlist.get('data_source', 'yahoo')
        st.info(f"🔍 Using data source: **{current_data_source.upper()}**")
        
        for idx, symbol in enumerate(stocks):
            progress = (idx + 1) / len(stocks)
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {symbol}... ({idx + 1}/{len(stocks)})")
            
            # Force analysis with correct data source
            try:
                analyze_stock_enhanced(symbol, current_data_source, columns_to_show)
            except Exception as e:
                st.warning(f"⚠️ Could not analyze {symbol}: {str(e)[:100]}")
        
        progress_bar.empty()
        status_text.empty()
        st.session_state[f"analyzing_{watchlist_id}"] = False
        st.success(f"✅ Analysis complete!")
        # Don't call st.rerun() - will rerun naturally
    
    # Build stock data - ONLY use cached data, don't fetch on every rerun
    stock_data = []
    # Get current data source from watchlist
    current_data_source = watchlist.get('data_source', 'yahoo')
    for symbol in stocks:
        # Try to get from cache first
        cache_key = f"{symbol}_{current_data_source}"
        if cache_key in st.session_state.stock_tr_cache:
            cached_data = st.session_state.stock_tr_cache[cache_key]
            # Check if cache is still valid (5 minutes)
            cached_time = cached_data.get('timestamp', datetime.min)
            if (datetime.now() - cached_time).total_seconds() < 300:
                stock_data.append(cached_data)
                continue
        
        # If not in cache or expired, create minimal placeholder
        stock_data.append({
            'symbol': symbol,
            'tr_status': None,
            'price': None
        })
    
    # Display table header
    st.subheader(f"📊 Stocks in {watchlist['name']}")
    
    # Create header with checkbox
    header_cols = st.columns([0.5] + [AVAILABLE_COLUMNS[col]['width'] for col in columns_to_show] + [0.8])
    
    with header_cols[0]:
        st.write("☑️")
    
    for idx, col_id in enumerate(columns_to_show):
        with header_cols[idx + 1]:
            st.markdown(f"**{AVAILABLE_COLUMNS[col_id]['name']}**")
    
    with header_cols[-1]:
        st.markdown("**Action**")
    
    # Show bulk delete controls if stocks are selected
    if st.session_state[bulk_delete_key]:
        selected_count = len(st.session_state[bulk_delete_key])
        if selected_count > 0:
            st.caption(f"📌 {selected_count} stock(s) selected")
    
    st.markdown("---")
    
    # Create CSV Export button
    with export_col:
        if stock_data and any(s.get('tr_status') != None or s.get('price') != None for s in stock_data):
            # Prepare CSV data
            export_data = []
            for stock in stock_data:
                row = {}
                for col_id in columns_to_show:
                    value = stock.get(col_id, 'N/A')
                    
                    # Clean HTML formatting for CSV
                    if isinstance(value, str):
                        import re
                        value = re.sub(r'<[^>]+>', '', value)
                        value = value.strip()
                    
                    row[AVAILABLE_COLUMNS[col_id]['name']] = value
                export_data.append(row)
            
            # Create DataFrame and CSV
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{watchlist['name'].replace(' ', '_')}_{timestamp}.csv"
            
            # Download button
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key=f"download_csv_{watchlist_id}",
                help=f"Download {len(stock_data)} stocks to CSV"
            )
        else:
            st.button("📥 Export CSV", key=f"export_disabled_{watchlist_id}", disabled=True, help="Click 'Analyze All' first")
    
    # Display stocks
    for idx, stock in enumerate(stock_data):
        data_cols = st.columns([0.5] + [AVAILABLE_COLUMNS[col]['width'] for col in columns_to_show] + [0.8])
        
        # Checkbox column
        with data_cols[0]:
            symbol = stock.get('symbol', '')
            is_checked = symbol in st.session_state[bulk_delete_key]
            if st.checkbox("", value=is_checked, key=f"check_{watchlist_id}_{idx}_{symbol}", label_visibility="collapsed"):
                st.session_state[bulk_delete_key].add(symbol)
            else:
                st.session_state[bulk_delete_key].discard(symbol)
        
        for col_idx, col_id in enumerate(columns_to_show):
            with data_cols[col_idx + 1]:
                # Special handling for symbol
                if col_id == 'symbol':
                    symbol = stock.get('symbol', 'N/A')
                    if st.button(f"🔍 {symbol}", key=f"goto_{watchlist_id}_{idx}_{symbol}", use_container_width=True):
                        st.session_state.selected_symbol = symbol
                        st.switch_page("pages/1_Stocks_Analysis.py")
                else:
                    formatted_value = format_column_value(stock, col_id)
                    # Fields that use HTML for coloring
                    if col_id in ['price_change_pct', 'tr_status', 'perf_1m', 'perf_3m', 'perf_6m', 
                                  'perf_ytd', 'perf_1y', 'perf_3y', 'perf_5y']:
                        st.markdown(formatted_value, unsafe_allow_html=True)
                    else:
                        st.write(formatted_value)
        
        with data_cols[-1]:
            if st.button("❌", key=f"remove_{watchlist_id}_{idx}_{stock['symbol']}"):
                remove_stock_from_watchlist(watchlist_id, stock['symbol'])
                st.rerun()
        
        st.divider()
    
    # Summary statistics
    if 'tr_status' in columns_to_show:
        st.divider()
        st.subheader("📈 Watchlist Summary")
        
        analyzed_stocks = [s for s in stock_data if s.get('tr_status') and s.get('tr_status') != "N/A"]
        
        if analyzed_stocks:
            strong_buy = sum(1 for s in analyzed_stocks if s['tr_status'] == 'Strong Buy')
            buy = sum(1 for s in analyzed_stocks if s['tr_status'] == 'Buy')
            neutral = sum(1 for s in analyzed_stocks if s['tr_status'] == 'Neutral')
            sell = sum(1 for s in analyzed_stocks if s['tr_status'] == 'Sell')
            strong_sell = sum(1 for s in analyzed_stocks if s['tr_status'] == 'Strong Sell')
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Strong Buy", strong_buy)
            with col2:
                st.metric("Buy", buy)
            with col3:
                st.metric("Neutral", neutral)
            with col4:
                st.metric("Sell", sell)
            with col5:
                st.metric("Strong Sell", strong_sell)
        else:
            st.info("Click 'Analyze All' to see TR status for all stocks")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application"""
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True
    
    if not st.session_state.logged_in:
        st.warning("⚠️ Please log in to access Watchlists")
        return
    
    initialize_session_state()
    
    st.title("📋 Watchlists")
    st.markdown("*Create and manage stock watchlists with **32 available fields** and custom views*")
    st.divider()
    
    # Emergency reset button (for debugging)
    with st.sidebar.expander("🔧 Advanced", expanded=False):
        st.caption("**Troubleshooting Tools:**")
        if st.button("🗑️ Clear All Cache", key="clear_cache_btn"):
            st.session_state.stock_tr_cache = {}
            st.success("✅ Cache cleared!")
        
        if st.button("🔄 Reset Session", key="reset_session_btn"):
            keys_to_keep = ['logged_in']
            keys_to_delete = [k for k in st.session_state.keys() if k not in keys_to_keep]
            for key in keys_to_delete:
                del st.session_state[key]
            st.rerun()
    
    show_watchlist_selector()
    show_create_watchlist_form()
    
    if st.session_state.active_watchlist is None:
        st.info("👈 Select a watchlist from the sidebar or create a new one")
        
        st.subheader("🚀 Quick Start Guide")
        st.markdown("""
        **Getting Started:**
        
        1. **Create a Watchlist** - Click "Create New Watchlist" in sidebar
        2. **Add Stocks** - Enter symbols (single or bulk: AAPL, MSFT, GOOGL)
        3. **Choose/Create View** - 7 presets + unlimited custom views
        4. **Analyze** - Click "Analyze All" to see all 32 fields
        
        **32 Available Fields:**
        - Basic: Symbol, Price, Change %, Volume
        - TR: TR Status, TR Value, Buy Point, Stop Loss, Risk %
        - Technical: RSI, MACD
        - EMAs: 6, 10, 13, 20, 30, 50, 200
        - 52 Week: High, Low
        - Fundamentals: Beta, P/E, Market Cap
        - Performance: 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y
        
        **Custom Views:**
        Click "⚙️ Customize Columns" to create your own view with any combination of fields!
        """)
    else:
        watchlist = st.session_state.watchlists.get(st.session_state.active_watchlist)
        
        if watchlist:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.header(f"📊 {watchlist['name']}")
                st.caption(f"Created: {watchlist['created_at'].strftime('%B %d, %Y')}")
            
            with col2:
                with st.expander("⚙️ Settings", expanded=False):
                    new_name = st.text_input("Rename Watchlist", value=watchlist['name'], key=f"rename_{st.session_state.active_watchlist}")
    
                # Data source selector
                current_source = watchlist.get('data_source', 'yahoo')
                data_source = st.selectbox(
                    "Data Source",
                    ["yahoo", "tiingo"],
                    index=0 if current_source == 'yahoo' else 1,
                    help="Yahoo: Free, Tiingo: More reliable ($50/month)",
                    key=f"datasource_{st.session_state.active_watchlist}"
                )
    
                if st.button("Save Settings", key=f"save_settings_{st.session_state.active_watchlist}"):
                    rename_watchlist(st.session_state.active_watchlist, new_name)
                    st.session_state.watchlists[st.session_state.active_watchlist]['data_source'] = data_source
                    # Clear cache when data source changes
                    if data_source != current_source:
                        st.session_state.stock_tr_cache = {}
                        st.success(f"✅ Settings saved! Switched to {data_source.upper()}. Cache cleared. Click 'Analyze All' to refresh data.")
                    else:
                        st.success("✅ Settings saved!")
                    st.rerun()
            
            st.divider()
            
            show_add_stock_form(st.session_state.active_watchlist)
            show_watchlist_stocks_enhanced(st.session_state.active_watchlist)
        else:
            st.error("Watchlist not found")

if __name__ == "__main__":
    main()
