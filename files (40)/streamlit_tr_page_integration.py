"""
TR Indicator Page with ML Confidence Integration
=================================================

This is the STREAMLIT PAGE code that displays TR indicator with ML confidence.
This goes in your pages/TR_Indicator.py or similar Streamlit page file.

Your tr_indicator.py stays as is - this is separate!
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Your existing imports
import tr_indicator as ti
import tr_calculations as tc

# ML predictor import
try:
    from ml_tr_predictor_hybrid import predict_confidence
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    st.warning("ML models not available. Train models first!")


def display_tr_analysis_page():
    """
    Main TR Indicator page with ML confidence
    """
    
    st.title("📊 TR Indicator Analysis")
    
    # Stock selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_symbol = st.text_input("Stock Symbol", value="AAPL", key="stock_input")
    
    with col2:
        timeframe = st.selectbox("Timeframe", ["Daily", "Weekly"], key="timeframe_select")
    
    if st.button("Analyze", type="primary"):
        
        with st.spinner(f"Analyzing {stock_symbol}..."):
            
            # ================================================================
            # YOUR EXISTING TR CALCULATION CODE
            # ================================================================
            
            # Get stock data (your existing code)
            # data = get_stock_data(stock_symbol, timeframe)  # Your function
            
            # For demo, using sample data structure
            # Replace this with your actual data loading!
            try:
                # YOUR CODE HERE to load data
                # data = load_stock_data(stock_symbol)
                
                # Analyze with TR indicator (your existing function!)
                # df = ti.analyze_tr_indicator(data)
                
                # Get current (latest) values
                # current_idx = len(df) - 1
                # current_status = df['TR_Status'].iloc[current_idx]
                
                # For demo purposes (replace with your actual data):
                # This is just to show structure
                df = pd.DataFrame({
                    'Close': [150.50],
                    'EMA_3': [149.80],
                    'EMA_9': [148.20],
                    'EMA_20': [145.80],
                    'EMA_34': [142.00],
                    'PPO_Line': [2.1],
                    'PPO_Histogram': [0.5],
                    'PMO_Line': [3.2],
                    'TR_Status': ['Strong Buy']
                })
                
                current_idx = 0
                current_status = df['TR_Status'].iloc[current_idx]
                
                # ================================================================
                # DISPLAY TR STATUS (YOUR EXISTING DISPLAY CODE)
                # ================================================================
                
                st.success(f"**Current TR Status:** {current_status}")
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Close Price", f"${df['Close'].iloc[current_idx]:.2f}")
                
                with col2:
                    st.metric("PPO", f"{df['PPO_Line'].iloc[current_idx]:.2f}")
                
                with col3:
                    st.metric("PMO", f"{df['PMO_Line'].iloc[current_idx]:.2f}")
                
                # Show your chart/indicators here
                # ... your existing chart code ...
                
                # ================================================================
                # ML CONFIDENCE INTEGRATION (NEW SECTION)
                # ================================================================
                
                # Only show ML for buy signals
                if current_status in ['Strong Buy', 'Buy', 'Neutral Buy']:
                    
                    if ML_AVAILABLE:
                        
                        st.markdown("---")
                        st.subheader("🤖 Machine Learning Confidence Score")
                        
                        # Map TR status to numeric stage
                        tr_stage_map = {
                            'Strong Buy': 1,
                            'Buy': 2,
                            'Neutral Buy': 3,
                            'Neutral Sell': 4,
                            'Sell': 5,
                            'Strong Sell': 6,
                            'Neutral': 3
                        }
                        
                        tr_stage = tr_stage_map.get(current_status, 3)
                        
                        # Prepare signal data for ML
                        signal_data = {
                            'tr_stage': tr_stage,
                            'entry_price': float(df['Close'].iloc[current_idx]),
                            'ema_3': float(df['EMA_3'].iloc[current_idx]),
                            'ema_9': float(df['EMA_9'].iloc[current_idx]),
                            'ema_20': float(df['EMA_20'].iloc[current_idx]),
                            'ema_34': float(df['EMA_34'].iloc[current_idx]),
                            'ppo_value': float(df['PPO_Line'].iloc[current_idx]),
                            'ppo_histogram': float(df['PPO_Histogram'].iloc[current_idx]),
                            'pmo_value': float(df['PMO_Line'].iloc[current_idx]),
                            'quality_level': 1,  # Basic for now, you can enhance this
                            'has_buy_point': 0,  # You can add logic to detect this
                            'has_uptrend': 1 if current_status == 'Strong Buy' else 0,
                            'has_rs_chaikin': 0  # You can add logic to detect elite signals
                        }
                        
                        try:
                            # Get ML prediction
                            prediction = predict_confidence(signal_data, timeframe=timeframe)
                            
                            # Display confidence metrics
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                # Color code by confidence
                                if prediction['confidence'] >= 70:
                                    st.metric(
                                        label="🔥 ML Confidence",
                                        value=f"{prediction['confidence']:.1f}%",
                                        delta=prediction['confidence_level']
                                    )
                                elif prediction['confidence'] >= 60:
                                    st.metric(
                                        label="✅ ML Confidence",
                                        value=f"{prediction['confidence']:.1f}%",
                                        delta=prediction['confidence_level']
                                    )
                                elif prediction['confidence'] >= 50:
                                    st.metric(
                                        label="⚠️ ML Confidence",
                                        value=f"{prediction['confidence']:.1f}%",
                                        delta=prediction['confidence_level']
                                    )
                                else:
                                    st.metric(
                                        label="❌ ML Confidence",
                                        value=f"{prediction['confidence']:.1f}%",
                                        delta=prediction['confidence_level']
                                    )
                            
                            with col2:
                                st.metric(
                                    label="🎯 Target",
                                    value=f"{prediction['target']}%",
                                    delta=timeframe
                                )
                            
                            with col3:
                                quality_display = prediction['quality_tier'].split('(')[0].strip()
                                if prediction['is_elite']:
                                    st.metric(
                                        label="⭐ Quality",
                                        value=quality_display
                                    )
                                else:
                                    st.metric(
                                        label="📊 Quality",
                                        value=quality_display
                                    )
                            
                            # Elite signal warning
                            if prediction['is_elite']:
                                st.markdown("---")
                                st.warning("""
                                ### ⭐ ELITE SIGNAL DETECTED!
                                
                                This signal has **both Relative Strength and Chaikin A/D in top 5%**.
                                
                                **Important:** The confidence shown is for a {}% target, but elite signals 
                                perform better with **10-15% targets**.
                                
                                Historical Performance:
                                - 5% target: 37% success ⬇️
                                - 10-15% target: 47-50% success ⬆️
                                
                                💡 **Recommendation:** Use wider targets and stops for elite signals.
                                """.format(prediction['target']))
                            
                            # Show contributing factors
                            with st.expander("📋 Why This Confidence?", expanded=True):
                                st.markdown("**Contributing Factors:**")
                                for factor in prediction['factors']:
                                    st.write(f"• {factor}")
                            
                            # Trading recommendation
                            st.markdown("---")
                            st.subheader("💼 Trading Recommendation")
                            
                            confidence = prediction['confidence']
                            is_elite = prediction['is_elite']
                            
                            if is_elite and confidence < 50:
                                st.warning("""
                                ⚠️ **Elite Signal - Adjust Strategy**
                                
                                This is a high-volatility elite setup. Consider:
                                - Target: 10-15% (not {}%)
                                - Stop Loss: -12% (wider)
                                - Position: Standard to large (high conviction)
                                - Hold: Days to weeks (swing trade)
                                """.format(prediction['target']))
                            
                            elif confidence >= 70:
                                st.success("""
                                🔥 **HIGH CONFIDENCE ENTRY**
                                
                                Strong setup with {}% probability of reaching {}% target.
                                
                                Suggested Trade:
                                - Entry: Current price (${:.2f})
                                - Target: {}% (${:.2f})
                                - Stop Loss: -10% (${:.2f})
                                - Position Size: Standard to Large
                                """.format(
                                    confidence,
                                    prediction['target'],
                                    signal_data['entry_price'],
                                    prediction['target'],
                                    signal_data['entry_price'] * (1 + prediction['target']/100),
                                    signal_data['entry_price'] * 0.9
                                ))
                            
                            elif confidence >= 60:
                                st.success("""
                                ✅ **GOOD ENTRY OPPORTUNITY**
                                
                                Decent setup with {}% probability.
                                
                                Suggested Trade:
                                - Entry: Current price or slight pullback
                                - Target: {}%
                                - Stop Loss: -10%
                                - Position Size: Standard
                                """.format(confidence, prediction['target']))
                            
                            elif confidence >= 50:
                                st.info("""
                                ⚠️ **MODERATE CONFIDENCE**
                                
                                Consider smaller position or wait for confirmation.
                                
                                {}% probability of success.
                                """.format(confidence))
                            
                            else:
                                st.warning("""
                                ❌ **LOW CONFIDENCE - CONSIDER WAITING**
                                
                                This setup has lower probability ({}%).
                                
                                Recommendation: Look for better entry or different stock.
                                """.format(confidence))
                            
                            # Model info
                            with st.expander("🔧 Model Information"):
                                info = prediction['model_info']
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Algorithm:** {info['algorithm']}")
                                    st.write(f"**Training Samples:** {info['training_samples']:,}")
                                
                                with col2:
                                    st.write(f"**Model Accuracy:** {info['accuracy']}%")
                                    st.write(f"**Historical Success:** {info['success_rate']}%")
                        
                        except Exception as e:
                            st.error(f"ML Prediction Error: {str(e)}")
                            st.write("Debug info:", signal_data)
                    
                    else:
                        st.info("""
                        💡 **ML Confidence Not Available**
                        
                        To enable ML predictions:
                        1. Run: `python train_tr_hybrid_final.py`
                        2. Restart the app
                        """)
                
                else:
                    # Not a buy signal
                    st.info(f"ML confidence only available for buy signals. Current status: {current_status}")
            
            except Exception as e:
                st.error(f"Error analyzing {stock_symbol}: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# ================================================================
# RUN THE PAGE
# ================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="TR Indicator with ML",
        page_icon="📊",
        layout="wide"
    )
    
    display_tr_analysis_page()
