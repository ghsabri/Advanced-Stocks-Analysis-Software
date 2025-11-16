# Daily Trading Guide - Calculation Reference
**Technical Documentation for Support/Resistance Calculations**

---

## 📐 CALCULATION FORMULAS

### 1. **PIVOT POINTS (Classic Method)**

**Formula:**
```
Pivot Point (PP) = (High + Low + Close) / 3

Resistance 1 (R1) = (2 × PP) - Low
Resistance 2 (R2) = PP + (High - Low)
Resistance 3 (R3) = High + 2 × (PP - Low)

Support 1 (S1) = (2 × PP) - High
Support 2 (S2) = PP - (High - Low)
Support 3 (S3) = Low - 2 × (High - PP)
```

**Example (ORCL from your Excel):**
```
Previous Day:
High = 237.45
Low = 228.83
Close = 240.83

Calculations:
PP = (237.45 + 228.83 + 240.83) / 3 = 235.70
R1 = (2 × 235.70) - 228.83 = 242.57
R2 = 235.70 + (237.45 - 228.83) = 244.32
R3 = 237.45 + 2 × (235.70 - 228.83) = 251.19
S1 = (2 × 235.70) - 237.45 = 233.95
S2 = 235.70 - (237.45 - 228.83) = 227.08
S3 = 228.83 - 2 × (237.45 - 235.70) = 225.33
```

---

### 2. **FIBONACCI RETRACEMENTS**

**Formula:**
```
For Uptrend (from Low to High):
38.2% Level = Low + (0.382 × Range)
50.0% Level = Low + (0.500 × Range)
61.8% Level = Low + (0.618 × Range)

For Downtrend (from High to Low):
38.2% Level = High - (0.382 × Range)
50.0% Level = High - (0.500 × Range)
61.8% Level = High - (0.618 × Range)

Where: Range = High - Low
```

**Example (1 Month for ORCL):**
```
1 Month High = 322.54
1 Month Low = 228.83
Range = 322.54 - 228.83 = 93.71

From High (Retracement):
38.2% from High = 322.54 - (0.382 × 93.71) = 286.77
50.0% from High = 322.54 - (0.500 × 93.71) = 275.71

From Low (Retracement):
38.2% from Low = 228.83 + (0.382 × 93.71) = 264.66
```

---

### 3. **MOVING AVERAGES (EMA)**

**Exponential Moving Average (EMA) Formula:**
```
EMA_today = (Price_today × Multiplier) + (EMA_yesterday × (1 - Multiplier))

Where:
Multiplier = 2 / (Period + 1)

For 9-period EMA: Multiplier = 2 / (9 + 1) = 0.2
For 20-period EMA: Multiplier = 2 / (20 + 1) = 0.095
For 50-period EMA: Multiplier = 2 / (50 + 1) = 0.039
```

**Why EMA instead of SMA:**
- More responsive to recent price changes
- Better for support/resistance identification
- Matches your Excel VBA implementation

**Python Implementation:**
```python
ema_9 = df['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
```

---

### 4. **STANDARD DEVIATION**

**Formula (Sample Standard Deviation):**
```
σ = √(Σ(x - x̄)² / (n - 1))

Where:
x = Each price in the sample
x̄ = Mean of all prices
n = Number of periods (14)
```

**Resistance/Support Levels:**
```
+1σ Resistance = Current Price + (1 × σ)
+2σ Resistance = Current Price + (2 × σ)
+3σ Resistance = Current Price + (3 × σ)

-1σ Support = Current Price - (1 × σ)
-2σ Support = Current Price - (2 × σ)
-3σ Support = Current Price - (3 × σ)
```

**Example (ORCL):**
```
Last 14 closing prices: [240.83, 237.45, ...]
Mean (x̄) = 235.50
Standard Deviation (σ) = 8.50

Levels:
+1σ = 236.20 + 8.50 = 244.70
+2σ = 236.20 + 17.00 = 253.20
+3σ = 236.20 + 25.50 = 261.70

-1σ = 236.20 - 8.50 = 227.70
-2σ = 236.20 - 17.00 = 219.20
-3σ = 236.20 - 25.50 = 210.70
```

---

### 5. **RSI LEVELS (Reverse RSI)**

**Standard RSI Formula:**
```
RSI = 100 - (100 / (1 + RS))

Where:
RS (Relative Strength) = Average Gain / Average Loss
```

**Reverse RSI (Calculate Price for Target RSI):**
```
Given:
- Current Price
- Average Gain (14-period)
- Average Loss (14-period)
- Target RSI (20%, 30%, 50%, 70%, 80%)

This is a complex calculation that requires iterative solving.
```

