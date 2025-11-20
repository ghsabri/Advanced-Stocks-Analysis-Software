"""
Watchlists Page V3 - Enhanced with Custom View Creator
COMPLETE VERSION - November 11, 2025

Features:
✅ 22 Available Fields (12 existing + 10 new)
✅ Custom View Creator - Select any fields you want
✅ Save/Load/Delete Custom Templates
✅ 5 Built-in Preset Views + Unlimited Custom Views
✅ Bulk Stock Addition (comma-separated)
✅ Fixed TR Status and TR Value
✅ Fixed EMA calculations
✅ Progress indicators
✅ Smart caching

NEW FIELDS ADDED:
- EMA 50, EMA 200
- 52 Week High, 52 Week Low
- Beta, P/E Ratio, Market Cap
- 1 Month Perf %, 3 Month Perf %, YTD Perf %
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
# COLUMN CONFIGURATION - 22 FIELDS AVAILABLE
# ============================================================================

AVAILABLE_COLUMNS = {
    # Basic Fields (6)
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
    
    # Moving Averages (7) - NEW: EMA 6, 10, 20, 50, 200
    'ema_6': {'name': 'EMA 6', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_10': {'name': 'EMA 10', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_13': {'name': 'EMA 13', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_20': {'name': 'EMA 20', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_30': {'name': 'EMA 30', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_50': {'name': 'EMA 50', 'width': 1.5, 'category': 'Moving Averages'},
    'ema_200': {'name': 'EMA 200', 'width': 1.5, 'category': 'Moving Averages'},
    
    # 52 Week Stats (2) - NEW
    'high_52w': {'name': '52W High', 'width': 1.5, 'category': '52 Week Stats'},
    'low_52w': {'name': '52W Low', 'width': 1.5, 'category': '52 Week Stats'},
    
    # Fundamentals (3) - NEW
    'beta': {'name': 'Beta', 'width': 1.2, 'category': 'Fundamentals'},
    'pe_ratio': {'name': 'P/E', 'width': 1.2, 'category': 'Fundamentals'},
    'market_cap': {'name': 'Market Cap', 'width': 1.8, 'category': 'Fundamentals'},
    
    # Performance (7) - NEW: All periods
    'perf_1m': {'name': '1M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_3m': {'name': '3M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_6m': {'name': '6M Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_ytd': {'name': 'YTD Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_1y': {'name': '1Y Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_3y': {'name': '3Y Perf%', 'width': 1.5, 'category': 'Performance'},
    'perf_5y': {'name': '5Y Perf%', 'width': 1.5, 'category': 'Performance'},
}

# Built-in preset views (for convenience)
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
    """Initialize session state for watchlists"""
    if 'watchlists' not in st.session_state:
        st.session_state.watchlists = {}
    
    if 'next_watchlist_id' not in st.session_state:
        st.session_state.next_watchlist_id = 1
    
    if 'active_watchlist' not in st.session_state:
        st.session_state.active_watchlist = None
    
    if 'stock_tr_cache' not in st.session_state:
        st.session_state.stock_tr_cache = {}
    
    # Custom views storage
    if 'custom_views' not in st.session_state:
        st.session_state.custom_views = {}  # {view_name: [field_list]}
    
    # View preference per watchlist (can be preset or custom)
    if 'watchlist_view_prefs' not in st.session_state:
        st.session_state.watchlist_view_prefs = {}  # {watchlist_id: view_name}
    
    # Sorting state per watchlist
    if 'watchlist_sort' not in st.session_state:
        st.session_state.watchlist_sort = {}  # {watchlist_id: {'column': 'symbol', 'ascending': True}}

# ============================================================================
# WATCHLIST MANAGEMENT FUNCTIONS
# ============================================================================

def create_watchlist(name, data_source='yahoo'):
    """Create a new watchlist"""
    watchlist_id = st.session_state.next_watchlist_id
    st.session_state.watchlists[watchlist_id] = {
        'name': name,
        'created_at': datetime.now(),
        'stocks': [],
        'data_source': data_source  # Save preferred data source
    }
    st.session_state.next_watchlist_id += 1
    st.session_state.active_watchlist = watchlist_id
    st.session_state.watchlist_view_prefs[watchlist_id] = 'Standard'
    return watchlist_id

def delete_watchlist(watchlist_id):
    """Delete a watchlist"""
    if watchlist_id in st.session_state.watchlists:
        del st.session_state.watchlists[watchlist_id]
        if watchlist_id in st.session_state.watchlist_view_prefs:
            del st.session_state.watchlist_view_prefs[watchlist_id]
        if st.session_state.active_watchlist == watchlist_id:
            st.session_state.active_watchlist = None

def rename_watchlist(watchlist_id, new_name):
    """Rename a watchlist"""
    if watchlist_id in st.session_state.watchlists:
        st.session_state.watchlists[watchlist_id]['name'] = new_name

def add_stock_to_watchlist(watchlist_id, symbol):
    """Add a stock to a watchlist"""
    if watchlist_id in st.session_state.watchlists:
        stocks = st.session_state.watchlists[watchlist_id]['stocks']
        if symbol not in stocks:
            stocks.append(symbol)
            return True
    return False

def remove_stock_from_watchlist(watchlist_id, symbol):
    """Remove a stock from a watchlist"""
    if watchlist_id in st.session_state.watchlists:
        stocks = st.session_state.watchlists[watchlist_id]['stocks']
        if symbol in stocks:
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
# CUSTOM VIEW MANAGEMENT
# ============================================================================

def save_custom_view(view_name, field_list):
    """Save a custom view template"""
    st.session_state.custom_views[view_name] = field_list

def delete_custom_view(view_name):
    """Delete a custom view template"""
    if view_name in st.session_state.custom_views:
        del st.session_state.custom_views[view_name]

def get_all_views():
    """Get all available views (presets + custom)"""
    all_views = {}
    all_views.update(PRESET_VIEWS)
    all_views.update(st.session_state.custom_views)
    return all_views

# ============================================================================
# ENHANCED ANALYSIS WITH ALL 22 FIELDS
# ============================================================================

def calculate_rsi(df, period=14):
    """Calculate RSI"""
    try:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except:
        return None

def calculate_macd(df):
    """Calculate MACD"""
    try:
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        return macd.iloc[-1]
    except:
        return None

def get_fundamentals(symbol):
    """Get fundamental data from yfinance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.info
        
        return {
            'beta': info.get('beta'),
            'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
            'market_cap': info.get('marketCap')
        }
    except:
        return {'beta': None, 'pe_ratio': None, 'market_cap': None}

