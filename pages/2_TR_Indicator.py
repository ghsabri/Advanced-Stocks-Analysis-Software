"""
Stock Analysis Page - SIMPLIFIED VERSION
Works around import issues by loading modules directly
"""

import streamlit as st
import sys
import os
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="TR Indicator - MJ Software",
    page_icon="📊",
    layout="wide"
)

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# ML Import
ML_AVAILABLE = False
try:
    from ml_tr_predictor_hybrid import predict_confidence
    ML_AVAILABLE = True
except ImportError:
    pass

# Header
st.title("📊 TR Indicator Chart")
st.markdown("**Technical Rating Indicator with Buy/Stop Signals, EMA Lines, and Stage Analysis**")
st.markdown("---")

# Note: TR modules will be imported only when needed (inside analyze button)
# This prevents slow imports when other pages are accessed

# Sidebar - API Source Toggle (same as Home page)
with st.sidebar:
    st.markdown("### ⚙️ Global Settings")
    
    # Initialize session state if not exists
    if 'api_source' not in st.session_state:
        st.session_state['api_source'] = 'Yahoo Finance'
    
    # Currently only Yahoo Finance is enabled
    st.session_state['api_source'] = 'Yahoo Finance'
    
    st.markdown("---")
    st.info(f"📡 Data Source: **Yahoo Finance**")
    
    st.markdown("---")
    
    duration_option = st.selectbox(
        "Analysis Duration",
        ["3 Months", "6 Months", "1 Year", "3 Years", "5 Years"],
        index=4,  # Default to 5 Years
        help="Fetches historical data - 5 years recommended for full analysis"
    )
    
    duration_map = {
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365,
        "3 Years": 1095,
        "5 Years": 1825
    }
    duration_days = duration_map[duration_option]

# Stock input section

# Check for sync from Stocks Analysis page
synced_symbol = ""
synced_tf = "daily"
synced_timeframe_idx = 0
should_auto_analyze = False

if st.session_state.get('auto_sync_enabled', False) and st.session_state.get('sync_tr_indicator', False):
    if st.session_state.get('synced_symbol', ''):
        synced_symbol = st.session_state.get('synced_symbol', '')
        synced_tf = st.session_state.get('synced_timeframe', 'daily')
        synced_timeframe_idx = 0 if synced_tf == 'daily' else 1
        
        # Check if this is a NEW sync (symbol changed)
        last_synced = st.session_state.get('tr_last_synced', '')
        current_sync_key = f"{synced_symbol}_{synced_tf}"
        
        if current_sync_key != last_synced:
            st.session_state['tr_last_synced'] = current_sync_key
            should_auto_analyze = True

# Determine default symbol for input
if synced_symbol:
    default_symbol = synced_symbol
elif 'tr_last_analyzed_symbol' in st.session_state:
    default_symbol = st.session_state['tr_last_analyzed_symbol']
else:
    default_symbol = ""

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    symbol = st.text_input(
        "Enter Stock Symbol",
        value=default_symbol,
        placeholder="e.g., AAPL, GOOGL, TSLA",
        help="Enter a valid stock ticker symbol"
    ).upper()

