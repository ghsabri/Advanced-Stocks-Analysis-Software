"""
Home Page - Login and Introduction
"""

import yfinance as yf
import streamlit as st
import requests
print("🔧 Initializing network for Yahoo Finance...")
try:
    # Make a simple request to Yahoo Finance domain
    r = requests.get("https://query1.finance.yahoo.com", timeout=10)
    print(f"✅ Yahoo Finance network initialized (Status: {r.status_code})")
except Exception as e:
    print(f"⚠️ Request warning: {e}")
    print("   (This is OK, initialization should still work)")
print("Done.")

# CRITICAL FIX: Ensure yfinance cookies are initialized
# This prevents 429 errors on fresh app start
# if 'yf_cookies_initialized' not in st.session_state:
#     try:
#         # Force yfinance to create/update its cookie files
#         # Use a reliable ticker that always works
#         test_ticker = yf.Ticker("SPY")
#         _ = test_ticker.history(period="5d")
#         st.session_state.yf_cookies_initialized = True
#     except Exception as e:
#         # If this fails, app will likely have issues
#         # but we don't want to crash on startup
#         pass

# Now continue with normal imports and app code


st.set_page_config(
    page_title="Advanced Stock Analysis",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Center column for login
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    
    # Logo and title
    st.markdown("<h1 style='text-align: center;'>📈 MJ SOFTWARE LLC</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>AI-Powered Stock Analysis Platform</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not st.session_state['logged_in']:
        
        # Login form
        st.markdown("### 🔐 Login to Access")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                # TODO: Replace with actual authentication in Week 9-10
                # For now, any username/password works
                if username and password:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Please enter both username and password")
        
        st.markdown("---")
        
        # Welcome message
        st.markdown("""
        ### Welcome to MJ Software Stock Analysis Platform
        
        **Features:**
        - 📊 **Stocks Analysis**: Complete stock analysis dashboard with TradingView charts
        - 📈 **TR Indicator**: Proprietary trend recognition indicator
        - 🔺 **Pattern Detection**: Automatic chart pattern detection
        - 📊 **Seasonality Analysis**: Monthly performance patterns
        - 💼 **Portfolio Management**: Track your investments
        - ⭐ **Watchlists**: Monitor stocks of interest
        - 🔔 **Alerts**: Get notified of important changes
        
        **Two Service Tiers:**
        - **Commentary Only**: $9.99/month - Weekly market commentary and stock picks
        - **Basic**: $25/month - Full software access, Everything + AI + Weekly picks        
        ---
        
        **Note**: Authentication system will be fully implemented in Week 9-10 of development.
        For now, enter any username/password to access the platform.
        """)
    
    else:
        # User is logged in
        st.success(f"✅ Logged in as: **{st.session_state.get('username', 'User')}**")
        
        st.markdown("---")
        
        st.markdown("""
        ### 🎉 Welcome to Your Stock Analysis Platform!
        
        **Quick Start:**
        1. Click **"Stocks Analysis"** in the sidebar for complete stock analysis
        2. Use **"TR Indicator"** to analyze trend strength
        3. Check **"Pattern Detection"** to find chart patterns
        4. View **"Seasonality"** to see monthly performance trends
        
        **Navigation:**
        All features are now available in the sidebar. Click any page to get started!
        
        ---
        
        ### 📊 What's New:
        - ✅ Complete Stocks Analysis dashboard
        - ✅ TradingView Advanced Charts
        - ✅ Performance comparison tables
        - ✅ Technical indicators & signals
        - ✅ Support/Resistance levels
        - ✅ Profit & Stop Loss targets
        - ✅ Watchlist Features with Quick Charts
        - ✅ Daily Trading Guide
                          
        
        ### 🔮 Coming Soon:
        - Portfolio Management
        - Alert System
        """)
        
        st.markdown("---")
        
        # Logout button
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_b:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.rerun()

# Footer
st.markdown("---")

# Legal Disclaimer
st.markdown("""
<div style='background-color: #2C3E50; color: white; padding: 20px; border-radius: 5px; margin-top: 20px;'>
<h4 style='color: white; margin-top: 0;'>MJ Software LLC</h4>
<p style='margin: 5px 0;'><strong>Disclaimer:</strong></p>
<p style='margin: 5px 0; font-size: 13px;'>
The material presented here, and the results generated by Advance Stock Analysis Software are for informational / educational / learning purposes only and should not be taken as purchase or sell recommendation.
</p>
<p style='margin: 5px 0; font-size: 13px;'>
Trading / Investing in Stocks and derivatives (Futures, Options etc.) is highly risky and could result in a substantial or complete loss of invested capital.
</p>
<p style='margin: 5px 0; font-size: 13px;'>
The owner(s) and employees of MJ Software are not registered as Financial Advisors with FINRA or SEC and for any financial advice pertaining to individual circumstances and decisions, please consult a registered financial advisor.
</p>
<p style='margin: 5px 0; font-size: 13px;'>
Microsoft, Excel, Excel 365, Microsoft Office, Refinitiv and TradingView are registered trademarks of Microsoft Corporation, Refinitiv and TradingView Inc.
</p>
</div>
""", unsafe_allow_html=True)

st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
