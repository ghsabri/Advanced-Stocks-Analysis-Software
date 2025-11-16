"""
Day Trading Guide - Support & Resistance Levels
Similar to Barchart's Trader's Cheat Sheet
Matches the Excel VBA output format

USES EXISTING PROJECT CODE - NO DUPLICATION
FIXED: Correct imports
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import yfinance as yf

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Use existing project modules
from universal_cache import get_stock_data as get_cached_data
from tr_calculations import calculate_ema  # Use existing EMA function

# Page configuration
st.set_page_config(
    page_title="Day Trading Guide",
    page_icon="📊",
    layout="wide"
)

def get_stock_info(ticker):
    """Get stock information using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except:
        return {'longName': ticker}

def calculate_pivot_points(high, low, close):
    """Calculate Classic Pivot Points"""
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    r2 = pp + (high - low)
    r3 = high + 2 * (pp - low)
    s1 = 2 * pp - high
    s2 = pp - (high - low)
    s3 = low - 2 * (high - pp)
    
    return {
        'Pivot Point': pp,
        'Pivot Point 1st Resistance level': r1,
        'Pivot Point 2nd Resistance level': r2,
        'Pivot Point 3rd Resistance level': r3,
        'Pivot Point 1st Support level': s1,
        'Pivot Point 2nd Support level': s2,
        'Pivot Point 3rd Support level': s3
    }

def calculate_standard_deviation(prices, periods=14):
    """Calculate standard deviation for last N periods"""
    if len(prices) < periods:
        periods = len(prices)
    recent_prices = prices[-periods:]
    return np.std(recent_prices, ddof=1)  # Sample standard deviation

def reverse_rsi_approx(current_price, target_rsi):
    """
    Approximate price level for target RSI
    Simplified approximation method
    """
    if target_rsi == 50:
        return current_price
    
    if target_rsi > 50:
        # RSI above 50 = price needs to rise
        price_change_pct = (target_rsi - 50) / 50 * 0.1
        return current_price * (1 + price_change_pct)
    else:
        # RSI below 50 = price needs to fall
        price_change_pct = (50 - target_rsi) / 50 * 0.1
        return current_price * (1 - price_change_pct)

def calculate_rsi_levels(df, last_price):
    """Calculate price levels at different RSI values"""
    rsi_levels = {}
    for rsi_value in [20, 30, 50, 70, 80]:
        price = reverse_rsi_approx(last_price, rsi_value)
        rsi_levels[f'14 Period RSI at {rsi_value}%'] = price
    
    return rsi_levels

