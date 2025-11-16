from tr_chart_plotter import quick_tr_chart

# Generate basic chart (one line!)
quick_tr_chart('AAPL', timeframe='daily', duration_days=180, chart_type='basic')

# Generate enhanced chart with buy zones
quick_tr_chart('MSFT', timeframe='daily', duration_days=180, chart_type='enhanced')