def get_tr_status_badge(tr_status):
    """Get HTML badge for TR status"""
    if not tr_status or tr_status == "N/A":
        return '<span class="tr-loading">N/A</span>'
    
    status_map = {
        'Strong Buy': 'tr-strong-buy',
        'Buy': 'tr-buy',
        'Neutral': 'tr-neutral',
        'Sell': 'tr-sell',
        'Strong Sell': 'tr-strong-sell'
    }
    
    css_class = status_map.get(tr_status, 'tr-loading')
    return f'<span class="{css_class}">{tr_status}</span>'

def analyze_stock_enhanced(symbol, data_source='yahoo', needed_fields=None):
    """
    Enhanced analysis with ALL 32 fields
    Returns complete stock analysis including new fields
    
    Args:
        symbol: Stock ticker symbol
        data_source: 'yahoo' or 'tiingo' (default: 'yahoo')
        needed_fields: List of field IDs that are actually needed (for optimization)
    """
    # Check cache first
    cache_key = f"{symbol}_{data_source}"
    if cache_key in st.session_state.stock_tr_cache:
        cached_time = st.session_state.stock_tr_cache[cache_key].get('timestamp')
        if cached_time and (datetime.now() - cached_time).total_seconds() < 300:  # 5 minute cache
            return st.session_state.stock_tr_cache[cache_key]
    
    try:
        # Determine if TR calculation is needed
        tr_fields = {'tr_status', 'tr_value', 'buy_point', 'stop_loss', 'risk_pct'}
        needs_tr = needed_fields is None or bool(tr_fields & set(needed_fields))
        
        # Get stock data - only calculate TR if needed!
        df = get_shared_stock_data(
            ticker=symbol,
            duration_days=1825,  # 5 years (365 * 5)
            timeframe='daily',
            api_source=data_source,
            include_tr=needs_tr  # Only calculate TR if needed! ✅
        )
        
        if df is None or df.empty:
            return None
        
        # DEBUG: Print data length (temporary - remove after testing)
        # st.info(f"DEBUG {symbol}: Got {len(df)} days of data (need 1260 for 5Y)")
        
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
        
        # 1 Month Performance (21 trading days)
        if len(df) >= 21:
            price_1m_ago = df.iloc[-21]['Close']
            perf_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
        else:
            perf_1m = None
        
        # 3 Month Performance (63 trading days)
        if len(df) >= 63:
            price_3m_ago = df.iloc[-63]['Close']
            perf_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        else:
            perf_3m = None
        
        # 6 Month Performance (126 trading days)
        if len(df) >= 126:
            price_6m_ago = df.iloc[-126]['Close']
            perf_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        else:
            perf_6m = None
        
        # YTD Performance - FIXED
        perf_ytd = None
        try:
            year_start = datetime(datetime.now().year, 1, 1)
            # Handle timezone-aware index
            if hasattr(df.index, 'tz') and df.index.tz is not None:
                import pytz
                year_start = year_start.replace(tzinfo=pytz.UTC)
            
            # Filter data from year start
            df_ytd = df[df.index >= year_start]
            if len(df_ytd) > 0:
                price_ytd_start = df_ytd.iloc[0]['Close']
                perf_ytd = ((current_price - price_ytd_start) / price_ytd_start) * 100
        except Exception as e:
            # If YTD fails, try calculating from trading days (assume ~252 days/year, so far this year)
            days_this_year = (datetime.now() - datetime(datetime.now().year, 1, 1)).days
            trading_days_ytd = int(days_this_year * 0.69)  # ~252/365 = 0.69
            if len(df) >= trading_days_ytd and trading_days_ytd > 0:
                price_ytd_start = df.iloc[-trading_days_ytd]['Close']
                perf_ytd = ((current_price - price_ytd_start) / price_ytd_start) * 100
        
        # 1 Year Performance (252 trading days)
        if len(df) >= 252:
            price_1y_ago = df.iloc[-252]['Close']
            perf_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        else:
            perf_1y = None
        
        # 3 Year Performance (756 trading days)
        if len(df) >= 756:
            price_3y_ago = df.iloc[-756]['Close']
            perf_3y = ((current_price - price_3y_ago) / price_3y_ago) * 100
        else:
            perf_3y = None
        
        # 5 Year Performance (1260 trading days) - FIXED with fallback
        perf_5y = None
        if len(df) >= 1260:
            try:
                price_5y_ago = df.iloc[-1260]['Close']
                perf_5y = ((current_price - price_5y_ago) / price_5y_ago) * 100
            except:
                perf_5y = None
        elif len(df) >= 1000:  # If we have 4+ years, calculate from what we have
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
        
        # ============= BUILD COMPLETE RESULT WITH ALL 22 FIELDS =============
        result = {
            # Basic (6)
            'symbol': symbol,
            'current_price': latest['Close'],
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': latest.get('Volume', None),
            
            # TR Indicators (2)
            'tr_status': tr_status,
            'tr_value': tr_value,
            
            # Technical (2)
            'rsi': rsi,
            'macd': macd,
            
            # TR Levels (3)
            'buy_point': buy_point,
            'stop_loss': stop_loss,
            'risk_pct': risk_pct,
            
            # Moving Averages (7) - NEW: EMA 6, 10, 20
            'ema_6': ema_6,
            'ema_10': ema_10,
            'ema_13': ema_13,
            'ema_20': ema_20,
            'ema_30': ema_30,
            'ema_50': ema_50,
            'ema_200': ema_200,
            
            # 52 Week Stats (2)
            'high_52w': high_52w,
            'low_52w': low_52w,
            
            # Fundamentals (3)
            'beta': fundamentals['beta'],
            'pe_ratio': fundamentals['pe_ratio'],
            'market_cap': fundamentals['market_cap'],
            
            # Performance (7) - NEW: 6M, 1Y, 3Y, 5Y
            'perf_1m': perf_1m,
            'perf_3m': perf_3m,
            'perf_6m': perf_6m,
            'perf_ytd': perf_ytd,
            'perf_1y': perf_1y,
            'perf_3y': perf_3y,
            'perf_5y': perf_5y,
            
            'timestamp': datetime.now()
        }
        
        # Cache result with data source in key
        cache_key = f"{symbol}_{data_source}"
        st.session_state.stock_tr_cache[cache_key] = result
        return result
    
    except Exception as e:
        st.warning(f"Error analyzing {symbol}: {str(e)}")
        return None

