"""
Pattern Detection Page
Detects 8 major chart patterns in stock price data
"""

import streamlit as st
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pattern_detection import detect_patterns_for_chart
from tr_enhanced import analyze_stock_complete_tr

st.set_page_config(
    page_title="Pattern Detection - MJ Software",
    page_icon="🔺",
    layout="wide"
)

# GLOBAL CSS - Apply to entire page
st.markdown("""
<style>
    /* Make ALL buttons on this page smaller */
    .stButton > button {
        height: 32px !important;
        min-height: 32px !important;
        padding: 4px 12px !important;
        font-size: 12px !important;
    }
    
    /* Compact columns */
    [data-testid="column"] {
        padding: 0px 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# Use tr_enhanced but cache it (TR calculation happens once, then cached)
@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data_cached(ticker, duration_days, api_source):
    """Get stock data with caching - supports both Yahoo and Tiingo"""
    try:
        # Convert "Yahoo Finance" -> "yahoo", "Tiingo API" -> "tiingo"
        api = 'yahoo' if 'yahoo' in api_source.lower() else 'tiingo'
        
        df = analyze_stock_complete_tr(
            ticker=ticker,
            timeframe='daily',
            duration_days=duration_days,
            api_source=api
        )
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def detect_patterns_cached(ticker, duration_days, remove_overlaps, api_source):
    """Cached pattern detection"""
    df = get_stock_data_cached(ticker, duration_days, api_source)
    if df is None or df.empty:
        return None, None
    # Pattern detection only uses price data, ignores TR columns
    patterns = detect_patterns_for_chart(df, remove_overlaps=remove_overlaps)
    return df, patterns
    return detect_patterns_for_chart(df, remove_overlaps=remove_overlaps)

# Page header
st.title("🔺 Pattern Detection")
st.markdown("**Automatically detect chart patterns with confidence scores**")

# Input section
col1, col2 = st.columns([3, 3])

with col1:
    symbol = st.text_input("Stock Symbol", value="AAPL", help="Enter ticker symbol")

with col2:
    timeframe = st.selectbox("Timeframe", ["Daily", "Weekly"], index=0)

# Get API source from session state (set in TR Indicator page sidebar)
api_source = st.session_state.get('api_source', 'Yahoo Finance')

# Time period buttons (like TR Chart)
st.markdown("**Select Duration:**")

# Create buttons in a more compact row
duration_cols = st.columns([1, 1, 1, 1, 1, 1, 1])

duration_options = [
    ("1M", "1 Month", 30),
    ("3M", "3 Months", 90),
    ("6M", "6 Months", 180),
    ("1Y", "1 Year", 365),
    ("2Y", "2 Years", 730),
    ("3Y", "3 Years", 1095),
    ("5Y", "5 Years", 1825)
]

# Initialize duration in session state if not exists
if 'pattern_duration_days' not in st.session_state:
    st.session_state['pattern_duration_days'] = 365
    st.session_state['pattern_duration_label'] = "1 Year"

# Create buttons
for i, (label, full_label, days) in enumerate(duration_options):
    with duration_cols[i]:
        # Check if this is the selected duration
        is_selected = st.session_state.get('pattern_duration_days') == days
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(label, key=f"dur_{label}", type=button_type, use_container_width=True):
            st.session_state['pattern_duration_days'] = days
            st.session_state['pattern_duration_label'] = full_label
            st.rerun()

# Show selected duration
st.caption(f"Selected: **{st.session_state.get('pattern_duration_label', '1 Year')}**")

# Add toggle for showing overlapping patterns
show_all = st.checkbox(
    "Show all patterns (including overlaps)", 
    value=False,
    help="By default, only non-overlapping patterns are shown (highest confidence kept). Enable this to see ALL detected patterns."
)

# Analyze button
if st.button("🔍 Detect Patterns", type="primary", use_container_width=True):
    
    # Get duration from session state
    duration_days = st.session_state.get('pattern_duration_days', 365)
    duration_label = st.session_state.get('pattern_duration_label', '1 Year')
    
    with st.spinner(f"🔄 Analyzing {symbol} for patterns ({duration_label})..."):
        
        try:
            # Use cached pattern detection (includes price data fetch)
            # Note: Timeframe not used - patterns work on daily data
            df, patterns = detect_patterns_cached(
                ticker=symbol,
                duration_days=duration_days,
                remove_overlaps=not show_all,
                api_source=api_source
            )
            
            if df is None or df.empty:
                st.error(f"❌ Could not get data for {symbol}")
                st.stop()
            
            if patterns is None:
                patterns = []
            
            # Store in session state
            st.session_state['pattern_df'] = df
            st.session_state['patterns'] = patterns
            st.session_state['symbol'] = symbol
            st.session_state['show_all'] = show_all
            
            # st.success(f"✅ Found {len(patterns)} patterns (cached: {st.cache_data.cache_info()})")
            st.success(f"✅ Found {len(patterns)} patterns")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

# Display results if available
if 'patterns' in st.session_state and st.session_state['patterns']:
    
    patterns = st.session_state['patterns']
    df = st.session_state['pattern_df']
    symbol = st.session_state['symbol']
    
    # Summary section
    st.markdown("---")
    st.subheader(f"📊 Results for {symbol}")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    bullish = len([p for p in patterns if p['direction'] == 'bullish'])
    bearish = len([p for p in patterns if p['direction'] == 'bearish'])
    neutral = len([p for p in patterns if p['direction'] == 'neutral'])
    avg_conf = sum(p['confidence'] for p in patterns) / len(patterns) if patterns else 0
    
    col1.metric("Total Patterns", len(patterns))
    col2.metric("Bullish 🟢", bullish)
    col3.metric("Bearish 🔴", bearish)
    col4.metric("Avg Confidence", f"{avg_conf:.1f}%")
    
    # Info message based on mode
    if st.session_state.get('show_all', False):
        st.warning("⚠️ **Showing ALL patterns including overlaps.** Chart may be confusing. Uncheck the box above to show only non-overlapping patterns.")
    else:
        st.info("ℹ️ **Smart Filtering:** Non-overlapping patterns only. **Recent patterns prioritized** over older ones (then by confidence). Pattern sections shown in **colored lines**: 🟢 Green (Bullish), 🔴 Red (Bearish), 🟠 Orange (Neutral).")
    
    # Chart with patterns
    st.markdown("### 📈 Price Chart with Pattern Annotations")
    
    fig = go.Figure()
    
    # First, add the base price line (gray for non-pattern areas)
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='Price',
        line=dict(color='lightgray', width=1),
        showlegend=False
    ))
    
    # Add colored price lines for each pattern
    for i, pattern in enumerate(patterns):
        start_idx = pattern['start_idx']
        end_idx = pattern['end_idx']
        
        # Get pattern section
        section_dates = df['Date'].iloc[start_idx:end_idx+1]
        section_prices = df['Close'].iloc[start_idx:end_idx+1]
        
        # Color based on direction
        if pattern['direction'] == 'bullish':
            line_color = 'green'
            fill_color = 'rgba(0, 255, 0, 0.1)'
            border_color = 'green'
            curve_color = 'blue'  # Contrasting color for curve
        elif pattern['direction'] == 'bearish':
            line_color = 'red'
            fill_color = 'rgba(255, 0, 0, 0.1)'
            border_color = 'red'
            curve_color = 'darkmagenta'  # Contrasting color for curve
        else:
            line_color = 'orange'
            fill_color = 'rgba(255, 165, 0, 0.1)'
            border_color = 'orange'
            curve_color = 'brown'  # Contrasting color for curve
        
        # Add colored price line for this pattern
        fig.add_trace(go.Scatter(
            x=section_dates,
            y=section_prices,
            mode='lines',
            name=f"{pattern['type']}",
            line=dict(color=line_color, width=3),
            hovertemplate=f"<b>{pattern['type']}</b><br>%{{y:.2f}}<extra></extra>"
        ))
        
        # ============================================================
        # ADD SMOOTH CURVE FOR THIS PATTERN
        # ============================================================
        key_points = pattern.get('key_points', [])
        pattern_type = pattern['type']
        
        if len(key_points) >= 3 and pattern_type in ['Cup & Handle', 'Double Bottom', 'Double Top', 'Head & Shoulders', 'Inverse Head & Shoulders']:
            try:
                # Extract prices from key_points (each is (date, price) tuple)
                kp_prices = [kp[1] for kp in key_points]
                
                # Generate smooth curve points based on pattern type
                num_curve_points = 30
                
                if pattern_type == 'Cup & Handle':
                    # U-shape curve WITH HANDLE
                    # Cup takes 85% of the pattern, handle takes 15%
                    cup_points = int(num_curve_points * 0.85)
                    handle_points = num_curve_points - cup_points
                    
                    left_p, bottom_p, right_p = kp_prices[0], kp_prices[1], kp_prices[2]
                    
                    # Cup portion (U-shape)
                    t_cup = np.linspace(0, 1, cup_points)
                    cup_y = left_p * (1-t_cup)**2 + 2 * bottom_p * (1-t_cup) * t_cup + right_p * t_cup**2
                    # Adjust to make it more U-shaped (deeper in middle)
                    mid_adjustment = -abs(left_p - bottom_p) * 0.3 * np.sin(np.pi * t_cup)
                    cup_y = cup_y + mid_adjustment
                    
                    # Handle portion (downward drift only - no recovery)
                    handle_top = right_p
                    handle_bottom = right_p * 0.93  # 7% pullback for handle
                    t_handle = np.linspace(0, 1, handle_points)
                    # Downward slope only
                    handle_y = handle_top - (handle_top - handle_bottom) * t_handle
                    
                    # Combine cup and handle
                    curve_y = np.concatenate([cup_y, handle_y])
                    num_curve_points = len(curve_y)  # Update for combined length
                
                elif pattern_type == 'Double Bottom':
                    # W-shape curve
                    t = np.linspace(0, 1, num_curve_points)
                    trough1, peak, trough2 = kp_prices[0], kp_prices[1], kp_prices[2]
                    # Two parabolas joined
                    curve_y = np.where(t < 0.5,
                        trough1 + (peak - trough1) * (2*t)**2,  # First V
                        peak - (peak - trough2) * (2*(t-0.5))**2)  # Second V (inverted approach)
                    # Smooth W shape using sine
                    curve_y = peak - (peak - min(trough1, trough2)) * np.abs(np.sin(2 * np.pi * t))
                
                elif pattern_type == 'Double Top':
                    # M-shape curve (inverted W)
                    t = np.linspace(0, 1, num_curve_points)
                    peak1, trough, peak2 = kp_prices[0], kp_prices[1], kp_prices[2]
                    # M shape using sine
                    curve_y = trough + (max(peak1, peak2) - trough) * np.abs(np.sin(2 * np.pi * t))
                
                elif pattern_type in ['Head & Shoulders', 'Inverse Head & Shoulders']:
                    # 3-peak or 3-trough shape
                    t = np.linspace(0, 1, num_curve_points)
                    left_p, head_p, right_p = kp_prices[0], kp_prices[1], kp_prices[2]
                    neckline = (left_p + right_p) / 2
                    
                    if pattern_type == 'Head & Shoulders':
                        # Peaks up from neckline
                        curve_y = neckline + np.abs(np.sin(3 * np.pi * t)) * (head_p - neckline)
                        # Make middle peak higher
                        middle_boost = np.exp(-((t - 0.5) ** 2) / 0.05) * (head_p - left_p) * 0.5
                        curve_y = curve_y + middle_boost
                    else:
                        # Troughs down from neckline
                        curve_y = neckline - np.abs(np.sin(3 * np.pi * t)) * (neckline - head_p)
                        # Make middle trough deeper
                        middle_dip = np.exp(-((t - 0.5) ** 2) / 0.05) * (left_p - head_p) * 0.5
                        curve_y = curve_y - middle_dip
                
                # Generate x coordinates (dates)
                curve_indices = np.linspace(start_idx, end_idx, num_curve_points).astype(int)
                curve_indices = np.clip(curve_indices, 0, len(df) - 1)
                curve_dates = df['Date'].iloc[curve_indices].values
                
                # Add the smooth curve trace
                fig.add_trace(go.Scatter(
                    x=curve_dates,
                    y=curve_y,
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
            except Exception as e:
                print(f"  Curve error for {pattern_type}: {e}")
        
        # Add trendlines for Triangle patterns
        elif 'Triangle' in pattern_type:
            try:
                # Get high and low points for trendlines
                section_high = section_prices.max()
                section_low = section_prices.min()
                
                # Find highs and lows at start and end of pattern
                first_third = section_prices.iloc[:len(section_prices)//3]
                last_third = section_prices.iloc[-len(section_prices)//3:]
                
                high_start = first_third.max()
                high_end = last_third.max()
                low_start = first_third.min()
                low_end = last_third.min()
                
                start_date = section_dates.iloc[0]
                end_date = section_dates.iloc[-1]
                
                # Upper trendline
                fig.add_trace(go.Scatter(
                    x=[start_date, end_date],
                    y=[high_start, high_end],
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Lower trendline
                fig.add_trace(go.Scatter(
                    x=[start_date, end_date],
                    y=[low_start, low_end],
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
            except Exception as e:
                print(f"  Trendline error for {pattern_type}: {e}")
        
        # Add horizontal lines for Flat Base only
        elif pattern_type == 'Flat Base':
            try:
                start_date = section_dates.iloc[0]
                end_date = section_dates.iloc[-1]
                
                # Get resistance and support from pattern data
                resistance = pattern.get('resistance', section_prices.max())
                support = pattern.get('support', section_prices.min())
                
                # Top horizontal line (resistance)
                fig.add_trace(go.Scatter(
                    x=[start_date, end_date],
                    y=[resistance, resistance],
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Bottom horizontal line (support)
                fig.add_trace(go.Scatter(
                    x=[start_date, end_date],
                    y=[support, support],
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dash'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
            except Exception as e:
                print(f"  Flat Base lines error: {e}")
        
        # Add curves for Saucer Base and Ascending Base
        elif pattern_type in ['Saucer Base', 'Ascending Base']:
            try:
                key_points = pattern.get('key_points', [])
                num_curve_points = 30
                
                if pattern_type == 'Saucer Base' and len(key_points) >= 3:
                    # Shallow U-shape curve
                    kp_prices = [kp[1] for kp in key_points]
                    t = np.linspace(0, 1, num_curve_points)
                    left_p, bottom_p, right_p = kp_prices[0], kp_prices[1], kp_prices[2]
                    # Cosine curve for gentle saucer shape
                    curve_y = bottom_p + (max(left_p, right_p) - bottom_p) * (1 - np.cos(np.pi * t)) / 2
                    
                elif pattern_type == 'Ascending Base' and len(key_points) >= 3:
                    # Stair-step pattern with higher lows
                    kp_prices = [kp[1] for kp in key_points]
                    t = np.linspace(0, 1, num_curve_points)
                    min_p = min(kp_prices)
                    max_p = max(kp_prices)
                    num_steps = len(kp_prices)
                    # Rising line with pullback waves
                    curve_y = min_p + (max_p - min_p) * t
                    pullback_wave = -0.1 * (max_p - min_p) * np.abs(np.sin(num_steps * np.pi * t))
                    curve_y = curve_y + pullback_wave
                else:
                    continue
                
                # Generate x coordinates (dates)
                curve_indices = np.linspace(start_idx, end_idx, num_curve_points).astype(int)
                curve_indices = np.clip(curve_indices, 0, len(df) - 1)
                curve_dates = df['Date'].iloc[curve_indices].values
                
                # Add the curve
                fig.add_trace(go.Scatter(
                    x=curve_dates,
                    y=curve_y,
                    mode='lines',
                    line=dict(color=curve_color, width=2, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
            except Exception as e:
                print(f"  {pattern_type} curve error: {e}")
        
        # Get price range for rectangle
        y_min = section_prices.min() * 0.98
        y_max = section_prices.max() * 1.02
        
        # Rectangle background - HIDDEN (patterns now use curves/lines instead)
        # To re-enable: uncomment the code below
        # fig.add_shape(
        #     type="rect",
        #     x0=section_dates.iloc[0],
        #     x1=section_dates.iloc[-1],
        #     y0=y_min,
        #     y1=y_max,
        #     fillcolor=fill_color,
        #     line=dict(color=border_color, width=2, dash='dash'),
        #     layer='below'
        # )
        
        # Add annotation with pattern name and confidence
        fig.add_annotation(
            x=section_dates.iloc[0],
            y=y_max,
            text=f"<b>{pattern['type']}</b><br>{pattern['confidence']}% confidence",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=border_color,
            ax=-40,
            ay=-40,
            font=dict(size=10, color=border_color),
            bgcolor='white',
            bordercolor=border_color,
            borderwidth=2,
            xanchor='left',
            yanchor='bottom'
        )
    
    fig.update_layout(
        height=600,
        hovermode='x unified',
        showlegend=True,
        xaxis_title="Date",
        yaxis_title="Price ($)"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed pattern list
    st.markdown("### 📋 Detected Patterns (Details)")
    
    for i, pattern in enumerate(patterns, 1):
        
        # Direction emoji
        if pattern['direction'] == 'bullish':
            direction_emoji = "🟢 Bullish"
        elif pattern['direction'] == 'bearish':
            direction_emoji = "🔴 Bearish"
        else:
            direction_emoji = "⚪ Neutral"
        
        with st.expander(f"**{i}. {pattern['type']}** - {direction_emoji} ({pattern['confidence']}% confidence)"):
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Convert dates to string if they aren't already
                start_date_str = str(pattern['start_date'])[:10] if isinstance(pattern['start_date'], (str, pd.Timestamp)) else pattern['start_date'].strftime('%Y-%m-%d')
                end_date_str = str(pattern['end_date'])[:10] if isinstance(pattern['end_date'], (str, pd.Timestamp)) else pattern['end_date'].strftime('%Y-%m-%d')
                
                st.markdown(f"**Detected:** {start_date_str}")
                st.markdown(f"**Period:** {start_date_str} to {end_date_str}")
                st.markdown(f"**Confidence:** {pattern['confidence']}%")
            
            with col2:
                if pattern.get('target_price'):
                    st.markdown(f"**Target Price:** ${pattern['target_price']:.2f}")
                
                current_price = df.iloc[-1]['Close']
                if pattern.get('target_price'):
                    potential = ((pattern['target_price'] - current_price) / current_price) * 100
                    st.markdown(f"**Potential Move:** {potential:+.1f}%")
            
            # Pattern-specific details
            if 'neckline' in pattern:
                st.markdown(f"**Neckline:** ${pattern['neckline']:.2f}")
            if 'support' in pattern:
                st.markdown(f"**Support:** ${pattern['support']:.2f}")
            if 'resistance' in pattern:
                st.markdown(f"**Resistance:** ${pattern['resistance']:.2f}")
    
    # Export button
    st.markdown("---")
    if st.button("📥 Export Pattern Data"):
        # Create export dataframe
        export_data = []
        for p in patterns:
            export_data.append({
                'Pattern': p['type'],
                'Direction': p['direction'],
                'Confidence': p['confidence'],
                'Start Date': p['start_date'],
                'End Date': p['end_date'],
                'Target Price': p.get('target_price', '')
            })
        
        export_df = pd.DataFrame(export_data)
        csv = export_df.to_csv(index=False)
        
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{symbol}_patterns.csv",
            mime="text/csv"
        )

elif 'patterns' in st.session_state and not st.session_state['patterns']:
    st.info("ℹ️ No patterns detected for this stock and time period.")
    
else:
    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 📚 How to Use:
    
    1. **Enter a stock symbol** (e.g., AAPL, GOOGL, NVDA)
    2. **Select timeframe** (Daily or Weekly)
    3. **Choose duration** (6 months to 5 years)
    4. **Click "Detect Patterns"**
    
    ### 🔺 Patterns Detected (11 Total):
    
    **Bullish Patterns:**
    - Inverse Head & Shoulders
    - Double Bottom
    - Ascending Triangle
    - Cup & Handle
    - Flat Base *(NEW)*
    - Saucer Base *(NEW)*
    - Ascending Base *(NEW)*
    
    **Bearish Patterns:**
    - Head & Shoulders
    - Double Top
    - Descending Triangle
    
    **Neutral Patterns:**
    - Symmetrical Triangle
    
    ### 💡 Understanding Results:
    
    - **Confidence Score:** Higher = More reliable pattern
    - **Target Price:** Expected price if pattern completes
    - **Pattern Boxes:** Green (bullish), Red (bearish), Orange (neutral)
    - **Smooth Curves:** Blue/purple dotted lines show idealized pattern shape
    """)



# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
