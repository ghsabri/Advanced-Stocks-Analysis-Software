"""
Configuration Settings
Store your API keys and preferences here
"""

# ==============================================================================
# DATA SOURCE CONFIGURATION
# ==============================================================================

# Default data source: 'yahoo' or 'tiingo'
# - 'yahoo': Free, unlimited, good for development
# - 'tiingo': Professional, rate-limited (50/hour free tier)
DEFAULT_DATA_SOURCE = 'yahoo'

# ==============================================================================
# TIINGO API CONFIGURATION
# ==============================================================================

# Get your free Tiingo API key at: https://www.tiingo.com/
# Free tier: 50 API calls per hour, 5 years of historical data
# Paid tier: $49/month for 100,000 calls per day

TIINGO_API_KEY = None  # Replace with your key: 'your-api-key-here'

# Example (replace with your actual key):
# TIINGO_API_KEY = 'abc123def456ghi789jkl012mno345pqr678stu901'

# ==============================================================================
# APPLICATION SETTINGS
# ==============================================================================

# Default timeframe for analysis
DEFAULT_TIMEFRAME = 'daily'  # 'daily' or 'weekly'

# Default duration for analysis (in days)
DEFAULT_DURATION_DAYS = 180  # 6 months

# Cache settings
ENABLE_CACHING = True
CACHE_EXPIRY_HOURS = 24  # How long to cache data

# ==============================================================================
# DISPLAY SETTINGS
# ==============================================================================

# Number of stocks to show in summaries
MAX_RESULTS_DISPLAY = 10

# Number of recent signals to display
RECENT_SIGNALS_COUNT = 10

# ==============================================================================
# SUBSCRIPTION TIERS (for future use)
# ==============================================================================

TIERS = {
    'commentary': {
        'name': 'Commentary Only',
        'price': 9.99,
        'features': ['Weekly picks', 'Market commentary', 'No software access']
    },
    'basic': {
        'name': 'Basic',
        'price': 29.00,
        'features': ['Full TR Indicator', 'Pattern detection', '20+ indicators', 
                     'TradingView charts', 'No AI features', 'No weekly picks']
    },
    'pro': {
        'name': 'Pro',
        'price': 39.00,
        'features': ['Everything in Basic', 'AI confidence scores', 
                     'ML predictions', 'Weekly picks included', 
                     'Priority support', 'Unlimited watchlists']
    }
}

# ==============================================================================
# NOTES
# ==============================================================================

"""
SETUP INSTRUCTIONS:

1. For Yahoo Finance (Free, unlimited):
   - No setup needed! Just use DEFAULT_DATA_SOURCE = 'yahoo'
   - Good for development and testing
   
2. For Tiingo API (Professional):
   - Sign up at https://www.tiingo.com/
   - Get your free API key
   - Set TIINGO_API_KEY = 'your-key-here'
   - Set DEFAULT_DATA_SOURCE = 'tiingo'
   
3. For production (after beta):
   - Upgrade to Tiingo Business Plan ($49/month)
   - 100,000 API calls per day
   - Set DEFAULT_DATA_SOURCE = 'tiingo'
"""
