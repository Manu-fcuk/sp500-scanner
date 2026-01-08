import yfinance as yf

def calculate_intrinsic_value(ticker_symbol, growth_rate, required_rate_of_return):
    """
    Calculates the intrinsic value of a stock using the Dividend Discount Model (DDM).

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').
        growth_rate (float): The expected constant growth rate of dividends (e.g., 0.05 for 5%).
        required_rate_of_return (float): The investor's required rate of return (e.g., 0.10 for 10%).

    Returns:
        float: The calculated intrinsic value of the stock, or None if data is unavailable.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Get historical dividends
        dividends = stock.dividends
        
        if dividends.empty:
            print(f"No dividend data found for {ticker_symbol}. Cannot calculate intrinsic value using DDM.")
            return None
        
        latest_dividend = dividends.iloc[-1]
        
        # Ensure required rate of return is greater than growth rate
        if required_rate_of_return <= growth_rate:
            print("Error: Required rate of return must be greater than the growth rate for DDM.")
            return None
            
        # DDM Formula: Intrinsic Value = Latest_Dividend * (1 + Growth_Rate) / (Required_Rate_of_Return - Growth_Rate)
        intrinsic_value = latest_dividend * (1 + growth_rate) / (required_rate_of_return - growth_rate)
        
        return intrinsic_value

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    # Example Usage:
    ticker = 'GOOG'  # Microsoft
    expected_growth = 0.04  # 4% annual dividend growth
    required_return = 0.09  # 9% required rate of return

    value = calculate_intrinsic_value(ticker, expected_growth, required_return)

    if value is not None:
        print(f"The calculated intrinsic value for {ticker} is: ${value:.2f}")

    ticker_no_dividends = 'GOOG' # Google (doesn't pay dividends)
    value_no_dividends = calculate_intrinsic_value(ticker_no_dividends, expected_growth, required_return)

    # You can also visualize some stock data using yfinance
    msft_data = yf.Ticker('MSFT').history(period="1y")
    print("\nMSFT Stock Price History (last 5 days):")
    print(msft_data.tail())