"""
Streamlit TR Indicator Page - ML Confidence Integration
========================================================

This module shows how to integrate ML confidence predictions
into your existing TR Indicator Streamlit page.

Copy the relevant functions into your tr_indicator.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Import your ML predictor
from ml_tr_predictor_hybrid import predict_confidence

# ============================================================================
# MAIN ML CONFIDENCE DISPLAY COMPONENT
# ============================================================================

def display_ml_confidence(signal_data, timeframe='Daily'):
    """
    Display ML confidence with context-aware messaging
    
    Parameters:
    -----------
    signal_data : dict
        All the signal features needed for prediction
    timeframe : str
        'Daily' or 'Weekly'
    """
    
    # Get ML prediction
    try:
        prediction = predict_confidence(signal_data, timeframe=timeframe)
    except Exception as e:
        st.error(f"ML Prediction Error: {e}")
        return
    
    confidence = prediction['confidence']
    is_elite = prediction['is_elite']
    quality_tier = prediction['quality_tier']
    
    # ========================================================================
    # SECTION 1: MAIN CONFIDENCE DISPLAY
    # ========================================================================
    
    st.markdown("---")
    st.subheader("🤖 Machine Learning Confidence Score")
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Confidence score with color coding
        if confidence >= 70:
            delta_color = "normal"
            icon = "🔥"
        elif confidence >= 60:
            delta_color = "normal"
            icon = "✅"
        elif confidence >= 50:
            delta_color = "off"
            icon = "⚠️"
        else:
            delta_color = "inverse"
            icon = "❌"
        
        st.metric(
            label=f"{icon} Confidence",
            value=f"{confidence:.1f}%",
            delta=prediction['confidence_level'],
            delta_color=delta_color
        )
    
    with col2:
        # Target
        target = prediction['target']
        st.metric(
            label="🎯 Target",
            value=f"{target}%",
            delta=timeframe
        )
    
    with col3:
        # Quality Tier
        if is_elite:
            tier_icon = "⭐"
        elif "Premium" in quality_tier:
            tier_icon = "🏆"
        elif "Good" in quality_tier:
            tier_icon = "✅"
        else:
            tier_icon = "📊"
        
        st.metric(
            label=f"{tier_icon} Quality",
            value=quality_tier.split('(')[0].strip()
        )
    
    # ========================================================================
    # SECTION 2: ELITE SIGNAL WARNING (IF APPLICABLE)
    # ========================================================================
    
    if is_elite:
        st.markdown("---")
        
        if confidence < 50:
            # Low confidence for elite - explain why
            st.warning(f"""
            ### ⚠️ Elite Signal - Adjust Your Strategy!
            
            **The {confidence:.1f}% confidence is for a {target}% target, but elite signals perform better with LARGER targets.**
            """)
            
            # Show comparison table
            st.markdown("#### 📊 Elite Signal Performance by Target:")
            
            performance_df = pd.DataFrame({
                'Target': ['5% (Quick Scalp)', '10% (Swing)', '15% (Position)'],
                'Success Rate': ['37% ⬇️', '~50% ➡️', '47% ⬆️'],
                'Recommended': ['❌ Not Ideal', '✅ Good', '✅ Best']
            })
            
            st.dataframe(
                performance_df,
                hide_index=True,
                use_container_width=True
            )
            
            st.info("""
            💡 **Recommendation for Elite Signals:**
            - Set target to **10-15%** instead of 5%
            - Use wider stop loss (-12% to -15%)
            - Hold for **swing trades** (days to weeks)
            - These are "moonshot" setups, not scalps
            """)
        
        else:
            # High confidence even for elite
            st.success(f"""
            ### ⭐ Elite Signal with {confidence:.1f}% Confidence!
            
            This elite setup shows good probability even for the {target}% target.
            Consider going for 10-15% for maximum potential.
            """)
        
        # Elite characteristics
        with st.expander("⭐ What Makes This Elite?", expanded=False):
            st.markdown("""
            **Elite signals have BOTH:**
            - ✅ **Relative Strength** (vs SPY) in top 5%
            - ✅ **Chaikin Accumulation/Distribution** in top 5%
            
            **Characteristics:**
            - 🚀 High momentum
            - 📈 Strong institutional buying
            - 💎 Outperforming the market
            - ⚡ High volatility (bigger swings)
            
            **Best Use:**
            - Swing trades (not day trades)
            - Larger position sizes (high conviction)
            - Wider targets (10-15%+)
            - Trail stops aggressively
            """)
    
    # ========================================================================
    # SECTION 3: CONFIDENCE FACTORS
    # ========================================================================
    
    if prediction['factors']:
        with st.expander("📋 Why This Confidence?", expanded=True):
            st.markdown("**Contributing Factors:**")
            
            for factor in prediction['factors']:
                # Add visual icons
                if '⭐' in factor:
                    st.markdown(f"- {factor}")
                elif '✅' in factor:
                    st.success(factor, icon="✅")
                else:
                    st.info(factor)
    
    # ========================================================================
    # SECTION 4: TRADING RECOMMENDATION
    # ========================================================================
    
    st.markdown("---")
    st.subheader("💼 Trading Recommendation")
    
    # Generate recommendation based on confidence and type
    if is_elite:
        # Elite signal recommendations
        if confidence >= 50:
            st.success("""
            ### ✅ CONSIDER ENTRY (Elite Setup)
            
            **Suggested Trade Parameters:**
            - Entry: Current price
            - Target: 10-15% gain
            - Stop Loss: -12%
            - Position Size: Standard to Large (high conviction)
            - Hold Period: Days to weeks
            
            **Risk/Reward:** 1:3 to 1:5
            """)
        else:
            st.warning("""
            ### ⚠️ WAIT FOR BETTER SETUP
            
            While this is an elite signal, the confidence for quick gains is lower.
            
            **Options:**
            1. Wait for better entry (pullback to support)
            2. Use smaller position size
            3. Set wider target (12-15%)
            """)
    
    else:
        # Regular signal recommendations
        if confidence >= 70:
            st.success("""
            ### 🔥 HIGH CONFIDENCE ENTRY
            
            **Suggested Trade Parameters:**
            - Entry: Current price
            - Target: 5% gain (Daily) / 8% (Weekly)
            - Stop Loss: -10%
            - Position Size: Standard to Large
            - Hold Period: Days
            
            **Risk/Reward:** 1:2
            """)
        
        elif confidence >= 60:
            st.success("""
            ### ✅ GOOD ENTRY OPPORTUNITY
            
            **Suggested Trade Parameters:**
            - Entry: Current price or slight pullback
            - Target: 5% gain (Daily) / 8% (Weekly)
            - Stop Loss: -10%
            - Position Size: Standard
            - Hold Period: Days
            
            **Risk/Reward:** 1:2
            """)
        
        elif confidence >= 50:
            st.info("""
            ### ⚠️ MODERATE CONFIDENCE
            
            **Suggested Trade Parameters:**
            - Entry: Wait for confirmation or better entry
            - Target: 5% gain (Daily) / 8% (Weekly)
            - Stop Loss: -10%
            - Position Size: Reduced (half size)
            - Hold Period: Days
            
            **Risk/Reward:** 1:2
            
            Consider waiting for stronger setup.
            """)
        
        else:
            st.warning("""
            ### ❌ LOW CONFIDENCE - AVOID
            
            This setup has lower probability of success.
            
            **Recommendation:**
            - Do NOT enter
            - Wait for better signal
            - Look for other opportunities
            """)
    
    # ========================================================================
    # SECTION 5: MODEL INFORMATION
    # ========================================================================
    
    with st.expander("🔧 Model Information", expanded=False):
        info = prediction['model_info']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Model Details:**
            - Algorithm: {info['algorithm']}
            - Timeframe: {timeframe}
            - Training Samples: {info['training_samples']:,}
            """)
        
        with col2:
            st.markdown(f"""
            **Performance:**
            - Model Accuracy: {info['accuracy']}%
            - Historical Success: {info['success_rate']}%
            - Target: {target}% gain
            """)
        
        st.info("""
        💡 **How Confidence Works:**
        
        The ML model analyzes 19 different features including:
        - TR stage and momentum indicators
        - EMA alignment and positioning
        - Quality markers (buy points, uptrends, elite status)
        
        It then predicts the probability that this setup will reach the
        target profit without hitting the stop loss, based on 18,000+
        historical signals.
        """)

