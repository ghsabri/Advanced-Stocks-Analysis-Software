"""
Investment Ideas Page
=====================
Curated stock lists with performance metrics.

Features:
- 4 curated lists from Supabase
- Lazy loading - only fetches data when Refresh clicked
- Performance columns: Price, Daily, 1W, 3W, 6W, YTD, 1Y
- Quick Chart with TradingView widget (Prev/Next navigation)
- Add All to Watchlist
- Export to CSV
- Clickable symbols in table → Stock Analysis page

Created: December 2025
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import re

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cached_data import get_shared_stock_data

# Import database module for Supabase - use the supabase client directly
try:
    from database import (
        supabase,
        get_all_watchlists,
        create_watchlist,
        add_stock_to_watchlist,
        add_multiple_stocks
    )
    DATABASE_ENABLED = True
    print("✅ Database connection available for Investment Ideas")
except Exception as e:
    DATABASE_ENABLED = False
    supabase = None
    print(f"⚠️ Database not available: {e}")

# Import batch fetcher
try:
    from batch_fetcher import fetch_watchlist_data_batch
    BATCH_FETCHING_AVAILABLE = True
except ImportError:
    BATCH_FETCHING_AVAILABLE = False

st.set_page_config(
    page_title="Investment Ideas - MJ Software",
    page_icon="💡",
    layout="wide"
)

# ============================================================================
# CSS STYLING
# ============================================================================

st.markdown("""
<style>
    /* Compact buttons for action bar */
    div[data-testid="stMain"] .stButton > button {
        height: 32px !important;
        padding: 4px 16px !important;
        font-size: 13px !important;
    }
    
    /* List meta styling */
    .list-meta {
        font-size: 12px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'ideas_cache' not in st.session_state:
    st.session_state['ideas_cache'] = {}

if 'ideas_last_fetch' not in st.session_state:
    st.session_state['ideas_last_fetch'] = {}

# Track which lists have been loaded
if 'ideas_loaded_lists' not in st.session_state:
    st.session_state['ideas_loaded_lists'] = set()

# Quick Chart state
if 'ideas_chart_stocks' not in st.session_state:
    st.session_state['ideas_chart_stocks'] = []

if 'ideas_chart_index' not in st.session_state:
    st.session_state['ideas_chart_index'] = 0

if 'show_ideas_chart' not in st.session_state:
    st.session_state['show_ideas_chart'] = False

# Add to Watchlist state
if 'show_add_to_watchlist' not in st.session_state:
    st.session_state['show_add_to_watchlist'] = False

if 'add_to_watchlist_symbols' not in st.session_state:
    st.session_state['add_to_watchlist_symbols'] = []

if 'add_to_watchlist_title' not in st.session_state:
    st.session_state['add_to_watchlist_title'] = ""


# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_investment_lists():
    """Fetch all investment idea lists from Supabase"""
    if not DATABASE_ENABLED or supabase is None:
        print("⚠️ Database not enabled, using fallback lists")
        return get_fallback_lists()
    
    try:
        response = supabase.table('investment_ideas') \
            .select('*') \
            .eq('is_active', True) \
            .order('display_order') \
            .execute()
        
        if response.data:
            print(f"✅ Loaded {len(response.data)} investment lists from Supabase")
            return response.data
        else:
            print("⚠️ No data returned from Supabase, using fallback")
            return get_fallback_lists()
    except Exception as e:
        print(f"❌ Error fetching investment lists: {e}")
        return get_fallback_lists()


def get_fallback_lists():
    """Fallback lists if database unavailable"""
    return [
        {
            'list_key': 'weekly_picks',
            'title': '🔥 Our Weekly Picks',
            'description': 'Stocks selected using our proprietary TR Indicator system. Look for Buy or Strong Buy TR signal while around a buy point for potential entry. List updated every Sunday.',
            'symbols': ['NVDA', 'AAPL', 'GOOGL', 'MSFT', 'AMZN'],
            'update_frequency': 'Weekly',
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'list_key': 'ai_picks',
            'title': '🤖 AI Monthly Picks',
            'description': 'Stocks identified by our machine learning model. The AI analyzes chart patterns, volume trends, and technical indicators to find high-probability setups. Refreshed monthly.',
            'symbols': ['SMCI', 'AVGO', 'AMD', 'PLTR', 'CRWD'],
            'update_frequency': 'Monthly',
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'list_key': 'growth_tech',
            'title': '🚀 Growth: Quantum, AI & Semiconductors',
            'description': 'High-growth technology stocks',
            'symbols': ['IONQ', 'RGTI', 'QBTS', 'AMD', 'AVGO', 'SMCI', 'NVDA', 'MRVL'],
            'update_frequency': 'Quarterly',
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'list_key': 'value_stocks',
            'title': '💎 Value Stocks',
            'description': 'Established companies with dividends',
            'symbols': ['BRK.B', 'JPM', 'JNJ', 'PG', 'KO', 'XOM', 'CVX'],
            'update_frequency': 'Quarterly',
            'updated_at': datetime.now().strftime('%Y-%m-%d')
        }
    ]


# ============================================================================
# PERFORMANCE CALCULATION FUNCTIONS
# ============================================================================

def calculate_performance(df, periods):
    """Calculate performance over given periods"""
    if df is None or df.empty or len(df) < periods:
        return None
    try:
        start_price = df['Close'].iloc[-periods]
        end_price = df['Close'].iloc[-1]
        return ((end_price - start_price) / start_price) * 100
    except:
        return None


def calculate_ytd_performance(df):
    """Calculate year-to-date performance"""
    if df is None or df.empty:
        return None
    try:
        # Ensure we have a Date column or DatetimeIndex
        if 'Date' in df.columns:
            df_temp = df.copy()
            df_temp['Date'] = pd.to_datetime(df_temp['Date'])
            df_temp = df_temp.set_index('Date')
        else:
            df_temp = df.copy()
        
        current_year = datetime.now().year
        ytd_data = df_temp[df_temp.index.year == current_year]
        
        if ytd_data.empty or len(ytd_data) < 2:
            return None
            
        start_price = ytd_data['Close'].iloc[0]
        end_price = ytd_data['Close'].iloc[-1]
        return ((end_price - start_price) / start_price) * 100
    except Exception as e:
        print(f"YTD calc error: {e}")
        return None


def fetch_stock_performance(symbol, api_source='yahoo'):
    """Fetch stock data and calculate all performance metrics"""
    cache_key = f"{symbol}_perf"
    
    # Check cache (valid for 30 minutes)
    if cache_key in st.session_state['ideas_cache']:
        cached_time = st.session_state['ideas_last_fetch'].get(cache_key, 0)
        if time.time() - cached_time < 1800:  # 30 minutes
            return st.session_state['ideas_cache'][cache_key]
    
    try:
        # Fetch 2 years of data for 1Y performance
        df = get_shared_stock_data(symbol, duration_days=500, timeframe='daily', api_source=api_source)
        
        if df is None or df.empty:
            return None
        
        # Ensure proper structure
        if 'Date' not in df.columns and df.index.name == 'Date':
            df = df.reset_index()
        
        latest = df.iloc[-1]
        
        # Calculate daily change
        if len(df) >= 2:
            prev_close = df['Close'].iloc[-2]
            curr_close = df['Close'].iloc[-1]
            daily_change = ((curr_close - prev_close) / prev_close) * 100
        else:
            daily_change = 0
        
        result = {
            'symbol': symbol,
            'price': latest.get('Close', 0),
            'daily_change': daily_change,
            'perf_1w': calculate_performance(df, 5),       # 1 week = 5 trading days
            'perf_1m': calculate_performance(df, 21),      # 1 month = 21 trading days
            'perf_3m': calculate_performance(df, 63),      # 3 months = 63 trading days
            'perf_6m': calculate_performance(df, 126),     # 6 months = 126 trading days
            'perf_ytd': calculate_ytd_performance(df),
            'perf_1y': calculate_performance(df, 252),    # 1 year = 252 trading days
        }
        
        # Cache result
        st.session_state['ideas_cache'][cache_key] = result
        st.session_state['ideas_last_fetch'][cache_key] = time.time()
        
        return result
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def fetch_list_data_batch(symbols, list_key, force_refresh=False, api_source='yahoo'):
    """
    Fetch performance data for all symbols in a list using TRUE BATCH approach.
    Uses batch_fetcher for single API call instead of one-by-one fetching.
    """
    results = []
    symbols_to_fetch = []
    
    # Check which symbols need fetching
    for symbol in symbols:
        cache_key = f"{symbol}_perf"
        cached_time = st.session_state['ideas_last_fetch'].get(cache_key, 0)
        
        if force_refresh or cache_key not in st.session_state['ideas_cache'] or (time.time() - cached_time > 1800):
            symbols_to_fetch.append(symbol)
    
    # Fetch ALL symbols that need data in ONE batch call
    if symbols_to_fetch:
        status_text = st.empty()
        status_text.info(f"🚀 Batch loading {len(symbols_to_fetch)} stocks...")
        
        try:
            # Use batch_fetcher for single API call
            if BATCH_FETCHING_AVAILABLE:
                from batch_fetcher import batch_fetch_stocks
                
                # Fetch all stocks in ONE call (500 days for 1Y performance)
                batch_data = batch_fetch_stocks(
                    symbols=symbols_to_fetch,
                    api_source=api_source,
                    duration_days=500,
                    timeframe='daily'
                )
                
                # Process batch results and cache them
                for symbol in symbols_to_fetch:
                    df = batch_data.get(symbol)
                    
                    if df is not None and not df.empty:
                        # Reset index if needed
                        if df.index.name == 'Date' or 'Date' not in df.columns:
                            df = df.reset_index()
                        
                        # Ensure Date column exists
                        if 'Date' not in df.columns and 'index' in df.columns:
                            df = df.rename(columns={'index': 'Date'})
                        
                        latest = df.iloc[-1]
                        
                        # Calculate daily change
                        if len(df) >= 2:
                            prev_close = df['Close'].iloc[-2]
                            curr_close = df['Close'].iloc[-1]
                            daily_change = ((curr_close - prev_close) / prev_close) * 100
                        else:
                            daily_change = 0
                        
                        # Build result
                        result = {
                            'symbol': symbol,
                            'price': float(latest['Close']) if 'Close' in latest else None,
                            'daily_change': daily_change,
                            'perf_1w': calculate_performance(df, 5),
                            'perf_1m': calculate_performance(df, 21),
                            'perf_3m': calculate_performance(df, 63),
                            'perf_6m': calculate_performance(df, 126),
                            'perf_ytd': calculate_ytd_performance(df),
                            'perf_1y': calculate_performance(df, 252),
                        }
                        
                        # Cache result
                        cache_key = f"{symbol}_perf"
                        st.session_state['ideas_cache'][cache_key] = result
                        st.session_state['ideas_last_fetch'][cache_key] = time.time()
                    else:
                        print(f"⚠️ No data for {symbol}")
                
                status_text.success(f"✅ Loaded {len(symbols_to_fetch)} stocks in batch!")
                time.sleep(0.5)
            else:
                # Fallback to one-by-one if batch not available
                status_text.warning("Batch fetching not available, loading one by one...")
                for idx, symbol in enumerate(symbols_to_fetch):
                    status_text.text(f"Loading {symbol}... ({idx + 1}/{len(symbols_to_fetch)})")
                    fetch_stock_performance(symbol, api_source)
                    
        except Exception as e:
            print(f"❌ Batch fetch error: {e}")
            status_text.error(f"Batch fetch failed: {e}")
            # Fallback to individual fetching
            for symbol in symbols_to_fetch:
                fetch_stock_performance(symbol, api_source)
        
        status_text.empty()
    
    # Build results from cache
    for symbol in symbols:
        cache_key = f"{symbol}_perf"
        if cache_key in st.session_state['ideas_cache']:
            results.append(st.session_state['ideas_cache'][cache_key])
        else:
            # Placeholder for failed fetches
            results.append({
                'symbol': symbol,
                'price': None,
                'daily_change': None,
                'perf_1w': None,
                'perf_1m': None,
                'perf_3m': None,
                'perf_6m': None,
                'perf_ytd': None,
                'perf_1y': None,
            })
    
    # Mark list as loaded
    st.session_state['ideas_loaded_lists'].add(list_key)
    
    return results


def get_cached_list_data(symbols):
    """Get data from cache only - no fetching"""
    results = []
    all_cached = True
    
    for symbol in symbols:
        cache_key = f"{symbol}_perf"
        if cache_key in st.session_state['ideas_cache']:
            results.append(st.session_state['ideas_cache'][cache_key])
        else:
            all_cached = False
            results.append({
                'symbol': symbol,
                'price': None,
                'daily_change': None,
                'perf_1w': None,
                'perf_1m': None,
                'perf_3m': None,
                'perf_6m': None,
                'perf_ytd': None,
                'perf_1y': None,
            })
    
    return results, all_cached


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

# Column definitions for sorting
IDEAS_COLUMNS = {
    'symbol': {'name': 'Symbol', 'type': 'text'},
    'price': {'name': 'Price', 'type': 'number'},
    'daily_change': {'name': 'Daily', 'type': 'number'},
    'perf_1w': {'name': '1 Week', 'type': 'number'},
    'perf_1m': {'name': '1 Month', 'type': 'number'},
    'perf_3m': {'name': '3 Months', 'type': 'number'},
    'perf_6m': {'name': '6 Months', 'type': 'number'},
    'perf_ytd': {'name': 'YTD', 'type': 'number'},
    'perf_1y': {'name': '1 Year', 'type': 'number'},
}

def display_stock_table(stocks_data, list_key, data_loaded=False):
    """Display stock table with clickable column headers for sorting"""
    
    if not stocks_data:
        st.info("No stocks in this list")
        return
    
    # Sort state keys for this list
    sort_key = f"ideas_sort_{list_key}"
    sort_dir_key = f"ideas_sort_dir_{list_key}"
    
    # Initialize sort state
    if sort_key not in st.session_state:
        st.session_state[sort_key] = None
    if sort_dir_key not in st.session_state:
        st.session_state[sort_dir_key] = 'desc'
    
    # Toggle sort function
    def toggle_sort(column_id):
        if st.session_state[sort_key] == column_id:
            # Toggle direction
            st.session_state[sort_dir_key] = 'asc' if st.session_state[sort_dir_key] == 'desc' else 'desc'
        else:
            # New column, default descending
            st.session_state[sort_key] = column_id
            st.session_state[sort_dir_key] = 'desc'
    
    # Apply sorting if active
    if st.session_state[sort_key] and stocks_data:
        sort_col = st.session_state[sort_key]
        sort_reverse = st.session_state[sort_dir_key] == 'desc'
        
        def get_sort_value(stock):
            val = stock.get(sort_col, None)
            if val is None:
                return float('-inf') if sort_reverse else float('inf')
            if sort_col == 'symbol':
                return val.lower()
            return float(val) if isinstance(val, (int, float)) else float('-inf')
        
        stocks_data = sorted(stocks_data, key=get_sort_value, reverse=sort_reverse)
    
    # Show sort status with clear option
    if st.session_state[sort_key]:
        col_name = IDEAS_COLUMNS.get(st.session_state[sort_key], {}).get('name', st.session_state[sort_key])
        sort_direction = "↓ Desc" if st.session_state[sort_dir_key] == 'desc' else "↑ Asc"
        
        sort_info_col, clear_sort_col = st.columns([4, 1])
        with sort_info_col:
            st.caption(f"📊 Sorted by: **{col_name}** ({sort_direction})")
        with clear_sort_col:
            if st.button("✖ Clear", key=f"clear_sort_{list_key}", use_container_width=True):
                st.session_state[sort_key] = None
                st.rerun()
    
    # Format performance value
    def fmt_perf(val):
        if val is None:
            return "-"
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}%"
    
    # Color for performance
    def get_perf_color(val):
        if val is None:
            return "gray"
        return "green" if val >= 0 else "red"
    
    # Table header with clickable sort buttons
    header_cols = st.columns([1.2, 1.2, 1, 1, 1, 1, 1, 1, 1])
    col_ids = ['symbol', 'price', 'daily_change', 'perf_1w', 'perf_1m', 'perf_3m', 'perf_6m', 'perf_ytd', 'perf_1y']
    
    for col, col_id in zip(header_cols, col_ids):
        col_info = IDEAS_COLUMNS[col_id]
        col_name = col_info['name']
        
        # Add sort icon if this column is sorted
        if st.session_state[sort_key] == col_id:
            sort_icon = "🔽" if st.session_state[sort_dir_key] == 'desc' else "🔼"
            btn_label = f"{col_name} {sort_icon}"
        else:
            btn_label = col_name
        
        with col:
            if st.button(btn_label, key=f"sort_{list_key}_{col_id}", 
                        help=f"Sort by {col_name}", use_container_width=True):
                toggle_sort(col_id)
                st.rerun()
    
    st.divider()
    
    # Table rows with clickable symbols
    for stock in stocks_data:
        symbol = stock['symbol']
        row_cols = st.columns([1.2, 1.2, 1, 1, 1, 1, 1, 1, 1])
        
        # Symbol as clickable link (bold, compact)
        with row_cols[0]:
            if st.button(symbol, key=f"sym_{list_key}_{symbol}", type="tertiary"):
                # Set session state same way as Watchlists page
                st.session_state.selected_symbol = symbol
                st.switch_page("pages/1_Stocks_Analysis.py")
        
        # Price
        with row_cols[1]:
            price_val = stock.get('price')
            price = f"${price_val:,.2f}" if price_val else "-"
            st.markdown(price)
        
        # Performance columns
        perf_keys = ['daily_change', 'perf_1w', 'perf_1m', 'perf_3m', 'perf_6m', 'perf_ytd', 'perf_1y']
        for col, key in zip(row_cols[2:], perf_keys):
            val = stock.get(key)
            color = get_perf_color(val)
            formatted = fmt_perf(val)
            col.markdown(f"<span style='color:{color}'>{formatted}</span>", unsafe_allow_html=True)


