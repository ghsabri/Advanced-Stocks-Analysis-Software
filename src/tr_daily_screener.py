# Find stocks with Strong Buy + Star (market leaders)
from tr_enhanced import analyze_stock_complete_tr, display_complete_tr_summary
stocks = ['UBER', 'HOOD', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']
for stock in stocks:
    df = analyze_stock_complete_tr(stock)
    if '* ' in df.iloc[-1]['TR_Status_Enhanced']:
        print(f"{stock}: Market Leader with Strong Buy!")