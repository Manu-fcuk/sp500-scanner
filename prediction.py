import yfinance as yf

# Define the list of tickers
tickers = ["AAPL", "MSFT", "GOOGL"]

# Download the historical data
data = yf.download(tickers, start="2023-01-01", end="2023-12-31")

# Display the 'Close' price for all tickers
print(data['Close'])