def generate_csv_data(stocks_data, list_title):
    """Generate CSV string from stock data"""
    rows = []
    for stock in stocks_data:
        def fmt_val(val):
            if val is None:
                return ""
            if isinstance(val, float):
                return f"{val:.2f}"
            return str(val)
        
        rows.append({
            'Symbol': stock['symbol'],
            'Price': fmt_val(stock.get('price')),
            'Daily %': fmt_val(stock.get('daily_change')),
            '1 Week %': fmt_val(stock.get('perf_1w')),
            '1 Month %': fmt_val(stock.get('perf_1m')),
            '3 Months %': fmt_val(stock.get('perf_3m')),
            '6 Months %': fmt_val(stock.get('perf_6m')),
            'YTD %': fmt_val(stock.get('perf_ytd')),
            '1 Year %': fmt_val(stock.get('perf_1y')),
        })
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


# ============================================================================
# ADD TO WATCHLIST DIALOG
# ============================================================================

@st.dialog("➕ Add to Watchlist", width="small")
def show_add_to_watchlist_dialog():
    """Dialog to add all stocks to a watchlist"""
    
    symbols = st.session_state.get('add_to_watchlist_symbols', [])
    list_title = st.session_state.get('add_to_watchlist_title', 'Selected List')
    
    if not symbols:
        st.warning("No stocks to add")
        return
    
    st.markdown(f"**Adding {len(symbols)} stocks from:**")
    st.caption(list_title)
    
    st.divider()
    
    # Get user's existing watchlists
    if DATABASE_ENABLED:
        watchlists = get_all_watchlists()
    else:
        watchlists = []
    
    # Option selection
    add_option = st.radio(
        "Choose an option:",
        ["Add to existing watchlist", "Create new watchlist"],
        key="add_watchlist_option"
    )
    
    if add_option == "Add to existing watchlist":
        if watchlists:
            watchlist_options = {f"{wl['name']} ({wl['id']})": wl['id'] for wl in watchlists}
            selected = st.selectbox(
                "Select watchlist:",
                options=list(watchlist_options.keys()),
                key="select_existing_watchlist"
            )
            selected_id = watchlist_options[selected] if selected else None
        else:
            st.warning("No watchlists found. Create one first.")
            selected_id = None
    else:
        new_name = st.text_input(
            "New watchlist name:",
            placeholder="e.g., AI Picks Copy",
            key="new_watchlist_name_input"
        )
        selected_id = None
    
    st.divider()
    
    # Show symbols to be added
    with st.expander(f"📋 Stocks to add ({len(symbols)})", expanded=False):
        st.write(", ".join(symbols))
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state['show_add_to_watchlist'] = False
            st.rerun()
    
    with col2:
        if st.button("✅ Add Stocks", type="primary", use_container_width=True):
            if add_option == "Add to existing watchlist":
                if selected_id:
                    # Add to existing watchlist
                    result = add_multiple_stocks(selected_id, symbols)
                    added = len(result.get('added', []))
                    failed = len(result.get('failed', []))
                    
                    if added > 0:
                        st.success(f"✅ Added {added} stocks to watchlist!")
                    if failed > 0:
                        st.warning(f"⚠️ {failed} stocks were already in the watchlist")
                    
                    time.sleep(1.5)
                    st.session_state['show_add_to_watchlist'] = False
                    st.rerun()
                else:
                    st.error("Please select a watchlist")
            else:
                # Create new watchlist
                if new_name and new_name.strip():
                    new_watchlist = create_watchlist(new_name.strip())
                    if new_watchlist:
                        new_id = new_watchlist['id']
                        result = add_multiple_stocks(new_id, symbols)
                        added = len(result.get('added', []))
                        
                        st.success(f"✅ Created '{new_name}' with {added} stocks!")
                        time.sleep(1.5)
                        st.session_state['show_add_to_watchlist'] = False
                        st.rerun()
                    else:
                        st.error("Failed to create watchlist")
                else:
                    st.error("Please enter a watchlist name")


