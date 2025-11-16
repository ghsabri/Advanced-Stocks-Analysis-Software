"""
Alerts Page - Price Alerts and Notification Management
"""

import streamlit as st

st.set_page_config(
    page_title="Alerts - MJ Software",
    page_icon="🔔",
    layout="wide"
)

# Check login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = True

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Please login from the Home page to access this feature.")
    st.stop()

st.title("🔔 Alerts")
st.markdown("**Price Alerts & Notification Management**")

st.info("🚧 **This feature is under development and will be available in Week 6-7.**")

st.markdown("""
### Coming Soon:
- Price threshold alerts (above/below specific price)
- TR Indicator signal change alerts
- Pattern detection alerts
- Volume spike alerts
- Email and push notifications
- Alert history and management
""")

# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
