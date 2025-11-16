"""
MJ Software LLC - Stock Analysis Platform
Main Streamlit Application
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="MJ Software - Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar - Global Settings (API Source)
with st.sidebar:
    st.markdown("### ⚙️ Global Settings")
    
    api_source = st.radio(
        "Data Source",
        ["Yahoo Finance", "Tiingo API"],
        index=0,
        help="Yahoo: Free, unlimited\nTiingo: Requires API key, more data"
    )
    
    # Store in session state for ALL pages to use
    st.session_state['api_source'] = api_source
    
    st.markdown("---")
    st.caption(f"Current: **{api_source}**")

# Main page
st.title("📊 MJ Software - Stock Analysis Platform")
st.markdown("### Analyze stocks with our proprietary TR indicator")

st.markdown("---")

st.markdown(f"""
## Welcome! 👋

**Data Source:** {api_source} ({'✅ Active' if api_source else ''})

Use the sidebar to navigate to:
- **📊 TR Indicator** - Analyze any stock with TR indicator
- **🔺 Pattern Detection** - Detect chart patterns
- **📈 Seasonality** - Analyze seasonal trends
- **💼 Portfolio** - Manage your portfolio
- **⭐ Watchlist** - Track stocks you're watching
- **🔔 Alerts** - Set up price and signal alerts

---

### Getting Started:

1. **Choose your data source** in the sidebar (Yahoo or Tiingo)
2. Click **TR Indicator** in the sidebar
3. Enter a stock symbol (e.g., AAPL, TSLA, MSFT)
4. Select your preferred timeframe and duration
5. Click **Analyze Stock** to see TR indicator analysis

---

*Powered by proprietary TR indicator technology*
""")

# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis")
