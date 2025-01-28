import yfinance as yf

def fetch_prices():
    print("Loading Tickers...")
    tickers = ['QQQ', 'SPY', 'BTC-USD', 'ETH-USD', 'AAPL', 'TSLA']
    prices = {}

    for ticker in tickers:
        print(f"Fetching {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period='5d')
        price = hist['Close'].iloc[-1]
        print("Price: ", price)
        prev_close = hist['Close'].iloc[-2]
        change = ((price - prev_close) / prev_close) * 100
        prices[ticker] = {
            'price': round(price, 2),
            'change': round(change, 2)
        }

    return prices
def fetch_price_and_date(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    prices = []
    for date, row in hist.iterrows():
        prices.append({
            'date': date.strftime('%Y-%m-%d'),
            'price': round(row['Close'], 2)
        })
    return prices

if __name__ == "__main__":
    prices = fetch_prices()
    for ticker, data in prices.items():
        print(f"{ticker}: {data['price']} ({data['change']}%)")