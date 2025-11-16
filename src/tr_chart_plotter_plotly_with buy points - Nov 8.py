"""
TR Indicator Chart Plotter - PLOTLY VERSION
Interactive charts with all TR features: bands, markers, buy points, patterns
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime


def plot_tr_indicator_chart_plotly(df, ticker, timeframe='Daily', figsize=(1400, 800)):
    """
    Plot interactive TR indicator chart using Plotly
    
    Features:
    - All 6 TR stages with proper visualization
    - Stage 1: Markers only (green triangles ▲ and red diamonds ◆)
    - Stage 2 & 3: Colored bands
    - Interactive hover tooltips
    - Zoom, pan capabilities
    
    Args:
        df (pd.DataFrame): Data with TR_Status, Date, Close columns
        ticker (str): Stock symbol
        timeframe (str): 'Daily', 'Weekly', or 'Monthly'
        figsize (tuple): Figure size (width, height) in pixels
    
    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    
    # Ensure Date column is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Create figure
    fig = go.Figure()
    
    # ═══════════════════════════════════════════════════════════
    # STAGE 2 & 3: BACKGROUND BANDS (as filled areas)
    # ═══════════════════════════════════════════════════════════
    
    # Define colors for bands
    stage_band_config = {
        'Buy': {'color': 'rgba(144, 238, 144, 0.3)', 'name': 'Stage 2 Uptrend (Buy)'},
        'Strong Buy': {'color': 'rgba(0, 100, 0, 0.3)', 'name': 'Stage 3 Uptrend (Strong Buy)'},
        'Sell': {'color': 'rgba(255, 255, 224, 0.4)', 'name': 'Stage 2 Downtrend (Sell)'},
        'Strong Sell': {'color': 'rgba(255, 165, 0, 0.4)', 'name': 'Stage 3 Downtrend (Strong Sell)'}
    }
    
    # Track and draw bands
    current_band = None
    band_start = None
    bands_added = set()  # Track which bands we've added to legend
    
    def add_band_trace(start_idx, end_idx, band_type):
        """Add a filled area for a TR stage band"""
        band_df = df.iloc[start_idx:end_idx+1]
        config = stage_band_config[band_type]
        
        # Only show in legend once per band type
        show_legend = band_type not in bands_added
        if show_legend:
            bands_added.add(band_type)
        
        fig.add_trace(go.Scatter(
            x=pd.concat([band_df['Date'], band_df['Date'][::-1]]),
            y=pd.concat([pd.Series([df['Close'].min() * 0.95] * len(band_df)),
                        pd.Series([df['Close'].max() * 1.05] * len(band_df))[::-1]]),
            fill='toself',
            fillcolor=config['color'],
            line=dict(width=0),
            name=config['name'],
            showlegend=show_legend,
            hoverinfo='skip',
            legendgroup=band_type
        ))
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        
        if status in stage_band_config:
            if current_band != status:
                # End previous band if exists
                if current_band is not None:
                    add_band_trace(band_start, i-1, current_band)
                # Start new band
                current_band = status
                band_start = i
        else:
            # Stage 1 (Neutral Buy/Sell) - end any active band
            if current_band is not None:
                add_band_trace(band_start, i-1, current_band)
                current_band = None
                band_start = None
    
    # Handle band that extends to end of chart
    if current_band is not None:
        add_band_trace(band_start, len(df)-1, current_band)
    
    # ═══════════════════════════════════════════════════════════
    # PRICE LINE
    # ═══════════════════════════════════════════════════════════
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='Close Price',
        line=dict(color='black', width=2),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' +
                      'Price: $%{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # ═══════════════════════════════════════════════════════════
    # EMA LINES (50/200 for daily, 10/30 for weekly)
    # ═══════════════════════════════════════════════════════════
    
    # Calculate EMAs if they don't exist
    # For Daily: 50 and 200 day EMAs
    # For Weekly: 10 and 30 week EMAs
    if timeframe.lower() == 'daily':
        if 'EMA_50' not in df.columns:
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        if 'EMA_200' not in df.columns:
            df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Plot 50-day EMA (blue)
        if 'EMA_50' in df.columns and df['EMA_50'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['EMA_50'],
                mode='lines',
                name='50 Day EMA',
                line=dict(color='blue', width=1.5, dash='dot'),  # Dotted line
                hovertemplate='<b>50 Day EMA</b><br>' +
                              '%{x|%Y-%m-%d}<br>' +
                              'EMA: $%{y:.2f}<br>' +
                              '<extra></extra>'
            ))
        
        # Plot 200-day EMA (red)
        if 'EMA_200' in df.columns and df['EMA_200'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['EMA_200'],
                mode='lines',
                name='200 Day EMA',
                line=dict(color='red', width=1.5, dash='dot'),  # Dotted line
                hovertemplate='<b>200 Day EMA</b><br>' +
                              '%{x|%Y-%m-%d}<br>' +
                              'EMA: $%{y:.2f}<br>' +
                              '<extra></extra>'
            ))
    else:  # Weekly
        if 'EMA_10' not in df.columns:
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        if 'EMA_30' not in df.columns:
            df['EMA_30'] = df['Close'].ewm(span=30, adjust=False).mean()
        
        # Plot 10-week EMA (blue)
        if 'EMA_10' in df.columns and df['EMA_10'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['EMA_10'],
                mode='lines',
                name='10 Week EMA',
                line=dict(color='blue', width=1.5, dash='dot'),  # Dotted line
                hovertemplate='<b>10 Week EMA</b><br>' +
                              '%{x|%Y-%m-%d}<br>' +
                              'EMA: $%{y:.2f}<br>' +
                              '<extra></extra>'
            ))
        
        # Plot 30-week EMA (red)
        if 'EMA_30' in df.columns and df['EMA_30'].notna().any():
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['EMA_30'],
                mode='lines',
                name='30 Week EMA',
                line=dict(color='red', width=1.5, dash='dot'),  # Dotted line
                hovertemplate='<b>30 Week EMA</b><br>' +
                              '%{x|%Y-%m-%d}<br>' +
                              'EMA: $%{y:.2f}<br>' +
                              '<extra></extra>'
            ))
    
    # ═══════════════════════════════════════════════════════════
    # STAGE 1 MARKERS: Triangles & Diamonds
    # ═══════════════════════════════════════════════════════════
    
    # Track first occurrences for markers
    prev_status = None
    neutral_buy_dates = []
    neutral_buy_prices = []
    neutral_sell_dates = []
    neutral_sell_prices = []
    
    for i in range(len(df)):
        status = df.iloc[i]['TR_Status']
        
        # Neutral Buy - Green Triangle (Stage 1 Uptrend)
        if status == 'Neutral Buy' and prev_status != 'Neutral Buy':
            neutral_buy_dates.append(df.iloc[i]['Date'])
            neutral_buy_prices.append(df.iloc[i]['Close'])
        
        # Neutral Sell - Red Diamond (Stage 1 Downtrend)
        elif status == 'Neutral Sell' and prev_status != 'Neutral Sell':
            neutral_sell_dates.append(df.iloc[i]['Date'])
            neutral_sell_prices.append(df.iloc[i]['Close'])
        
        prev_status = status
    
    # Add Neutral Buy markers (green triangles)
    if neutral_buy_dates:
        fig.add_trace(go.Scatter(
            x=neutral_buy_dates,
            y=neutral_buy_prices,
            mode='markers',
            name='Stage 1 Uptrend',
            marker=dict(
                symbol='triangle-up',
                size=10,  # Reduced from 12 to 10 for consistency
                color='lightgreen',
                line=dict(color='darkgreen', width=1.5)  # Match diamond border
            ),
            hovertemplate='<b>Stage 1 Uptrend Entry</b><br>' +
                          '%{x|%Y-%m-%d}<br>' +
                          'Price: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
    
    # Add Neutral Sell markers (red diamonds)
    if neutral_sell_dates:
        fig.add_trace(go.Scatter(
            x=neutral_sell_dates,
            y=neutral_sell_prices,
            mode='markers',
            name='Stage 1 Downtrend',
            marker=dict(
                symbol='diamond',
                size=8,  # Reduced from 10 to 8
                color='red',
                line=dict(color='darkred', width=1.5)  # Also reduced border width
            ),
            hovertemplate='<b>Stage 1 Downtrend Entry</b><br>' +
                          '%{x|%Y-%m-%d}<br>' +
                          'Price: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
    
    # ═══════════════════════════════════════════════════════════
    # CHART LAYOUT & FORMATTING
    # ═══════════════════════════════════════════════════════════
    
    fig.update_layout(
        title=dict(
            text=f'{ticker} - TR Indicator Chart ({timeframe})',
            font=dict(size=20, color='#1f77b4', family='Arial Black'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Date',
            title_font=dict(size=14, color='black'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            # Set initial range to actual data range (no blank space!)
            range=[df['Date'].min(), df['Date'].max()],
            fixedrange=False,  # Allow zooming
            type='date'
        ),
        yaxis=dict(
            title='Price ($)',
            title_font=dict(size=14, color='black'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            tickformat='$,.2f',
            autorange=True,  # Auto-scale Y-axis
            fixedrange=False
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        width=figsize[0],
        height=figsize[1],
        legend=dict(
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='left',
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='black',
            borderwidth=1
        ),
        margin=dict(l=60, r=30, t=80, b=60)
    )
    
    # CRITICAL: Configure Y-axis to auto-scale when X-axis range changes
    fig.update_yaxes(autorange=True)
    
    # Add custom time period buttons with Y-axis auto-scaling
    # These buttons will dynamically adjust BOTH X and Y axes
    
    # Calculate time period ranges
    from datetime import timedelta
    max_date = df['Date'].max()
    
    # Helper function to get Y range for visible X range
    def get_y_range_for_period(days):
        start_date = max_date - timedelta(days=days)
        visible_data = df[df['Date'] >= start_date]
        if len(visible_data) > 0:
            y_min = visible_data['Close'].min() * 0.95  # 5% padding below
            y_max = visible_data['Close'].max() * 1.05  # 5% padding above
            return [y_min, y_max]
        return None
    
    # Create custom buttons with both X and Y range updates
    buttons = []
    
    # 1M button
    y_range_1m = get_y_range_for_period(30)
    if y_range_1m:
        buttons.append(dict(
            label="1M",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=30), max_date],
                "yaxis.range": y_range_1m
            }]
        ))
    
    # 3M button
    y_range_3m = get_y_range_for_period(90)
    if y_range_3m:
        buttons.append(dict(
            label="3M",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=90), max_date],
                "yaxis.range": y_range_3m
            }]
        ))
    
    # 6M button
    y_range_6m = get_y_range_for_period(180)
    if y_range_6m:
        buttons.append(dict(
            label="6M",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=180), max_date],
                "yaxis.range": y_range_6m
            }]
        ))
    
    # 1Y button
    y_range_1y = get_y_range_for_period(365)
    if y_range_1y:
        buttons.append(dict(
            label="1Y",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=365), max_date],
                "yaxis.range": y_range_1y
            }]
        ))
    
    # 3Y button
    y_range_3y = get_y_range_for_period(1095)
    if y_range_3y:
        buttons.append(dict(
            label="3Y",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=1095), max_date],
                "yaxis.range": y_range_3y
            }]
        ))
    
    # 5Y button
    y_range_5y = get_y_range_for_period(1825)
    if y_range_5y:
        buttons.append(dict(
            label="5Y",
            method="relayout",
            args=[{
                "xaxis.range": [max_date - timedelta(days=1825), max_date],
                "yaxis.range": y_range_5y
            }]
        ))
    
    # ALL button
    all_y_min = df['Close'].min() * 0.95
    all_y_max = df['Close'].max() * 1.05
    buttons.append(dict(
        label="ALL",
        method="relayout",
        args=[{
            "xaxis.range": [df['Date'].min(), df['Date'].max()],
            "yaxis.range": [all_y_min, all_y_max]
        }]
    ))
    
    # Add buttons to figure
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.15,
                yanchor="top",
                bgcolor='rgba(230, 230, 230, 0.8)',
                bordercolor='#333',
                borderwidth=1,
                font=dict(size=11, color='black')
            )
        ]
    )
    
    return fig


