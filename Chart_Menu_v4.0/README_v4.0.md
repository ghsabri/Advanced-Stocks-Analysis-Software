# 📊 TR Chart Generator v4.0

**Complete Stock Analysis Platform with TR Indicators, Technical Charts, and Seasonality Analysis**

![Version](https://img.shields.io/badge/version-4.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

---

## ✨ **What's New in v4.0**

### 🆕 Three Powerful Features in One Platform:

1. **TR Indicator Charts** (Original Feature)
   - Split-adjusted stock prices
   - Proprietary TR indicator with stages
   - Buy points and stop losses
   - Multiple timeframes and durations

2. **Standard Charts** (NEW!)
   - Line charts
   - Candlestick charts
   - OHLC (Hi-Lo) charts
   - With Volume and RSI indicators
   - Professional TradingView widgets

3. **Seasonality Analysis** (NEW!)
   - Monthly performance patterns
   - 1, 3, 5, and 20-year analysis
   - Absolute returns
   - Relative performance vs S&P 500
   - Visual bar charts

---

## 🎯 **Perfect For:**

- Day traders needing multiple chart perspectives
- Swing traders using TR methodology
- Investors analyzing seasonal patterns
- Anyone wanting professional stock analysis tools
- Traders comparing stock vs market performance

---

## 🚀 **Quick Start**

### **Installation**

1. **Download and Extract:**
   ```bash
   # Extract TR-Chart-Generator-v4.0.zip to C:\TR-Chart-Generator\
   ```

2. **Install Dependencies:**
   ```bash
   cd C:\TR-Chart-Generator
   pip install -r requirements.txt
   ```

3. **Configure API Key:**
   Create `.env` file:
   ```
   TIINGO_API_KEY=your_api_key_here
   ```
   Get free key at: https://www.tiingo.com/

4. **Run:**
   ```bash
   python chart_menu_v4.0_LOCAL.py
   ```

---

## 📖 **Features Overview**

### 1️⃣ **TR Indicator Charts**

Generate charts with proprietary TR indicator system:

**Features:**
- ✅ Automatic split adjustment
- ✅ TR stage visualization (4 colors)
- ✅ Buy point markers
- ✅ Stop loss levels (8% rule)
- ✅ 50/200 Day or 10/30 Week EMAs
- ✅ Multiple durations (3M - 5Y)

**Use Cases:**
- Identify trend stages
- Find entry points
- Set stop losses
- Track stage changes

**Example:**
```
Menu: 1
Symbol: AAPL
Timeframe: Daily
Duration: 1 Year
→ Generates: AAPL_Daily_1_Year_TR_Chart.png
```

---

### 2️⃣ **Standard Charts** (NEW)

Professional technical analysis charts powered by TradingView:

**Chart Types:**
- 📈 **Line Chart** - Simple price movement
- 🕯️ **Candlestick Chart** - OHLC with patterns
- 📊 **OHLC Chart** - Traditional bar format

**Indicators Included:**
- Volume bars (color-coded)
- RSI (14-period)
- Overbought/Oversold zones

**Interactive Features:**
- Zoom and pan
- Multiple timeframes
- Professional styling
- Opens in web browser

**Use Cases:**
- Quick price overview (Line)
- Detailed pattern analysis (Candlestick)
- Traditional technical analysis (OHLC)
- Identify overbought/oversold (RSI)

**Example:**
```
Menu: 2
Symbol: NVDA
Chart Type: Candlestick
Interval: Daily
→ Generates: NVDA_Candlestick_D_TradingView.html
```

---

### 3️⃣ **Seasonality Analysis** (NEW)

Discover monthly performance patterns:

**Analysis Types:**

**A. Absolute Seasonality**
- Average return per month (Jan-Dec)
- Identifies best/worst months historically
- Green bars (positive), Red bars (negative)

**B. Relative Seasonality**
- Performance vs S&P 500
- Shows when stock outperforms/underperforms market
- Green = beat SPY, Red = trailed SPY

**Periods Available:**
- 1 Year - Recent trend
- 3 Years - Medium-term pattern
- 5 Years - Stable pattern
- 20 Years - Long-term pattern (if data exists)

**Output:**
8 charts per stock (4 periods × 2 types)

**Use Cases:**
- Find seasonally strong months
- Identify weak periods
- Time entries/exits based on patterns
- Compare stock vs market by month

**Example:**
```
Menu: 3
Symbol: MSFT
Periods: All (1Y, 3Y, 5Y, 20Y)
→ Generates: 8 charts showing monthly patterns
```

---

### 4️⃣ **Generate All** (Complete Package)

One-click comprehensive analysis:

**Generates:**
- 1 TR Indicator chart
- 3 Standard charts (Line, Candle, OHLC)
- 8 Seasonality charts (all periods)

**Total:** 12 charts in ~60 seconds

**Perfect for:**
- Complete stock analysis
- Due diligence research
- Portfolio reviews
- Client presentations

**Example:**
```
Menu: 4
Symbol: TSLA
→ Generates: Complete 12-chart package
```

---

## 🎨 **Chart Examples**

### TR Indicator Chart
```
[Price chart with colored background showing stages]
- Dark Green: Stage 3 Uptrend (Strong Buy)
- Lime Green: Stage 2 Uptrend (Buy)
- Yellow: Stage 2 Downtrend (Sell)
- Dark Orange: Stage 3 Downtrend (Strong Sell)
```

### Candlestick Chart
```
[Interactive TradingView chart]
- OHLC candlesticks
- Volume bars below
- RSI indicator
- Zoom/pan controls
```

### Seasonality Chart
```
[Bar chart showing monthly averages]
Jan: +3.2%  ████ (green)
Feb: +1.8%  ██ (green)
Mar: -0.5%  █ (red)
...
```

---

## 📋 **Menu Structure**

```
TR CHART GENERATOR v4.0
══════════════════════════════════════════════════════════

📊 CHART GENERATION:
  1. TR Indicator Chart (Stages & Signals)
  2. Standard Charts (Line/Candlestick/OHLC)
  3. Seasonality Analysis (Monthly Patterns)
  4. Generate All (Complete Package)

🔧 UTILITIES:
  5. View Cache Status
  6. Clear Cache

  0. Exit
══════════════════════════════════════════════════════════
```

---

## 🐛 **Troubleshooting**

### Common Issues

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"API key not found"**
- Check `.env` file exists
- Verify format: `TIINGO_API_KEY=your_key`
- No spaces around `=`

**"Symbol not found"**
- Use uppercase (AAPL not aapl)
- Verify symbol exists
- Try different symbol to test

**Charts not opening**
- Standard charts open in browser automatically
- TR/Seasonality charts saved as PNG
- Check `charts/` folder

**Seasonality fails for 20 years**
- Not all stocks have 20 years of data
- Try shorter period (1Y, 3Y, 5Y)
- Recent IPOs won't have long history

---

## 📁 **File Structure**

```
TR-Chart-Generator-v4.0/
├── chart_menu_v4.0_LOCAL.py    # Main program
├── standard_charts.py           # NEW: Standard charts module
├── seasonality.py               # NEW: Seasonality module
├── stock_cache.py               # Data caching
├── requirements.txt             # Dependencies
├── .env                         # Your API key
└── src/
    ├── tr_enhanced.py           # TR chart generation
    ├── tr_indicator.py
    ├── tr_calculations.py
    └── stock_data_formatter.py
```

---

## 💻 **System Requirements**

- **OS:** Windows 10/11 (64-bit)
- **Python:** 3.11 or higher
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB
- **Internet:** Required for data and TradingView charts

---

## 📦 **Dependencies**

```
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
requests>=2.31.0
python-dotenv>=1.0.0
validators>=0.22.0
```

---

## 🔄 **Caching**

- **24-hour cache** reduces API calls
- **Automatic** - no configuration needed
- **View status** - Option 5 in menu
- **Clear cache** - Option 6 in menu

---

## 📊 **Performance**

| Operation | First Run | Cached |
|-----------|-----------|--------|
| TR Chart | 15-20s | 3-5s |
| Standard Charts (1) | 5s | Instant |
| Seasonality (1 period) | 20-25s | 5-8s |
| Generate All (12 charts) | 60-90s | 20-30s |

---

## 🎓 **Usage Tips**

### For Split-Adjusted Charts
- **Always use TR charts** for stocks with recent splits
- Examples: NVDA, GOOGL, TSLA, AVGO
- TR system automatically adjusts historical prices

### For Pattern Analysis
- **Use Candlestick charts** for detailed technical patterns
- Look for RSI divergences
- Watch volume confirmation

### For Seasonal Strategies
- **Check 5-year seasonality** for stable patterns
- **Compare to 1-year** to see if pattern still holds
- **Use relative charts** to see vs market performance

### For Complete Research
- **Generate All** for comprehensive analysis
- Review TR for stages
- Check standard charts for patterns
- Analyze seasonality for timing

---

## 📞 **Support**

**Issues?**
1. Check troubleshooting section above
2. Verify API key is correct
3. Try with simple symbol (AAPL) first
4. Check Python version: `python --version`

**Feature Requests?**
Email: support@analyzestocks.net

---

## 🔐 **Security**

- API key stored in `.env` (not in code)
- `.env` should be in `.gitignore`
- Never share your API key
- Get your own free key at Tiingo.com

---

## 📝 **Version History**

**v4.0** (November 2025) - **CURRENT**
- ✅ Added Standard Charts (TradingView widgets)
- ✅ Added Seasonality Analysis
- ✅ Added "Generate All" option
- ✅ Enhanced menu system
- ✅ Improved error handling

**v3.6** (November 2025)
- Fixed split adjustment timing
- Improved TR calculations
- Added diagnostic tools

**v3.0** (October 2025)
- Initial release
- TR indicator charts
- Split detection
- Stage visualization

---

## 📜 **License**

**Proprietary Software**  
© 2025 MJ Software LLC  
All rights reserved.

For authorized users only.

---

## ⚠️ **Disclaimer**

This tool is for **educational and informational purposes only**.

- Not financial advice
- Not investment recommendations
- Do your own research
- Trade at your own risk

---

## 🎉 **Get Started Now!**

```bash
python chart_menu_v4.0_LOCAL.py
```

**Generate professional stock analysis in minutes!** 📈

---

**Questions?** support@analyzestocks.net  
**Version:** 4.0 | **MJ Software LLC** | **November 2025**