def generate_trading_guide(ticker, timeframe_str, settings):
    """Generate complete trading guide similar to Excel VBA output"""
    
    # Convert timeframe
    interval = '1d' if timeframe_str == 'Daily' else '1wk'
    period_str = 'Days' if timeframe_str == 'Daily' else 'Weeks'
    
    # Get data (2 years for sufficient history)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    # Try to get cached data first (USES EXISTING CACHE SYSTEM)
    try:
        df = get_cached_data(ticker, start_date.strftime('%Y-%m-%d'), 
                             end_date.strftime('%Y-%m-%d'), interval)
    except Exception as e:
        return None, f"Unable to fetch data: {str(e)}", None
    
    if df is None or len(df) == 0:
        return None, "Unable to fetch data for this ticker", None
    
    # Get stock info
    stock_info = get_stock_info(ticker)
    stock_name = stock_info.get('longName', ticker) if stock_info else ticker
    
    # Get latest values
    last_price = df['Close'].iloc[-1]
    last_high = df['High'].iloc[-1]
    last_low = df['Low'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else last_price
    
    # Initialize results list
    results = []
    
    # 1. Pivot Points
    if settings['pivot_points']:
        pp_values = calculate_pivot_points(last_high, last_low, prev_close)
        for label, value in pp_values.items():
            key_description = label if 'Pivot Point' in label and label != 'Pivot Point' else 'Pivot Point'
            results.append({
                'Support / Resistance': label,
                'Key Levels': round(value, 2),
                'Description': key_description
            })
    
    # 2. High, Low and Close
    if settings['hlc']:
        results.append({'Support / Resistance': 'Last Price', 'Key Levels': round(last_price, 2), 'Description': 'Last Price'})
        results.append({'Support / Resistance': 'Previous Close', 'Key Levels': round(prev_close, 2), 'Description': 'Previous Close'})
        results.append({'Support / Resistance': 'High', 'Key Levels': round(last_high, 2), 'Description': 'High'})
        results.append({'Support / Resistance': 'Low', 'Key Levels': round(last_low, 2), 'Description': 'Low'})
    
    # 3. Highs/Lows and Fibonacci Retracements
    if settings['highs_lows']:
        # 1 Month High/Low - Use last ~22 trading days
        df_1m = df.iloc[-22:] if len(df) >= 22 else df
        if len(df_1m) > 0:
            high_1m = df_1m['High'].max()
            low_1m = df_1m['Low'].min()
            results.append({'Support / Resistance': '1Month High', 'Key Levels': round(high_1m, 2), 'Description': '1 Month High'})
            results.append({'Support / Resistance': '1Month Low', 'Key Levels': round(low_1m, 2), 'Description': '1 Month Low'})
            
            # Fibonacci retracements for 1 month
            diff_1m = high_1m - low_1m
            if diff_1m > 0:
                results.append({'Support / Resistance': '', 'Key Levels': round(high_1m - 0.382 * diff_1m, 2), 
                              'Description': '38.2% from Retracement from 1Month High'})
                results.append({'Support / Resistance': '', 'Key Levels': round(high_1m - 0.5 * diff_1m, 2), 
                              'Description': '50% Retracement from 1Month High/Low'})
                results.append({'Support / Resistance': '', 'Key Levels': round(low_1m + 0.382 * diff_1m, 2), 
                              'Description': '38.2% Retracement from 1Month Low'})
        
        # 3 Months / 13 Weeks High/Low - Use last ~65 trading days
        df_3m = df.iloc[-65:] if len(df) >= 65 else df
        if len(df_3m) > 0:
            high_3m = df_3m['High'].max()
            low_3m = df_3m['Low'].min()
            results.append({'Support / Resistance': '3Months High', 'Key Levels': round(high_3m, 2), 'Description': '3 Months High'})
            results.append({'Support / Resistance': '3Months Low', 'Key Levels': round(low_3m, 2), 'Description': '3 Months Low'})
            
            # Fibonacci retracements for 3 months
            diff_3m = high_3m - low_3m
            if diff_3m > 0:
                results.append({'Support / Resistance': '', 'Key Levels': round(high_3m - 0.382 * diff_3m, 2), 
                              'Description': '38.2% from Retracement from 3Months High'})
                results.append({'Support / Resistance': '', 'Key Levels': round(high_3m - 0.5 * diff_3m, 2), 
                              'Description': '50% Retracement from 3Months High/Low'})
                results.append({'Support / Resistance': '', 'Key Levels': round(low_3m + 0.382 * diff_3m, 2), 
                              'Description': '38.2% Retracement from 3 Month Low'})
        
        # 1 Year / 52 Weeks High/Low - Use last ~252 trading days
        df_1y = df.iloc[-252:] if len(df) >= 252 else df
        if len(df_1y) > 0:
            high_1y = df_1y['High'].max()
            low_1y = df_1y['Low'].min()
            results.append({'Support / Resistance': '1Year High', 'Key Levels': round(high_1y, 2), 'Description': '1 Year High'})
            results.append({'Support / Resistance': '1Year Low', 'Key Levels': round(low_1y, 2), 'Description': '1 Year Low'})
            
            # Fibonacci retracements for 1 year
            diff_1y = high_1y - low_1y
            if diff_1y > 0:
                results.append({'Support / Resistance': '', 'Key Levels': round(low_1y + 0.618 * diff_1y, 2), 
                              'Description': '61.8% Retracement from 1Year Low'})
                results.append({'Support / Resistance': '', 'Key Levels': round(low_1y + 0.5 * diff_1y, 2), 
                              'Description': '50% Retracement from 1Year High/Low'})
                results.append({'Support / Resistance': '', 'Key Levels': round(low_1y + 0.382 * diff_1y, 2), 
                              'Description': '38.2% Retracement from 1Year Low'})
    
    # 4. Moving Averages - USE EXISTING calculate_ema() FUNCTION
    if settings['moving_avg']:
        try:
            # Use the existing calculate_ema function from tr_calculations.py
            closes = df['Close'].values
            
            # Calculate EMAs using existing function (same as TR Indicator page)
            ema_9_array = calculate_ema(closes, 9)
            ema_20_array = calculate_ema(closes, 20)
            ema_50_array = calculate_ema(closes, 50)
            
            # Get the last values
            ema_9 = ema_9_array[-1] if len(ema_9_array) > 0 else last_price
            ema_20 = ema_20_array[-1] if len(ema_20_array) > 0 else last_price
            ema_50 = ema_50_array[-1] if len(ema_50_array) > 0 else last_price
            
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_50, 2), 
                           'Description': f'50 {period_str} Exponential Moving Average'})
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_20, 2), 
                           'Description': f'20 {period_str} Exponential Moving Average'})
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_9, 2), 
                           'Description': f'9 {period_str} Exponential Moving Average'})
        except Exception as e:
            # Fallback to pandas if calculate_ema fails
            ema_9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
            ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_50, 2), 
                           'Description': f'50 {period_str} Exponential Moving Average'})
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_20, 2), 
                           'Description': f'20 {period_str} Exponential Moving Average'})
            results.append({'Support / Resistance': '', 'Key Levels': round(ema_9, 2), 
                           'Description': f'9 {period_str} Exponential Moving Average'})
    
    # 5. Standard Deviation
    if settings['std_dev']:
        std_dev = calculate_standard_deviation(df['Close'].values, periods=14)
        
        results.append({'Support / Resistance': 'Price - 3 Standard Deviation Resistanc', 
                       'Key Levels': round(last_price + 3 * std_dev, 2), 
                       'Description': 'Price - 3 Standard Deviation Resistance'})
        results.append({'Support / Resistance': 'Price - 2 Standard Deviation Resistanc', 
                       'Key Levels': round(last_price + 2 * std_dev, 2), 
                       'Description': 'Price - 2 Standard Deviation Resistance'})
        results.append({'Support / Resistance': 'Price - 1 Standard Deviation Resistanc', 
                       'Key Levels': round(last_price + std_dev, 2), 
                       'Description': 'Price - 1 Standard Deviation Resistance'})
        results.append({'Support / Resistance': 'Price - 1 Standard Deviation Support', 
                       'Key Levels': round(last_price - std_dev, 2), 
                       'Description': 'Price - 1 Standard Deviation Support'})
        results.append({'Support / Resistance': 'Price - 2 Standard Deviation Support', 
                       'Key Levels': round(last_price - 2 * std_dev, 2), 
                       'Description': 'Price - 2 Standard Deviation Support'})
        results.append({'Support / Resistance': 'Price - 3 Standard Deviation Support', 
                       'Key Levels': round(last_price - 3 * std_dev, 2), 
                       'Description': 'Price - 3 Standard Deviation Support'})
    
    # 6. RSI Levels
    if settings['rsi']:
        rsi_levels = calculate_rsi_levels(df, last_price)
        for label, value in rsi_levels.items():
            results.append({'Support / Resistance': label.replace('14 Period ', ''), 
                           'Key Levels': round(value, 2), 
                           'Description': label})
    
    # Create DataFrame and sort by price (descending)
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('Key Levels', ascending=False).reset_index(drop=True)
    
    return result_df, stock_name, last_price