def plot_tr_with_buy_zones_plotly(df, ticker, timeframe='Daily', figsize=(1400, 1000)):
    """
    Enhanced TR chart with buy points, stop losses, and pattern detection
    
    Features:
    - All TR stage bands and markers
    - Suggested buy points (black dashed lines)
    - Stop loss levels (red dashed lines)
    - Pattern detection annotations
    - Interactive hover tooltips
    
    Args:
        df (pd.DataFrame): Full TR data with all columns
        ticker (str): Stock symbol
        timeframe (str): 'Daily', 'Weekly', or 'Monthly'
        figsize (tuple): Figure size (width, height) in pixels
    
    Returns:
        plotly.graph_objects.Figure: Enhanced interactive chart
    """
    
    # Start with basic TR chart
    fig = plot_tr_indicator_chart_plotly(df, ticker, timeframe, figsize)
    
    # ═══════════════════════════════════════════════════════════
    # BUY POINTS & STOP LOSS LINES
    # ═══════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════
    # BUY POINTS & STOP LOSS - TEMPORARILY DISABLED
    # ═══════════════════════════════════════════════════════════
    
    # TODO: Re-enable after fixing the logic
    # Disabled to focus on TR bands and chart duration first
    
    pass  # Placeholder
    
    # ═══════════════════════════════════════════════════════════
    # PATTERN DETECTION ANNOTATIONS
    # ═══════════════════════════════════════════════════════════
    
    pattern_columns = [col for col in df.columns if 'Pattern' in col or 'pattern' in col]
    
    for pattern_col in pattern_columns:
        patterns = df[df[pattern_col].notna()]
        
        for idx, row in patterns.iterrows():
            pattern_name = row[pattern_col]
            
            # Add annotation for pattern
            fig.add_annotation(
                x=row['Date'],
                y=row['Close'] * 1.05,  # Slightly above price
                text=f"📊 {pattern_name}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='blue',
                bgcolor='rgba(173, 216, 230, 0.8)',
                bordercolor='blue',
                borderwidth=2,
                font=dict(size=10, color='darkblue')
            )
    
    return fig


