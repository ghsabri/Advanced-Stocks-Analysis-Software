"""
TR Indicator Chart Plotter
Visualizes stock prices with TR indicator stages
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from datetime import datetime


def plot_tr_indicator_chart(df, ticker, timeframe='Daily', save_path=None, figsize=(16, 10)):
    """
    Plot stock price chart with TR indicator visualization
    
    TR INDICATOR VISUAL RULES:
    ═══════════════════════════════════════════════════════════
    
    STAGE 1 SIGNALS (Markers only, white background):
    - Uptrend Stage 1: Small light green triangle (▲) pointing up
    - Downtrend Stage 1: Small red diamond (◆)
    - Marker appears ONLY on the FIRST price point of Stage 1
    
    STAGE 2 & 3 SIGNALS (Background bands):
    - Uptrend Stage 2: Light green vertical band
    - Uptrend Stage 3: Dark green vertical band
    - Downtrend Stage 2: Light yellow vertical band
    - Downtrend Stage 3: Orange vertical band
    - Bands disappear when returning to Stage 1
    
    Args:
        df (pd.DataFrame): Data with TR_Status, Date, Close, High, Low
        ticker (str): Stock symbol
        timeframe (str): 'Daily', 'Weekly', or 'Monthly'
        save_path (str): Path to save chart (optional)
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: The chart figure
    """
    
    # Ensure Date column is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot price line (Close prices)
    ax.plot(df['Date'], df['Close'], color='black', linewidth=1.5, label='Close Price', zorder=5)
    
    # ═══════════════════════════════════════════════════════════
    # STAGE 2 & 3: BACKGROUND BANDS
    # ═══════════════════════════════════════════════════════════
    
    # Define colors for background bands
    stage_colors = {
        'Buy': '#90EE90',              # Light green (Uptrend Stage 2)
        'Strong Buy': '#006400',        # Dark green (Uptrend Stage 3)
        'Sell': '#FFFFE0',             # Light yellow (Downtrend Stage 2)
        'Strong Sell': '#FFA500'        # Orange (Downtrend Stage 3)
    }
    
    # Track band regions
    current_band_status = None
    band_start_idx = None
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        
        # Check if we should draw a band for this status
        if status in stage_colors:
            if current_band_status != status:
                # New band starting
                current_band_status = status
                band_start_idx = i
        else:
            # Status is Neutral Buy or Neutral Sell (Stage 1) - end any active band
            if current_band_status is not None:
                # Draw the band that just ended
                band_end_idx = i - 1
                
                # Get date range for the band
                x_start = df.iloc[band_start_idx]['Date']
                x_end = df.iloc[band_end_idx]['Date']
                
                # Calculate width (time span)
                width = (x_end - x_start).total_seconds() / 86400  # Convert to days
                
                # Draw vertical band from bottom to top of chart
                y_min, y_max = ax.get_ylim()
                rect = Rectangle(
                    (x_start, y_min), 
                    width, 
                    y_max - y_min,
                    facecolor=stage_colors[current_band_status],
                    alpha=0.3,
                    zorder=1
                )
                ax.add_patch(rect)
                
                # Reset
                current_band_status = None
                band_start_idx = None
    
    # Handle case where chart ends while in a band
    if current_band_status is not None and band_start_idx is not None:
        x_start = df.iloc[band_start_idx]['Date']
        x_end = df.iloc[-1]['Date']
        width = (x_end - x_start).total_seconds() / 86400
        
        y_min, y_max = ax.get_ylim()
        rect = Rectangle(
            (x_start, y_min), 
            width, 
            y_max - y_min,
            facecolor=stage_colors[current_band_status],
            alpha=0.3,
            zorder=1
        )
        ax.add_patch(rect)
    
    # ═══════════════════════════════════════════════════════════
    # STAGE 1: MARKERS (Triangle & Diamond)
    # ═══════════════════════════════════════════════════════════
    
    # Track previous status to detect FIRST occurrence of Stage 1
    prev_status = None
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        date = df.iloc[i]['Date']
        price = df.iloc[i]['Close']
        
        # Check if this is the FIRST bar of Stage 1 (Neutral Buy or Neutral Sell)
        if i > 0:
            prev_status = df.iloc[i - 1]['TR_Status']
        
        # Neutral Buy (Stage 1 Uptrend) - Light green triangle
        if status == 'Neutral Buy':
            # Only mark the FIRST occurrence (transition into Stage 1)
            if prev_status != 'Neutral Buy':
                ax.scatter(
                    date, 
                    price, 
                    marker='^',              # Triangle pointing up
                    color='lightgreen', 
                    s=100,                   # Size
                    edgecolors='darkgreen', 
                    linewidths=1,
                    zorder=10,
                    label='Stage 1 Uptrend' if i == 0 else ''
                )
        
        # Neutral Sell (Stage 1 Downtrend) - Red diamond
        elif status == 'Neutral Sell':
            # Only mark the FIRST occurrence (transition into Stage 1)
            if prev_status != 'Neutral Sell':
                ax.scatter(
                    date, 
                    price, 
                    marker='D',              # Diamond
                    color='red', 
                    s=80,                    # Size (slightly smaller)
                    edgecolors='darkred', 
                    linewidths=1,
                    zorder=10,
                    label='Stage 1 Downtrend' if i == 0 else ''
                )
    
    # ═══════════════════════════════════════════════════════════
    # CHART FORMATTING
    # ═══════════════════════════════════════════════════════════
    
    # Set labels and title
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
    ax.set_title(f'{ticker} - TR Indicator Chart ({timeframe})', fontsize=16, fontweight='bold', pad=20)
    
    # Format grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f'${y:.2f}'))
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Create custom legend
    legend_elements = [
        plt.Line2D([0], [0], color='black', linewidth=2, label='Close Price'),
        plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='lightgreen', 
                   markeredgecolor='darkgreen', markersize=10, label='Stage 1 Uptrend', linestyle='None'),
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='red', 
                   markeredgecolor='darkred', markersize=8, label='Stage 1 Downtrend', linestyle='None'),
        mpatches.Patch(facecolor='#90EE90', alpha=0.3, label='Stage 2 Uptrend (Buy)'),
        mpatches.Patch(facecolor='#006400', alpha=0.3, label='Stage 3 Uptrend (Strong Buy)'),
        mpatches.Patch(facecolor='#FFFFE0', alpha=0.3, label='Stage 2 Downtrend (Sell)'),
        mpatches.Patch(facecolor='#FFA500', alpha=0.3, label='Stage 3 Downtrend (Strong Sell)')
    ]
    
    ax.legend(handles=legend_elements, loc='best', fontsize=10, framealpha=0.9)
    
    # Tight layout
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Chart saved to: {save_path}")
    
    return fig


def plot_tr_with_buy_zones(df, ticker, timeframe='Daily', save_path=None, figsize=(16, 12)):
    """
    Plot TR indicator chart with buy zones, buy points, and stop losses
    
    This is an enhanced version that includes:
    - All TR indicator visualization (bands and markers)
    - Buy points (horizontal lines at peaks)
    - Buy zones (±5% shaded regions)
    - Stop loss levels (8% below buy points)
    - Buy signals (green stars)
    - Exit signals (red X markers)
    
    Args:
        df (pd.DataFrame): Complete TR data with all indicators
        ticker (str): Stock symbol
        timeframe (str): 'Daily', 'Weekly', or 'Monthly'
        save_path (str): Path to save chart (optional)
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: The chart figure
    """
    
    # First create the basic TR chart
    fig = plot_tr_indicator_chart(df, ticker, timeframe, save_path=None, figsize=figsize)
    ax = fig.axes[0]
    
    # ═══════════════════════════════════════════════════════════
    # ADD BUY ZONES, BUY POINTS, AND STOP LOSSES
    # ═══════════════════════════════════════════════════════════
    
    if 'Buy_Point' in df.columns and 'Buy_Zone_Lower' in df.columns:
        # Track current buy point to avoid drawing duplicates
        current_buy_point = None
        
        for i in range(len(df)):
            buy_point = df.iloc[i].get('Buy_Point', np.nan)
            
            if pd.notna(buy_point) and buy_point != current_buy_point:
                current_buy_point = buy_point
                
                # Get zone boundaries
                zone_lower = df.iloc[i].get('Buy_Zone_Lower', np.nan)
                zone_upper = df.iloc[i].get('Buy_Zone_Upper', np.nan)
                stop_loss = df.iloc[i].get('Stop_Loss', np.nan)
                
                date = df.iloc[i]['Date']
                
                # Find when this buy point ends (when a new buy point appears)
                end_idx = i
                for j in range(i + 1, len(df)):
                    next_bp = df.iloc[j].get('Buy_Point', np.nan)
                    if pd.notna(next_bp) and next_bp != buy_point:
                        end_idx = j - 1
                        break
                    end_idx = j
                
                end_date = df.iloc[end_idx]['Date']
                
                # Draw buy zone (shaded region)
                if pd.notna(zone_lower) and pd.notna(zone_upper):
                    ax.fill_between(
                        [date, end_date],
                        [zone_lower, zone_lower],
                        [zone_upper, zone_upper],
                        color='blue',
                        alpha=0.1,
                        zorder=2
                    )
                
                # Draw buy point line (dashed blue)
                ax.hlines(
                    y=buy_point,
                    xmin=date,
                    xmax=end_date,
                    colors='blue',
                    linestyles='dashed',
                    linewidth=1.5,
                    alpha=0.7,
                    zorder=3
                )
                
                # Draw stop loss line (dashed red)
                if pd.notna(stop_loss):
                    ax.hlines(
                        y=stop_loss,
                        xmin=date,
                        xmax=end_date,
                        colors='red',
                        linestyles='dashed',
                        linewidth=1.5,
                        alpha=0.7,
                        zorder=3
                    )
    
    # ═══════════════════════════════════════════════════════════
    # ADD BUY AND EXIT SIGNALS
    # ═══════════════════════════════════════════════════════════
    
    if 'Buy_Signal' in df.columns:
        buy_signals = df[df['Buy_Signal'] == True]
        if not buy_signals.empty:
            ax.scatter(
                buy_signals['Date'],
                buy_signals['Close'],
                marker='*',
                color='green',
                s=300,
                edgecolors='darkgreen',
                linewidths=2,
                zorder=15,
                label='BUY Signal'
            )
    
    if 'Exit_Signal' in df.columns:
        exit_signals = df[df['Exit_Signal'] == True]
        if not exit_signals.empty:
            ax.scatter(
                exit_signals['Date'],
                exit_signals['Close'],
                marker='X',
                color='red',
                s=200,
                edgecolors='darkred',
                linewidths=2,
                zorder=15,
                label='EXIT Signal'
            )
    
    # Update legend
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Enhanced chart saved to: {save_path}")
    
    return fig


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTION: QUICK CHART FROM TICKER
# ═══════════════════════════════════════════════════════════════════

def quick_tr_chart(ticker, timeframe='daily', duration_days=180, chart_type='basic'):
    """
    Quick function to generate TR chart directly from ticker symbol
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL')
        timeframe (str): 'daily', 'weekly', or 'monthly'
        duration_days (int): Number of days of historical data
        chart_type (str): 'basic' or 'enhanced'
    
    Returns:
        matplotlib.figure.Figure: The chart
    """
    from tr_enhanced import analyze_stock_complete_tr
    
    print(f"\n🎨 Generating {chart_type} TR chart for {ticker}...")
    
    # Get TR data
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe=timeframe,
        duration_days=duration_days
    )
    
    if df is None:
        print(f"❌ Could not get data for {ticker}")
        return None
    
    # Generate chart
    save_path = f"charts/{ticker}_{timeframe.capitalize()}_TR_Chart.png"
    
    if chart_type == 'enhanced':
        fig = plot_tr_with_buy_zones(
            df=df,
            ticker=ticker,
            timeframe=timeframe.capitalize(),
            save_path=save_path
        )
    else:
        fig = plot_tr_indicator_chart(
            df=df,
            ticker=ticker,
            timeframe=timeframe.capitalize(),
            save_path=save_path
        )
    
    plt.show()
    
    return fig


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*80)
    print("🎨 TR INDICATOR CHART PLOTTER")
    print("="*80)
    
    # Generate sample charts
    tickers = ['AAPL', 'MSFT', 'TSLA']
    
    for ticker in tickers:
        print(f"\n📊 Creating chart for {ticker}...")
        fig = quick_tr_chart(ticker, timeframe='daily', duration_days=180, chart_type='basic')
        
    print("\n✅ All charts generated!")
    print("="*80)
