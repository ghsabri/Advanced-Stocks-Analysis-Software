"""
Seasonality Analysis Page
Analyzes monthly performance patterns for stocks
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cached_data import get_shared_stock_data

st.set_page_config(
    page_title="Seasonality - MJ Software",
    page_icon="📈",
    layout="wide"
)

# CSS for button styling
st.markdown("""
<style>
    /* Duration buttons - smaller size */
    div[data-testid="column"] .stButton > button {
        height: 32px !important;
        min-height: 32px !important;
        padding: 4px 8px !important;
        font-size: 12px !important;
        width: 60px !important;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📈 Seasonality Analysis")
st.markdown("**Analyze monthly performance patterns and seasonal trends**")

# Input section
col1, col2 = st.columns([3, 3])

with col1:
    symbol = st.text_input("Stock Symbol", value="AAPL", help="Enter ticker symbol")

with col2:
    analysis_type = st.selectbox(
        "Analysis Type",
        ["Absolute Performance", "Relative to S&P 500"],
        help="Absolute: Stock performance alone\nRelative: Stock vs SPY performance"
    )

# Get API source from session state
api_source = st.session_state.get('api_source', 'Yahoo Finance')

# Duration buttons
st.markdown("**Select Period:**")

duration_cols = st.columns(6)
duration_options = [
    ("1Y", "1 Year", 365),
    ("3Y", "3 Years", 1095),
    ("5Y", "5 Years", 1825),
    ("10Y", "10 Years", 3650),
    ("15Y", "15 Years", 5475),
    ("20Y", "20 Years", 7300)
]

# Initialize duration in session state
if 'seasonality_duration_days' not in st.session_state:
    st.session_state['seasonality_duration_days'] = 1825
    st.session_state['seasonality_duration_label'] = "5 Years"

# Create duration buttons
for i, (label, full_label, days) in enumerate(duration_options):
    with duration_cols[i]:
        is_selected = st.session_state.get('seasonality_duration_days') == days
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(label, key=f"seas_dur_{label}", type=button_type):
            st.session_state['seasonality_duration_days'] = days
            st.session_state['seasonality_duration_label'] = full_label
            st.rerun()

st.caption(f"Selected: **{st.session_state.get('seasonality_duration_label', '5 Years')}**")


def calculate_monthly_stats(df):
    """Calculate monthly statistics from price data"""
    
    # Ensure we have a date column
    if 'Date' not in df.columns:
        df = df.reset_index()
    
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year
    
    # Group by Year-Month and get first/last values
    monthly_data = df.groupby([df['Year'], df['Month']]).agg({
        'Open': 'first',
        'Close': 'last'
    }).reset_index()
    
    # Calculate monthly return
    monthly_data['Return'] = ((monthly_data['Close'] - monthly_data['Open']) / 
                              monthly_data['Open'] * 100)
    
    # Calculate stats by month
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    stats = {}
    for month_num in range(1, 13):
        month_data = monthly_data[monthly_data['Month'] == month_num]
        
        if len(month_data) == 0:
            stats[month_names[month_num-1]] = {
                'win_rate': 0,
                'avg_return': 0,
                'sample_size': 0
            }
            continue
        
        wins = (month_data['Return'] > 0).sum()
        total = len(month_data)
        win_rate = (wins / total * 100) if total > 0 else 0
        avg_return = month_data['Return'].mean()
        
        stats[month_names[month_num-1]] = {
            'win_rate': win_rate,
            'avg_return': avg_return,
            'sample_size': total
        }
    
    return stats


def create_seasonality_chart(stats, ticker, years, chart_type='absolute'):
    """Create interactive Plotly bar chart for seasonality"""
    
    months = list(stats.keys())
    win_rates = [stats[m]['win_rate'] for m in months]
    avg_returns = [stats[m]['avg_return'] for m in months]
    sample_sizes = [stats[m]['sample_size'] for m in months]
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=months,
        y=win_rates,
        text=[f"{avg:.1f}%" for avg in avg_returns],
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        marker=dict(
            color='#4472C4',
            line=dict(color='black', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>' +
                      'Win Rate: %{y:.1f}%<br>' +
                      'Avg Return: %{text}<br>' +
                      '<extra></extra>',
        showlegend=False
    ))
    
    # Update layout
    title_text = f"SEASONALITY CHART - {ticker}<br>Last {years} Year{'s' if years > 1 else ''}"
    if chart_type == 'relative':
        title_text = f"RELATIVE SEASONALITY - {ticker} vs SPY<br>Last {years} Year{'s' if years > 1 else ''}"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center',
            font=dict(size=16, family='Arial Black')
        ),
        xaxis=dict(
            title="",
            showgrid=False
        ),
        yaxis=dict(
            title="% Symbol closed higher than month open",
            range=[0, 100],
            dtick=10,
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        height=500,
        margin=dict(t=80, b=100)
    )
    
    # Add footer annotation
    footer_text = "Avg Gain/Loss (%)" if chart_type == 'absolute' else "Outperformance / Underperformance vs SPY (%)"
    fig.add_annotation(
        text=footer_text,
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=11, color='gray', family='Arial'),
        xanchor='center'
    )
    
    return fig