**Simplified Approximation (Used in Code):**
```python
def reverse_rsi_approx(current_price, target_rsi):
    if target_rsi > 50:
        # RSI above 50 = price needs to rise
        price_change_pct = (target_rsi - 50) / 50 * 0.1
        return current_price * (1 + price_change_pct)
    else:
        # RSI below 50 = price needs to fall
        price_change_pct = (50 - target_rsi) / 50 * 0.1
        return current_price * (1 - price_change_pct)
```

**Example (ORCL at $236.20):**
```
RSI 80% = 236.20 × (1 + 0.06) = $250.37 (approx)
RSI 70% = 236.20 × (1 + 0.04) = $245.65 (approx)
RSI 50% = 236.20 (neutral)
RSI 30% = 236.20 × (1 - 0.04) = $226.75 (approx)
RSI 20% = 236.20 × (1 - 0.06) = $222.03 (approx)
```

**Note:** These are approximations. For exact RSI levels, would need to solve:
```
Target_RSI = 100 - (100 / (1 + (Avg_Gain / Avg_Loss)))
```

---

## 📊 HIGH/LOW TIMEFRAMES

### **1 Month:**
```
Date Range: Current Date - 30 days
Calculation: Max(High) and Min(Low) within range
```

### **3 Months / 13 Weeks:**
```
Date Range: Current Date - 91 days (or 13 weeks)
Calculation: Max(High) and Min(Low) within range
```

### **1 Year / 52 Weeks:**
```
Date Range: Current Date - 365 days
Calculation: Max(High) and Min(Low) within range
```

---

## 🎯 SORTING AND DISPLAY

### **Sort Order:**
```
All levels sorted DESCENDING by price (highest to lowest)
```

**Why?**
- Easy to see resistance levels above current price
- Easy to see support levels below current price
- Matches traditional support/resistance charts

---

## 🎨 COLOR CODING LOGIC

### **Decision Tree:**

```
IF price level = Last Price OR Previous Close:
    → Color: YELLOW (#FFFF99)

ELIF price level > current_price:
    IF "High" in description OR "Resistance" in description OR "Pivot Point" in description:
        → Color: ORANGE (#FFE6CC)
    ELIF "Moving Average" in description:
        → Color: BLUE (#CCE5FF)
    ELSE:
        → Color: ORANGE (#FFE6CC)

ELIF price level < current_price:
    IF "Low" in description OR "Support" in description:
        → Color: BLUE (#CCE5FF)
    ELIF "Moving Average" in description:
        → Color: ORANGE (#FFE6CC)
    ELSE:
        → Color: BLUE (#CCE5FF)
```

**Reasoning:**
- **Above price = Resistance** (orange) - price needs to break through to go higher
- **Below price = Support** (blue) - price may bounce off these levels
- **Moving Averages** - color based on whether they're acting as support or resistance
- **Current levels** (yellow) - reference point for all other levels

---

## 🔄 DAILY VS WEEKLY DIFFERENCES

### **Daily Timeframe:**
```
Interval: 1d (daily bars)
Period Description: "Days" (e.g., "50 Days Exponential Moving Average")
Pivot Points: Based on previous day's High, Low, Close
Timeframe Ranges:
  - 1 Month = Last 30 days
  - 3 Months = Last 91 days  
  - 1 Year = Last 365 days
```

### **Weekly Timeframe:**
```
Interval: 1wk (weekly bars)
Period Description: "Weeks" (e.g., "50 Weeks Exponential Moving Average")
Pivot Points: Based on previous week's High, Low, Close
Timeframe Ranges:
  - 1 Month = Last ~4 weeks
  - 3 Months = Last ~13 weeks
  - 1 Year = Last ~52 weeks
```

---

## 🧪 VALIDATION TESTING

### **How to Verify Calculations:**

1. **Pivot Points:**
   ```
   Compare with: https://www.investing.com/technical/pivot-points
   Or calculate manually using High/Low/Close from previous period
   ```

2. **Fibonacci Levels:**
   ```
   Compare with: TradingView Fibonacci Retracement tool
   Manually verify: (High - Low) × percentage + Low
   ```

3. **Moving Averages:**
   ```
   Compare with: TradingView or Yahoo Finance chart
   Verify EMA 9, 20, 50 match chart overlays
   ```

4. **Standard Deviation:**
   ```
   Calculate in Excel: =STDEV.S(range)
   Compare with last 14 closing prices
   ```

5. **RSI Levels:**
   ```
   These are approximations - verify price movements
   make sense relative to current RSI
   ```

---

## 📈 EXAMPLE WALKTHROUGH: ORCL

### **Input Data:**
```
Ticker: ORCL
Timeframe: Daily
Last Price: $236.20
Previous Close: $240.83
Last High: $237.45
Last Low: $228.83
```

