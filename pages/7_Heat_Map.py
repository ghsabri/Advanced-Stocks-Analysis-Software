"""
🗺️ Sector Heat Map
MJ Software LLC - AI-Powered Stock Analysis Platform

Visual representation of S&P 500 or sector stocks, color-coded by performance.
Matches the Excel-based heat map design with:
- S&P 500 or 11 sector ETFs selection
- Time periods: Today, 1 Week, 2 Weeks, 1 Month, 2 Months, 3 Months
- Color bands: 3% (green) → 0% (blue) → -3% (red)
- Single batch download for speed
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import time
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import stock list manager
try:
    from utils.stock_list_manager import (
        get_stocks_by_sector_etf,
        get_sp500_stocks,
        get_stock_list,
        get_all_sector_etfs,
        ETF_SECTOR_MAP
    )
    STOCK_MANAGER_AVAILABLE = True
except ImportError:
    STOCK_MANAGER_AVAILABLE = False
    print("⚠️ stock_list_manager not available, using fallback")

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Heat Map - MJ Software",
    page_icon="🗺️",
    layout="wide"
)

# ============================================================
# CONSTANTS
# ============================================================

# Index/Sector options (matching Excel dropdown)
INDEX_OPTIONS = {
    'S&P 500': 'SPY',
    'XLK': 'XLK',      # Technology
    'XLC': 'XLC',      # Communication Services
    'XLV': 'XLV',      # Health Care
    'XLF': 'XLF',      # Financials
    'XLRE': 'XLRE',    # Real Estate
    'XLB': 'XLB',      # Materials
    'XLP': 'XLP',      # Consumer Staples
    'XLI': 'XLI',      # Industrials
    'XLE': 'XLE',      # Energy
    'XLY': 'XLY',      # Consumer Discretionary
    'XLU': 'XLU',      # Utilities
}

# Sector ETF to full name mapping
SECTOR_NAMES = {
    'XLK': 'Technology',
    'XLC': 'Communication Services',
    'XLV': 'Health Care',
    'XLF': 'Financials',
    'XLRE': 'Real Estate',
    'XLB': 'Materials',
    'XLP': 'Consumer Staples',
    'XLI': 'Industrials',
    'XLE': 'Energy',
    'XLY': 'Consumer Discretionary',
    'XLU': 'Utilities',
    'SPY': 'S&P 500',
}

# Time period options (matching Excel dropdown)
TIME_PERIODS = {
    'Today': '2d',
    '1 Week': '5d',
    '2 Weeks': '15d',
    '1 Month': '1mo',
    '2 Months': '2mo',
    '3 Months': '3mo',
}

# Color scale matching Excel (3% green → 0% blue → -3% red)
# Custom colorscale: red (-3%) → blue (0%) → green (3%)
CUSTOM_COLORSCALE = [
    [0.0, 'rgb(255, 0, 0)'],       # -3% or less: Red
    [0.167, 'rgb(255, 100, 100)'], # -2%: Light Red
    [0.333, 'rgb(255, 180, 180)'], # -1%: Pale Red
    [0.5, 'rgb(100, 100, 255)'],   # 0%: Blue
    [0.667, 'rgb(180, 255, 180)'], # 1%: Pale Green
    [0.833, 'rgb(100, 255, 100)'], # 2%: Light Green
    [1.0, 'rgb(0, 200, 0)'],       # 3% or more: Green
]


# ============================================================
# FALLBACK STOCK LISTS (if stock_list_manager not available)
# ============================================================

FALLBACK_STOCKS = {
    'XLK': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'AMD', 'CSCO', 'ACN', 'ADBE', 
            'IBM', 'INTC', 'QCOM', 'TXN', 'NOW', 'INTU', 'AMAT', 'MU', 'LRCX', 'ADI'],
    'XLV': ['UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'PFE', 'TMO', 'ABT', 'DHR', 'AMGN',
            'BMY', 'MDT', 'ISRG', 'ELV', 'GILD', 'CVS', 'SYK', 'VRTX', 'REGN', 'ZTS'],
    'XLF': ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'SPGI',
            'BLK', 'C', 'SCHW', 'CB', 'MMC', 'PGR', 'USB', 'AON', 'CME', 'ICE'],
    'XLE': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PXD', 'PSX', 'VLO', 'OXY',
            'WMB', 'KMI', 'HES', 'HAL', 'DVN', 'FANG', 'BKR', 'TRGP', 'OKE', 'MRO'],
    'XLY': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'CMG',
            'MAR', 'ORLY', 'AZO', 'DHI', 'GM', 'F', 'ROST', 'YUM', 'HLT', 'DG'],
    'XLC': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'CHTR', 'TMUS',
            'EA', 'ATVI', 'WBD', 'OMC', 'TTWO', 'LYV', 'FOXA', 'MTCH', 'PARA', 'NWS'],
    'XLI': ['RTX', 'HON', 'UNP', 'UPS', 'CAT', 'BA', 'DE', 'LMT', 'GE', 'ADP',
            'MMM', 'ETN', 'ITW', 'EMR', 'FDX', 'NSC', 'WM', 'CSX', 'JCI', 'GD'],
    'XLB': ['LIN', 'SHW', 'APD', 'FCX', 'ECL', 'NEM', 'DD', 'NUE', 'DOW', 'VMC',
            'PPG', 'CTVA', 'MLM', 'ALB', 'IFF', 'CE', 'CF', 'FMC', 'MOS', 'PKG'],
    'XLU': ['NEE', 'SO', 'DUK', 'SRE', 'AEP', 'D', 'EXC', 'XEL', 'PEG', 'ED',
            'WEC', 'ES', 'AWK', 'EIX', 'DTE', 'FE', 'PPL', 'AEE', 'CMS', 'CNP'],
    'XLRE': ['PLD', 'AMT', 'EQIX', 'CCI', 'PSA', 'O', 'WELL', 'SPG', 'DLR', 'AVB',
             'VICI', 'SBAC', 'EQR', 'WY', 'VTR', 'ARE', 'EXR', 'MAA', 'ESS', 'INVH'],
    'XLP': ['PG', 'KO', 'PEP', 'COST', 'WMT', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
            'GIS', 'STZ', 'KHC', 'SYY', 'ADM', 'HSY', 'K', 'MKC', 'CHD', 'CLX'],
}


# ============================================================
# DYNAMIC INDEX OPTIONS BUILDER
# ============================================================

def get_dynamic_index_options() -> dict:
    """
    Build the dropdown options dynamically from CSV data.
    Always starts with S&P 500, then adds sector ETFs found in data.
    """
    # Start with S&P 500
    options = {'S&P 500': 'SPY'}
    
    # Get sectors from CSV
    sector_etfs = get_sector_etfs_from_csv()
    
    # Add each sector ETF
    for etf in sector_etfs:
        options[etf] = etf
    
    return options


# ============================================================
# DATA FUNCTIONS
# ============================================================

def get_stocks_for_selection(selection: str) -> list:
    """Get list of stocks for the selected index/sector"""
    
    if selection == 'S&P 500':
        # For S&P 500, return the 11 sector ETFs (NOT individual stocks)
        return None  # Special case - handled separately
    
    # For sector ETFs - get individual stocks
    if STOCK_MANAGER_AVAILABLE:
        stocks = get_stocks_by_sector_etf(selection)
        if stocks:
            return stocks
    
    # Fallback to predefined list
    return FALLBACK_STOCKS.get(selection, [])


def get_sector_etfs_from_csv() -> list:
    """
    DYNAMICALLY get unique sector ETFs from the CSV/database.
    This automatically adapts if sectors change in the future.
    NO hardcoded filtering - reads whatever is in your data.
    """
    # Fallback list - only used if CSV read completely fails
    FALLBACK_SECTOR_ETFS = ['XLK', 'XLV', 'XLF', 'XLE', 'XLY', 'XLC', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLP']
    
    if STOCK_MANAGER_AVAILABLE:
        try:
            df = get_stock_list()
            if not df.empty:
                # Check for "Sector Name" column (your CSV format)
                sector_col = None
                for col in ['Sector Name', 'sector_etf', 'sector_name', 'SectorETF']:
                    if col in df.columns:
                        sector_col = col
                        break
                
                if sector_col:
                    # Get unique values, remove nulls and empty strings
                    etfs = df[sector_col].dropna().unique().tolist()
                    etfs = [e for e in etfs if e and isinstance(e, str) and e.strip()]
                    
                    if etfs:
                        print(f"✅ Found {len(etfs)} sector ETFs from data: {sorted(etfs)}")
                        return sorted(etfs)
        except Exception as e:
            print(f"⚠️ Error reading sectors from data: {e}")
    
    # Fallback only if CSV read fails completely
    print("⚠️ Using fallback sector ETF list")
    return FALLBACK_SECTOR_ETFS


@st.cache_data(ttl=300, show_spinner=False)
def fetch_sector_etfs_performance(period: str) -> pd.DataFrame:
    """
    Fetch performance data for sector ETFs found in the CSV.
    Dynamically adjusts based on sectors in your data.
    Used when S&P 500 is selected to show sector-level heat map.
    """
    # Get sector ETFs dynamically from CSV
    sector_etfs = get_sector_etfs_from_csv()
    
    if not sector_etfs:
        # Ultimate fallback
        sector_etfs = ['XLK', 'XLV', 'XLF', 'XLE', 'XLY', 'XLC', 'XLI', 'XLB', 'XLU', 'XLRE', 'XLP']
    
    try:
        # Single batch download for all sector ETFs - FAST!
        data = yf.download(
            sector_etfs,
            period=period,
            group_by='ticker',
            auto_adjust=True,
            threads=True,
            progress=False
        )
        
        if data.empty:
            return pd.DataFrame()
        
        results = []
        
        for etf in sector_etfs:
            try:
                if len(sector_etfs) == 1:
                    stock_data = data
                else:
                    if etf in data.columns.get_level_values(0):
                        stock_data = data[etf]
                    else:
                        continue
                
                if 'Close' in stock_data.columns:
                    closes = stock_data['Close'].dropna()
                    if len(closes) >= 2:
                        first_price = closes.iloc[0]
                        last_price = closes.iloc[-1]
                        if first_price > 0:
                            change_pct = ((last_price - first_price) / first_price) * 100
                            
                            # Get sector name for display
                            sector_name = SECTOR_NAMES.get(etf, etf)
                            
                            results.append({
                                'symbol': etf,
                                'name': sector_name,
                                'change_pct': round(change_pct, 2),
                                'last_price': round(last_price, 2),
                            })
            except Exception as e:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        st.error(f"Error fetching sector ETF data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_stock_data_batch(symbols: list, period: str) -> pd.DataFrame:
    """
    Fetch price data for multiple stocks in a SINGLE batch download.
    This is the key to speed - one API call for all stocks.
    
    Args:
        symbols: List of stock symbols
        period: yfinance period string ('2d', '5d', '1mo', etc.)
    
    Returns:
        DataFrame with performance data for each stock
    """
    if not symbols:
        return pd.DataFrame()
    
    try:
        # Single batch download - FAST!
        data = yf.download(
            symbols,
            period=period,
            group_by='ticker',
            auto_adjust=True,
            threads=True,
            progress=False
        )
        
        if data.empty:
            return pd.DataFrame()
        
        results = []
        
        # Handle single stock case
        if len(symbols) == 1:
            symbol = symbols[0]
            if 'Close' in data.columns:
                try:
                    first_price = data['Close'].iloc[0]
                    last_price = data['Close'].iloc[-1]
                    if pd.notna(first_price) and pd.notna(last_price) and first_price > 0:
                        change_pct = ((last_price - first_price) / first_price) * 100
                        results.append({
                            'symbol': symbol,
                            'change_pct': round(change_pct, 2),
                            'last_price': round(last_price, 2),
                        })
                except:
                    pass
        else:
            # Multiple stocks
            for symbol in symbols:
                try:
                    if symbol in data.columns.get_level_values(0):
                        stock_data = data[symbol]
                        if 'Close' in stock_data.columns:
                            closes = stock_data['Close'].dropna()
                            if len(closes) >= 2:
                                first_price = closes.iloc[0]
                                last_price = closes.iloc[-1]
                                if first_price > 0:
                                    change_pct = ((last_price - first_price) / first_price) * 100
                                    results.append({
                                        'symbol': symbol,
                                        'change_pct': round(change_pct, 2),
                                        'last_price': round(last_price, 2),
                                    })
                except Exception as e:
                    continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)  # Short cache for fresher data
def fetch_index_performance(symbol: str, period: str) -> float:
    """
    Fetch performance for index/ETF (SPY or sector ETF).
    For 'Today', compares current price to previous day's close.
    """
    try:
        # Download data for single symbol (no group_by)
        data = yf.download(symbol, period=period, progress=False, auto_adjust=True)
        
        if data.empty:
            return 0.0
        
        # For single symbol download, columns are simple (not MultiIndex)
        # Columns: Open, High, Low, Close, Volume
        if 'Close' not in data.columns:
            return 0.0
        
        closes = data['Close'].dropna()
        
        # Need at least 2 data points to calculate change
        if len(closes) >= 2:
            first_price = float(closes.iloc[0])
            last_price = float(closes.iloc[-1])
            
            if first_price > 0 and last_price > 0:
                change_pct = ((last_price - first_price) / first_price) * 100
                return round(change_pct, 2)
        
        # If only 1 data point, try open vs close for today's change
        if len(closes) >= 1 and 'Open' in data.columns:
            opens = data['Open'].dropna()
            if len(opens) >= 1:
                open_price = float(opens.iloc[-1])
                close_price = float(closes.iloc[-1])
                if open_price > 0:
                    change_pct = ((close_price - open_price) / open_price) * 100
                    return round(change_pct, 2)
        
        return 0.0
        
    except Exception as e:
        print(f"Error fetching performance for {symbol}: {e}")
        return 0.0


def get_market_caps_batch(symbols: list) -> dict:
    """Get market caps for sizing treemap boxes"""
    market_caps = {}
    
    # Use default values for speed (avoid individual API calls)
    # In production, this could be stored in Supabase
    default_cap = 50_000_000_000  # $50B default
    
    for symbol in symbols:
        market_caps[symbol] = default_cap
    
    return market_caps


# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================

def create_treemap(df: pd.DataFrame, title: str, is_sector_view: bool = False) -> go.Figure:
    """
    Create a treemap visualization matching Excel heat map style.
    
    Args:
        df: DataFrame with 'symbol', 'change_pct', 'last_price'
        title: Chart title
        is_sector_view: If True, show sector names with larger text
    
    Returns:
        Plotly Figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Add market cap for sizing (use equal size for now)
    df = df.copy()
    df['market_cap'] = 1  # Equal size boxes
    
    # Clip change_pct to -3% to 3% range for color mapping
    df['color_value'] = df['change_pct'].clip(-3, 3)
    
    # Create treemap - use empty string for root to hide it
    fig = px.treemap(
        df,
        path=['symbol'],  # No root label - just symbols
        values='market_cap',
        color='color_value',
        color_continuous_scale=CUSTOM_COLORSCALE,
        range_color=[-3, 3],
        custom_data=['symbol', 'change_pct', 'last_price'],
    )
    
    # Update text display based on view type
    if is_sector_view:
        # For S&P 500 sector view - show ETF symbol and percentage with larger text
        fig.update_traces(
            texttemplate='<b>%{customdata[0]}</b><br>%{customdata[1]:+.2f}%',
            textposition='middle center',
            textfont=dict(size=18, color='white'),
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                          'Change: %{customdata[1]:+.2f}%<br>' +
                          'Price: $%{customdata[2]:.2f}<extra></extra>',
        )
    else:
        # For individual stock view - smaller text
        fig.update_traces(
            texttemplate='<b>%{customdata[0]}</b><br>%{customdata[1]:+.2f}%',
            textposition='middle center',
            textfont=dict(size=12, color='white'),
            hovertemplate='<b>%{customdata[0]}</b><br>' +
                          'Change: %{customdata[1]:+.2f}%<br>' +
                          'Price: $%{customdata[2]:.2f}<extra></extra>',
        )
    
    fig.update_layout(
        margin=dict(t=60, l=10, r=10, b=10),
        height=700,
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=24, color='#1f77b4', family='Arial Black'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        coloraxis_colorbar=dict(
            title='Change %',
            tickvals=[-3, -2, -1, 0, 1, 2, 3],
            ticktext=['-3%', '-2%', '-1%', '0%', '1%', '2%', '3%'],
            len=0.6,
        ),
    )
    
    return fig