# ============================================================================
# COMPACT VERSION (For Watchlist/Screener)
# ============================================================================

def display_ml_confidence_compact(signal_data, timeframe='Daily'):
    """
    Compact ML confidence display for watchlist/screener pages
    
    Shows just the essentials:
    - Confidence score
    - Quality badge
    - Quick recommendation
    """
    
    try:
        prediction = predict_confidence(signal_data, timeframe=timeframe)
    except Exception as e:
        st.error(f"ML Error: {e}")
        return
    
    confidence = prediction['confidence']
    is_elite = prediction['is_elite']
    
    # Single row display
    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        # Confidence with color
        if confidence >= 70:
            st.markdown(f"🔥 **{confidence:.0f}%**")
        elif confidence >= 60:
            st.markdown(f"✅ **{confidence:.0f}%**")
        elif confidence >= 50:
            st.markdown(f"⚠️ **{confidence:.0f}%**")
        else:
            st.markdown(f"❌ **{confidence:.0f}%**")
    
    with col2:
        # Quality badge
        if is_elite:
            st.markdown("⭐ **ELITE**")
        elif "Premium" in prediction['quality_tier']:
            st.markdown("🏆 **Premium**")
        elif "Good" in prediction['quality_tier']:
            st.markdown("✅ **Good**")
        else:
            st.markdown("📊 **Basic**")
    
    with col3:
        # Quick action
        if is_elite and confidence < 50:
            st.markdown("⚠️ *Use 10-15% target*")
        elif confidence >= 60:
            st.markdown("✅ *Good Entry*")
        elif confidence >= 50:
            st.markdown("⚠️ *Moderate*")
        else:
            st.markdown("❌ *Avoid*")

# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

def example_tr_indicator_page():
    """
    Example of how to integrate into your TR Indicator page
    """
    
    st.title("📊 TR Indicator Analysis")
    
    # Your existing TR calculation code here
    # ... calculate TR stage, EMAs, PPO, PMO, etc ...
    
    # Example signal data (replace with your actual calculations)
    signal_data = {
        'tr_stage': 1,  # Strong Buy
        'entry_price': 150.50,
        'ema_3': 149.80,
        'ema_9': 148.20,
        'ema_20': 145.80,
        'ema_34': 142.00,
        'ppo_value': 2.1,
        'ppo_histogram': 0.5,
        'pmo_value': 3.2,
        'quality_level': 2,
        'has_buy_point': 1,
        'has_uptrend': 1,
        'has_rs_chaikin': 0  # Set to 1 for elite
    }
    
    # Display your existing TR indicator visuals
    st.subheader("TR Indicator Status")
    st.success("Strong Buy ✓ 🔵BUY")
    
    # Add price chart, EMAs, etc.
    # ... your existing chart code ...
    
    # ADD ML CONFIDENCE SECTION
    display_ml_confidence(signal_data, timeframe='Daily')
    
    # Continue with rest of your page
    # ... signal details, history, etc ...

# ============================================================================
# WATCHLIST INTEGRATION EXAMPLE
# ============================================================================

def example_watchlist_page():
    """
    Example of integrating ML confidence into watchlist
    """
    
    st.title("📋 Watchlist")
    
    # Your watchlist data
    watchlist = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
    
    # Create dataframe with ML predictions
    results = []
    
    for symbol in watchlist:
        # Get TR data for symbol
        # ... your TR calculation code ...
        
        signal_data = {
            # ... populate with actual data ...
            'tr_stage': 1,
            'entry_price': 150.0,
            # ... etc ...
        }
        
        # Get ML prediction
        try:
            prediction = predict_confidence(signal_data)
            
            results.append({
                'Symbol': symbol,
                'TR Status': 'Strong Buy',
                'ML Confidence': f"{prediction['confidence']:.1f}%",
                'Quality': prediction['quality_tier'],
                'Target': f"{prediction['target']}%",
                'Action': 'Enter' if prediction['confidence'] >= 60 else 'Wait'
            })
        except:
            pass
    
    # Display as dataframe
    df = pd.DataFrame(results)
    
    # Color code by confidence
    def highlight_confidence(row):
        if 'Enter' in str(row['Action']):
            return ['background-color: lightgreen'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        df.style.apply(highlight_confidence, axis=1),
        use_container_width=True,
        hide_index=True
    )
    
    # Expandable details for each stock
    for symbol in watchlist:
        with st.expander(f"{symbol} Details"):
            st.write("Click to see full ML analysis")
            # Show compact version
            signal_data = {...}  # Get data
            display_ml_confidence_compact(signal_data)


# ============================================================================
# RUN DEMO
# ============================================================================

if __name__ == '__main__':
    # Demo page
    st.set_page_config(
        page_title="TR ML Integration Demo",
        page_icon="🤖",
        layout="wide"
    )
    
    # Tabs for different examples
    tab1, tab2, tab3 = st.tabs([
        "Full TR Page",
        "Watchlist View",
        "Test Different Signals"
    ])
    
    with tab1:
        example_tr_indicator_page()
    
    with tab2:
        example_watchlist_page()
    
    with tab3:
        st.subheader("Test Different Signal Types")
        
        signal_type = st.selectbox(
            "Select Signal Type",
            ["Basic Strong Buy", "With Buy Point", "With Uptrend", "ELITE"]
        )
        
        # Prepare test data based on selection
        if signal_type == "ELITE":
            test_data = {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 3.0,
                'ppo_histogram': 1.0,
                'pmo_value': 4.0,
                'quality_level': 3,
                'has_buy_point': 1,
                'has_uptrend': 1,
                'has_rs_chaikin': 1
            }
        elif signal_type == "With Uptrend":
            test_data = {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.5,
                'ppo_histogram': 0.7,
                'pmo_value': 3.5,
                'quality_level': 2,
                'has_buy_point': 1,
                'has_uptrend': 1,
                'has_rs_chaikin': 0
            }
        elif signal_type == "With Buy Point":
            test_data = {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.1,
                'ppo_histogram': 0.5,
                'pmo_value': 3.2,
                'quality_level': 2,
                'has_buy_point': 1,
                'has_uptrend': 0,
                'has_rs_chaikin': 0
            }
        else:  # Basic
            test_data = {
                'tr_stage': 1,
                'entry_price': 150.5,
                'ema_3': 149.8,
                'ema_9': 148.2,
                'ema_20': 145.8,
                'ema_34': 142.0,
                'ppo_value': 2.1,
                'ppo_histogram': 0.5,
                'pmo_value': 3.2,
                'quality_level': 1,
                'has_buy_point': 0,
                'has_uptrend': 0,
                'has_rs_chaikin': 0
            }
        
        display_ml_confidence(test_data, timeframe='Daily')