### **Expected Output (Sample):**

| Support / Resistance | Key Levels | Description |
|---------------------|------------|-------------|
| 14 Period RSI at 80% | $436.24 | 14 Period RSI at 80% |
| 1Year High | $345.72 | 1 Year High |
| Price - 3σ Resistance | $286.62 | Price - 3 Standard Deviation Resistance |
| Pivot Point 3rd Resistance | $256.53 | Pivot Point 3rd Resistance |
| Pivot Point | $241.71 | Pivot Point |
| **Last Price** | **$236.20** | **Last Price** (YELLOW) |
| Pivot Point 1st Support | $236.19 | Pivot Point 1st Support |
| Low | $228.83 | Low |
| 1Year Low | $116.86 | 1 Year Low |

*Full output would have ~40-50 levels*

---

## 💻 CODE SNIPPETS

### **Getting Data with Cache:**
```python
from cached_data import get_stock_data
from universal_cache import get_cached_data

# Method 1: Using cached_data wrapper
df = get_stock_data(ticker, timeframe='daily')

# Method 2: Direct cache access
df = get_cached_data(
    ticker='AAPL',
    start_date='2023-01-01',
    end_date='2025-11-14',
    interval='1d'
)
```

### **Calculating Pivot Points:**
```python
def calculate_pivot_points(high, low, close):
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    r2 = pp + (high - low)
    r3 = high + 2 * (pp - low)
    s1 = 2 * pp - high
    s2 = pp - (high - low)
    s3 = low - 2 * (high - pp)
    return {'PP': pp, 'R1': r1, 'R2': r2, 'R3': r3, 
            'S1': s1, 'S2': s2, 'S3': s3}
```

### **Sorting Results:**
```python
# Sort descending by price
result_df = result_df.sort_values('Key Levels', ascending=False)
```

---

## 🐛 DEBUGGING TIPS

### **If Levels Don't Match Excel:**

1. **Check data source:**
   ```python
   # Verify last price matches
   print(f"Last Close: {df['Close'].iloc[-1]}")
   print(f"Last High: {df['High'].iloc[-1]}")
   print(f"Last Low: {df['Low'].iloc[-1]}")
   ```

2. **Check timeframe:**
   ```python
   # Verify interval
   print(f"Interval: {interval}")  # Should be '1d' or '1wk'
   ```

3. **Check date ranges:**
   ```python
   # Verify historical data availability
   print(f"Data from {df.index[0]} to {df.index[-1]}")
   print(f"Number of periods: {len(df)}")
   ```

4. **Manual calculation:**
   ```python
   # Verify pivot point calculation
   high = df['High'].iloc[-1]
   low = df['Low'].iloc[-1]
   close = df['Close'].iloc[-2]  # Previous close
   pp = (high + low + close) / 3
   print(f"Manual PP: {pp}")
   ```

---

## ✅ ACCURACY CHECKLIST

- [ ] Pivot Points match standard PP calculator
- [ ] Fibonacci levels are correct percentages
- [ ] Moving Averages match TradingView
- [ ] Standard Deviation reasonable (typically 2-5% of price)
- [ ] RSI levels increase monotonically (20% < 30% < 50% < 70% < 80%)
- [ ] High/Low values match recent price history
- [ ] All calculations use proper previous period data
- [ ] Weekly timeframe uses weekly bars (not daily)

---

## 📚 REFERENCES

### **Trading Concepts:**
- Pivot Points: https://www.investopedia.com/terms/p/pivotpoint.asp
- Fibonacci: https://www.investopedia.com/terms/f/fibonacciretracement.asp
- EMAs: https://www.investopedia.com/terms/e/ema.asp
- Standard Deviation: https://www.investopedia.com/terms/s/standarddeviation.asp
- RSI: https://www.investopedia.com/terms/r/rsi.asp

### **Similar Tools:**
- Barchart Trader's Cheat Sheet: https://www.barchart.com/stocks/quotes/
- Investing.com Pivot Points: https://www.investing.com/technical/pivot-points
- TradingView Technical Analysis: https://www.tradingview.com/

---

## 🎓 LEARNING RESOURCES

### **For Users:**
1. Watch Barchart video on Trader's Cheat Sheet usage
2. Practice identifying support/resistance on charts
3. Backtest: Do levels actually hold in practice?
4. Study confluence zones (multiple levels close together)

### **For Developers:**
1. Study pivot point variations (Camarilla, Fibonacci, Woodie's)
2. Learn advanced Fibonacci techniques (extensions, fans)
3. Understand RSI calculation in depth
4. Study market profile and volume-based levels

---

**Last Updated:** November 14, 2025  
**Version:** 1.0  
**Status:** Complete ✅
