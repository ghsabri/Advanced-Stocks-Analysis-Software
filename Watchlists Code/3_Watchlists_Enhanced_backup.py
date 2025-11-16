"""
Watchlists Page V2 - Enhanced with Customizable Column Views
COMPLETE FIXED VERSION - November 11, 2025

Includes:
✅ Multiple preset views (5 options)
✅ Bulk stock addition (comma-separated)
✅ Fixed TR Status and TR Value display
✅ Fixed EMA calculations
✅ Progress indicators for bulk operations
✅ Smart caching system
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

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
    }
    
    .watchlist-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #1f77b4;
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
# COLUMN CONFIGURATION
# ============================================================================

AVAILABLE_COLUMNS = {
    'symbol': {'name': 'Symbol', 'width': 1.5, 'always_show': True},
    'current_price': {'name': 'Price', 'width': 1.5, 'always_show': False},
    'price_change_pct': {'name': 'Change %', 'width': 1.5, 'always_show': False},
    'volume': {'name': 'Volume', 'width': 1.5, 'always_show': False},
    'tr_status': {'name': 'TR Status', 'width': 2, 'always_show': False},
    'tr_value': {'name': 'TR Value', 'width': 1.5, 'always_show': False},
    'rsi': {'name': 'RSI', 'width': 1, 'always_show': False},
    'buy_point': {'name': 'Buy Point', 'width': 1.5, 'always_show': False},
    'stop_loss': {'name': 'Stop Loss', 'width': 1.5, 'always_show': False},
    'risk_pct': {'name': 'Risk %', 'width': 1.5, 'always_show': False},
    'ema_13': {'name': 'EMA 13', 'width': 1.5, 'always_show': False},
    'ema_30': {'name': 'EMA 30', 'width': 1.5, 'always_show': False},
}

# Preset column views
COLUMN_PRESETS = {
    'Compact': ['symbol', 'current_price', 'price_change_pct', 'tr_status'],
    'Standard': ['symbol', 'current_price', 'price_change_pct', 'volume', 'rsi', 'tr_status'],
    'Detailed': ['symbol', 'current_price', 'price_change_pct', 'tr_status', 'tr_value', 'buy_point', 'stop_loss', 'risk_pct'],
    'Trading': ['symbol', 'current_price', 'price_change_pct', 'tr_status', 'buy_point', 'stop_loss', 'ema_13', 'ema_30'],
    'Technical': ['symbol', 'current_price', 'volume', 'rsi', 'tr_status', 'tr_value', 'ema_13', 'ema_30'],
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
    
    # Column view preference per watchlist
    if 'watchlist_view_prefs' not in st.session_state:
        st.session_state.watchlist_view_prefs = {}

# ============================================================================
# WATCHLIST MANAGEMENT FUNCTIONS
# ============================================================================

def create_watchlist(name):
    """Create a new watchlist"""
    watchlist_id = st.session_state.next_watchlist_id
    st.session_state.watchlists[watchlist_id] = {
        'name': name,
        'created_at': datetime.now(),
        'stocks': []
    }
    st.session_state.next_watchlist_id += 1
    st.session_state.active_watchlist = watchlist_id
    # Set default view for new watchlist
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
    stock_count = len(watchlist['stocks'])
    
    return {
        'name': watchlist['name'],
        'stock_count': stock_count,
        'created_at': watchlist['created_at']
    }

# ============================================================================
# ENHANCED TR ANALYSIS WITH ALL FIELDS - FIXED VERSION
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

def analyze_stock_enhanced(symbol):
    """
    Enhanced TR analysis with all available fields - FIXED VERSION
    
    Fixes:
    - Tries multiple column name variations for TR, EMAs, Buy Point, Stop Loss
    - Calculates EMAs if not in dataframe
    - Calculates TR value from EMAs if TR column doesn't exist
    - Better error handling
    """
    # Check cache first
    if symbol in st.session_state.stock_tr_cache:
        cached_time = st.session_state.stock_tr_cache[symbol].get('timestamp', datetime.min)
        # Cache valid for 5 minutes
        if (datetime.now() - cached_time).seconds < 300:
            return st.session_state.stock_tr_cache[symbol]
    
    try:
        # Get stock data with TR analysis
        df = get_shared_stock_data(
            ticker=symbol,
            duration_days=365,
            timeframe='daily',
            api_source='yahoo',
            include_tr=True  # CRITICAL: Must be True to get TR data
        )
        
        if df is None or df.empty:
            return None
        
        # Get latest data
        latest = df.iloc[-1]
        
        # ============= FIX 1: GET TR VALUE - Try multiple column names =============
        tr_value = None
        possible_tr_names = ['TR', 'TR Indicator', 'TR_Value', 'tr', 'TR_Indicator', 'TR Value']
        
        for col_name in possible_tr_names:
            if col_name in df.columns:
                tr_value = latest.get(col_name, None)
                if tr_value is not None and not pd.isna(tr_value):
                    break
        
        # If TR not found, calculate from EMAs
        if tr_value is None or pd.isna(tr_value):
            close = latest['Close']
            
            # Get or calculate EMAs
            ema_13 = None
            ema_30 = None
            
            # Try to get EMA 13
            ema13_names = ['EMA_13', 'EMA13', 'ema_13', 'EMA 13']
            for col_name in ema13_names:
                if col_name in df.columns:
                    ema_13 = latest.get(col_name, None)
                    if ema_13 is not None and not pd.isna(ema_13):
                        break
            
            if ema_13 is None or pd.isna(ema_13):
                if len(df) >= 13:
                    ema_13 = df['Close'].ewm(span=13, adjust=False).mean().iloc[-1]
            
            # Try to get EMA 30
            ema30_names = ['EMA_30', 'EMA30', 'ema_30', 'EMA 30']
            for col_name in ema30_names:
                if col_name in df.columns:
                    ema_30 = latest.get(col_name, None)
                    if ema_30 is not None and not pd.isna(ema_30):
                        break
            
            if ema_30 is None or pd.isna(ema_30):
                if len(df) >= 30:
                    ema_30 = df['Close'].ewm(span=30, adjust=False).mean().iloc[-1]
            
            # Calculate TR from price vs EMAs
            if ema_13 and ema_30 and not pd.isna(ema_13) and not pd.isna(ema_30):
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
        
        # ============= FIX 2: DETERMINE TR STATUS =============
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
        
        # ============= GET OTHER FIELDS =============
        
        # Calculate price change
        if len(df) > 1:
            prev_close = df.iloc[-2]['Close']
            price_change = latest['Close'] - prev_close
            price_change_pct = (price_change / prev_close) * 100
        else:
            price_change = 0
            price_change_pct = 0
        
        # Calculate RSI
        rsi = calculate_rsi(df)
        
        # Get EMAs (recalculate if needed for display)
        ema_13 = None
        ema_30 = None
        
        ema13_names = ['EMA_13', 'EMA13', 'ema_13', 'EMA 13']
        ema30_names = ['EMA_30', 'EMA30', 'ema_30', 'EMA 30']
        
        for col_name in ema13_names:
            if col_name in df.columns:
                ema_13 = latest.get(col_name, None)
                if ema_13 is not None and not pd.isna(ema_13):
                    break
        
        if ema_13 is None or pd.isna(ema_13):
            if len(df) >= 13:
                ema_13 = df['Close'].ewm(span=13, adjust=False).mean().iloc[-1]
        
        for col_name in ema30_names:
            if col_name in df.columns:
                ema_30 = latest.get(col_name, None)
                if ema_30 is not None and not pd.isna(ema_30):
                    break
        
        if ema_30 is None or pd.isna(ema_30):
            if len(df) >= 30:
                ema_30 = df['Close'].ewm(span=30, adjust=False).mean().iloc[-1]
        
        # Get buy point and stop loss
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
        
        # Calculate risk percentage
        risk_pct = None
        if buy_point and stop_loss and buy_point > 0:
            risk_pct = ((buy_point - stop_loss) / buy_point) * 100
        
        # ============= BUILD RESULT =============
        result = {
            'symbol': symbol,
            'current_price': latest['Close'],
            'tr_status': tr_status,
            'tr_value': tr_value if tr_value is not None else None,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': latest.get('Volume', None),
            'rsi': rsi,
            'buy_point': buy_point,
            'stop_loss': stop_loss,
            'risk_pct': risk_pct,
            'ema_13': ema_13,
            'ema_30': ema_30,
            'timestamp': datetime.now()
        }
        
        # Cache result
        st.session_state.stock_tr_cache[symbol] = result
        
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
    """
    Show form to add stocks to current watchlist
    FIXED: Now supports bulk addition with comma-separated symbols
    """
    st.subheader("➕ Add Stock(s) to Watchlist")
    
    # Instructions for bulk addition
    st.caption("💡 Tip: Add multiple stocks at once by separating with commas (e.g., AAPL, MSFT, GOOGL)")
    
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
        # Parse comma-separated symbols
        symbols_list = [s.strip().upper() for s in new_symbols.split(',') if s.strip()]
        
        if not symbols_list:
            st.error("❌ Please enter at least one stock symbol")
            return
        
        # Track results
        added = []
        already_exists = []
        invalid = []
        
        # Progress bar for multiple stocks
        if len(symbols_list) > 1:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Process each symbol
        for idx, symbol in enumerate(symbols_list):
            # Update progress
            if len(symbols_list) > 1:
                progress = (idx + 1) / len(symbols_list)
                progress_bar.progress(progress)
                status_text.text(f"Processing {symbol}... ({idx + 1}/{len(symbols_list)})")
            
            # Validate stock symbol
            stock_info = get_stock_info(symbol)
            
            if stock_info:
                # Try to add to watchlist
                success = add_stock_to_watchlist(watchlist_id, symbol)
                if success:
                    added.append(f"{symbol} - {stock_info.get('name', '')}")
                else:
                    already_exists.append(symbol)
            else:
                invalid.append(symbol)
        
        # Clear progress indicators
        if len(symbols_list) > 1:
            progress_bar.empty()
            status_text.empty()
        
        # Show results
        if added:
            st.success(f"✅ Added {len(added)} stock(s):")
            for stock in added:
                st.write(f"  • {stock}")
        
        if already_exists:
            st.warning(f"⚠️ Already in watchlist ({len(already_exists)}):")
            st.write(f"  {', '.join(already_exists)}")
        
        if invalid:
            st.error(f"❌ Invalid symbol(s) ({len(invalid)}):")
            st.write(f"  {', '.join(invalid)}")
        
        # Rerun to update the display
        if added:
            st.rerun()
    
    st.divider()

def format_column_value(stock, col_id):
    """Format a column value for display"""
    value = stock.get(col_id)
    
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    
    if col_id == 'symbol':
        return f"**{value}**"
    elif col_id == 'current_price':
        return f"${value:.2f}"
    elif col_id == 'price_change_pct':
        color = "green" if value >= 0 else "red"
        sign = "+" if value >= 0 else ""
        return f"<span style='color:{color}'>{sign}{value:.2f}%</span>"
    elif col_id == 'volume':
        return f"{value:,.0f}"
    elif col_id == 'tr_status':
        return get_tr_status_badge(value)
    elif col_id == 'tr_value':
        return f"{value:.2f}" if value is not None else "—"
    elif col_id == 'rsi':
        return f"{value:.1f}" if value is not None else "—"
    elif col_id in ['buy_point', 'stop_loss', 'ema_13', 'ema_30']:
        return f"${value:.2f}" if value is not None else "—"
    elif col_id == 'risk_pct':
        return f"{value:.1f}%" if value is not None else "—"
    else:
        return str(value)

def show_watchlist_stocks_enhanced(watchlist_id):
    """Display all stocks with customizable columns"""
    watchlist = st.session_state.watchlists.get(watchlist_id)
    
    if not watchlist:
        st.error("Watchlist not found")
        return
    
    stocks = watchlist['stocks']
    
    if not stocks:
        st.info("📊 This watchlist is empty. Add some stocks to get started!")
        return
    
    st.subheader(f"📊 Stocks in {watchlist['name']} ({len(stocks)})")
    
    # Controls row
    col1, col2, col3, col4 = st.columns([2, 2, 2, 3])
    
    with col1:
        analyze_all = st.button("🔄 Analyze All", key=f"analyze_all_{watchlist_id}")
    
    with col2:
        clear_cache = st.button("🗑️ Clear Cache", key=f"clear_cache_{watchlist_id}")
    
    with col3:
        # View selector
        current_view = st.session_state.watchlist_view_prefs.get(watchlist_id, 'Standard')
        view_type = st.selectbox(
            "View Type",
            list(COLUMN_PRESETS.keys()),
            index=list(COLUMN_PRESETS.keys()).index(current_view),
            key=f"view_selector_{watchlist_id}"
        )
        # Save preference
        st.session_state.watchlist_view_prefs[watchlist_id] = view_type
    
    if clear_cache:
        st.session_state.stock_tr_cache = {}
        st.success("✅ Cache cleared")
        st.rerun()
    
    # Get columns to display based on view type
    columns_to_show = COLUMN_PRESETS[view_type]
    
    # Show column headers
    header_cols = []
    for col_id in columns_to_show:
        header_cols.append(AVAILABLE_COLUMNS[col_id]['width'])
    header_cols.append(1)  # Actions column
    
    header_row = st.columns(header_cols)
    for idx, col_id in enumerate(columns_to_show):
        with header_row[idx]:
            st.markdown(f"**{AVAILABLE_COLUMNS[col_id]['name']}**")
    with header_row[-1]:
        st.markdown("**Actions**")
    
    st.divider()
    
    # Analyze stocks
    stock_data = []
    
    with st.spinner("Analyzing stocks..."):
        for symbol in stocks:
            if analyze_all or symbol in st.session_state.stock_tr_cache:
                analysis = analyze_stock_enhanced(symbol)
                if analysis:
                    stock_data.append(analysis)
            else:
                # Show placeholder
                stock_data.append({'symbol': symbol})
    
    # Display stocks
    for idx, stock in enumerate(stock_data):
        data_cols = st.columns(header_cols)
        
        # Display each column
        for col_idx, col_id in enumerate(columns_to_show):
            with data_cols[col_idx]:
                formatted_value = format_column_value(stock, col_id)
                if col_id in ['price_change_pct', 'tr_status']:
                    st.markdown(formatted_value, unsafe_allow_html=True)
                else:
                    st.write(formatted_value)
        
        # Actions column
        with data_cols[-1]:
            if st.button("❌", key=f"remove_{watchlist_id}_{idx}_{stock['symbol']}"):
                remove_stock_from_watchlist(watchlist_id, stock['symbol'])
                st.rerun()
        
        st.divider()
    
    # Summary statistics
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
        st.info("Click 'Analyze All' to see TR status for all stocks in this watchlist")

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
    st.markdown("*Create and manage stock watchlists with customizable views*")
    st.divider()
    
    show_watchlist_selector()
    show_create_watchlist_form()
    
    if st.session_state.active_watchlist is None:
        st.info("👈 Select a watchlist from the sidebar or create a new one to get started")
        
        st.subheader("🚀 Quick Start Guide")
        st.markdown("""
        **Getting Started with Watchlists:**
        
        1. **Create a Watchlist**: Click "Create New Watchlist" in the sidebar
        2. **Add Stocks**: Enter stock symbols (one or multiple separated by commas)
        3. **Choose View**: Select from Compact, Standard, Detailed, Trading, or Technical views
        4. **Analyze Stocks**: Click "Analyze All" to see metrics for all stocks
        
        **View Types:**
        - 📊 **Compact**: Symbol, Price, Change %, TR Status
        - 📈 **Standard**: + Volume, RSI
        - 📋 **Detailed**: + TR Value, Buy Point, Stop Loss, Risk %
        - 💹 **Trading**: + Buy Point, Stop Loss, EMAs
        - 🔧 **Technical**: Volume, RSI, TR Value, EMAs
        
        **Bulk Addition:**
        - Add multiple stocks at once: `AAPL, MSFT, GOOGL, TSLA`
        - Progress bar shows processing status
        - Results summary shows what succeeded/failed
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
                    if st.button("Save Name"):
                        rename_watchlist(st.session_state.active_watchlist, new_name)
                        st.success("✅ Renamed!")
                        st.rerun()
            
            st.divider()
            
            show_add_stock_form(st.session_state.active_watchlist)
            show_watchlist_stocks_enhanced(st.session_state.active_watchlist)
        else:
            st.error("Watchlist not found")

if __name__ == "__main__":
    main()