# ============================================================================
# QUICK CHART DIALOG - Same style as Watchlists page with Prev/Next
# ============================================================================

@st.dialog("📈 Quick Chart", width="large")
def show_quick_chart_dialog():
    """Display quick chart popup with dropdown AND Prev/Next navigation"""
    
    # Get stocks
    if 'ideas_chart_stocks' not in st.session_state or not st.session_state['ideas_chart_stocks']:
        st.warning("No stocks available")
        if st.button("Close"):
            st.session_state['show_ideas_chart'] = False
            st.rerun()
        return
    
    stocks = st.session_state['ideas_chart_stocks']
    
    # Initialize current index
    if 'ideas_chart_index' not in st.session_state:
        st.session_state['ideas_chart_index'] = 0
    
    # Ensure index is within bounds
    current_idx = st.session_state['ideas_chart_index']
    if current_idx >= len(stocks):
        current_idx = 0
        st.session_state['ideas_chart_index'] = 0
    if current_idx < 0:
        current_idx = 0
        st.session_state['ideas_chart_index'] = 0
    
    current_symbol = stocks[current_idx]
    
    # Initialize dropdown value in session state if needed
    if 'ideas_chart_dropdown' not in st.session_state:
        st.session_state['ideas_chart_dropdown'] = current_symbol
    
    # Sync dropdown with index (for when Prev/Next changes index)
    if st.session_state['ideas_chart_dropdown'] != current_symbol:
        st.session_state['ideas_chart_dropdown'] = current_symbol
    
    # Callback functions for Prev/Next
    def go_prev():
        if st.session_state['ideas_chart_index'] > 0:
            st.session_state['ideas_chart_index'] -= 1
            # Update dropdown to match
            st.session_state['ideas_chart_dropdown'] = stocks[st.session_state['ideas_chart_index']]
    
    def go_next():
        if st.session_state['ideas_chart_index'] < len(stocks) - 1:
            st.session_state['ideas_chart_index'] += 1
            # Update dropdown to match
            st.session_state['ideas_chart_dropdown'] = stocks[st.session_state['ideas_chart_index']]
    
    def on_dropdown_change():
        selected = st.session_state['ideas_chart_dropdown']
        st.session_state['ideas_chart_index'] = stocks.index(selected)
    
    # Navigation row: Prev | Dropdown | Next
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    
    with nav_col1:
        st.button("◀ Prev", key="ideas_chart_prev", use_container_width=True, 
                  disabled=(current_idx == 0), on_click=go_prev)
    
    with nav_col2:
        # Dropdown to select any stock - uses session state key directly
        st.selectbox(
            "Select Stock",
            options=stocks,
            key="ideas_chart_dropdown",
            label_visibility="collapsed",
            on_change=on_dropdown_change
        )
    
    with nav_col3:
        st.button("Next ▶", key="ideas_chart_next", use_container_width=True, 
                  disabled=(current_idx >= len(stocks) - 1), on_click=go_next)
    
    # Get current symbol from session state
    current_symbol = st.session_state['ideas_chart_dropdown']
    current_idx = stocks.index(current_symbol)
    
    # Stock counter
    st.caption(f"Stock {current_idx + 1} of {len(stocks)}")
    
    # Get cached price info
    cache_key = f"{current_symbol}_perf"
    stock_info = st.session_state['ideas_cache'].get(cache_key, {})
    
    price = stock_info.get('price')
    daily_change = stock_info.get('daily_change')
    
    # Display price info
    info_parts = []
    if price:
        info_parts.append(f"**Price:** ${price:,.2f}")
    if daily_change is not None:
        color = "🟢" if daily_change >= 0 else "🔴"
        sign = "+" if daily_change >= 0 else ""
        info_parts.append(f"**Daily:** {color} {sign}{daily_change:.2f}%")
    
    if info_parts:
        st.markdown(" | ".join(info_parts))
    
    st.divider()
    
    # TradingView Chart with EMA 20 and EMA 50
    tradingview_html = f'''
    <div class="tradingview-widget-container" style="height:450px;width:100%;">
      <div id="tradingview_ideas_{current_symbol}" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{current_symbol}",
        "interval": "D",
        "timezone": "America/New_York",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": false,
        "container_id": "tradingview_ideas_{current_symbol}",
        "hide_volume": false,
        "studies": [
          {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": 20}}}},
          {{"id": "MAExp@tv-basicstudies", "inputs": {{"length": 50}}}}
        ]
      }});
      </script>
    </div>
    '''
    
    st.components.v1.html(tradingview_html, height=480)


