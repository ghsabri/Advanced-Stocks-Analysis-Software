"""
Test Runner for Watchlists Page
Port 8502 - Testing Mode
"""

import streamlit as st
import sys

# Add current directory to path for imports
sys.path.insert(0, '.')

# Import the main function from the fixed watchlists file
from importlib.machinery import SourceFileLoader

# Load the watchlists module
watchlists = SourceFileLoader("watchlists", "3_Watchlists.py").load_module()

# Show test banner in sidebar
st.sidebar.warning("🧪 TESTING MODE - Port 8502")
st.sidebar.caption("This is a test instance")

# Run the main function
if __name__ == "__main__":
    watchlists.main()