# ============================================================
# MAIN PAGE
# ============================================================

def main():
    # Title
    st.title("🗺️ Sector Heat Map")
    
    # Get current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Get dynamic index options from CSV
    dynamic_options = get_dynamic_index_options()
    
    # Layout: Main area + Sidebar controls
    col_main, col_controls = st.columns([4, 1])
    
    with col_controls:
        st.markdown(f"**{current_date}**")
        st.markdown("---")
        
        # Index/Sector selection dropdown - DYNAMIC from CSV
        selection = st.selectbox(
            "Select Index/Sector",
            options=list(dynamic_options.keys()),
            index=0,  # Default to S&P 500
            help="Choose S&P 500 for all sectors or a specific sector ETF for individual stocks"
        )
        
        # Time period dropdown
        time_period = st.selectbox(
            "Period",
            options=list(TIME_PERIODS.keys()),
            index=0,
            help="Select the time period for performance calculation"
        )
        
        # Update button
        update_clicked = st.button("🔄 Update", type="primary", use_container_width=True)
        
        st.markdown("---")
    
    with col_main:
        # Initialize session state
        if 'heat_map_data' not in st.session_state:
            st.session_state.heat_map_data = None
            st.session_state.heat_map_selection = None
            st.session_state.heat_map_period = None
            st.session_state.index_performance = None
            st.session_state.load_time = None
            st.session_state.is_sector_view = False
        
        # ONLY update when button is clicked - NO auto-load
        if update_clicked:
            # Check if S&P 500 (show sectors) or specific sector (show stocks)
            is_sp500 = (selection == 'S&P 500')
            
            if is_sp500:
                # S&P 500: Show 11 sector ETFs
                with st.spinner("Loading S&P 500 sectors..."):
                    start_time = time.time()
                    
                    # Fetch data for sector ETFs
                    period = TIME_PERIODS[time_period]
                    df = fetch_sector_etfs_performance(period)
                    
                    # Fetch SPY performance
                    index_perf = fetch_index_performance('SPY', period)
                    
                    elapsed = time.time() - start_time
                    
                    # Store in session state
                    st.session_state.heat_map_data = df
                    st.session_state.heat_map_selection = selection
                    st.session_state.heat_map_period = time_period
                    st.session_state.index_performance = index_perf
                    st.session_state.load_time = elapsed
                    st.session_state.is_sector_view = True
            else:
                # Specific sector: Show individual stocks
                stocks = get_stocks_for_selection(selection)
                
                if not stocks:
                    st.warning(f"No stocks found for {selection}. Please check your stock list configuration.")
                    return
                
                with st.spinner(f"Loading {len(stocks)} stocks for {selection}..."):
                    start_time = time.time()
                    
                    # Fetch data in batch
                    period = TIME_PERIODS[time_period]
                    df = fetch_stock_data_batch(stocks, period)
                    
                    # Fetch sector ETF performance (selection is the ETF symbol itself)
                    index_symbol = dynamic_options.get(selection, selection)
                    index_perf = fetch_index_performance(index_symbol, period)
                    
                    elapsed = time.time() - start_time
                    
                    # Store in session state
                    st.session_state.heat_map_data = df
                    st.session_state.heat_map_selection = selection
                    st.session_state.heat_map_period = time_period
                    st.session_state.index_performance = index_perf
                    st.session_state.load_time = elapsed
                    st.session_state.is_sector_view = False
        
        # Display results if we have data
        df = st.session_state.heat_map_data
        
        if df is not None and not df.empty:
            # Check if this is sector view or stock view
            is_sector_view = st.session_state.get('is_sector_view', False)
            
            # Create fancy title - just the name, no "Heat Map for"
            selection_display = st.session_state.heat_map_selection
            if selection_display == 'S&P 500':
                fancy_title = "📊 S&P 500"
            else:
                # Get full sector name
                sector_full_name = SECTOR_NAMES.get(selection_display, selection_display)
                fancy_title = f"📊 {sector_full_name} ({selection_display})"
            
            # Create and display treemap
            fig = create_treemap(df, fancy_title, is_sector_view=is_sector_view)
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance display BELOW the chart
            perf = st.session_state.index_performance
            # For sector ETFs, the selection IS the symbol. For S&P 500, use SPY.
            index_symbol = 'SPY' if selection_display == 'S&P 500' else selection_display
            sector_name = SECTOR_NAMES.get(index_symbol, selection_display)
            
            perf_color = "green" if perf >= 0 else "red"
            perf_icon = "📈" if perf >= 0 else "📉"
            
            col_perf1, col_perf2 = st.columns([2, 1])
            
            with col_perf1:
                st.markdown(f"**{sector_name} Performance ({st.session_state.heat_map_period}):**")
                st.markdown(
                    f"<span style='font-size: 28px; color: {perf_color}; font-weight: bold;'>{perf_icon} {perf:+.2f}%</span>",
                    unsafe_allow_html=True
                )
            
            with col_perf2:
                label = "Sectors" if st.session_state.get('is_sector_view', False) else "Stocks"
                st.metric(f"{label} Loaded", len(df))
            
            # Summary statistics
            with st.expander("📊 Summary Statistics", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    gainers = len(df[df['change_pct'] > 0])
                    st.metric("Gainers", gainers, delta=None)
                
                with col2:
                    losers = len(df[df['change_pct'] < 0])
                    st.metric("Losers", losers, delta=None)
                
                with col3:
                    avg_change = df['change_pct'].mean()
                    st.metric("Avg Change", f"{avg_change:+.2f}%")
                
                with col4:
                    unchanged = len(df[df['change_pct'] == 0])
                    st.metric("Unchanged", unchanged)
                
                # Top gainers and losers
                st.markdown("---")
                col_gain, col_lose = st.columns(2)
                
                with col_gain:
                    st.markdown("**🚀 Top Gainers**")
                    # Only show stocks with POSITIVE change
                    gainers_df = df[df['change_pct'] > 0].nlargest(5, 'change_pct')[['symbol', 'change_pct', 'last_price']]
                    if not gainers_df.empty:
                        gainers_df.columns = ['Symbol', 'Change %', 'Price']
                        st.dataframe(gainers_df, hide_index=True, use_container_width=True)
                    else:
                        st.caption("No gainers today")
                
                with col_lose:
                    st.markdown("**📉 Top Losers**")
                    # Only show stocks with NEGATIVE change
                    losers_df = df[df['change_pct'] < 0].nsmallest(5, 'change_pct')[['symbol', 'change_pct', 'last_price']]
                    if not losers_df.empty:
                        losers_df.columns = ['Symbol', 'Change %', 'Price']
                        st.dataframe(losers_df, hide_index=True, use_container_width=True)
                    else:
                        st.caption("No losers today")
        
        else:
            # Show instructions when no data loaded
            st.info("👆 Select an Index/Sector and Time Period, then click **Update** to generate the heat map.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