def apply_color_coding(df, last_price):
    """Apply color coding similar to Excel output"""
    def color_row(row):
        price = row['Key Levels']
        description = row.get('Description', '')
        
        # Yellow for current price levels
        if 'Last Price' in description or 'Previous Close' in description:
            return ['background-color: #FFFF99'] * len(row)
        # Orange/Pink for resistance (above price)
        elif price > last_price:
            if 'Retracement' in description and 'High' in description:
                return ['background-color: #FFE6CC'] * len(row)
            elif 'RSI' in description:
                return ['background-color: #FFE6CC'] * len(row)
            elif 'Resistance' in description or 'Pivot Point' in description:
                return ['background-color: #FFE6CC'] * len(row)
            elif 'Moving Average' in description:
                return ['background-color: #CCE5FF'] * len(row)
            else:
                return ['background-color: #FFE6CC'] * len(row)
        # Blue for support (below price)
        elif price < last_price:
            if 'Retracement' in description and 'Low' in description:
                return ['background-color: #CCE5FF'] * len(row)
            elif 'RSI' in description:
                return ['background-color: #CCE5FF'] * len(row)
            elif 'Support' in description or 'Low' in description:
                return ['background-color: #CCE5FF'] * len(row)
            elif 'Moving Average' in description:
                return ['background-color: #FFE6CC'] * len(row)
            else:
                return ['background-color: #CCE5FF'] * len(row)
        else:
            return [''] * len(row)
    
    return df.style.apply(color_row, axis=1)

# ==================== MAIN APP ====================

# Title
st.title("📊 Daily Trading Guide")
st.markdown("**Identify Support & Resistance Levels**")

# Input Section
col1, col2 = st.columns([2, 1])

with col1:
    ticker = st.text_input(
        "Enter Stock Ticker",
        value="AAPL",
        help="Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
    ).upper()

with col2:
    timeframe = st.selectbox(
        "Timeframe",
        options=["Daily", "Weekly"],
        index=0
    )