# Analyze button
if st.button("📊 Generate Seasonality Chart", type="primary", use_container_width=True):
    
    duration_days = st.session_state.get('seasonality_duration_days', 1825)
    duration_label = st.session_state.get('seasonality_duration_label', '5 Years')
    years = duration_days // 365
    
    with st.spinner(f"🔄 Analyzing {symbol} seasonality ({duration_label})..."):
        
        try:
            # Fetch stock data using shared cache
            df = get_shared_stock_data(
                ticker=symbol,
                duration_days=duration_days,
                timeframe='daily',
                api_source='yahoo' if 'Yahoo' in api_source else 'tiingo'
            )
            
            if df is None or df.empty:
                st.error(f"❌ Could not get data for {symbol}")
                st.stop()
            
            # Calculate seasonality stats
            stock_stats = calculate_monthly_stats(df)
            
            # If relative analysis, fetch SPY data
            if analysis_type == "Relative to S&P 500":
                spy_df = get_shared_stock_data(
                    ticker='SPY',
                    duration_days=duration_days,
                    timeframe='daily',
                    api_source='yahoo' if 'Yahoo' in api_source else 'tiingo'
                )
                
                if spy_df is None or spy_df.empty:
                    st.warning("⚠️ Could not get SPY data, showing absolute performance instead")
                    chart_type = 'absolute'
                    final_stats = stock_stats
                else:
                    spy_stats = calculate_monthly_stats(spy_df)
                    
                    # Calculate relative performance
                    final_stats = {}
                    for month in stock_stats.keys():
                        stock_return = stock_stats[month]['avg_return']
                        spy_return = spy_stats[month]['avg_return']
                        
                        final_stats[month] = {
                            'win_rate': stock_stats[month]['win_rate'],
                            'avg_return': stock_return - spy_return,
                            'sample_size': stock_stats[month]['sample_size']
                        }
                    
                    chart_type = 'relative'
            else:
                final_stats = stock_stats
                chart_type = 'absolute'
            
            # Store in session state
            st.session_state['seasonality_stats'] = final_stats
            st.session_state['seasonality_symbol'] = symbol
            st.session_state['seasonality_years'] = years
            st.session_state['seasonality_type'] = chart_type
            
            st.success(f"✅ Seasonality analysis complete!")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()


# Display results if available
if 'seasonality_stats' in st.session_state:
    
    stats = st.session_state['seasonality_stats']
    symbol = st.session_state['seasonality_symbol']
    years = st.session_state['seasonality_years']
    chart_type = st.session_state['seasonality_type']
    
    st.markdown("---")
    st.subheader(f"📊 Seasonality Results for {symbol}")
    
    # Create and display chart
    fig = create_seasonality_chart(stats, symbol, years, chart_type)
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistics table
    st.markdown("### 📈 Monthly Statistics")
    
    # Create DataFrame for display
    table_data = []
    for month, data in stats.items():
        table_data.append({
            'Month': month,
            'Win Rate (%)': f"{data['win_rate']:.1f}",
            'Avg Return (%)': f"{data['avg_return']:+.2f}",
            'Sample Size': data['sample_size']
        })
    
    table_df = pd.DataFrame(table_data)
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    
    # Best and Worst months
    col1, col2 = st.columns(2)
    
    # Sort by average return
    sorted_months = sorted(stats.items(), key=lambda x: x[1]['avg_return'], reverse=True)
    
    with col1:
        st.markdown("#### 🟢 Best Months")
        for i in range(min(3, len(sorted_months))):
            month, data = sorted_months[i]
            st.metric(
                month,
                f"{data['avg_return']:+.2f}%",
                f"Win Rate: {data['win_rate']:.0f}%"
            )
    
    with col2:
        st.markdown("#### 🔴 Worst Months")
        for i in range(min(3, len(sorted_months))):
            month, data = sorted_months[-(i+1)]
            st.metric(
                month,
                f"{data['avg_return']:+.2f}%",
                f"Win Rate: {data['win_rate']:.0f}%"
            )
    
    # Export option
    if st.button("💾 Export to CSV"):
        csv = table_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{symbol}_Seasonality_{years}Y.csv",
            mime="text/csv"
        )

# Footer
st.markdown("---")


# Footer
st.markdown("---")
st.caption("© 2025 MJ Software LLC | AI-Powered Stock Analysis Platform")