# ============================================================================
# UI COMPONENTS
# ============================================================================

def show_watchlist_selector():
    """Show watchlist selector sidebar"""
    st.sidebar.header("📋 Your Watchlists")
    
    watchlists = st.session_state.watchlists
    
    if not watchlists:
        st.sidebar.info("No watchlists yet. Create one to get started!")
    else:
        for wl_id, wl_data in watchlists.items():
            summary = get_watchlist_summary(wl_id)
            if summary:
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    if st.button(
                        f"📊 {summary['name']} ({summary['stock_count']})",
                        key=f"select_wl_{wl_id}",
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
    """Show form to create a new watchlist"""
    st.sidebar.subheader("➕ Create New Watchlist")
    
    with st.sidebar.form("create_watchlist_form"):
        new_name = st.text_input("Watchlist Name", placeholder="e.g., Tech Stocks")
        submit = st.form_submit_button("Create Watchlist")
        
        if submit and new_name:
            wl_id = create_watchlist(new_name.strip())
            st.success(f"✅ Created watchlist: {new_name}")
            st.rerun()
        elif submit:
            st.error("Please enter a name for the watchlist")

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
            
            stock_info = get_stock_info(symbol)
            
            if stock_info:
                success = add_stock_to_watchlist(watchlist_id, symbol)
                if success:
                    added.append(f"{symbol} - {stock_info.get('name', '')}")
                else:
                    already_exists.append(symbol)
            else:
                invalid.append(symbol)
        
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
            st.error(f"❌ Invalid symbol(s) ({len(invalid)}): {', '.join(invalid)}")
        
        if added:
            st.rerun()
    
    st.divider()

def show_custom_view_manager(watchlist_id):
    """Show custom view creator and manager"""
    
    # ============= SAVE WATCHLIST AS (above expander) =============
    st.markdown("**💾 Save Watchlist As:**")
    
    col1, col2 = st.columns([6, 2])  # Wider button column
    
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
            # Get current watchlist data
            watchlists = st.session_state.watchlists
            current_watchlist = watchlists.get(watchlist_id, {})
            
            # Create new watchlist with same stocks
            new_id = len(watchlists) + 1
            watchlists[new_id] = {
                'name': new_watchlist_name,
                'stocks': current_watchlist.get('stocks', []).copy()
            }
            
            st.session_state.watchlists = watchlists
            st.session_state.active_watchlist = new_id
            st.success(f"✅ Watchlist saved as: {new_watchlist_name}")
            st.rerun()
        else:
            st.error("Please enter a watchlist name")
    
    st.markdown("")  # Small spacing
    
    with st.expander("⚙️ Customize Columns & Manage Views", expanded=False):
        # ============= CREATE NEW CUSTOM VIEW =============
        st.subheader("📊 Create Custom View")
        st.caption("Select fields manually to create a custom view from scratch")
        
        # Get current view for reference
        all_views = get_all_views()
        current_view_name = st.session_state.watchlist_view_prefs.get(watchlist_id, 'Standard')
        current_columns = all_views.get(current_view_name, PRESET_VIEWS['Standard'])
        
        # Save custom view - Put everything in form
        with st.form(key=f"save_view_form_{watchlist_id}"):
            # Group fields by category
            categories = {}
            for field_id, field_info in AVAILABLE_COLUMNS.items():
                category = field_info.get('category', 'Other')
                if category not in categories:
                    categories[category] = []
                categories[category].append((field_id, field_info['name']))
            
            # Multi-select for fields
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
            
            # Save button - Wide enough for text
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
                        selected_fields.insert(0, 'symbol')  # Always include symbol
                    save_custom_view(view_name, selected_fields)
                    st.session_state.watchlist_view_prefs[watchlist_id] = view_name
                    st.success(f"✅ Saved view: {view_name}")
                    st.rerun()
                elif not view_name:
                    st.error("Please enter a view name")
                elif not selected_fields:
                    st.error("Please select at least one field")
        
        # Show existing custom views
        if st.session_state.custom_views:
            st.divider()
            st.subheader("📚 Your Custom Views")
            for view_name in list(st.session_state.custom_views.keys()):
                col1, col2 = st.columns([4, 1])
                with col1:
                    fields = st.session_state.custom_views[view_name]
                    st.write(f"**{view_name}** ({len(fields)} fields)")
                with col2:
                    if st.button("🗑️", key=f"del_view_{view_name}"):
                        delete_custom_view(view_name)
                        st.success(f"Deleted: {view_name}")
                        st.rerun()

def format_column_value(stock, col_id):
    """Format a column value for display"""
    value = stock.get(col_id)
    
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    
    if col_id == 'symbol':
        return f"**{value}**"
    elif col_id in ['current_price', 'buy_point', 'stop_loss', 'high_52w', 'low_52w']:
        return f"${value:.2f}"
    elif col_id in ['ema_6', 'ema_10', 'ema_13', 'ema_20', 'ema_30', 'ema_50', 'ema_200']:
        return f"${value:.2f}" if value else "—"
    elif col_id == 'price_change_pct':
        color = "green" if value >= 0 else "red"
        sign = "+" if value >= 0 else ""
        return f"<span style='color:{color}'>{sign}{value:.2f}%</span>"
    elif col_id in ['perf_1m', 'perf_3m', 'perf_6m', 'perf_ytd', 'perf_1y', 'perf_3y', 'perf_5y']:
        if value is None:
            return "—"
        color = "green" if value >= 0 else "red"
        sign = "+" if value >= 0 else ""
        return f"<span style='color:{color}'>{sign}{value:.1f}%</span>"
    elif col_id == 'volume':
        if value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        return f"{value:,.0f}"
    elif col_id == 'market_cap':
        if value is None:
            return "—"
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        return f"${value:,.0f}"
    elif col_id == 'tr_status':
        return get_tr_status_badge(value)
    elif col_id == 'tr_value':
        return f"{value:.2f}" if value is not None else "—"
    elif col_id in ['rsi', 'beta']:
        return f"{value:.2f}" if value is not None else "—"
    elif col_id == 'macd':
        return f"{value:.2f}" if value is not None else "—"
    elif col_id == 'pe_ratio':
        return f"{value:.1f}" if value is not None else "—"
    elif col_id == 'risk_pct':
        return f"{value:.1f}%" if value is not None else "—"
    else:
        return str(value)

def show_watchlist_stocks_enhanced(watchlist_id):
    """Display stocks with customizable columns"""
    watchlist = st.session_state.watchlists.get(watchlist_id)
    
    if not watchlist:
        st.error("Watchlist not found")
        return
    
    stocks = watchlist['stocks']
    
    if not stocks:
        st.info("📊 This watchlist is empty. Add some stocks to get started!")
        return
    
    st.subheader(f"📊 Stocks in {watchlist['name']} ({len(stocks)})")
    
    # Controls row - Export is now a download button
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 2])
    
    with col1:
        analyze_all = st.button("🔄 Analyze All", key=f"analyze_all_{watchlist_id}")
    
    with col2:
        clear_cache = st.button("🗑️ Clear Cache", key=f"clear_cache_{watchlist_id}")
    
    # Export button will be created after we have data
    export_col = col3  # Save for later
    
    with col4:
        # View selector (presets + custom)
        all_views = get_all_views()
        current_view = st.session_state.watchlist_view_prefs.get(watchlist_id, 'Standard')
        
        if current_view not in all_views:
            current_view = 'Standard'
        
        view_type = st.selectbox(
            "View",
            list(all_views.keys()),
            index=list(all_views.keys()).index(current_view),
            key=f"view_selector_{watchlist_id}"
        )
        st.session_state.watchlist_view_prefs[watchlist_id] = view_type
    
    with col5:
        show_custom_view_manager(watchlist_id)
    
    if clear_cache:
        st.session_state.stock_tr_cache = {}
        st.success("✅ Cache cleared")
        st.rerun()
    
    # Get columns to display
    all_views = get_all_views()
    columns_to_show = all_views.get(view_type, PRESET_VIEWS['Standard'])
    
    # DEBUG: Show what view is active and what columns
    # st.info(f"Active view: {view_type} | Fields: {len(columns_to_show)} | {columns_to_show}")
    
    # Ensure symbol is always first
    if 'symbol' not in columns_to_show:
        columns_to_show = ['symbol'] + list(columns_to_show)
    
    # ============= SIMPLE FILTERS =============
    st.markdown("**🔍 Quick Filters:**")
    filter_col1, filter_col2, filter_col3 = st.columns([2, 3, 7])
    
    with filter_col1:
        price_filter = st.selectbox(
            "Price Range",
            options=["All Prices", "Under $50", "$50-$200", "$200-$500", "Over $500"],
            key=f"simple_price_{watchlist_id}"
        )
    
    with filter_col2:
        # Only show if performance columns exist
        perf_cols = [c for c in columns_to_show if 'perf_' in c]
        if perf_cols:
            perf_filter = st.selectbox(
                "Performance (uses first visible perf column)",
                options=["All Stocks", "Gainers Only", "Losers Only", "Up >10%", "Down >10%"],
                key=f"simple_perf_{watchlist_id}"
            )
        else:
            perf_filter = "All Stocks"
    
    st.markdown("---")
    
    # Show column headers (clickable for sorting)
    header_cols = []
    header_cols.append(0.5)  # Checkbox column
    for col_id in columns_to_show:
        header_cols.append(AVAILABLE_COLUMNS[col_id]['width'])
    header_cols.append(1)  # Actions
    
    # Get current sort state
    sort_state = st.session_state.watchlist_sort.get(watchlist_id, {'column': 'symbol', 'ascending': True})
    
    header_row = st.columns(header_cols)
    header_row[0].markdown("**☑**")  # Checkbox header
    for idx, col_id in enumerate(columns_to_show):
        with header_row[idx + 1]:  # +1 because of checkbox column
            # Add sort indicator if this column is sorted
            sort_indicator = ""
            if sort_state['column'] == col_id:
                sort_indicator = " ▲" if sort_state['ascending'] else " ▼"
            
            # Create button for sorting
            if st.button(f"{AVAILABLE_COLUMNS[col_id]['name']}{sort_indicator}", 
                        key=f"sort_{watchlist_id}_{col_id}",
                        use_container_width=True):
                # Toggle sort direction if same column, otherwise set to ascending
                if sort_state['column'] == col_id:
                    st.session_state.watchlist_sort[watchlist_id] = {
                        'column': col_id,
                        'ascending': not sort_state['ascending']
                    }
                else:
                    st.session_state.watchlist_sort[watchlist_id] = {
                        'column': col_id,
                        'ascending': True
                    }
                st.rerun()
    with header_row[-1]:
        st.markdown("**Actions**")
    
    st.divider()
    
    # Analyze stocks
    stock_data = []
    
    # Get data source for this watchlist
    watchlist_data_source = watchlist.get('data_source', 'yahoo')
    
    with st.spinner("Analyzing stocks..."):
        for symbol in stocks:
            cache_key = f"{symbol}_{watchlist_data_source}"
            if analyze_all or cache_key in st.session_state.stock_tr_cache:
                try:
                    # Pass needed fields for optimization - only calculate what's needed!
                    analysis = analyze_stock_enhanced(symbol, watchlist_data_source, needed_fields=columns_to_show)
                    if analysis:
                        stock_data.append(analysis)
                    else:
                        # Analysis returned None - show symbol with empty fields
                        stock_data.append({'symbol': symbol})
                except Exception as e:
                    st.error(f"Error analyzing {symbol}: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    stock_data.append({'symbol': symbol})
            else:
                stock_data.append({'symbol': symbol})
    
    # Sort stock data based on current sort state
    sort_state = st.session_state.watchlist_sort.get(watchlist_id, {'column': 'symbol', 'ascending': True})
    sort_column = sort_state['column']
    sort_ascending = sort_state['ascending']
    
    def get_sort_value(stock, col_id):
        """Extract sortable value from stock data"""
        value = stock.get(col_id)
        
        # Handle None/N/A values - put them at the end
        if value is None or value == "N/A" or value == "-":
            return float('inf') if sort_ascending else float('-inf')
        
        # Handle percentage strings (e.g., "5.2%", "+3.1%", "-2.5%")
        if isinstance(value, str) and '%' in value:
            try:
                return float(value.replace('%', '').replace('+', '').replace(',', ''))
            except:
                return float('inf') if sort_ascending else float('-inf')
        
        # Handle currency strings (e.g., "$150.25", "$1,234.56")
        if isinstance(value, str) and '$' in value:
            try:
                return float(value.replace('$', '').replace(',', ''))
            except:
                return float('inf') if sort_ascending else float('-inf')
        
        # Handle TR Status (categorical)
        if col_id == 'tr_status':
            status_order = {'Strong Buy': 5, 'Buy': 4, 'Neutral': 3, 'Sell': 2, 'Strong Sell': 1, 'N/A': 0}
            return status_order.get(value, 0)
        
        # Handle market cap with suffixes (e.g., "1.5T", "250B", "5M")
        if col_id == 'market_cap' and isinstance(value, str):
            try:
                multipliers = {'T': 1e12, 'B': 1e9, 'M': 1e6, 'K': 1e3}
                for suffix, mult in multipliers.items():
                    if suffix in value:
                        return float(value.replace(suffix, '').replace('$', '').replace(',', '')) * mult
                return float(value.replace('$', '').replace(',', ''))
            except:
                return float('inf') if sort_ascending else float('-inf')
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            return value
        
        # Handle strings (alphabetical)
        if isinstance(value, str):
            return value.lower()
        
        return value
    
    try:
        stock_data.sort(key=lambda x: get_sort_value(x, sort_column), reverse=not sort_ascending)
    except Exception as e:
        # If sorting fails, just continue with unsorted data
        st.warning(f"Note: Could not sort by {AVAILABLE_COLUMNS[sort_column]['name']}")
    
    # ============= APPLY SIMPLE FILTERS =============
    original_count = len(stock_data)
    
    if price_filter != "All Prices" or perf_filter != "All Stocks":
        filtered_stocks = []
        
        for stock in stock_data:
            # Price filter
            if price_filter != "All Prices":
                price = stock.get('current_price')
                if price and isinstance(price, (int, float)):
                    if price_filter == "Under $50" and price >= 50:
                        continue
                    elif price_filter == "$50-$200" and (price < 50 or price > 200):
                        continue
                    elif price_filter == "$200-$500" and (price < 200 or price > 500):
                        continue
                    elif price_filter == "Over $500" and price <= 500:
                        continue
            
            # Performance filter (use first available perf column)
            if perf_filter != "All Stocks" and perf_cols:
                perf_val = None
                # Get value from first perf column in view
                for col in perf_cols:
                    val = stock.get(col)
                    if val:
                        try:
                            if isinstance(val, (int, float)):
                                perf_val = float(val)
                            elif isinstance(val, str):
                                perf_val = float(val.replace('%', '').replace('+', '').replace(',', ''))
                            break
                        except:
                            pass
                
                if perf_val is not None:
                    if perf_filter == "Gainers Only" and perf_val <= 0:
                        continue
                    elif perf_filter == "Losers Only" and perf_val >= 0:
                        continue
                    elif perf_filter == "Up >10%" and perf_val <= 10:
                        continue
                    elif perf_filter == "Down >10%" and perf_val >= -10:
                        continue
            
            # Stock passed all filters
            filtered_stocks.append(stock)
        
        stock_data = filtered_stocks
        if len(stock_data) < original_count:
            st.info(f"🔍 Showing {len(stock_data)} of {original_count} stocks (filtered)")
    
    # ============= BULK DELETE SECTION =============
    # Initialize bulk delete state
    bulk_delete_key = f"bulk_delete_{watchlist_id}"
    if bulk_delete_key not in st.session_state:
        st.session_state[bulk_delete_key] = set()
    
    # Bulk delete controls (only show if we have stock data)
    if stock_data:
        bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 2, 7])
        
        with bulk_col1:
            select_all = st.checkbox("Select All", key=f"select_all_{watchlist_id}")
            if select_all:
                # Select all stocks
                st.session_state[bulk_delete_key] = set([s.get('symbol', '') for s in stock_data if s.get('symbol')])
            elif not select_all and len(st.session_state[bulk_delete_key]) == len(stock_data):
                # Deselect all if "Select All" was unchecked
                st.session_state[bulk_delete_key] = set()
        
        with bulk_col2:
            selected_count = len(st.session_state[bulk_delete_key])
            if selected_count > 0:
                if st.button(f"🗑️ Delete Selected ({selected_count})", key=f"bulk_delete_btn_{watchlist_id}", type="secondary"):
                    # Delete all selected stocks
                    for symbol in list(st.session_state[bulk_delete_key]):
                        remove_stock_from_watchlist(watchlist_id, symbol)
                    st.session_state[bulk_delete_key] = set()
                    st.success(f"✅ Deleted {selected_count} stocks")
                    st.rerun()
        
        with bulk_col3:
            if selected_count > 0:
                st.caption(f"📌 {selected_count} stock(s) selected")
        
        st.markdown("---")
    
    # Create CSV Export button (in the saved col3 position) - only if we have data
    with export_col:
        if stock_data and any(s.get('tr_status') != None or s.get('price') != None for s in stock_data):
            # Prepare CSV data
            export_data = []
            for stock in stock_data:
                row = {}
                for col_id in columns_to_show:
                    # Get raw value (clean for CSV)
                    value = stock.get(col_id, 'N/A')
                    
                    # Clean HTML formatting for CSV
                    if isinstance(value, str):
                        # Remove HTML tags
                        import re
                        value = re.sub(r'<[^>]+>', '', value)
                        # Remove extra whitespace
                        value = value.strip()
                    
                    row[AVAILABLE_COLUMNS[col_id]['name']] = value
                export_data.append(row)
            
            # Create DataFrame and CSV
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{watchlist['name'].replace(' ', '_')}_{timestamp}.csv"
            
            # Single-click download button
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=filename,
                mime="text/csv",
                key=f"download_csv_{watchlist_id}",
                help=f"Download {len(stock_data)} stocks to CSV"
            )
        else:
            # Show disabled-looking button if no data
            st.button("📥 Export CSV", key=f"export_disabled_{watchlist_id}", disabled=True, help="Click 'Analyze All' first")
    
    # Display stocks
    for idx, stock in enumerate(stock_data):
        data_cols = st.columns(header_cols)
        
        # Checkbox column
        with data_cols[0]:
            symbol = stock.get('symbol', '')
            is_checked = symbol in st.session_state[bulk_delete_key]
            if st.checkbox("", value=is_checked, key=f"check_{watchlist_id}_{idx}_{symbol}", label_visibility="collapsed"):
                st.session_state[bulk_delete_key].add(symbol)
            else:
                st.session_state[bulk_delete_key].discard(symbol)
        
        for col_idx, col_id in enumerate(columns_to_show):
            with data_cols[col_idx + 1]:  # +1 because of checkbox column
                # Special handling for symbol - make it clickable
                if col_id == 'symbol':
                    symbol = stock.get('symbol', 'N/A')
                    # Create a link button to Stocks Analysis page
                    if st.button(f"🔍 {symbol}", key=f"goto_{watchlist_id}_{idx}_{symbol}", use_container_width=True):
                        # Set the symbol in session state and navigate
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
    
    # Summary statistics - ONLY show if TR Status is in the displayed columns
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
    st.markdown("*Create and manage stock watchlists with **22 available fields** and custom views*")
    st.divider()
    
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
        4. **Analyze** - Click "Analyze All" to see all 22 fields
        
        **22 Available Fields:**
        - Basic: Symbol, Price, Change %, Volume
        - TR: TR Status, TR Value, Buy Point, Stop Loss, Risk %
        - Technical: RSI, MACD
        - EMAs: 13, 30, 50, 200
        - 52 Week: High, Low
        - Fundamentals: Beta, P/E, Market Cap
        - Performance: 1M, 3M, YTD
        
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
                with st.popover("⚙️ Settings"):
                    new_name = st.text_input("Rename Watchlist", value=watchlist['name'])
                    
                    # Data source selector
                    current_source = watchlist.get('data_source', 'yahoo')
                    data_source = st.selectbox(
                        "Data Source",
                        ["yahoo", "tiingo"],
                        index=0 if current_source == 'yahoo' else 1,
                        help="Yahoo: Free, Tiingo: More reliable ($50/month)"
                    )
                    
                    if st.button("Save Settings"):
                        rename_watchlist(st.session_state.active_watchlist, new_name)
                        st.session_state.watchlists[st.session_state.active_watchlist]['data_source'] = data_source
                        # Clear cache when data source changes
                        if data_source != current_source:
                            st.session_state.stock_tr_cache = {}
                        st.success("✅ Settings saved!")
                        st.rerun()
            
            st.divider()
            
            show_add_stock_form(st.session_state.active_watchlist)
            show_watchlist_stocks_enhanced(st.session_state.active_watchlist)
        else:
            st.error("Watchlist not found")

if __name__ == "__main__":
    main()