# ============================================================================
# INVESTMENT LIST DISPLAY
# ============================================================================

def display_investment_list(list_data):
    """Display a single investment list with expander - lazy loading"""
    
    list_key = list_data['list_key']
    title = list_data['title']
    description = list_data.get('description', '')
    symbols = list_data.get('symbols', [])
    update_freq = list_data.get('update_frequency', 'N/A')
    updated_at = list_data.get('updated_at', 'N/A')
    
    # Format updated_at (remove time if present)
    if updated_at and isinstance(updated_at, str):
        updated_at = updated_at.split('T')[0]
    
    # Check if data is loaded for this list
    data_loaded = list_key in st.session_state['ideas_loaded_lists']
    
    with st.expander(f"{title} ({len(symbols)} stocks)", expanded=False):
        # Meta info row
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.caption(f"📝 {description}")
        with col2:
            st.caption(f"🔄 Updates: {update_freq}")
        with col3:
            st.caption(f"📅 Last Update: {updated_at}")
        
        st.divider()
        
        # Get cached data (or placeholders)
        stocks_data, all_cached = get_cached_list_data(symbols)
        
        # Action buttons row
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 1])
        
        with btn_col1:
            if st.button("📊 Load Data", key=f"refresh_{list_key}", use_container_width=True):
                # Reset chart flag to prevent auto-opening
                st.session_state['show_ideas_chart'] = False
                # Fetch data for this list only
                stocks_data = fetch_list_data_batch(symbols, list_key, force_refresh=True)
                st.rerun()
        
        with btn_col2:
            if st.button("📈 Charts", key=f"charts_{list_key}", use_container_width=True):
                st.session_state['ideas_chart_stocks'] = symbols
                st.session_state['ideas_chart_index'] = 0
                st.session_state['show_ideas_chart'] = True
                st.rerun()
        
        with btn_col3:
            # Add to Watchlist button
            if st.button("➕ Add All", key=f"add_all_{list_key}", use_container_width=True,
                        help="Add all stocks to a watchlist"):
                st.session_state['add_to_watchlist_symbols'] = symbols
                st.session_state['add_to_watchlist_title'] = title
                st.session_state['show_add_to_watchlist'] = True
                st.rerun()
        
        with btn_col4:
            # Export CSV button
            if data_loaded and all_cached:
                csv_data = generate_csv_data(stocks_data, title)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name=f"{list_key}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key=f"export_{list_key}",
                    use_container_width=True
                )
            else:
                st.button("📥 Export CSV", key=f"export_disabled_{list_key}", 
                         use_container_width=True, disabled=True,
                         help="Load data first to enable export")
        
        # Show status message if data not loaded
        if not data_loaded:
            st.info("👆 Click **Load Data** to fetch performance metrics for this list")
        
        # Display table with clickable symbols
        display_stock_table(stocks_data, list_key, data_loaded)


# ============================================================================
# MAIN PAGE
# ============================================================================

def main():
    st.title("💡 Investment Ideas")
    st.caption("Curated stock lists updated regularly by our team")
    
    # Show Add to Watchlist dialog if triggered (reset flag AFTER dialog closes)
    if st.session_state.get('show_add_to_watchlist', False):
        show_add_to_watchlist_dialog()
    
    # Show Quick Chart dialog if triggered (DON'T reset flag - let dialog manage it)
    if st.session_state.get('show_ideas_chart', False):
        show_quick_chart_dialog()
    
    st.divider()
    
    # Fetch lists from database
    lists = get_investment_lists()
    
    if not lists:
        st.warning("No investment lists available")
        return
    
    # Display summary
    total_stocks = sum(len(l.get('symbols', [])) for l in lists)
    loaded_count = len(st.session_state['ideas_loaded_lists'])
    
    st.info(f"📊 **{len(lists)} Lists** containing **{total_stocks} stocks** total  •  {loaded_count}/{len(lists)} lists loaded")
    
    st.divider()
    
    # Display each list
    for list_data in lists:
        display_investment_list(list_data)
        st.markdown("")  # Spacing between lists


if __name__ == "__main__":
    main()
