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
        Calculate monthly statistics: win rate and average gain/loss
        
        Args:
            df (pd.DataFrame): Monthly price data with 'open' and 'close'
        
        Returns:
            dict: Stats for each month
        """
        month_stats = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month_num in range(1, 13):
            # Get all data for this calendar month
            month_data = df[df.index.month == month_num].copy()
            
            if len(month_data) == 0:
                month_stats[month_names[month_num-1]] = {
                    'win_rate': 0,
                    'avg_return': 0,
                    'sample_size': 0
                }
                continue
            
            # Calculate month-over-month return (close vs open)
            month_data['return'] = ((month_data['adjClose'] - month_data['adjOpen']) / 
                                    month_data['adjOpen'] * 100)
            
            # Win rate: % of times close > open
            wins = (month_data['return'] > 0).sum()
            total = len(month_data)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Average return
            avg_return = month_data['return'].mean()
            
            month_stats[month_names[month_num-1]] = {
                'win_rate': win_rate,
                'avg_return': avg_return,
                'sample_size': total
            }
        
        return month_stats
    
    def calculate_absolute_seasonality(self, ticker, years=5):
        """
        Calculate absolute monthly seasonality
        
        Args:
            ticker (str): Stock symbol
            years (int): Years of history to analyze
        
        Returns:
            dict: Monthly statistics with win_rate and avg_return
        """
        print(f"\n📈 Calculating absolute seasonality for {ticker} ({years} years)...")
        
        # Fetch data
        df = self.fetch_monthly_data(ticker, years)
        
        # Calculate statistics
        monthly_stats = self.calculate_monthly_returns(df)
        
        print(f"✅ Seasonality calculated")
        
        return monthly_stats
    
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
        stock_stats = self.calculate_monthly_returns(stock_df)
        
        # Fetch SPY data
        spy_df = self.fetch_monthly_data('SPY', years)
        spy_stats = self.calculate_monthly_returns(spy_df)
        
        # Calculate relative performance
        relative_stats = {}
        for month in stock_stats.keys():
            stock_return = stock_stats[month]['avg_return']
            spy_return = spy_stats[month]['avg_return']
            
            relative_stats[month] = {
                'win_rate': stock_stats[month]['win_rate'],  # Use stock's win rate
                'avg_return': stock_return - spy_return,     # Relative return
                'sample_size': stock_stats[month]['sample_size']
            }
        
        print(f"✅ Relative seasonality calculated")
        
        return relative_stats
    
    def plot_seasonality(self, ticker, data, years, chart_type='absolute'):
        """
        Create bar chart for seasonality data
        
        Args:
            ticker (str): Stock symbol
            data (dict): Monthly data with win_rate and avg_return
            years (int): Number of years analyzed
            chart_type (str): 'absolute' or 'relative'
        
        Returns:
            str: Path to saved chart
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Prepare data
        months = list(data.keys())
        win_rates = [data[m]['win_rate'] for m in months]
        avg_returns = [data[m]['avg_return'] for m in months]
        
        # Create bar chart - height is win rate (0-100%)
        bars = ax.bar(months, win_rates, color='#4472C4', edgecolor='black', linewidth=0.8)
        
        # Add average return labels inside bars
        for i, (bar, avg_ret) in enumerate(zip(bars, avg_returns)):
            height = bar.get_height()
            
            # Position label in middle of bar
            label_y = height / 2
            
            # Format the label
            label_text = f'{avg_ret:+.1f}%'  # Shows as +5.2% or -3.1%
            
            ax.text(bar.get_x() + bar.get_width()/2., label_y,
                   label_text,
                   ha='center', va='center',
                   fontsize=10, fontweight='bold', color='white')
        
        # Set Y-axis to 0-100%
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 10))
        
        # Grid
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Labels and title
        if chart_type == 'absolute':
            title = f'SEASONALITY CHART - {ticker}\nlast {years} years'
            ylabel = '% Symbol closed higher than the month open'
            footer = f'Avg Gain/Loss (%)'
        else:
            title = f'RELATIVE SEASONALITY - {ticker} vs SPY\nlast {years} years'
            ylabel = '% Symbol closed higher than the month open'
            footer = 'Outperformance / Underperformance vs SPY (%)'
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('', fontsize=10)  # No X label
        ax.set_ylabel(ylabel, fontsize=9)
        
        # Footer text
        fig.text(0.5, 0.02, footer, ha='center', fontsize=9, 
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
            periods (list): List of years to analyze (default: [1, 3, 5, 10, 15, 20])
            open_charts (bool): Whether to display charts
        
        Returns:
            dict: Paths to all generated charts
        """
        if periods is None:
            periods = [1, 3, 5, 10, 15, 20]
        
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
            print("4. Analyze 10 Years")
            print("5. Analyze 15 Years")
            print("6. Analyze 20 Years")
            print("7. Analyze All Periods (1Y, 3Y, 5Y, 10Y, 15Y, 20Y)")
            print("0. Back to Main Menu")
            print(f"{'='*70}")
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                break
            
            if choice not in ['1', '2', '3', '4', '5', '6', '7']:
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
                '4': [10],
                '5': [15],
                '6': [20],
                '7': [1, 3, 5, 10, 15, 20]
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
