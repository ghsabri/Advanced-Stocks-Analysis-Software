"""
MJ Software LLC - AI-Powered Stock Analysis Platform
Main Application Entry Point (Homepage)
"""

import streamlit as st
import datetime

# Page configuration
st.set_page_config(
    page_title="MJ Software - Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=MJ+Software", 
             use_container_width=True)
    st.markdown("---")
    
    # User info placeholder (will add authentication later)
    st.markdown("### 👤 User")
    st.info("Not logged in")
    
    st.markdown("---")
    
    # Quick stats placeholder
    st.markdown("### 📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Watchlist", "0")
    with col2:
        st.metric("Alerts", "0")
    
    st.markdown("---")
    
    # Navigation helper
    st.markdown("### 🧭 Navigation")
    st.markdown("""
    - **🔍 Stock Analysis**: Analyze any stock with TR indicator
    - **💼 Portfolio**: Track your holdings
    - **👁️ Watchlist**: Monitor favorite stocks
    - **🔔 Alerts**: Set price & pattern alerts
    """)

# Main content
st.markdown('<p class="main-header">📈 MJ Software - AI Stock Analysis</p>', 
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Proprietary TR Indicator + AI-Powered Pattern Detection</p>', 
            unsafe_allow_html=True)

# Welcome message
st.success(f"👋 Welcome! Today is {datetime.datetime.now().strftime('%B %d, %Y')}")

# Quick Start Section
st.markdown("## 🚀 Quick Start")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🔍 Analyze a Stock</h3>
        <p>Enter any stock symbol to get instant analysis with our proprietary TR indicator, 
        pattern detection, and AI confidence scores.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Analysis →", key="btn_analysis", use_container_width=True):
        st.switch_page("pages/1_🔍_Stock_Analysis.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>💼 Portfolio</h3>
        <p>Track your holdings with real-time performance metrics, gains/losses, 
        and TR signals for all your positions.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Portfolio →", key="btn_portfolio", use_container_width=True):
        st.switch_page("pages/2_💼_Portfolio.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>👁️ Watchlist</h3>
        <p>Monitor stocks you're interested in with customizable watchlists 
        and instant signal updates.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Create Watchlist →", key="btn_watchlist", use_container_width=True):
        st.switch_page("pages/3_👁️_Watchlist.py")

st.markdown("---")

# Features Overview
st.markdown("## ✨ Platform Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🎯 Core Features
    - **Proprietary TR Indicator**: Our unique trend recognition algorithm
    - **10+ Pattern Detection**: Head & Shoulders, Double Tops, Triangles, and more
    - **AI Confidence Scores**: Machine learning-powered predictions (Pro tier)
    - **Multi-Timeframe Analysis**: Daily, Weekly, Monthly charts
    - **Volume Analysis**: Identify breakouts and divergences
    """)

with col2:
    st.markdown("""
    ### 🛠️ Tools & Analytics
    - **20+ Technical Indicators**: RSI, MACD, Bollinger Bands, and more
    - **TradingView Charts**: Professional interactive charting
    - **Risk Assessment**: Position sizing and stop-loss recommendations
    - **Price Alerts**: Get notified on price movements and pattern formations
    - **Export Reports**: PDF and CSV exports for your analysis
    """)

st.markdown("---")

# Subscription Tiers Preview
st.markdown("## 💎 Subscription Tiers")

tier_col1, tier_col2, tier_col3 = st.columns(3)

with tier_col1:
    st.markdown("""
    <div class="metric-card">
        <h3>💌 Commentary</h3>
        <h2>$9.99/mo</h2>
        <p>Weekly picks + commentary</p>
        <p><small>No software access</small></p>
    </div>
    """, unsafe_allow_html=True)

with tier_col2:
    st.markdown("""
    <div class="metric-card">
        <h3>⭐ Basic</h3>
        <h2>$29/mo</h2>
        <p>Full software access</p>
        <p><small>No AI features, no picks</small></p>
    </div>
    """, unsafe_allow_html=True)

with tier_col3:
    st.markdown("""
    <div class="metric-card">
        <h3>🏆 Pro</h3>
        <h2>$39/mo</h2>
        <p>Everything + AI + Picks</p>
        <p><small>Best value!</small></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>MJ Software LLC - AI-Powered Stock Analysis Platform</p>
    <p><small>Week 4-5 Development Build | Beta Version</small></p>
</div>
""", unsafe_allow_html=True)
