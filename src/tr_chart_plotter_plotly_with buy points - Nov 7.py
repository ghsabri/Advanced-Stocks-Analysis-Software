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
                size=12,
                color='lightgreen',
                line=dict(color='darkgreen', width=2)
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
                size=10,
                color='red',
                line=dict(color='darkred', width=2)
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
            titlefont=dict(size=14, color='black'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            # Add range selector buttons - data fetched for 5Y, display what user selects
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=3, label="3Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="ALL")
                ]),
                bgcolor='rgba(230, 230, 230, 0.8)',
                activecolor='#1f77b4',
                bordercolor='#333',
                borderwidth=1,
                font=dict(size=11, color='black'),
                x=0.01,
                y=1.15,
                xanchor='left',
                yanchor='top'
            ),
            # Set initial display to 1 year (not ALL) to avoid blank space
            range=[
                df['Date'].max() - pd.Timedelta(days=365),  # 1 year back
                df['Date'].max()  # to latest date
            ],
            type='date'
        ),
        yaxis=dict(
            title='Price ($)',
            titlefont=dict(size=14, color='black'),
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            zeroline=False,
            tickformat='$,.2f'
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
    # BUY POINTS & STOP LOSS - SHOW ONLY WHEN THEY CHANGE
    # ═══════════════════════════════════════════════════════════
    
    # Only draw dashes when a NEW buy point is detected (value changed from previous row)
    
    if 'Buy_Point' in df.columns and 'Stop_Loss' in df.columns:
        # Track previous values to detect changes
        prev_buy = None
        prev_stop = None
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            buy_point = row.get('Buy_Point')
            stop_loss = row.get('Stop_Loss')
            
            # Only draw if this is a NEW buy point (different from previous)
            if pd.notna(buy_point) and buy_point != prev_buy:
                from datetime import timedelta
                center_date = row['Date']
                
                # Calculate 5% of visible chart width for dash segment
                date_min = df['Date'].min()
                date_max = df['Date'].max()
                total_days = (date_max - date_min).days
                dash_width_days = max(total_days * 0.03, 3)  # At least 3 days wide
                
                dash_start = center_date - timedelta(days=dash_width_days/2)
                dash_end = center_date + timedelta(days=dash_width_days/2)
                
                # Draw BUY POINT dash
                fig.add_trace(go.Scatter(
                    x=[dash_start, dash_end],
                    y=[buy_point, buy_point],
                    mode='lines',
                    line=dict(color='black', width=3, dash='dash'),
                    showlegend=False,
                    hovertemplate=f'Buy Point: ${buy_point:.2f}<extra></extra>'
                ))
                
                # Add label
                fig.add_annotation(
                    x=center_date,
                    y=buy_point,
                    text=f"${buy_point:.2f}",
                    showarrow=False,
                    xshift=50,
                    font=dict(size=10, color='black', family='Arial Black'),
                    bgcolor='rgba(255, 255, 255, 0.9)',
                    bordercolor='black',
                    borderwidth=1,
                    borderpad=3
                )
                
                # Draw STOP LOSS dash
                if pd.notna(stop_loss):
                    fig.add_trace(go.Scatter(
                        x=[dash_start, dash_end],
                        y=[stop_loss, stop_loss],
                        mode='lines',
                        line=dict(color='red', width=3, dash='dash'),
                        showlegend=False,
                        hovertemplate=f'Stop Loss: ${stop_loss:.2f}<extra></extra>'
                    ))
                    
                    # Add label
                    fig.add_annotation(
                        x=center_date,
                        y=stop_loss,
                        text=f"${stop_loss:.2f}",
                        showarrow=False,
                        xshift=50,
                        font=dict(size=10, color='red', family='Arial Black'),
                        bgcolor='rgba(255, 255, 255, 0.9)',
                        bordercolor='red',
                        borderwidth=1,
                        borderpad=3
                    )
                
                # Update previous values
                prev_buy = buy_point
                prev_stop = stop_loss
    
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
