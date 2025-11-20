"""
EXACT ML INTEGRATION FOR YOUR 2_TR_Indicator.py

Copy the code blocks below and paste them into your 2_TR_Indicator.py file
at the specified line numbers.
"""

# ============================================================================
# STEP 1: ADD ML IMPORT AT LINE 25 (after sys.path.insert)
# ============================================================================

# Add this code at line 25, right after:
# if src_path not in sys.path:
#     sys.path.insert(0, src_path)

# Try to import ML predictor
ML_AVAILABLE = False
try:
    from ml_tr_predictor_hybrid import predict_confidence
    ML_AVAILABLE = True
except ImportError:
    pass  # ML not available yet


# ============================================================================
# STEP 2: ADD ML CONFIDENCE DISPLAY AT LINE 242 (after st.markdown("---"))
# ============================================================================

# Find line 242 which has:
# st.markdown("---")
# 
# Then add this ENTIRE SECTION right after it:

            # ================================================================
            # 🤖 MACHINE LEARNING CONFIDENCE SCORE
            # ================================================================
            
            # Only show ML for buy signals
            if result['current_status'] in ['Strong Buy', 'Buy', 'Neutral Buy']:
                
                if ML_AVAILABLE:
                    st.markdown("---")
                    st.markdown("### 🤖 Machine Learning Confidence Score")
                    
                    try:
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
                        
                        tr_stage = tr_stage_map.get(result['current_status'], 3)
                        
                        # Get latest data row
                        latest_idx = len(result['full_data']) - 1
                        latest = result['full_data'].iloc[latest_idx]
                        
                        # Prepare signal data for ML prediction
                        signal_data = {
                            'tr_stage': tr_stage,
                            'entry_price': float(latest['Close']),
                            'ema_3': float(latest['EMA_3']),
                            'ema_9': float(latest['EMA_9']),
                            'ema_20': float(latest['EMA_20']),
                            'ema_34': float(latest['EMA_34']),
                            'ppo_value': float(latest['PPO_Line']),
                            'ppo_histogram': float(latest['PPO_Histogram']),
                            'pmo_value': float(latest['PMO_Line']),
                            'quality_level': 1,  # Basic for now
                            'has_buy_point': 1 if '🔵BUY' in str(result['current_status']) else 0,
                            'has_uptrend': 1 if '↑' in str(result['current_status']) else 0,
                            'has_rs_chaikin': 1 if '*' in str(result['current_status']) else 0
                        }
                        
                        # Get ML prediction
                        prediction = predict_confidence(signal_data, timeframe=timeframe)
                        
                        # Display confidence metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Color-coded confidence
                            confidence = prediction['confidence']
                            if confidence >= 70:
                                st.metric(
                                    label="🔥 ML Confidence",
                                    value=f"{confidence:.1f}%",
                                    delta=prediction['confidence_level'],
                                    delta_color="normal"
                                )
                            elif confidence >= 60:
                                st.metric(
                                    label="✅ ML Confidence",
                                    value=f"{confidence:.1f}%",
                                    delta=prediction['confidence_level'],
                                    delta_color="normal"
                                )
                            elif confidence >= 50:
                                st.metric(
                                    label="⚠️ ML Confidence",
                                    value=f"{confidence:.1f}%",
                                    delta=prediction['confidence_level'],
                                    delta_color="off"
                                )
                            else:
                                st.metric(
                                    label="❌ ML Confidence",
                                    value=f"{confidence:.1f}%",
                                    delta=prediction['confidence_level'],
                                    delta_color="inverse"
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
                            elif "Premium" in quality_display:
                                st.metric(
                                    label="🏆 Quality",
                                    value=quality_display
                                )
                            elif "Good" in quality_display:
                                st.metric(
                                    label="✅ Quality",
                                    value=quality_display
                                )
                            else:
                                st.metric(
                                    label="📊 Quality",
                                    value=quality_display
                                )
                        
                        # Elite signal warning
                        if prediction['is_elite']:
                            st.warning(f"""
                            ### ⭐ ELITE SIGNAL DETECTED!
                            
                            This signal has **both Relative Strength and Chaikin A/D in top 5%**.
                            
                            **Important:** The {prediction['confidence']:.1f}% confidence is for a **{prediction['target']}% target**, 
                            but elite signals perform better with **10-15% targets**.
                            
                            **Historical Performance:**
                            - 5% target: 37% success ⬇️
                            - 10-15% target: 47-50% success ⬆️
                            
                            💡 **Recommendation:** Use wider targets (10-15%) and stops (-12%) for elite signals.
                            """)
                        
                        # Show contributing factors
                        with st.expander("📋 Why This Confidence?", expanded=True):
                            st.markdown("**Contributing Factors:**")
                            for factor in prediction['factors']:
                                st.write(f"• {factor}")
                        
                        # Trading recommendation
                        st.markdown("---")
                        st.subheader("💼 Trading Recommendation")
                        
                        is_elite = prediction['is_elite']
                        target_pct = prediction['target']
                        entry = signal_data['entry_price']
                        target_price = entry * (1 + target_pct/100)
                        stop_price = entry * 0.90
                        
                        if is_elite and confidence < 50:
                            st.warning(f"""
                            ⚠️ **ELITE SIGNAL - ADJUST STRATEGY**
                            
                            This is a high-volatility elite setup. Consider:
                            - **Target:** 10-15% (${entry * 1.10:.2f} - ${entry * 1.15:.2f}) instead of {target_pct}%
                            - **Stop Loss:** -12% (${entry * 0.88:.2f}) - wider than normal
                            - **Position:** Standard to large (high conviction)
                            - **Hold:** Days to weeks (swing trade, not day trade)
                            
                            Elite signals need more room to work - they're "moonshots", not scalps!
                            """)
                        
                        elif confidence >= 70:
                            st.success(f"""
                            🔥 **HIGH CONFIDENCE ENTRY**
                            
                            Strong setup with **{confidence:.1f}% probability** of reaching {target_pct}% target.
                            
                            **Suggested Trade Parameters:**
                            - **Entry:** Current price (${entry:.2f})
                            - **Target:** {target_pct}% (${target_price:.2f})
                            - **Stop Loss:** -10% (${stop_price:.2f})
                            - **Position Size:** Standard to Large
                            - **Risk/Reward:** 1:2
                            
                            ✅ This is a good entry opportunity!
                            """)
                        
                        elif confidence >= 60:
                            st.success(f"""
                            ✅ **GOOD ENTRY OPPORTUNITY**
                            
                            Decent setup with **{confidence:.1f}% probability** of success.
                            
                            **Suggested Trade Parameters:**
                            - **Entry:** Current price or slight pullback
                            - **Target:** {target_pct}% (${target_price:.2f})
                            - **Stop Loss:** -10% (${stop_price:.2f})
                            - **Position Size:** Standard
                            
                            This is a solid entry with good risk/reward.
                            """)
                        
                        elif confidence >= 50:
                            st.info(f"""
                            ⚠️ **MODERATE CONFIDENCE**
                            
                            **{confidence:.1f}% probability** - consider smaller position or wait for confirmation.
                            
                            **Suggested Approach:**
                            - Wait for better entry (pullback to support)
                            - Use reduced position size (half size)
                            - Set tighter stop loss
                            
                            Or look for higher-confidence setups.
                            """)
                        
                        else:
                            st.warning(f"""
                            ❌ **LOW CONFIDENCE - CONSIDER WAITING**
                            
                            This setup has lower probability (**{confidence:.1f}%**).
                            
                            **Recommendation:**
                            - ❌ Do NOT enter at current levels
                            - 🔍 Wait for better setup or confirmation
                            - 📊 Look for other opportunities with higher confidence
                            
                            Low confidence signals have reduced success rates.
                            """)
                        
                        # Model information
                        with st.expander("🔧 Model Information"):
                            info = prediction['model_info']
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Algorithm:** {info['algorithm']}")
                                st.write(f"**Training Samples:** {info['training_samples']:,}")
                                st.write(f"**Timeframe:** {timeframe}")
                            
                            with col2:
                                st.write(f"**Model Accuracy:** {info['accuracy']}%")
                                st.write(f"**Historical Success:** {info['success_rate']}%")
                                st.write(f"**Target:** {target_pct}% gain")
                            
                            st.info("""
                            💡 **How This Works:**
                            
                            The ML model analyzes 19 different features including:
                            - TR stage and momentum indicators
                            - EMA alignment and positioning  
                            - Quality markers (buy points, uptrends, elite status)
                            
                            It predicts the probability that this setup will reach the target 
                            profit without hitting the stop loss, based on 18,000+ historical signals.
                            
                            The model was trained on real market data and validated on out-of-sample data.
                            """)
                    
                    except Exception as e:
                        st.error(f"⚠️ ML Prediction Error: {str(e)}")
                        with st.expander("Debug Information"):
                            st.write("**Signal Data:**")
                            st.json(signal_data)
                            st.write("**Error:**")
                            st.exception(e)
                
                else:
                    # ML not available
                    st.info("""
                    ### 💡 Machine Learning Feature Available!
                    
                    Get AI-powered confidence scores for your trades.
                    
                    **To enable:**
                    1. Train the models: `python train_tr_hybrid_final.py`
                    2. Restart Streamlit
                    
                    **You'll get:**
                    - 📊 Confidence percentage (0-100%)
                    - 🎯 Success probability for each setup
                    - ⭐ Quality tier classifications
                    - 💼 Clear trading recommendations
                    """)
            
            st.markdown("---")


# ============================================================================
# THAT'S IT! Just add these TWO code blocks to your file.
# ============================================================================
