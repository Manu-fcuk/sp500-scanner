import yfinance as yf
import matplotlib.pyplot as plt
import datetime

def plot_stock_data(ticker_symbol, period="1y"):
    """
    Fetches and plots historical stock data for a given ticker symbol.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., "GOOG").
        period (str): The period for which to fetch data (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max").
    """
    try:
        # Fetch data
        stock_data = yf.Ticker(ticker_symbol)
        history = stock_data.history(period=period)

        if history.empty:
            print(f"No data found for {ticker_symbol} for the period {period}.")
            return

        # Plotting the 'Close' price
        plt.figure(figsize=(12, 6))
        plt.plot(history.index, history['Close'], label=f'{ticker_symbol} Close Price')
        plt.title(f'{ticker_symbol} Stock Price History ({period})')
        plt.xlabel('Date')
        plt.ylabel('Close Price (USD)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    plot_stock_data("GOOG", period="6mo") # Shows data for the last 1 year
    # You can try other periods:
    # plot_stock_data("GOOG", period="5y")
    # plot_stock_data("MSFT", period="6mo") # Example for Microsoft