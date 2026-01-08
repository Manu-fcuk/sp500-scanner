import yfinance as yf
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials
import os
import json
from concurrent.futures import ThreadPoolExecutor

# Define the Golden Cross logic
def calculate_golden_cross(df, short_window=50, long_window=200):
    if df is None or len(df) < long_window:
        return None, None
    
    sma50 = df['Close'].rolling(window=short_window).mean()
    sma200 = df['Close'].rolling(window=long_window).mean()
    
    # Check for cross
    prev_sma50 = sma50.shift(1)
    prev_sma200 = sma200.shift(1)
    
    # Find the most recent cross
    cross_dates = df.index[(sma50 > sma200) & (prev_sma50 <= prev_sma200)]
    cross_date = cross_dates[-1] if not cross_dates.empty else None
            
    is_bullish = sma50.iloc[-1] > sma200.iloc[-1] if not sma50.empty and not sma200.empty else False
    
    return cross_date, is_bullish

def get_sp500_tickers_with_info():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        table = pd.read_html(url)
        df = table[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        security_names = dict(zip(tickers, df['Security']))
        return tickers, security_names
    except Exception as e:
        print(f"Error fetching tickers from Wikipedia: {e}")
        return [], {}

def process_ticker(ticker, security_names):
    try:
        stock = yf.Ticker(ticker)
        # We need market cap. info is slow, but required if we want it.
        # However, we can also get market cap from the Wikipedia table if it's there?
        # Actually Wikipedia doesn't have Market Cap in that table.
        # Let's try to get it from yfinance info but maybe skip if it's too slow?
        # Or just use yf.download(tickers, group_by='ticker')
        
        # Alternative: We can fetch info for all at once if we had a list, but yf doesn't support batch info easily.
        # Let's use info but in threads.
        info = stock.info
        market_cap = info.get('marketCap', 'N/A')
        
        # Daily data
        hist_daily = stock.history(period="2y")
        cross_date, is_bullish = calculate_golden_cross(hist_daily)
        
        status = "Bullish" if is_bullish else "Bearish"
        hourly_cross_date = "N/A"
        
        if is_bullish:
            # 1 hour timeframe
            hist_hourly = stock.history(period="1mo", interval="1h")
            h_cross_date, _ = calculate_golden_cross(hist_hourly)
            if h_cross_date:
                hourly_cross_date = h_cross_date.strftime('%Y-%m-%d %H:%M')
        
        return {
            'Ticker': ticker,
            'Name': security_names.get(ticker, ticker),
            'Market Cap': market_cap,
            'Daily Golden Cross Date': cross_date.strftime('%Y-%m-%d') if cross_date else "N/A",
            'Status': status,
            'Hourly Golden Cross Date (if Bullish)': hourly_cross_date
        }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

def main():
    print("Fetching S&P 500 tickers...")
    tickers, security_names = get_sp500_tickers_with_info()
    
    if not tickers:
        print("No tickers found.")
        return

    print(f"Analyzing {len(tickers)} stocks with multithreading...")
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker, ticker, security_names) for ticker in tickers]
        for future in futures:
            res = future.result()
            if res:
                results.append(res)

    df_results = pd.DataFrame(results)
    
    # Sort by Market Cap if possible
    try:
        df_results['Market Cap Numeric'] = pd.to_numeric(df_results['Market Cap'], errors='coerce')
        df_results = df_results.sort_values(by='Market Cap Numeric', ascending=False).drop(columns=['Market Cap Numeric'], errors='ignore')
    except:
        pass
    
    # Upload to Google Sheets
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            print("GOOGLE_CREDENTIALS not found. Saving to local CSV.")
            df_results.to_csv(f"sp500_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv", index=False)
            return

        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet_name = "S&P 500 Golden Cross Master Report"
        
        try:
            # Try to open the existing master sheet
            sh = client.open(sheet_name)
            print(f"Opened existing sheet: {sheet_name}")
        except gspread.exceptions.SpreadsheetNotFound:
            # Create a new one if it doesn't exist
            sh = client.create(sheet_name)
            print(f"Created new sheet: {sheet_name}")
            
            # Share with user (only needed on creation)
            user_email = os.environ.get('USER_EMAIL')
            if user_email:
                sh.share(user_email, perm_type='user', role='writer')
                print(f"Shared with {user_email}")
        
        worksheet = sh.get_worksheet(0)
        
        # Clear existing content
        worksheet.clear()
        
        # Add a timestamp so the user knows when it was last updated
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Convert df to list of lists for gspread
        data = [df_results.columns.values.tolist()] + df_results.astype(str).values.tolist()
        
        # Update the sheet starting from A1
        worksheet.update(data)
        
        # Add 'Last Updated' at the bottom or top? Let's add it to the Title or a specific cell.
        # Let's just print it. The user will see the data.
        print(f"Successfully updated master sheet at {timestamp}")
        print(f"Link: {sh.url}")
        
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        df_results.to_csv("emergency_backup.csv", index=False)

if __name__ == "__main__":
    main()
