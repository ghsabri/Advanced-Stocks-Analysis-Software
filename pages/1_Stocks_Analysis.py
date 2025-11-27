"""
Stocks Analysis Page - Complete Stock Analysis Dashboard
Matches Excel "User Interface" worksheet layout
"""

import streamlit as st
import sys
import os
import re
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from stock_lookup import get_stock_info, get_sector_etf
from cached_data import get_shared_stock_data, get_simple_stock_data


def format_tr_status_display(tr_status):
    """
    Format TR Status for display - strips extra markers but keeps enhancement signals (↑↓✓*+)
    Returns: (display_text, emoji) tuple
    """
    if tr_status is None or tr_status == 'N/A':
        return 'N/A', ''
    
    value_str = str(tr_status)
    
    # Strip extra markers - keep ONLY the stage name + enhancements (↑↓✓*+)
    # Remove EXIT markers
    value_str = re.sub(r'🔴\s*EXIT\s*', '', value_str, flags=re.IGNORECASE)
    value_str = re.sub(r'🔴\s*', '', value_str)
    value_str = re.sub(r'\s+EXIT$', '', value_str, flags=re.IGNORECASE)
    
    # Remove colored circle emojis AND any "BUY" that follows them
    value_str = re.sub(r'🟢\s*BUY\b', '', value_str, flags=re.IGNORECASE)
    value_str = re.sub(r'🟢\s*', '', value_str)
    value_str = re.sub(r'🟣\s*', '', value_str)
    value_str = re.sub(r'🔵\s*', '', value_str)
    value_str = re.sub(r'⚫\s*', '', value_str)
    value_str = re.sub(r'⚪\s*', '', value_str)
    
    # Remove any stray bullet points or circles AND any "BUY" that follows them
    value_str = re.sub(r'[●○•◦◉◎⬤]\s*BUY\b', '', value_str, flags=re.IGNORECASE)
    value_str = re.sub(r'[●○•◦◉◎⬤]\s*', '', value_str)
    
    # Remove standalone "BUY" ONLY when it directly follows an enhancement signal
    value_str = re.sub(r'([✓✔↑↓\*\+])\s+BUY\b', r'\1', value_str, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and trim
    value_str = re.sub(r'\s+', ' ', value_str).strip()
    
    # Determine emoji based on status
    if 'Strong Buy' in value_str:
        emoji = '🟢'
    elif 'Strong Sell' in value_str:
        emoji = '🔴'
    elif 'Buy' in value_str and 'Sell' not in value_str:
        emoji = '🟢'
    elif 'Sell' in value_str:
        emoji = '🔴'
    elif 'Neutral' in value_str:
        emoji = '🟡'
    else:
        emoji = ''
    
    return value_str, emoji


# Helper functions for technical indicators
def calculate_macd(df):
    """Calculate MACD"""
    try:
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd.iloc[-1], signal.iloc[-1]
    except:
        return None, None

def calculate_ppo(df):
    """Calculate PPO"""
    try:
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        ppo = ((exp1 - exp2) / exp2) * 100
        signal = ppo.ewm(span=9, adjust=False).mean()
        return ppo.iloc[-1], signal.iloc[-1]
    except:
        return None, None

def calculate_pmo(df):
    """Calculate PMO"""
    try:
        roc = ((df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
        pmo = roc.ewm(span=35, adjust=False).mean().ewm(span=20, adjust=False).mean()
        signal = pmo.ewm(span=10, adjust=False).mean()
        return pmo.iloc[-1], signal.iloc[-1]
    except:
        return None, None

def calculate_chaikin(df):
    """Calculate Chaikin Money Flow"""
    try:
        mfm = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
        mfv = mfm * df['Volume']
        cmf = mfv.rolling(window=20).sum() / df['Volume'].rolling(window=20).sum()
        return cmf.iloc[-1]
    except:
        return None

def get_fundamentals_yf(symbol):
    """Get fundamentals using yfinance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'beta': info.get('beta')
        }
    except:
        return None

st.set_page_config(
    page_title="Stocks Analysis - MJ Software",
    page_icon="📊",
    layout="wide"
)

# CSS for button styling
st.markdown("""
<style>
    /* Update button - medium size */
    .stButton > button {
        height: 38px !important;
        padding: 6px 16px !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# Check if user is logged in (placeholder for now)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True  # TODO: Replace with actual authentication

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Please login from the Home page to access this feature.")
    st.stop()

# ============================================================
# SIDEBAR - Settings
# ============================================================
with st.sidebar:
    # Custom CSS to match sidebar navigation font size and style
    st.markdown("""
    <style>
    /* Match checkbox labels to sidebar nav style */
    [data-testid="stSidebar"] .stCheckbox label p {
        font-size: 0.875rem !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
    }
    /* Match radio labels to sidebar nav style */
    [data-testid="stSidebar"] .stRadio label p {
        font-size: 0.875rem !important;
        font-weight: 400 !important;
    }
    /* Match selectbox to sidebar nav style */
    [data-testid="stSidebar"] .stSelectbox label p {
        font-size: 0.875rem !important;
        font-weight: 400 !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        font-size: 0.875rem !important;
    }
    /* Settings header */
    [data-testid="stSidebar"] .settings-header {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.25rem;
    }
    /* Reduce checkbox vertical spacing */
    [data-testid="stSidebar"] .stCheckbox {
        margin-bottom: -10px !important;
    }
    /* Reduce radio button spacing */
    [data-testid="stSidebar"] .stRadio > div {
        margin-top: -5px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a container with border for all settings
    settings_container = st.container(border=True)
    
    with settings_container:
        st.markdown('<p class="settings-header">⚙️ Page Sync Settings</p>', unsafe_allow_html=True)
        
        # Master Auto-sync toggle
        auto_sync = st.checkbox(
            "Auto-Sync on",
            value=st.session_state.get('auto_sync_enabled', True),
            help="Enable/disable syncing to other pages"
        )
        st.session_state['auto_sync_enabled'] = auto_sync
        
        # Individual page checkboxes (only enabled when auto-sync is on)
        sync_tr = st.checkbox(
            "TR Indicator",
            value=st.session_state.get('sync_tr_indicator', True),
            disabled=not auto_sync
        )
        sync_seasonality = st.checkbox(
            "Seasonality",
            value=st.session_state.get('sync_seasonality', True),
            disabled=not auto_sync
        )
        sync_daytrading = st.checkbox(
            "Day Trading",
            value=st.session_state.get('sync_daytrading', True),
            disabled=not auto_sync
        )
        sync_indicator_chart = st.checkbox(
            "Indicator Chart",
            value=st.session_state.get('sync_indicator_chart', True),
            disabled=not auto_sync
        )
        
        # Indicator Chart dropdown - only show when both auto_sync and indicator_chart are on
        if auto_sync and sync_indicator_chart:
            indicator_options = [
                "RSI",
                "MACD",
                "EMA",
                "EMA Crossover",
                "Ichimoku Cloud",
                "SuperTrend",
                "TR / Ichimoku Combo Strategy"
            ]
            selected_indicator = st.selectbox(
                "Chart Type",
                indicator_options,
                index=indicator_options.index(st.session_state.get('sync_indicator_type', 'RSI')) if st.session_state.get('sync_indicator_type', 'RSI') in indicator_options else 0,
                label_visibility="collapsed"
            )
            st.session_state['sync_indicator_type'] = selected_indicator
        
        # Save individual sync settings
        st.session_state['sync_tr_indicator'] = sync_tr
        st.session_state['sync_seasonality'] = sync_seasonality
        st.session_state['sync_daytrading'] = sync_daytrading
        st.session_state['sync_indicator_chart'] = sync_indicator_chart
        
        # Timeframe selector - horizontal, only enabled when auto-sync is on
        selected_timeframe = st.radio(
            "Timeframe",
            ["Daily", "Weekly"],
            index=0 if st.session_state.get('selected_timeframe', 'daily') == 'daily' else 1,
            horizontal=True,
            disabled=not auto_sync,
            label_visibility="collapsed"
        )
        st.session_state['selected_timeframe'] = selected_timeframe.lower()

# Page title
st.title("📊 Stocks Analysis")
st.markdown("**Complete Stock Analysis Dashboard**")

# Stock symbol input with search
col1, col2 = st.columns([3, 1])

with col1:
    # Check if symbol was clicked from watchlist
    if 'selected_symbol' in st.session_state and st.session_state.selected_symbol:
        # Symbol clicked from watchlist - use it and trigger auto-update
        clicked_symbol = st.session_state.selected_symbol.upper().strip()
        del st.session_state.selected_symbol
        
        # Set the analysis symbol and trigger update
        st.session_state['analysis_symbol'] = clicked_symbol
        st.session_state['current_input_symbol'] = clicked_symbol
        st.session_state['update_triggered'] = True
        
        # Auto-sync: Set synced variables for other pages
        if st.session_state.get('auto_sync_enabled', True):
            st.session_state['synced_symbol'] = clicked_symbol
            st.session_state['synced_timeframe'] = st.session_state.get('selected_timeframe', 'daily')
    
    # Get the current input symbol (persists across reruns)
    current_symbol = st.session_state.get('current_input_symbol', '')
    
    symbol = st.text_input(
        "Stock Symbol",
        value=current_symbol,
        placeholder="Enter stock symbol (e.g., AAPL, GOOGL, MSFT)",
        help="Enter stock ticker symbol or click a symbol from your watchlist",
        key="symbol_input"
    )
    
    # Update current_input_symbol when user types
    if symbol != current_symbol:
        st.session_state['current_input_symbol'] = symbol

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    update_button = st.button("🔄 Update", type="primary", use_container_width=True)

# Auto-update only on button click
if update_button and symbol:
    # Validate: Only single stock symbol allowed
    symbol_clean = symbol.upper().strip()
    
    # Check for multiple symbols (comma, space, or semicolon separated)
    if ',' in symbol_clean or ';' in symbol_clean or ' ' in symbol_clean:
        st.error("❌ Please enter only ONE stock symbol. This page analyzes a single stock at a time.")
        st.info("💡 Tip: Use Watchlists to track multiple stocks.")
        st.stop()
    
    st.session_state['analysis_symbol'] = symbol_clean
    st.session_state['current_input_symbol'] = symbol_clean
    st.session_state['update_triggered'] = True
    
    # Auto-sync: Set synced variables for other pages
    if st.session_state.get('auto_sync_enabled', True):
        st.session_state['synced_symbol'] = symbol_clean
        st.session_state['synced_timeframe'] = st.session_state.get('selected_timeframe', 'daily')

# Main analysis section
if st.session_state.get('update_triggered', False):
    
    symbol = st.session_state['analysis_symbol']
    
    with st.spinner(f"🔄 Analyzing {symbol}..."):
        
        try:
            # Get stock info from hybrid lookup
            stock_info = get_stock_info(symbol)
            
            if not stock_info:
                st.error(f"❌ Could not find information for {symbol}")
                st.stop()
            
            # Get stock data
            # If TR Status was passed from Watchlist, use SIMPLE fetch (faster - no TR calc)
            # Otherwise use full TR analysis
            has_passed_tr = 'passed_tr_status' in st.session_state and st.session_state.passed_tr_status
            
            if has_passed_tr:
                # FAST PATH: Simple data fetch (no TR analysis needed)
                # TR Status already available from Watchlist
                print(f"⚡ Fast loading {symbol} (TR Status passed from Watchlist)")
                df = get_simple_stock_data(
                    ticker=symbol,
                    duration_days=400,  # ~1.1 years to ensure 252+ trading days
                    timeframe='daily'
                )
            else:
                # FULL PATH: Complete TR analysis
                print(f"📊 Full analysis {symbol} (TR Status not available)")
                df = get_shared_stock_data(
                    ticker=symbol,
                    duration_days=400,  # ~1.1 years to ensure 252+ trading days
                    timeframe='daily',
                    api_source='yahoo'
                )
            
            if df is None or df.empty:
                st.error(f"❌ Could not get price data for {symbol}")
                st.stop()
            
            # Store in session state
            st.session_state['stock_info'] = stock_info
            st.session_state['stock_data'] = df
            st.session_state['update_triggered'] = False
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("Show error details"):
                st.code(traceback.format_exc())
            st.stop()

# Display analysis if data is available
if 'stock_info' in st.session_state and 'stock_data' in st.session_state:
    
    stock_info = st.session_state['stock_info']
    df = st.session_state['stock_data']
    symbol = st.session_state['analysis_symbol']
    
    # Company Information Header
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"**Company:** {stock_info['name']}")
    
    with col2:
        st.markdown(f"**Exchange:** {stock_info['exchange']}")
    
    with col3:
        st.markdown(f"**Sector:** {stock_info['sector']}")
    
    with col4:
        st.markdown(f"**Industry:** {stock_info['industry']}")
    
    # Current price info
    if not df.empty:
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current Price",
                f"${current_price:.2f}",
                f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
            )
        
        with col2:
            volume = df['Volume'].iloc[-1]
            st.metric("Volume", f"{volume:,.0f}")
        
        with col3:
            # 52-week range
            recent_year = df.tail(252)  # Approx 1 year trading days
            low_52w = recent_year['Low'].min()
            high_52w = recent_year['High'].max()
            st.metric("52-Week Range", f"${low_52w:.2f} - ${high_52w:.2f}")
        
        with col4:
            # TR Status display logic:
            # 1. If passed from Watchlist (view had TR Status column) - display it
            # 2. If TR_Status_Enhanced or TR_Status exists in df - display it
            # 3. Otherwise - show message to use TR Indicator page
            
            passed_tr_status = st.session_state.get('passed_tr_status', None)
            
            if passed_tr_status:
                # TR Status was passed from Watchlist
                tr_status = passed_tr_status
                # Clear it after reading (so it doesn't persist)
                del st.session_state['passed_tr_status']
                
                # Format and display with enhancement signals
                display_text, emoji = format_tr_status_display(tr_status)
                st.metric("TR Status", f"{emoji} {display_text}")
                    
            elif 'TR_Status_Enhanced' in df.columns or 'TR_Status' in df.columns:
                # Use TR_Status_Enhanced if available, otherwise fall back to TR_Status
                if 'TR_Status_Enhanced' in df.columns:
                    tr_status = df['TR_Status_Enhanced'].iloc[-1]
                else:
                    tr_status = df['TR_Status'].iloc[-1]
                
                # Format and display with enhancement signals
                display_text, emoji = format_tr_status_display(tr_status)
                st.metric("TR Status", f"{emoji} {display_text}")
            else:
                # No TR Status available - show message
                st.markdown("**TR Status**")
                st.caption("Use [TR Indicator](/TR_Indicator) page")
        
        # Today's Price Range bar - Excel style (1/3 width, left-aligned)
        if not df.empty:
            col1, col2 = st.columns([1, 2])  # 1/3 and 2/3 split
            
            with col1:  # Use only the left 1/3
                today_high = df['High'].iloc[-1]
                today_low = df['Low'].iloc[-1]
                today_close = df['Close'].iloc[-1]
                
                # Create horizontal bar matching Excel
                fig_today = go.Figure()
                
                # Red bar from low to current price
                if today_close > today_low:
                    fig_today.add_trace(go.Bar(
                        x=[today_close - today_low],
                        y=['Range'],
                        orientation='h',
                        marker=dict(color='#5B9BD5', line=dict(color='black', width=1)),
                        base=today_low,
                        showlegend=False,
                        hoverinfo='skip',
                        text=f'${today_low:.2f}',
                        textposition='inside',
                        textfont=dict(size=11, color='white', family='Arial Black'),
                        insidetextanchor='start'
                    ))
                
                # Green bar from current price to high
                if today_high > today_close:
                    fig_today.add_trace(go.Bar(
                        x=[today_high - today_close],
                        y=['Range'],
                        orientation='h',
                        marker=dict(color='#70AD47', line=dict(color='black', width=1)),
                        base=today_close,
                        showlegend=False,
                        hoverinfo='skip',
                        text=f'${today_high:.2f}',
                        textposition='inside',
                        textfont=dict(size=11, color='white', family='Arial Black'),
                        insidetextanchor='end'
                    ))
                
                # Current price marker and label
                fig_today.add_trace(go.Scatter(
                    x=[today_close],
                    y=['Range'],
                    mode='text',
                    text=[f'${today_close:.2f}'],
                    textposition='top center',
                    textfont=dict(size=11, color='black', family='Arial Black'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig_today.update_layout(
                    height=80,
                    margin=dict(l=0, r=0, t=25, b=5),
                    xaxis=dict(
                        showticklabels=False,
                        showgrid=False,
                        zeroline=False
                    ),
                    yaxis=dict(
                        showticklabels=False,
                        showgrid=False
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    barmode='stack'
                )
                
                st.plotly_chart(fig_today, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    
    # TradingView Advanced Chart
    st.subheader("📈 Price Chart with Technical Indicators")
    
    # TradingView widget HTML - Main chart 2.5x height of indicator panels
    tradingview_html = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="height:900px;">
      <div id="tradingview_chart" style="height:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "width": "100%",
        "height": 900,
        "symbol": "{symbol}",
        "interval": "D",
        "timezone": "America/New_York",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "studies": [
          "MASimple@tv-basicstudies",
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies",
          "AccumDist@tv-basicstudies"
        ],
        "container_id": "tradingview_chart"
      }}
      );
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    
    st.components.v1.html(tradingview_html, height=950)
    
    st.markdown("---")
    
    # Two-column layout for detailed information
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        
        # Extended Hours section
        st.subheader("⏰ Extended Hours")
        ext_col1, ext_col2 = st.columns(2)
        with ext_col1:
            st.metric("Pre-Market", "—")
        with ext_col2:
            st.metric("After Hours", "—")
        
        st.markdown("---")
        
        # Fundamentals
        st.subheader("📊 Fundamentals")
        
        # Try to get real fundamentals data
        fund_info = get_fundamentals_yf(symbol)
        
        if fund_info:
            market_cap = fund_info['market_cap']
            if market_cap:
                if market_cap >= 1e12:
                    mc_display = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    mc_display = f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    mc_display = f"${market_cap/1e6:.2f}M"
                else:
                    mc_display = f"${market_cap:,.0f}"
            else:
                mc_display = "—"
            
            fund_data = {
                "Market Cap": mc_display,
                "P/E Ratio": f"{fund_info['pe_ratio']:.2f}" if fund_info['pe_ratio'] else "—",
                "Beta": f"{fund_info['beta']:.2f}" if fund_info['beta'] else "—"
            }
        else:
            fund_data = {
                "Market Cap": "—",
                "P/E Ratio": "—",
                "Beta": "—"
            }
        
        for label, value in fund_data.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text(label)
            with col2:
                st.text(value)
        
        st.markdown("---")
        
        # Technical Indicators
        st.subheader("📈 Technical Indicators")
        
        # Calculate some basic indicators
        if len(df) >= 14:
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # ATR
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
            
            # Calculate other indicators
            macd, macd_signal = calculate_macd(df)
            ppo, ppo_signal = calculate_ppo(df)
            pmo, pmo_signal = calculate_pmo(df)
            chaikin = calculate_chaikin(df)
            
            indicators_data = {
                "RSI (14)": f"{current_rsi:.2f}",
                "ATR (14)": f"{atr:.2f}",
                "MACD (26, 12, 9)": f"{macd:.2f}" if macd else "—",
                "PPO (26, 12, 9)": f"{ppo:.2f}%" if ppo else "—",
                "PMO (35, 20, 10)": f"{pmo:.2f}" if pmo else "—",
                "Chaikin Money Flow (20)": f"{chaikin:.4f}" if chaikin else "—"
            }
        else:
            indicators_data = {
                "RSI (14)": "—",
                "ATR (14)": "—",
                "MACD": "—",
                "PPO": "—",
                "PMO": "—",
                "Chaikin": "—"
            }
        
        for label, value in indicators_data.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text(label)
            with col2:
                st.text(value)
        
        st.markdown("---")
        
        # Support / Resistance
        st.subheader("📍 Support / Resistance")
        
        # Calculate all three types of pivot points
        if len(df) > 0:
            high = df['High'].iloc[-1]
            low = df['Low'].iloc[-1]
            close = df['Close'].iloc[-2] if len(df) > 1 else df['Close'].iloc[-1]
            
            # ============================================================
            # 1. CLASSIC PIVOT POINTS
            # ============================================================
            classic_pivot = (high + low + close) / 3
            classic_r1 = (2 * classic_pivot) - low
            classic_r2 = classic_pivot + (high - low)
            classic_r3 = high + 2 * (classic_pivot - low)
            classic_s1 = (2 * classic_pivot) - high
            classic_s2 = classic_pivot - (high - low)
            classic_s3 = low - 2 * (high - classic_pivot)
            
            # ============================================================
            # 2. CAMARILLA PIVOT POINTS
            # ============================================================
            cam_pivot = (high + low + close) / 3
            cam_r4 = close + ((high - low) * 1.1 / 2)
            cam_r3 = close + ((high - low) * 1.1 / 4)
            cam_r2 = close + ((high - low) * 1.1 / 6)
            cam_r1 = close + ((high - low) * 1.1 / 12)
            cam_s1 = close - ((high - low) * 1.1 / 12)
            cam_s2 = close - ((high - low) * 1.1 / 6)
            cam_s3 = close - ((high - low) * 1.1 / 4)
            cam_s4 = close - ((high - low) * 1.1 / 2)
            
            # ============================================================
            # 3. FIBONACCI PIVOT POINTS
            # ============================================================
            fib_pivot = (high + low + close) / 3
            fib_r1 = fib_pivot + 0.382 * (high - low)
            fib_r2 = fib_pivot + 0.618 * (high - low)
            fib_r3 = fib_pivot + 1.000 * (high - low)
            fib_s1 = fib_pivot - 0.382 * (high - low)
            fib_s2 = fib_pivot - 0.618 * (high - low)
            fib_s3 = fib_pivot - 1.000 * (high - low)
            
            # Create three columns for the three methods
            pivot_col1, pivot_col2, pivot_col3 = st.columns(3)
            
            with pivot_col1:
                st.markdown("**Classic Pivot Points**")
                st.text(f"Pivot: ${classic_pivot:.2f}")
                st.text(f"R3: ${classic_r3:.2f}")
                st.text(f"R2: ${classic_r2:.2f}")
                st.text(f"R1: ${classic_r1:.2f}")
                st.text(f"S1: ${classic_s1:.2f}")
                st.text(f"S2: ${classic_s2:.2f}")
                st.text(f"S3: ${classic_s3:.2f}")
            
            with pivot_col2:
                st.markdown("**Camarilla Pivot Points**")
                st.text(f"Pivot: ${cam_pivot:.2f}")
                st.text(f"R4: ${cam_r4:.2f}")
                st.text(f"R3: ${cam_r3:.2f}")
                st.text(f"R2: ${cam_r2:.2f}")
                st.text(f"R1: ${cam_r1:.2f}")
                st.text(f"S1: ${cam_s1:.2f}")
                st.text(f"S2: ${cam_s2:.2f}")
                st.text(f"S3: ${cam_s3:.2f}")
                st.text(f"S4: ${cam_s4:.2f}")
            
            with pivot_col3:
                st.markdown("**Fibonacci Pivot Points**")
                st.text(f"Pivot: ${fib_pivot:.2f}")
                st.text(f"R3: ${fib_r3:.2f}")
                st.text(f"R2: ${fib_r2:.2f}")
                st.text(f"R1: ${fib_r1:.2f}")
                st.text(f"S1: ${fib_s1:.2f}")
                st.text(f"S2: ${fib_s2:.2f}")
                st.text(f"S3: ${fib_s3:.2f}")
        else:
            st.info("Insufficient data to calculate pivot points")
    
    with col_right:
        
        # Markets section - LIVE DATA WITH GRID
        st.subheader("📊 Markets")
        
        try:
            from src.markets_data import fetch_markets_data_simple
            import pandas as pd
            
            # Fetch markets data in ONE batch call
            markets = fetch_markets_data_simple()
            
            if markets:
                # Create DataFrame for grid display
                markets_data = []
                for market in markets:
                    # Color code the text values
                    if market['direction'] == 'up':
                        change_display = f"<span style='color: green'>{market['arrow']} {abs(market['change']):.2f}</span>"
                        pct_display = f"<span style='color: green'>{market['change_percent']:+.2f}%</span>"
                    elif market['direction'] == 'down':
                        change_display = f"<span style='color: red'>{market['arrow']} {abs(market['change']):.2f}</span>"
                        pct_display = f"<span style='color: red'>{market['change_percent']:+.2f}%</span>"
                    else:
                        change_display = f"{market['arrow']} {abs(market['change']):.2f}"
                        pct_display = f"{market['change_percent']:+.2f}%"
                    
                    markets_data.append({
                        'Market': market['market'],
                        'Price': f"{market['price']:,.2f}",
                        'Change': change_display,
                        'Change %': pct_display
                    })
                
                df_markets = pd.DataFrame(markets_data)
                
                # Add CSS styling for right-aligned columns
                st.markdown("""
                <style>
                    .markets-table td:nth-child(2),
                    .markets-table td:nth-child(3),
                    .markets-table td:nth-child(4),
                    .markets-table th:nth-child(2),
                    .markets-table th:nth-child(3),
                    .markets-table th:nth-child(4) {
                        text-align: right !important;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                # Display with HTML formatting and custom class
                html_table = df_markets.to_html(escape=False, index=False, classes='markets-table')
                st.markdown(html_table, unsafe_allow_html=True)
                
            else:
                st.info("📊 Market data temporarily unavailable")
                
        except Exception as e:
            st.error(f"Error loading markets: {e}")
            st.info("📊 Market data temporarily unavailable")
        
        st.markdown("---")
        
        # Performance Table
        st.subheader("📈 Performance")
        
        # Dropdown aligned right, just below heading
        _, perf_dropdown_col = st.columns([3, 1])
        
        with perf_dropdown_col:
            perf_range = st.selectbox(
                "Range",
                ["1 Year", "3 Years", "5 Years"],
                key="perf_range_select",
                help="Select time range for performance comparison"
            )
        
        # Determine required days for performance calculation
        perf_duration_map = {
            "1 Year": 400,
            "3 Years": 1150,
            "5 Years": 1900
        }
        required_duration = perf_duration_map[perf_range]
        
        # For performance, we use SIMPLE data (no TR analysis needed)
        # This is separate from the main stock data used elsewhere on the page
        perf_data_key = f"perf_data_{symbol}_{perf_range}"
        
        if perf_data_key not in st.session_state:
            # Fetch simple price data for performance (fast - no TR analysis)
            with st.spinner(f"Loading {perf_range} performance data..."):
                perf_df = get_simple_stock_data(
                    ticker=symbol,
                    duration_days=required_duration,
                    timeframe='daily'
                )
                if perf_df is not None and not perf_df.empty:
                    st.session_state[perf_data_key] = perf_df
        
        # Use performance-specific data if available, otherwise fall back to main df
        if perf_data_key in st.session_state:
            perf_df = st.session_state[perf_data_key]
        else:
            perf_df = df
        
        # Get sector ETF
        sector_etf = get_sector_etf(symbol)
        
        # Calculate returns for different periods
        def calculate_returns(df, periods):
            """Calculate returns for various periods"""
            returns = {}
            current_price = df['Close'].iloc[-1]
            
            period_days = {
                '5 days': 5,
                '15 days': 15,
                '1 Mo': 21,
                '3 Mo': 63,
                '6 Mo': 126,
                '1 Yr': 252,
                '3 Yr': 756,
                '5 Yr': 1260
            }
            
            for period, days in period_days.items():
                if len(df) >= days:  # Changed from > to >= to include exact matches
                    try:
                        # Use min to avoid index out of bounds
                        idx = min(days, len(df) - 1)
                        past_price = df['Close'].iloc[-idx]
                        ret = ((current_price - past_price) / past_price) * 100
                        returns[period] = f"{ret:+.2f}%"
                    except:
                        returns[period] = "—"
                # Fallbacks: use earliest available data if we're close
                elif period == '1 Yr' and len(df) >= 200:  # ~80% of 1 year
                    try:
                        past_price = df['Close'].iloc[0]
                        ret = ((current_price - past_price) / past_price) * 100
                        returns[period] = f"{ret:+.2f}%*"  # * indicates approximate
                    except:
                        returns[period] = "—"
                elif period == '3 Yr' and len(df) >= 630:  # ~83% of 3 years
                    try:
                        past_price = df['Close'].iloc[0]
                        ret = ((current_price - past_price) / past_price) * 100
                        returns[period] = f"{ret:+.2f}%*"
                    except:
                        returns[period] = "—"
                elif period == '5 Yr' and len(df) >= 1000:  # ~80% of 5 years
                    try:
                        past_price = df['Close'].iloc[0]
                        ret = ((current_price - past_price) / past_price) * 100
                        returns[period] = f"{ret:+.2f}%*"
                    except:
                        returns[period] = "—"
                else:
                    returns[period] = "—"
            
            # YTD - Robust calculation with multiple fallbacks
            try:
                from datetime import datetime
                import pytz
                
                current_year = datetime.now().year
                year_start = datetime(current_year, 1, 1)
                
                # Try timezone-aware comparison first
                try:
                    if hasattr(df.index, 'tz') and df.index.tz is not None:
                        year_start = year_start.replace(tzinfo=pytz.UTC)
                    df_ytd = df[df.index >= year_start]
                    
                    if len(df_ytd) > 0:
                        year_start_price = df_ytd.iloc[0]['Close']
                        ytd_ret = ((current_price - year_start_price) / year_start_price) * 100
                        returns['YTD'] = f"{ytd_ret:+.2f}%"
                    else:
                        raise ValueError("No YTD data found")
                except:
                    # Fallback: Use trading days estimate
                    days_this_year = (datetime.now() - datetime(current_year, 1, 1)).days
                    trading_days_ytd = max(int(days_this_year * 0.69), 1)  # At least 1 day
                    
                    if len(df) > trading_days_ytd:
                        year_start_price = df['Close'].iloc[-trading_days_ytd]
                        ytd_ret = ((current_price - year_start_price) / year_start_price) * 100
                        returns['YTD'] = f"{ytd_ret:+.2f}%"
                    else:
                        # Last resort: Use earliest available data
                        year_start_price = df['Close'].iloc[0]
                        ytd_ret = ((current_price - year_start_price) / year_start_price) * 100
                        returns['YTD'] = f"{ytd_ret:+.2f}%"
            except Exception as e:
                # Absolute last resort
                try:
                    year_start_price = df['Close'].iloc[0]
                    ytd_ret = ((current_price - year_start_price) / year_start_price) * 100
                    returns['YTD'] = f"{ytd_ret:+.2f}%"
                except:
                    returns['YTD'] = "—"
            
            return returns
        
        # Calculate returns for stock using PERFORMANCE data (may have more history)
        stock_returns = calculate_returns(perf_df, ['5 days', '15 days', '1 Mo', '3 Mo', '6 Mo', '1 Yr', '3 Yr', '5 Yr', 'YTD'])
        
        # Fetch comparison data - use SIMPLE data (no TR analysis needed for performance)
        # Cache SPY and sector data for the selected range
        spy_cache_key = f"perf_spy_{perf_range}"
        sector_cache_key = f"perf_{sector_etf}_{perf_range}" if sector_etf else None
        
        spy_returns = None
        sector_returns = None
        
        # Fetch SPY
        if spy_cache_key not in st.session_state:
            with st.spinner("Loading SPY data..."):
                try:
                    spy_df = get_simple_stock_data('SPY', duration_days=required_duration, timeframe='daily')
                    if spy_df is not None and not spy_df.empty:
                        st.session_state[spy_cache_key] = spy_df
                except:
                    pass
        
        if spy_cache_key in st.session_state:
            spy_returns = calculate_returns(st.session_state[spy_cache_key], ['5 days', '15 days', '1 Mo', '3 Mo', '6 Mo', '1 Yr', '3 Yr', '5 Yr', 'YTD'])
        
        # Fetch Sector ETF
        if sector_etf and sector_cache_key:
            if sector_cache_key not in st.session_state:
                with st.spinner(f"Loading {sector_etf} data..."):
                    try:
                        sector_df = get_simple_stock_data(sector_etf, duration_days=required_duration, timeframe='daily')
                        if sector_df is not None and not sector_df.empty:
                            st.session_state[sector_cache_key] = sector_df
                    except:
                        pass
            
            if sector_cache_key in st.session_state:
                sector_returns = calculate_returns(st.session_state[sector_cache_key], ['5 days', '15 days', '1 Mo', '3 Mo', '6 Mo', '1 Yr', '3 Yr', '5 Yr', 'YTD'])
        
        # Create performance table
        performance_data = {
            'Metric': [symbol, 'ARCX:SPY', f'ARCX:{sector_etf}'],
            '5 days': [stock_returns['5 days'], spy_returns['5 days'] if spy_returns else '—', sector_returns['5 days'] if sector_returns else '—'],
            '15 days': [stock_returns['15 days'], spy_returns['15 days'] if spy_returns else '—', sector_returns['15 days'] if sector_returns else '—'],
            '1 Mo': [stock_returns['1 Mo'], spy_returns['1 Mo'] if spy_returns else '—', sector_returns['1 Mo'] if sector_returns else '—'],
            '3 Mo': [stock_returns['3 Mo'], spy_returns['3 Mo'] if spy_returns else '—', sector_returns['3 Mo'] if sector_returns else '—'],
            '6 Mo': [stock_returns['6 Mo'], spy_returns['6 Mo'] if spy_returns else '—', sector_returns['6 Mo'] if sector_returns else '—'],
            '1 Yr': [stock_returns['1 Yr'], spy_returns['1 Yr'] if spy_returns else '—', sector_returns['1 Yr'] if sector_returns else '—'],
            '3 Yrs': [stock_returns['3 Yr'], spy_returns['3 Yr'] if spy_returns else '—', sector_returns['3 Yr'] if sector_returns else '—'],
            '5 Yrs': [stock_returns['5 Yr'], spy_returns['5 Yr'] if spy_returns else '—', sector_returns['5 Yr'] if sector_returns else '—'],
            'YTD': [stock_returns['YTD'], spy_returns['YTD'] if spy_returns else '—', sector_returns['YTD'] if sector_returns else '—']
        }
        
        perf_df = pd.DataFrame(performance_data)
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Trading Signals
        st.subheader("🎯 Trading Signals")
        
        # Calculate signals based on indicators
        current_price = df['Close'].iloc[-1]
        
        # EMAs
        ema_20 = df['Close'].ewm(span=20).mean().iloc[-1] if len(df) >= 20 else current_price
        ema_50 = df['Close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else current_price
        ema_200 = df['Close'].ewm(span=200).mean().iloc[-1] if len(df) >= 200 else current_price
        
        # Determine signals
        ema20_signal = "🟢 Buy" if current_price > ema_20 else "🔴 Sell"
        ema50_signal = "🟢 Buy" if current_price > ema_50 else "🔴 Sell"
        ema200_signal = "🟢 Buy" if current_price > ema_200 else "🔴 Sell"
        
        # RSI signal
        if len(df) >= 14:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            if current_rsi > 70:
                rsi_signal = "🔴 Overbought"
            elif current_rsi < 30:
                rsi_signal = "🟢 Oversold"
            else:
                rsi_signal = "⚪ Neutral"
        else:
            rsi_signal = "⚪ Neutral"
        
        # MACD signal
        macd_val, macd_sig = calculate_macd(df)
        if macd_val and macd_sig:
            macd_signal = "🟢 Buy" if macd_val > macd_sig else "🔴 Sell"
        else:
            macd_signal = "⚪ Neutral"
        
        signals_col1, signals_col2 = st.columns(2)
        
        with signals_col1:
            st.markdown("**Short Term:**")
            st.markdown(f"EMA 20 Days: {ema20_signal}")
            st.markdown(f"RSI (14): {rsi_signal}")
            st.markdown(f"MACD: {macd_signal}")
        
        with signals_col2:
            st.markdown("**Medium Term:**")
            st.markdown(f"EMA 50 Days: {ema50_signal}")
            st.markdown("**Long Term:**")
            st.markdown(f"EMA 200 Days: {ema200_signal}")
        
        st.markdown("---")
        
        # Profit & Stop Loss Targets
        st.subheader("💰 Profit & Stop Loss Targets")
        
        if not df.empty:
            current_price = df['Close'].iloc[-1]
            
            # Calculate EMAs
            ema_20 = df['Close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else current_price
            ema_50 = df['Close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else current_price
            ema_200 = df['Close'].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else current_price
            
            # Build data array matching Excel format exactly
            # Format: (y_label, price, pct_from_current, color, annotation)
            chart_data = []
            
            # Profit targets (top) - percentages shown on left
            chart_data.append(('30%', current_price * 1.30, 30, '#90EE90', 'Profit Target'))
            chart_data.append(('25%', current_price * 1.25, 25, '#98FB98', 'Profit Target'))
            chart_data.append(('20%', current_price * 1.20, 20, '#ADFF2F', 'Profit Target'))
            chart_data.append(('15%', current_price * 1.15, 15, '#9ACD32', ''))
            chart_data.append(('10%', current_price * 1.10, 10, '#7CFC00', ''))
            
            # Current price (center) - no percentage
            chart_data.append(('', current_price, 0, '#4169E1', 'Price'))
            
            # Stop losses (below current)
            chart_data.append(('-3%', current_price * 0.97, 3, '#FFFF00', ''))
            chart_data.append(('-5%', current_price * 0.95, 5, '#FFD700', ''))
            chart_data.append(('-7%', current_price * 0.93, 7, '#FFA500', 'Stop Loss'))
            chart_data.append(('-10%', current_price * 0.90, 10, '#FF4500', 'Stop Loss'))
            
            # EMAs (bottom)
            pct_20 = abs((ema_20 - current_price) / current_price * 100)
            pct_50 = abs((ema_50 - current_price) / current_price * 100)
            pct_200 = abs((ema_200 - current_price) / current_price * 100)
            chart_data.append((f'{pct_20:.0f}%', ema_20, pct_20, '#ADFF2F', '20 period EMA'))
            chart_data.append((f'{pct_50:.0f}%', ema_50, pct_50, '#7CFC00', '50 period EMA'))
            chart_data.append((f'{pct_200:.0f}%', ema_200, pct_200, '#32CD32', '200 period EMA'))
            
            # Create figure
            fig = go.Figure()
            
            # Find min and max prices for proper scaling
            all_prices = [d[1] for d in chart_data]
            min_price = min(all_prices)
            max_price = max(all_prices)
            price_range = max_price - min_price
            
            # Add each bar separately with proper spacing
            for i, (label, price, pct, color, annot) in enumerate(chart_data):
                # Calculate bar width based on actual price (normalized to 0-100 scale)
                # This makes bars proportional to their actual price values
                normalized_price = ((price - min_price) / price_range) * 100 if price_range > 0 else 50
                bar_width = max(normalized_price, 10)  # Minimum 10 for visibility
                
                # Add bar
                fig.add_trace(go.Bar(
                    x=[bar_width],
                    y=[i],
                    orientation='h',
                    marker=dict(
                        color=color,
                        line=dict(color='black', width=1.5)
                    ),
                    text=f"${price:.2f}",
                    textposition='inside',
                    textangle=0,
                    textfont=dict(size=20, color='black', family='Arial Black'),
                    insidetextanchor='middle',
                    hoverinfo='skip',
                    showlegend=False,
                    width=0.9
                ))
                
                # Add annotation on the right if exists
                if annot:
                    fig.add_annotation(
                        x=105,  # Fixed position to right of bars
                        y=i,
                        text=f"<b>{annot}</b>",
                        showarrow=False,
                        font=dict(size=14, color='black', family='Arial'),
                        xanchor='left'
                    )
            
            # Update layout
            fig.update_layout(
                height=750,
                margin=dict(l=90, r=180, t=10, b=10),
                xaxis=dict(
                    showticklabels=False,
                    showgrid=False,
                    zeroline=False,
                    range=[0, 115]  # 0-100 for bars + 15 for annotations
                ),
                yaxis=dict(
                    tickmode='array',
                    tickvals=list(range(len(chart_data))),
                    ticktext=[d[0] for d in chart_data],  # Show percentage labels on left
                    tickfont=dict(size=18, family='Arial', color='black'),
                    showgrid=False,
                    autorange='reversed'  # Top to bottom
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")