# Settings Section
st.markdown("---")
st.subheader("⚙️ Settings - Select Indicators to Include")

col1, col2, col3 = st.columns(3)

with col1:
    show_pp = st.checkbox("Pivot Points", value=True)
    show_hlc = st.checkbox("High, Low and Close", value=True)

with col2:
    show_highs_lows = st.checkbox("Highs/Lows + Fibonacci", value=True)
    show_ma = st.checkbox("Moving Averages", value=True)

with col3:
    show_std = st.checkbox("Standard Deviation", value=True)
    show_rsi = st.checkbox("RSI", value=True)

# Prepare settings dictionary
settings = {
    'pivot_points': show_pp,
    'hlc': show_hlc,
    'highs_lows': show_highs_lows,
    'moving_avg': show_ma,
    'std_dev': show_std,
    'rsi': show_rsi
}

# Generate Button
st.markdown("---")
if st.button("🔍 Generate Trading Guide", type="primary", use_container_width=True):
    
    if not ticker:
        st.error("❌ Please enter a stock ticker")
    else:
        with st.spinner(f"Generating trading guide for {ticker}..."):
            try:
                result_df, stock_name, last_price = generate_trading_guide(ticker, timeframe, settings)
                
                if result_df is None:
                    st.error(f"❌ {stock_name}")
                else:
                    # Display header
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"### {stock_name} ({ticker})")
                    with col2:
                        st.markdown(f"### Time Frame (Period): {timeframe}")
                    
                    st.markdown(f"**Last Price:** ${last_price:.2f}")
                    
                    # Display the table with color coding
                    st.markdown("---")
                    styled_df = apply_color_coding(result_df, last_price)
                    
                    # Format the Key Levels column to 2 decimals
                    styled_df = styled_df.format({'Key Levels': '{:.2f}'})
                    
                    st.dataframe(
                        styled_df,
                        use_container_width=True,
                        height=600
                    )
                    
                    # Summary statistics
                    st.markdown("---")
                    st.subheader("📊 Summary")
                    
                    resistance_levels = result_df[result_df['Key Levels'] > last_price]
                    support_levels = result_df[result_df['Key Levels'] < last_price]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Levels", len(result_df))
                    with col2:
                        st.metric("Resistance Levels", len(resistance_levels))
                    with col3:
                        st.metric("Support Levels", len(support_levels))
                    
                    # Key turning points
                    st.markdown("---")
                    st.subheader("🎯 Key Turning Points")
                    
                    # Find nearest support and resistance
                    if len(resistance_levels) > 0:
                        nearest_resistance = resistance_levels.iloc[-1]  # Closest above
                        st.markdown(f"**Nearest Resistance:** ${nearest_resistance['Key Levels']:.2f} - {nearest_resistance['Description']}")
                    
                    if len(support_levels) > 0:
                        nearest_support = support_levels.iloc[0]  # Closest below
                        st.markdown(f"**Nearest Support:** ${nearest_support['Key Levels']:.2f} - {nearest_support['Description']}")
                    
                    # Export option
                    st.markdown("---")
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"{ticker}_trading_guide_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"❌ Error generating trading guide: {str(e)}")
                st.exception(e)

# Information section
st.markdown("---")
with st.expander("ℹ️ How to Use This Guide"):
    st.markdown("""
    ### Understanding Support & Resistance Levels
    
    **Color Coding:**
    - 🟡 **Yellow**: Current price levels (Last Price, Previous Close)
    - 🟠 **Orange/Pink**: Resistance levels (above current price)
    - 🔵 **Blue**: Support levels (below current price)
    
    **Types of Levels:**
    
    1. **Pivot Points**: Classic support and resistance levels calculated from previous day/week's high, low, and close
    
    2. **High, Low and Close**: Recent price action levels
    
    3. **Highs/Lows + Fibonacci**: Historical highs/lows with Fibonacci retracement levels (38.2%, 50%, 61.8%)
    
    4. **Moving Averages**: Key EMAs (9, 20, 50 periods) that often act as dynamic support/resistance
    
    5. **Standard Deviation**: Statistical price levels showing potential extreme moves
    
    6. **RSI Levels**: Price levels that would result in specific RSI values (20%, 30%, 50%, 70%, 80%)
    
    ### Trading Strategy:
    - Look for price to react at these levels
    - Multiple levels close together = stronger support/resistance zone
    - Use for setting entry points, stop losses, and profit targets
    """)

st.markdown("---")
st.caption("💡 Tip: Use the 'Settings' section to customize which indicators are included in your guide")