def quick_tr_chart_plotly(ticker, timeframe='daily', duration_days=180, chart_type='basic'):
    """
    Quick function to generate interactive Plotly TR chart
    
    Args:
        ticker (str): Stock symbol
        timeframe (str): 'daily', 'weekly', or 'monthly'
        duration_days (int): Historical data period
        chart_type (str): 'basic' or 'enhanced'
    
    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    from tr_enhanced import analyze_stock_complete_tr
    
    print(f"\n🎨 Generating interactive {chart_type} TR chart for {ticker}...")
    
    # Get TR data
    df = analyze_stock_complete_tr(
        ticker=ticker,
        timeframe=timeframe,
        duration_days=duration_days
    )
    
    if df is None:
        print(f"❌ Could not get data for {ticker}")
        return None
    
    # Generate appropriate chart
    if chart_type == 'enhanced':
        fig = plot_tr_with_buy_zones_plotly(
            df=df,
            ticker=ticker,
            timeframe=timeframe.capitalize()
        )
    else:
        fig = plot_tr_indicator_chart_plotly(
            df=df,
            ticker=ticker,
            timeframe=timeframe.capitalize()
        )
    
    print(f"✅ Interactive TR chart generated!")
    return fig


# ═══════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎨 TR INDICATOR CHART PLOTTER - PLOTLY VERSION")
    print("="*80)
    
    # Test chart generation
    ticker = 'AAPL'
    print(f"\n📊 Creating interactive chart for {ticker}...")
    
    fig = quick_tr_chart_plotly(ticker, timeframe='daily', duration_days=180, chart_type='basic')
    
    if fig:
        # Show in browser
        fig.show()
        print("\n✅ Chart displayed in browser!")
    
    print("="*80)