with col2:
    # Determine default timeframe
    if synced_symbol:
        tf_idx = synced_timeframe_idx
    elif 'tr_last_analyzed_timeframe' in st.session_state:
        tf_idx = 0 if st.session_state['tr_last_analyzed_timeframe'] == 'Daily' else 1
    else:
        tf_idx = 0
    
    timeframe = st.selectbox(
        "Timeframe",
        ["Daily", "Weekly"],
        index=tf_idx,
        help="Select chart timeframe"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_button = st.button("🔍 Analyze Stock", type="primary", use_container_width=True)

# Show sync indicator if synced
if synced_symbol:
    st.caption(f"🔗 Synced from Stocks Analysis ({synced_symbol}, {synced_tf.capitalize()})")

# Auto-analyze if:
# 1. New sync from Stocks Analysis, OR
# 2. Returning to page with previously analyzed symbol (re-run from cache)
if should_auto_analyze and symbol:
    analyze_button = True
elif not analyze_button:
    # Check if returning with same symbol that was last analyzed
    last_symbol = st.session_state.get('tr_last_analyzed_symbol', '')
    last_tf = st.session_state.get('tr_last_analyzed_timeframe', '')
    if last_symbol and last_symbol.upper() == symbol.upper() and last_tf == timeframe:
        analyze_button = True

st.markdown("---")

# Main analysis area
if analyze_button and symbol:
    
    # LAZY IMPORT: Only import TR modules when analyze button is clicked
    # This prevents slow page loads when accessing other pages
    TR_AVAILABLE = False
    error_message = ""
    
    try:
        with st.spinner("Loading TR analysis modules..."):
            # Import individual modules only when needed
            import stock_data_formatter
            import tr_indicator
            import tr_enhanced  # Enhanced version with arrows and checkmarks
            import tr_analyzer
            import tr_chart_plotter_plotly  # Plotly TR Chart visualization (INTERACTIVE!)
            
            TR_AVAILABLE = True
        
    except Exception as e:
        error_message = str(e)
        st.error(f"⚠️ Could not import TR modules: {e}")
        st.info(f"Looking for modules in: {src_path}")
        st.info("Make sure these files exist in your src folder:")
        st.code("""
        - stock_data_formatter.py
        - tr_indicator.py
        - tr_enhanced.py  ← MAKE SURE THIS EXISTS!
        - tr_analyzer.py
        """)
        st.stop()
    
    if not TR_AVAILABLE:
        st.error("❌ TR Indicator modules not available.")
        st.error(f"Error: {error_message}")
        st.info("""
        **To fix this:**
        1. Make sure these files exist in `C:\\Work\\Stock Analysis Project\\mj-stocks-analysis\\src\\`:
           - stock_data_formatter.py
           - tr_indicator.py
           - tr_analyzer.py
        
        2. Restart Streamlit (Ctrl+C, then `streamlit run app.py`)
        """)
        st.stop()
    
    # Show loading spinner
    with st.spinner(f"🔄 Analyzing {symbol}..."):
        
        try:
            # Call TR ENHANCED analyzer for full analysis with buy points and stop loss
            result_df = tr_enhanced.analyze_stock_complete_tr(
                ticker=symbol,
                timeframe=timeframe.lower(),
                duration_days=duration_days
            )
            
            if result_df is None:
                st.error(f"❌ Could not analyze {symbol}. Please check the symbol and try again.")
                st.stop()
            
            # Convert to result format expected by the page
            latest_row = result_df.iloc[-1]
            
            # Handle Date column (could be datetime or string)
            try:
                if pd.notna(latest_row['Date']):
                    if isinstance(latest_row['Date'], str):
                        latest_date = latest_row['Date']
                    else:
                        latest_date = str(latest_row['Date'].date())
                else:
                    latest_date = 'N/A'
            except:
                latest_date = str(latest_row['Date'])
            
            result = {
                'latest_date': latest_date,
                'latest_close': latest_row['Close'],
                'latest_tr_status': latest_row['TR_Status'],
                'current_status': latest_row['TR_Status'],
                'current_price': latest_row['Close'],
                'signal_counts': result_df['TR_Status'].value_counts().to_dict(),
                'recent_signals': result_df.tail(10)[['Date', 'Close', 'TR_Status']].copy(),
                'full_data': result_df
            }
            
            # Auto-save CSV file with FULL enhanced TR data
            try:
                # Make sure data folder exists
                import os
                data_folder = 'data'
                if not os.path.exists(data_folder):
                    os.makedirs(data_folder)
                
                csv_filename = tr_enhanced.save_tr_results(result_df)
                st.info(f"💾 Full analysis saved to: `{csv_filename}`")
            except Exception as save_error:
                st.warning(f"⚠️ Could not save CSV file: {save_error}")
            
            # Display results
            st.success(f"✅ Analysis complete for {symbol}!")
            
            # Store what was analyzed (for re-display on return)
            st.session_state['tr_last_analyzed_symbol'] = symbol
            st.session_state['tr_last_analyzed_timeframe'] = timeframe
            
            # Current Status Card
            st.markdown("### 🎯 Current TR Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Date", result['latest_date'])
            
            with col2:
                st.metric("Price", f"${result['latest_close']:.2f}")
            
            with col3:
                status = result['latest_tr_status']
                
                # Use enhanced status but clean it up
                has_enhanced = False
                if 'TR_Status_Enhanced' in result.get('full_data', pd.DataFrame()).columns:
                    enhanced_status = result['full_data'].iloc[-1]['TR_Status_Enhanced']
                    
                    # Remove ONLY the ENTRY/EXIT action words, keep * and ✓
                    display_status = (enhanced_status
                                     .replace('✅ ENTRY', '')  # Remove entry indicator
                                     .replace('🔴 EXIT', '')   # Remove exit indicator
                                     .replace('ENTRY', '')     # Remove text entry
                                     .replace('EXIT', '')      # Remove text exit
                                     # DO NOT remove * or ✓ - these are useful!
                                     .replace('  ', ' ')       # Clean double spaces
                                     .strip())
                    has_enhanced = True
                else:
                    display_status = status
                
                # Color-code the status
                if "Strong Buy" in display_status:
                    st.success(f"🟢 {display_status}")
                    if not has_enhanced:  # Only show stage if NOT using enhanced status
                        st.caption("Stage 3 Uptrend")
                elif "Buy" in display_status and "Strong" not in display_status:
                    st.success(f"🟢 {display_status}")
                    if not has_enhanced:
                        st.caption("Stage 2 Uptrend")
                elif "Neutral Buy" in display_status:
                    st.warning(f"🟡 {display_status}")
                    if not has_enhanced:
                        st.caption("Stage 1 Uptrend")
                elif "Neutral Sell" in display_status:
                    st.warning(f"🟡 {display_status}")
                    if not has_enhanced:
                        st.caption("Stage 1 Downtrend")
                elif "Sell" in display_status and "Strong" not in display_status:
                    st.error(f"🔴 {display_status}")
                    if not has_enhanced:
                        st.caption("Stage 2 Downtrend")
                elif "Strong Sell" in display_status:
                    st.error(f"🔴 {display_status}")
                    if not has_enhanced:
                        st.caption("Stage 3 Downtrend")
                else:
                    st.info(f"⚪ {display_status}")
            
            st.markdown("---")
            
            # ML Confidence Score
            if ML_AVAILABLE:
                st.markdown("### 🤖 Machine Learning Confidence Score")
                try:
                    tr_stage_map = {'Strong Buy': 1, 'Buy': 2, 'Neutral Buy': 3, 'Neutral': 3, 'Neutral Sell': 4, 'Sell': 5, 'Strong Sell': 6}
                    latest = result['full_data'].iloc[-1]
                    
                    signal_data = {
                        'tr_stage': tr_stage_map.get(result['current_status'], 3),
                        'entry_price': float(latest['Close']),
                        'ema_3': float(latest['EMA_3']),
                        'ema_9': float(latest['EMA_9']),
                        'ema_20': float(latest['EMA_20']),
                        'ema_34': float(latest['EMA_34']),
                        'ppo_value': float(latest['PPO_Line']),
                        'ppo_histogram': float(latest['PPO_Histogram']),
                        'pmo_value': float(latest['PMO_Line']),
                        'quality_level': 1,
                        'has_buy_point': 1 if '🔵BUY' in str(result['current_status']) else 0,
                        'has_uptrend': 1 if '↑' in str(result['current_status']) else 0,
                        'has_rs_chaikin': 1 if '*' in str(result['current_status']) else 0
                    }
                    
                    prediction = predict_confidence(signal_data, timeframe=timeframe)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        conf = prediction['confidence']
                        emoji = "🔥" if conf >= 70 else "✅" if conf >= 60 else "⚠️" if conf >= 50 else "❌"
                        st.metric(f"{emoji} ML Confidence", f"{conf:.1f}%", prediction['confidence_level'])
                    with col2:
                        st.metric("🎯 Target", f"{prediction['target']}%", timeframe)
                    with col3:
                        quality = prediction['quality_tier'].split('(')[0].strip()
                        emoji = "⭐" if prediction['is_elite'] else "📊"
                        st.metric(f"{emoji} Quality", quality)
                    
                    if prediction['is_elite']:
                        st.warning("⭐ **ELITE SIGNAL!** Use 10-15% targets instead of 5%")
                    
                    # Display Performance Metrics
                    metrics = prediction.get('performance_metrics')
                    if metrics:
                        st.markdown("#### 📈 Strategy Performance Metrics")
                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            pf = metrics['profit_factor']
                            st.metric(
                                f"{pf['emoji']} Profit Factor", 
                                pf['display'],
                                pf['rating'],
                                help=pf['help']
                            )
                        with mcol2:
                            exp = metrics['expectancy']
                            st.metric(
                                f"{exp['emoji']} Expectancy", 
                                exp['display'],
                                exp['rating'],
                                help=exp['help']
                            )
                        with mcol3:
                            ar = metrics['annual_return']
                            st.metric(
                                f"{ar['emoji']} Annual Return", 
                                ar['display'],
                                ar['rating'],
                                help=ar['help']
                            )
                        
                        # Show data source note
                        if metrics.get('data_source') == 'estimated':
                            st.caption(f"📊 Based on {metrics['total_trades']:,} training samples | Win Rate: {metrics['win_rate']}% | *Estimated metrics*")
                        else:
                            st.caption(f"📊 Based on {metrics['total_trades']:,} historical trades | Win Rate: {metrics['win_rate']}%")
                
                except Exception as e:
                    st.error(f"ML Error: {e}")
            
            st.markdown("---")
            
            # Tabbed interface with TR Chart
            tab1, tab2, tab3, tab4 = st.tabs(["📈 TR Chart", "📊 Signal Distribution", "📅 Recent Signals", "📋 Full Data"])
            
            with tab1:
                st.markdown("### 📈 TR Indicator Chart")
                st.caption("Interactive chart - zoom, pan, and hover for details!")
                
                try:
                    # Generate ENHANCED interactive Plotly TR chart with buy points and stop loss
                    with st.spinner("🎨 Generating enhanced TR chart..."):
                        fig = tr_chart_plotter_plotly.plot_tr_with_buy_zones_plotly(
                            df=result['full_data'],
                            ticker=symbol,
                            timeframe=timeframe,
                            figsize=(1400, 800)  # Slightly taller for annotations
                        )
                        
                        # Display interactive Plotly chart in Streamlit
                        # Config: Y-axis rescales automatically when clicking time buttons
                        st.plotly_chart(
                            fig, 
                            use_container_width=True,
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToAdd': ['autoscale'],
                                'responsive': True
                            }
                        )
                        
                        st.markdown("""
                        **💡 Interactive Features:**
                        - **Time Periods**: Click buttons (1M, 3M, 6M, 1Y, 3Y, 5Y, ALL) to change time range
                        - **Auto-Scale Y-Axis**: After clicking a time button, click the **🔄 Autoscale** button in the toolbar (top-right)
                        - **Or**: Double-click anywhere on the chart to reset both axes
                        - **Hover** over any point to see exact price, date, and TR status
                        - **Zoom** by dragging a box on the chart
                        - **Pan** by clicking and dragging
                        - **Double-click** to reset zoom
                        - **Click legend items** to show/hide elements
                        
                        **Chart Legend:**
                        - **Dark Green Bands** = Stage 3 Uptrend (Strong Buy)
                        - **Light Green Bands** = Stage 2 Uptrend (Buy)
                        - **Orange Bands** = Stage 3 Downtrend (Strong Sell)
                        - **Light Yellow Bands** = Stage 2 Downtrend (Sell)
                        - **Green Triangles ▲** = Stage 1 Uptrend Entry
                        - **Red Diamonds ◆** = Stage 1 Downtrend Entry
                        - **Black Dashed Lines** = Suggested Buy Points
                        - **Red Dashed Lines** = Stop Loss Levels
                        - **Blue Annotations** = Detected Patterns
                        """)
                        
                except Exception as chart_error:
                    st.error(f"⚠️ Could not generate TR chart: {chart_error}")
                    st.info("The analysis data is available in other tabs.")
                    with st.expander("Show error details"):
                        st.exception(chart_error)
            
            with tab2:
                st.markdown("### Signal Distribution")
                signal_counts = result['signal_counts']
                signal_order = ["Strong Buy", "Buy", "Neutral Buy", "Neutral", "Neutral Sell", "Sell", "Strong Sell"]
                
                for signal in signal_order:
                    count = signal_counts.get(signal, 0)
                    if count > 0:
                        total_days = len(result['full_data'])
                        percentage = (count / total_days) * 100
                        st.write(f"**{signal}**: {count} days ({percentage:.1f}%)")
                        st.progress(percentage / 100)
            
            with tab2:
                st.markdown("### Recent Signals (Last 10 Days)")
                recent_df = result['recent_signals'].copy()
                
                def get_emoji(status):
                    if "Strong Buy" in status:
                        return "🟢"
                    elif "Buy" in status:
                        return "🟢"
                    elif "Neutral Buy" in status:
                        return "🟡"
                    elif "Neutral Sell" in status:
                        return "🟡"
                    elif "Sell" in status:
                        return "🔴"
                    else:
                        return "⚪"
                
                recent_df['Signal'] = recent_df['TR_Status'].apply(get_emoji)
                recent_df = recent_df[['Date', 'Close', 'Signal', 'TR_Status']]
                recent_df['Close'] = recent_df['Close'].apply(lambda x: f"${x:.2f}")
                
                st.dataframe(recent_df, use_container_width=True, hide_index=True)
            
            with tab4:
                st.markdown("### Complete Analysis Data")
                st.caption(f"Showing {len(result['full_data'])} data points")
                
                display_df = result['full_data'][[
                    'Date', 'Close', 'TR_Status', 
                    'EMA_3', 'EMA_9', 'EMA_20', 'EMA_34'
                ]].tail(50)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                csv = result['full_data'].to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Data (CSV)",
                    data=csv,
                    file_name=f"{symbol}_{timeframe}_TR_Analysis.csv",
                    mime="text/csv"
                )
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 View Charts", use_container_width=True):
                    st.info("📈 Chart visualization coming soon!")
            
            with col2:
                if st.button("➕ Add to Watchlist", use_container_width=True):
                    st.info("👁️ Watchlist feature coming soon!")
            
            with col3:
                if st.button("🔔 Set Alert", use_container_width=True):
                    st.info("🔔 Alert feature coming soon!")
        
        except Exception as e:
            st.error(f"❌ Error analyzing {symbol}: {str(e)}")
            with st.expander("Show full error"):
                st.exception(e)

elif analyze_button and not symbol:
    st.warning("⚠️ Please enter a stock symbol")

else:
    # Welcome message
    st.info("""
    ### 👋 Welcome to Stock Analysis
    
    Enter a stock symbol above to get started with:
    - **TR Indicator Analysis**: Our proprietary trend recognition algorithm
    - **6-Stage Classification**: Strong Buy, Buy, Neutral Buy, Neutral Sell, Sell, Strong Sell
    - **Signal Distribution**: See how the stock has performed over time
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Quick Examples")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🟢 Strong Buy**
        - Stage 3 Uptrend
        """)
    
    with col2:
        st.markdown("""
        **🟡 Neutral**
        - Mixed signals
        """)
    
    with col3:
        st.markdown("""
        **🔴 Sell**
        - Stage 2 Downtrend
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <small>Stock Analysis Page with TR Indicator | Week 4-5 Development</small>
</div>
""", unsafe_allow_html=True)


# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
