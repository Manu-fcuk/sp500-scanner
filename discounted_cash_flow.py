import yfinance as yf
import pandas as pd
import numpy as np

def format_large_number(num):
    """
    Formats a large number into a more readable string with M, B, or T suffix.
    """
    if abs(num) >= 1_000_000_000_000:  # Trillions
        return f"{num / 1_000_000_000_000:,.2f}T"
    elif abs(num) >= 1_000_000_000:  # Billions
        return f"{num / 1_000_000_000:,.2f}B"
    elif abs(num) >= 1_000_000:  # Millions
        return f"{num / 1_000_000:,.2f}M"
    else:
        return f"{num:,.2f}" # Keep original formatting for smaller numbers

def get_free_cash_flow(ticker_symbol):
    """
    Fetches historical Free Cash Flow (FCF) from Yahoo Finance's financial statements.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        cash_flow = stock.cashflow
        
        if 'Free Cash Flow' in cash_flow.index:
            fcf_data = cash_flow.loc['Free Cash Flow']
            return fcf_data.iloc[0] # Most recent FCF
        else:
            print(f"Warning: 'Free Cash Flow' not directly found for {ticker_symbol}. Attempting approximation...")
            if 'Total Cash From Operating Activities' in cash_flow.index and 'Capital Expenditures' in cash_flow.index:
                operating_cf = cash_flow.loc['Total Cash From Operating Activities'].iloc[0]
                capex = cash_flow.loc['Capital Expenditures'].iloc[0] # Often negative
                return operating_cf + capex 
            else:
                print(f"Error: Could not find sufficient data to calculate FCF for {ticker_symbol}.")
                return None
    except Exception as e:
        print(f"An error occurred while fetching FCF for {ticker_symbol}: {e}")
        return None

def calculate_dcf_value(ticker_symbol, years_to_project=5, fcf_growth_rate_short_term=0.10, 
                        fcf_growth_rate_long_term=0.03, discount_rate=0.08, terminal_growth_rate=0.02):
    """
    Calculates the intrinsic value of a stock using a two-stage Discounted Cash Flow (DCF) model.
    Numbers are formatted for readability in M, B, or T.
    """
    
    current_fcf = get_free_cash_flow(ticker_symbol)
    if current_fcf is None:
        print(f"Could not retrieve current FCF for {ticker_symbol}. DCF calculation aborted.")
        return None

    print(f"Using latest reported Free Cash Flow for {ticker_symbol}: ${format_large_number(current_fcf)}")
    print(f"Projecting over {years_to_project} years with {fcf_growth_rate_short_term*100:.1f}% short-term growth.")
    print(f"Discount Rate (WACC): {discount_rate*100:.1f}%")
    print(f"Terminal Growth Rate: {terminal_growth_rate*100:.1f}%")

    # 1. Project Free Cash Flows (FCF) for the explicit period
    projected_fcf = []
    for i in range(1, years_to_project + 1):
        if i == 1:
            next_fcf = current_fcf * (1 + fcf_growth_rate_short_term)
        else:
            next_fcf = projected_fcf[-1] * (1 + fcf_growth_rate_short_term)
        projected_fcf.append(next_fcf)
    
    print("\nProjected Free Cash Flows:")
    for i, fcf in enumerate(projected_fcf):
        print(f"Year {i+1}: ${format_large_number(fcf)}")

    # 2. Calculate Present Value of Projected FCFs
    pv_fcf = []
    for i, fcf in enumerate(projected_fcf):
        pv = fcf / ((1 + discount_rate) ** (i + 1))
        pv_fcf.append(pv)
    
    pv_of_explicit_fcf = sum(pv_fcf)
    print(f"\nPresent Value of Explicit FCFs: ${format_large_number(pv_of_explicit_fcf)}")

    # 3. Calculate Terminal Value (TV)
    last_projected_fcf = projected_fcf[-1]
    
    if discount_rate <= terminal_growth_rate:
        print("Error: Discount rate must be greater than terminal growth rate for Terminal Value calculation.")
        return None
        
    terminal_value = (last_projected_fcf * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
    print(f"Terminal Value (Year {years_to_project}): ${format_large_number(terminal_value)}")

    # 4. Calculate Present Value of Terminal Value (PV_TV)
    pv_terminal_value = terminal_value / ((1 + discount_rate) ** years_to_project)
    print(f"Present Value of Terminal Value: ${format_large_number(pv_terminal_value)}")

    # 5. Calculate Total Enterprise Value (TEV)
    total_enterprise_value = pv_of_explicit_fcf + pv_terminal_value
    print(f"Total Enterprise Value: ${format_large_number(total_enterprise_value)}")

    # 6. Calculate Equity Value and Intrinsic Value Per Share
    try:
        stock_info = yf.Ticker(ticker_symbol).info
        cash = stock_info.get('totalCash', 0) 
        debt = stock_info.get('totalDebt', 0)
        shares_outstanding = stock_info.get('sharesOutstanding')

        if shares_outstanding is None or shares_outstanding == 0:
            print(f"Error: Could not retrieve shares outstanding for {ticker_symbol}.")
            return None

        equity_value = total_enterprise_value + cash - debt
        intrinsic_value_per_share = equity_value / shares_outstanding

        print(f"\nCash & Equivalents: ${format_large_number(cash)}")
        print(f"Total Debt: ${format_large_number(debt)}")
        print(f"Shares Outstanding: {shares_outstanding:,.0f}") 
        print(f"Total Equity Value: ${format_large_number(equity_value)}")
        print(f"Intrinsic Value Per Share: ${intrinsic_value_per_share:,.2f}") # Per share usually not M/B/T

        return intrinsic_value_per_share
        
    except Exception as e:
        print(f"An error occurred while fetching company info or shares outstanding: {e}")
        return None


if __name__ == "__main__":
    ticker = "pltr"  # Google (Alphabet Inc.)
    
    # DCF Model Assumptions
    years = 5                         
    growth_short_term = 0.12          
    wacc = 0.09                       
    terminal_growth = 0.025           

    intrinsic_value = calculate_dcf_value(
        ticker, 
        years_to_project=years,
        fcf_growth_rate_short_term=growth_short_term,
        discount_rate=wacc,
        terminal_growth_rate=terminal_growth
    )

    if intrinsic_value is not None:
        print(f"\n--- DCF Model Summary for {ticker} ---")
        print(f"Calculated Intrinsic Value Per Share: ${intrinsic_value:,.2f}")
        
        try:
            current_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            print(f"Current Market Price: ${current_price:,.2f}")
            if intrinsic_value > current_price:
                print(f"{ticker} appears to be Undervalued.")
            elif intrinsic_value < current_price:
                print(f"{ticker} appears to be Overvalued.")
            else:
                print(f"{ticker} appears to be Fairly Valued.")
        except Exception as e:
            print(f"Could not fetch current market price: {e}")