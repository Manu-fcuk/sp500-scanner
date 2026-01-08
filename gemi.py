import google.generativeai as genai
import pandas as pd
# import yfinance as yf # Uncomment and install if you want to fetch live historical data
import os # To get API key from environment variables (recommended)

# Configure the Gemini API with your API key
# It's highly recommended to load your API key from environment variables
# For example, set an environment variable like: GOOGLE_API_KEY="your_api_key_here"
# If you must hardcode it for a quick test, replace os.getenv with your key:
# genai.configure(api_key="YOUR_API_KEY_HERE")
genai.configure(api_key="GAIzaSyCH5dvqYejbsIR9v6oXzlIBjtLa0gMrAP4")

# Ensure the API key is set
genai.configure(api_key="GAIzaSyCH5dvqYejbsIR9v6oXzlIBjtLa0gMrAP4")
if genai.get_default_options().get('') is None:
    raise ValueError("Gemini API key not found. Please set the GOOGLE_API_KEY environment variable or replace os.getenv() with your key.")


# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

def get_stock_news(ticker):
    """
    Placeholder function to simulate fetching recent news for a stock.
    In a real application, you'd integrate with a news API (e.g., NewsAPI, Alpha Vantage).
    For demonstration, we use some static dummy news.
    """
    if ticker == "GOOGL":
        return [
            "Google announces record Q4 earnings, beating analyst expectations.",
            "Antitrust concerns raised again regarding Google's advertising practices.",
            "New AI division launched by Google, investing heavily in generative AI research.",
            "Google Cloud expands partnership with major enterprise client."
        ]
    elif ticker == "AAPL":
        return [
            "Apple's new Vision Pro headset receives mixed reviews on launch.",
            "Supply chain disruptions expected to impact iPhone production in Q1.",
            "Apple Services revenue continues strong growth, offsetting hardware slowdowns.",
            "Apple acquires a small AI startup specializing in privacy-focused machine learning."
        ]
    elif ticker == "MSFT":
        return [
            "Microsoft posts strong Azure cloud growth in latest earnings report.",
            "New gaming studio acquisition boosts Xbox content pipeline.",
            "Regulatory scrutiny on Activision Blizzard acquisition continues.",
            "Microsoft details new generative AI features coming to Office suite."
        ]
    else:
        return [f"No specific dummy news found for {ticker}."
                f"Consider fetching real-time news from a financial news API for a robust analysis."]

def analyze_stock_with_gemini(ticker):
    """
    Analyzes a stock using Gemini based on recent news.
    """
    news_articles = get_stock_news(ticker)

    # Check if there's any news to analyze
    if not news_articles or (len(news_articles) == 1 and "No specific dummy news found" in news_articles[0]):
        return f"Could not retrieve sufficient news for {ticker} to perform analysis."

    combined_news = "\n".join(news_articles)

    prompt = f"""
    Analyze the following recent news articles for the stock ticker {ticker}.
    Provide a concise summary of the key developments, identify potential positive impacts,
    and potential negative impacts on the stock price or company's future prospects.

    News Articles for {ticker}:
    {combined_news}

    Analysis for {ticker}:
    """

    try:
        response = model.generate_content(prompt)
        # Ensure the response is not empty
        if response and response.text:
            return response.text
        else:
            return f"Gemini returned an empty response for {ticker} analysis."
    except Exception as e:
        return f"An error occurred while calling the Gemini API for {ticker}: {e}"

# --- Main execution ---
if __name__ == "__main__": # Corrected this line!
    # Example 1: GOOGL
    stock_ticker_1 = "GOOGL"
    print(f"--- Analyzing {stock_ticker_1} ---")
    analysis_result_1 = analyze_stock_with_gemini(stock_ticker_1)
    print(analysis_result_1)

    print("\n" + "="*80 + "\n") # Separator

    # Example 2: AAPL
    stock_ticker_2 = "AAPL"
    print(f"--- Analyzing {stock_ticker_2} ---")
    analysis_result_2 = analyze_stock_with_gemini(stock_ticker_2)
    print(analysis_result_2)

    print("\n" + "="*80 + "\n") # Separator

    # Example 3: MSFT
    stock_ticker_3 = "MSFT"
    print(f"--- Analyzing {stock_ticker_3} ---")
    analysis_result_3 = analyze_stock_with_gemini(stock_ticker_3)
    print(analysis_result_3)

    print("\n" + "="*80 + "\n") # Separator

    # Example 4: A ticker with no specific dummy news
    stock_ticker_4 = "AMZN"
    print(f"--- Analyzing {stock_ticker_4} ---")
    analysis_result_4 = analyze_stock_with_gemini(stock_ticker_4)
    print(analysis_result_4)