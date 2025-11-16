"""
Seasonality Analysis Module - TR Chart Generator v4.0
Analyzes monthly performance patterns and compares to S&P 500
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()


class SeasonalityAnalysis:
    """Analyze and visualize seasonal patterns in stock performance"""
    
    def __init__(self, api_key=None, output_dir='charts'):
        """
        Initialize with API key and output directory
        
        Args:
            api_key (str): Tiingo API key
            output_dir (str): Directory to save charts
        """
        self.api_key = api_key or os.getenv('TIINGO_API_KEY')
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        if not self.api_key:
            raise ValueError("API key required. Set TIINGO_API_KEY environment variable.")
    
    def fetch_monthly_data(self, ticker, years=5):
        """
        Fetch historical monthly price data
        
        Args:
            ticker (str): Stock symbol
            years (int): Number of years of history
        
        Returns:
            pd.DataFrame: Monthly price data
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        # Fetch from Tiingo
        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        params = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'token': self.api_key,
            'resampleFreq': 'monthly'  # Get monthly data
        }
        
        print(f"📊 Fetching {years} years of monthly data for {ticker}...")
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        if not data:
            raise Exception(f"No data found for {ticker}")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        print(f"✅ Fetched {len(df)} months of data")
        
        return df
    
    def calculate_monthly_returns(self, df):
        """
        Calculate monthly returns from price data
        
        Args:
            df (pd.DataFrame): Monthly price data with 'adjClose' column
        
        Returns:
            pd.Series: Monthly returns
        """
        # Calculate percentage change month-over-month
        returns = df['adjClose'].pct_change() * 100  # Convert to percentage
        returns = returns.dropna()
        
        return returns
    
    def group_by_month(self, returns):
        """
        Group returns by calendar month and calculate averages
        
        Args:
            returns (pd.Series): Monthly returns with datetime index
        
        Returns:
            dict: Average return for each month
        """
        # Extract month number from index
        month_returns = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month_num in range(1, 13):
            # Get all returns for this calendar month
            month_data = returns[returns.index.month == month_num]
            
            if len(month_data) > 0:
                avg_return = month_data.mean()
                month_returns[month_names[month_num-1]] = avg_return
            else:
                month_returns[month_names[month_num-1]] = 0.0
        
        return month_returns
    
    def calculate_absolute_seasonality(self, ticker, years=5):
        """
        Calculate absolute monthly seasonality
        
        Args:
            ticker (str): Stock symbol
            years (int): Years of history to analyze
        
        Returns:
            dict: Average monthly returns
        """
        print(f"\n📈 Calculating absolute seasonality for {ticker} ({years} years)...")
        
        # Fetch data
        df = self.fetch_monthly_data(ticker, years)
        
        # Calculate returns
        returns = self.calculate_monthly_returns(df)
        
        # Group by month
        monthly_avg = self.group_by_month(returns)
        
        print(f"✅ Seasonality calculated")
        
        return monthly_avg
    
    def calculate_relative_seasonality(self, ticker, years=5):
        """
        Calculate seasonality relative to S&P 500
        
        Args:
            ticker (str): Stock symbol
            years (int): Years of history to analyze
        
        Returns:
            dict: Relative monthly performance vs SPY
        """
        print(f"\n📊 Calculating relative seasonality vs SPY ({years} years)...")
        
        # Fetch stock data
        stock_df = self.fetch_monthly_data(ticker, years)
        stock_returns = self.calculate_monthly_returns(stock_df)
        
        # Fetch SPY data
        spy_df = self.fetch_monthly_data('SPY', years)
        spy_returns = self.calculate_monthly_returns(spy_df)
        
        # Align dates (only compare months where both have data)
        aligned_dates = stock_returns.index.intersection(spy_returns.index)
        stock_returns = stock_returns[aligned_dates]
        spy_returns = spy_returns[aligned_dates]
        
        # Calculate relative performance
        relative_returns = stock_returns - spy_returns
        
        # Group by month
        monthly_relative = self.group_by_month(relative_returns)
        
        print(f"✅ Relative seasonality calculated")
        
        return monthly_relative
    
    def plot_seasonality(self, ticker, data, years, chart_type='absolute'):
        """
        Create bar chart for seasonality data
        
        Args:
            ticker (str): Stock symbol
            data (dict): Monthly data to plot
            years (int): Number of years analyzed
            chart_type (str): 'absolute' or 'relative'
        
        Returns:
            str: Path to saved chart
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data
        months = list(data.keys())
        values = list(data.values())
        
        # Color bars based on positive/negative
        colors = ['#00C853' if v >= 0 else '#D32F2F' for v in values]
        
        # Create bar chart
        bars = ax.bar(months, values, color=colors, edgecolor='black', linewidth=1.2)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            label_y = height + (0.3 if height >= 0 else -0.8)
            ax.text(bar.get_x() + bar.get_width()/2., label_y,
                   f'{value:.1f}%',
                   ha='center', va='bottom' if height >= 0 else 'top',
                   fontsize=11, fontweight='bold')
        
        # Styling
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Labels and title
        if chart_type == 'absolute':
            title = f'{ticker} - Average Monthly Returns (Last {years} Years)'
            ylabel = 'Average Return (%)'
            footer = f'Based on {years} years of monthly data'
        else:
            title = f'{ticker} vs SPY - Relative Monthly Performance (Last {years} Years)'
            ylabel = 'Outperformance / Underperformance (%)'
            footer = 'Positive = Outperform SPY | Negative = Underperform SPY'
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        
        # Footer text
        fig.text(0.5, 0.02, footer, ha='center', fontsize=10, 
                style='italic', color='gray')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0.03, 1, 1])
        
        # Save figure
        filename = f"{ticker}_Seasonality_{years}Y_{chart_type.title()}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Chart saved: {filename}")
        
        return filepath
    
    def generate_complete_analysis(self, ticker, periods=None, open_charts=False):
        """
        Generate complete seasonality analysis for all periods
        
        Args:
            ticker (str): Stock symbol
            periods (list): List of years to analyze (default: [1, 3, 5, 20])
            open_charts (bool): Whether to display charts
        
        Returns:
            dict: Paths to all generated charts
        """
        if periods is None:
            periods = [1, 3, 5, 20]
        
        print(f"\n{'='*70}")
        print(f"🌙 SEASONALITY ANALYSIS FOR {ticker}")
        print(f"{'='*70}")
        
        all_charts = {}
        
        for years in periods:
            try:
                print(f"\n--- Analyzing {years}-Year Period ---")
                
                # Calculate absolute seasonality
                abs_data = self.calculate_absolute_seasonality(ticker, years)
                abs_chart = self.plot_seasonality(ticker, abs_data, years, 'absolute')
                all_charts[f'{years}Y_absolute'] = abs_chart
                
                # Calculate relative seasonality
                rel_data = self.calculate_relative_seasonality(ticker, years)
                rel_chart = self.plot_seasonality(ticker, rel_data, years, 'relative')
                all_charts[f'{years}Y_relative'] = rel_chart
                
            except Exception as e:
                print(f"⚠️  Could not analyze {years}-year period: {str(e)}")
                continue
        
        print(f"\n{'='*70}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"📁 {len(all_charts)} charts generated in: {self.output_dir}/")
        print(f"{'='*70}")
        
        # Display charts if requested
        if open_charts:
            import matplotlib.pyplot as plt
            for chart_path in all_charts.values():
                try:
                    img = plt.imread(chart_path)
                    plt.figure(figsize=(14, 8))
                    plt.imshow(img)
                    plt.axis('off')
                    plt.tight_layout()
                    plt.show()
                except:
                    pass
        
        return all_charts
    
    def interactive_menu(self):
        """Interactive menu for seasonality analysis"""
        while True:
            print(f"\n{'='*70}")
            print("SEASONALITY ANALYSIS")
            print(f"{'='*70}")
            print("1. Analyze 1 Year")
            print("2. Analyze 3 Years")
            print("3. Analyze 5 Years")
            print("4. Analyze 20 Years")
            print("5. Analyze All Periods (1Y, 3Y, 5Y, 20Y)")
            print("0. Back to Main Menu")
            print(f"{'='*70}")
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                break
            
            if choice not in ['1', '2', '3', '4', '5']:
                print("❌ Invalid choice. Please try again.")
                continue
            
            # Get ticker
            ticker = input("\nEnter stock symbol (e.g., AAPL): ").strip().upper()
            if not ticker:
                print("❌ Invalid ticker symbol.")
                continue
            
            # Determine periods
            period_map = {
                '1': [1],
                '2': [3],
                '3': [5],
                '4': [20],
                '5': [1, 3, 5, 20]
            }
            
            periods = period_map[choice]
            
            # Generate analysis
            try:
                self.generate_complete_analysis(ticker, periods, open_charts=True)
                
                print("\n✅ Analysis complete!")
                print(f"📁 Charts saved to: {self.output_dir}/")
                
            except Exception as e:
                print(f"\n❌ Error during analysis: {str(e)}")
                continue


# Test function
def test_seasonality():
    """Test the seasonality module"""
    print("Testing Seasonality Analysis Module...")
    
    analyzer = SeasonalityAnalysis()
    
    # Test with AAPL
    analyzer.generate_complete_analysis('AAPL', periods=[1, 3], open_charts=True)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    # If run directly, show interactive menu
    analyzer = SeasonalityAnalysis()
    analyzer.interactive_menu()
