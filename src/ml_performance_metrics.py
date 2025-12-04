"""
ML Performance Metrics Calculator
=================================

Calculates Profit Factor, Expectancy, and Sharpe Ratio
for ML trading strategies.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple


def calculate_metrics_from_test_data(X_test: pd.DataFrame, y_test: pd.Series, trades_per_year: int = 20) -> Dict:
    """
    Calculate performance metrics from test data with actual trade outcomes.
    
    Parameters:
    -----------
    X_test : pd.DataFrame
        Test features containing 'max_gain_pct' and 'max_loss_pct' columns
    y_test : pd.Series
        Binary outcomes (1 = success/win, 0 = failure/loss)
    trades_per_year : int
        Estimated number of trades per year (default 20)
    
    Returns:
    --------
    Dict with profit_factor, expectancy, annual_return, and supporting stats
    """
    
    # Combine data
    df = X_test.copy()
    df['success'] = y_test.values
    
    # Split wins and losses
    wins = df[df['success'] == 1]
    losses = df[df['success'] == 0]
    
    n_wins = len(wins)
    n_losses = len(losses)
    n_total = len(df)
    
    # Win rate
    win_rate = n_wins / n_total if n_total > 0 else 0
    
    # Average gains and losses
    avg_gain = wins['max_gain_pct'].mean() if n_wins > 0 else 0
    avg_loss = abs(losses['max_loss_pct'].mean()) if n_losses > 0 else 0
    
    # PROFIT FACTOR = Total Gains / Total Losses
    total_gains = wins['max_gain_pct'].sum() if n_wins > 0 else 0
    total_losses = abs(losses['max_loss_pct'].sum()) if n_losses > 0 else 0
    profit_factor = total_gains / total_losses if total_losses > 0 else float('inf')
    
    # EXPECTANCY = (Win% × Avg Win) - (Loss% × Avg Loss)
    loss_rate = n_losses / n_total if n_total > 0 else 0
    expectancy = (win_rate * avg_gain) - (loss_rate * avg_loss)
    
    # ANNUALIZED RETURN = Expectancy per trade × Trades per year
    annual_return = expectancy * trades_per_year
    
    return {
        'profit_factor': round(profit_factor, 2),
        'expectancy': round(expectancy, 2),
        'annual_return': round(annual_return, 1),
        'win_rate': round(win_rate * 100, 1),
        'avg_gain': round(avg_gain, 2),
        'avg_loss': round(avg_loss, 2),
        'total_trades': n_total,
        'wins': n_wins,
        'losses': n_losses,
        'trades_per_year': trades_per_year,
        'data_source': 'actual'
    }


def calculate_estimated_metrics(success_rate: float, 
                                 avg_gain_pct: float = 5.0, 
                                 avg_loss_pct: float = 3.0,
                                 training_samples: int = 0,
                                 trades_per_year: int = 20) -> Dict:
    """
    Calculate estimated performance metrics when actual trade data is not available.
    
    Parameters:
    -----------
    success_rate : float
        Historical success rate (0.0 to 1.0)
    avg_gain_pct : float
        Assumed average gain percentage for winning trades
    avg_loss_pct : float
        Assumed average loss percentage for losing trades
    training_samples : int
        Number of training samples
    trades_per_year : int
        Estimated number of trades per year (default 20)
    
    Returns:
    --------
    Dict with estimated profit_factor, expectancy, annual_return
    """
    
    win_rate = success_rate
    loss_rate = 1 - success_rate
    
    # PROFIT FACTOR (estimated)
    # PF = (Win% × Avg Win) / (Loss% × Avg Loss)
    total_wins = win_rate * avg_gain_pct
    total_losses = loss_rate * avg_loss_pct
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # EXPECTANCY
    expectancy = (win_rate * avg_gain_pct) - (loss_rate * avg_loss_pct)
    
    # ANNUALIZED RETURN = Expectancy per trade × Trades per year
    annual_return = expectancy * trades_per_year
    
    return {
        'profit_factor': round(profit_factor, 2),
        'expectancy': round(expectancy, 2),
        'annual_return': round(annual_return, 1),
        'win_rate': round(win_rate * 100, 1),
        'avg_gain': avg_gain_pct,
        'avg_loss': avg_loss_pct,
        'total_trades': training_samples,
        'wins': int(training_samples * win_rate),
        'losses': int(training_samples * loss_rate),
        'trades_per_year': trades_per_year,
        'data_source': 'estimated'
    }


def format_metrics_display(metrics: Dict) -> Dict:
    """
    Format metrics for UI display with interpretations.
    
    Parameters:
    -----------
    metrics : Dict
        Metrics dictionary from calculate functions
    
    Returns:
    --------
    Dict with formatted values and interpretations
    """
    
    pf = metrics['profit_factor']
    exp = metrics['expectancy']
    annual = metrics['annual_return']
    
    # Profit Factor interpretation
    if pf >= 2.0:
        pf_rating = 'Excellent'
        pf_emoji = '🔥'
    elif pf >= 1.5:
        pf_rating = 'Good'
        pf_emoji = '✅'
    elif pf >= 1.0:
        pf_rating = 'Marginal'
        pf_emoji = '⚠️'
    else:
        pf_rating = 'Poor'
        pf_emoji = '❌'
    
    # Expectancy interpretation
    if exp >= 2.0:
        exp_rating = 'Excellent'
        exp_emoji = '🔥'
    elif exp >= 1.0:
        exp_rating = 'Good'
        exp_emoji = '✅'
    elif exp >= 0:
        exp_rating = 'Marginal'
        exp_emoji = '⚠️'
    else:
        exp_rating = 'Negative'
        exp_emoji = '❌'
    
    # Annual Return interpretation (compare to S&P 500 ~10%)
    if annual >= 20:
        annual_rating = 'Excellent'
        annual_emoji = '🔥'
    elif annual >= 10:
        annual_rating = 'Good'
        annual_emoji = '✅'
    elif annual >= 0:
        annual_rating = 'Marginal'
        annual_emoji = '⚠️'
    else:
        annual_rating = 'Negative'
        annual_emoji = '❌'
    
    return {
        'profit_factor': {
            'value': pf,
            'display': f"{pf:.2f}",
            'rating': pf_rating,
            'emoji': pf_emoji,
            'help': f"Ratio of gross profits to gross losses. >1 = profitable, >2 = excellent"
        },
        'expectancy': {
            'value': exp,
            'display': f"{exp:.2f}%",
            'rating': exp_rating,
            'emoji': exp_emoji,
            'help': f"Average expected return per trade"
        },
        'annual_return': {
            'value': annual,
            'display': f"{annual:.1f}%",
            'rating': annual_rating,
            'emoji': annual_emoji,
            'help': f"Estimated annual return based on ~{metrics.get('trades_per_year', 20)} trades/year. Compare to S&P 500 (~10%)"
        },
        'win_rate': metrics['win_rate'],
        'avg_gain': metrics['avg_gain'],
        'avg_loss': metrics['avg_loss'],
        'total_trades': metrics['total_trades'],
        'data_source': metrics['data_source']
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("ML PERFORMANCE METRICS - TEST")
    print("=" * 60)
    
    # Test estimated metrics
    print("\n--- Estimated Metrics (TR Indicator style) ---")
    est_metrics = calculate_estimated_metrics(
        success_rate=0.65,
        avg_gain_pct=5.0,
        avg_loss_pct=3.0,
        training_samples=15000
    )
    formatted = format_metrics_display(est_metrics)
    
    print(f"Win Rate: {formatted['win_rate']}%")
    print(f"Profit Factor: {formatted['profit_factor']['emoji']} {formatted['profit_factor']['display']} ({formatted['profit_factor']['rating']})")
    print(f"Expectancy: {formatted['expectancy']['emoji']} {formatted['expectancy']['display']} ({formatted['expectancy']['rating']})")
    print(f"Sharpe Ratio: {formatted['sharpe_ratio']['emoji']} {formatted['sharpe_ratio']['display']} ({formatted['sharpe_ratio']['rating']})")
    print(f"Data Source: {formatted['data_source']}")
    
    print("\n" + "=" * 60)
    print("✅ Metrics module ready!")
