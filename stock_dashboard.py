import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from textblob import TextBlob

# --- Page Configuration ---
st.set_page_config(
    page_title="Stock Evaluation Dashboard",
    page_icon="💹",
    layout="wide"
)

# --- Helper Functions ---

def format_large_number(num):
    """Formats a large number into a more readable string with M, B, or T suffix."""
    if num is None:
        return "N/A"
    if abs(num) >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:,.2f}T"
    elif abs(num) >= 1_000_000_000:
        return f"{num / 1_000_000_000:,.2f}B"
    elif abs(num) >= 1_000_000:
        return f"{num / 1_000_000:,.2f}M"
    else:
        return f"{num:,.2f}"

def get_free_cash_flow(stock):
    """Fetches historical Free Cash Flow (FCF) from Yahoo Finance's financial statements."""
    try:
        cash_flow = stock.cashflow
        if cash_flow.empty:
            return None
            
        if 'Free Cash Flow' in cash_flow.index:
            return cash_flow.loc['Free Cash Flow'].iloc[0]
        elif 'Total Cash From Operating Activities' in cash_flow.index and 'Capital Expenditures' in cash_flow.index:
            operating_cf = cash_flow.loc['Total Cash From Operating Activities'].iloc[0]
            capex = cash_flow.loc['Capital Expenditures'].iloc[0]
            return operating_cf + capex
        else:
            return None
    except Exception:
        return None

def perform_dcf_analysis(stock, growth_rate, discount_rate, terminal_growth_rate):
    """Performs a robust 5-year Discounted Cash Flow (DCF) analysis."""
    if discount_rate <= terminal_growth_rate:
        st.error("Error: Discount Rate must be greater than the Terminal Growth Rate.")
        return None, None, None

    try:
        free_cash_flow = get_free_cash_flow(stock)
        if free_cash_flow is None:
            st.warning("Could not calculate Free Cash Flow. DCF analysis cannot be performed.")
            return None, None, None

        future_fcf = [free_cash_flow * (1 + growth_rate) ** i for i in range(1, 6)]
        terminal_value = (future_fcf[-1] * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        discounted_fcf = [fcf / (1 + discount_rate) ** (i + 1) for i, fcf in enumerate(future_fcf)]
        discounted_terminal_value = terminal_value / (1 + discount_rate) ** 5
        enterprise_value = sum(discounted_fcf) + discounted_terminal_value

        total_debt = stock.info.get('totalDebt', 0)
        cash_and_equivalents = stock.info.get('totalCash', 0)
        shares_outstanding = stock.info.get('sharesOutstanding', 1)
        
        if shares_outstanding == 0:
            st.error("Shares Outstanding is zero.")
            return None, None, None

        equity_value = enterprise_value - total_debt + cash_and_equivalents
        intrinsic_value = equity_value / shares_outstanding
        return intrinsic_value, future_fcf, terminal_value

    except Exception as e:
        st.error(f"DCF Error: {e}")
        return None, None, None

def calculate_ddm_value(stock, growth_rate, required_return):
    """Calculates intrinsic value using Dividend Discount Model (DDM)."""
    try:
        dividends = stock.dividends
        if dividends.empty:
            return None
        
        latest_dividend = dividends.iloc[-1]
        
        if required_return <= growth_rate:
            st.error("Error: Required Return must be greater than Growth Rate for DDM.")
            return None
            
        intrinsic_value = latest_dividend * (1 + growth_rate) / (required_return - growth_rate)
        return intrinsic_value
    except Exception:
        return None

def calculate_rsi(data, window=14):
    """Calculates Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_fibonacci_levels(data):
    """Calculates Fibonacci Retracement Levels based on 1-year High/Low."""
    max_price = data['High'].max()
    min_price = data['Low'].min()
    diff = max_price - min_price
    
    levels = {
        '0% (High)': max_price,
        '23.6%': max_price - 0.236 * diff,
        '38.2%': max_price - 0.382 * diff,
        '50%': max_price - 0.5 * diff,
        '61.8%': max_price - 0.618 * diff,
        '100% (Low)': min_price
    }
    return levels

def analyze_sentiment(news_items):
    """Analyzes sentiment of news headlines using TextBlob."""
    if not news_items:
        return 0, "Neutral"
    
    polarity_sum = 0
    count = 0
    
    for item in news_items:
        # Handle nested structure if present
        if 'content' in item:
            title = item['content'].get('title', '')
        else:
            title = item.get('title', '')
            
        if title:
            blob = TextBlob(title)
            polarity_sum += blob.sentiment.polarity
            count += 1
            
    if count == 0:
        return 0, "Neutral"
        
    avg_polarity = polarity_sum / count
    
    if avg_polarity > 0.1:
        sentiment = "Positive"
    elif avg_polarity < -0.1:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
        
    return avg_polarity, sentiment

# --- Sidebar ---
st.sidebar.title("Configuration")
ticker_symbol = st.sidebar.text_input("Ticker Symbol", "NVDA").upper()

st.sidebar.subheader("DCF Parameters")
dcf_growth = st.sidebar.slider("Growth Rate (%)", 0.0, 50.0, 15.0, key="dcf_growth") / 100
dcf_discount = st.sidebar.slider("Discount Rate (%)", 5.0, 20.0, 9.0, key="dcf_discount") / 100
dcf_terminal = st.sidebar.slider("Terminal Growth (%)", 0.0, 5.0, 2.5, key="dcf_terminal") / 100

st.sidebar.subheader("DDM Parameters")
ddm_growth = st.sidebar.slider("Dividend Growth (%)", 0.0, 20.0, 5.0, key="ddm_growth") / 100
ddm_return = st.sidebar.slider("Required Return (%)", 5.0, 20.0, 10.0, key="ddm_return") / 100

# --- Main App ---
st.title("Stock Evaluation Dashboard")

if not ticker_symbol:
    st.warning("Enter a ticker symbol.")
else:
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        if 'regularMarketPrice' not in info:
             st.error(f"No data found for '{ticker_symbol}'.")
        else:
            # --- Header ---
            col1, col2 = st.columns([1, 5])
            with col1:
                if 'logo_url' in info and info['logo_url']:
                    st.image(info['logo_url'], width=80)
            with col2:
                st.header(info.get('longName', ticker_symbol))
                st.write(f"**{info.get('sector', 'N/A')}** | {info.get('industry', 'N/A')}")
            
            current_price = info.get('regularMarketPrice')
            
            # --- Tabs ---
            tab_overview, tab_financials, tab_valuation, tab_technicals, tab_news = st.tabs(["Overview", "Financials", "Valuation", "Technicals", "News & Social"])
            
            # --- Overview Tab ---
            with tab_overview:
                # Key Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Current Price", f"${current_price:,.2f}")
                m2.metric("Market Cap", format_large_number(info.get('marketCap')))
                m3.metric("PE Ratio", f"{info.get('trailingPE', 'N/A')}")
                m4.metric("Beta", f"{info.get('beta', 'N/A')}")
                
                st.subheader("Price History")
                hist = stock.history(period="1y")
                
                # Moving Averages
                hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Price'))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], line=dict(color='orange', width=1), name='SMA 50'))
                fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], line=dict(color='blue', width=1), name='SMA 200'))
                fig.update_layout(xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                st.write(info.get('longBusinessSummary', ''))

            # --- Financials Tab ---
            with tab_financials:
                st.subheader("Financial Statements")
                stmt_type = st.selectbox("Select Statement", ["Income Statement", "Balance Sheet", "Cash Flow"])
                
                if stmt_type == "Income Statement":
                    df = stock.financials
                elif stmt_type == "Balance Sheet":
                    df = stock.balance_sheet
                else:
                    df = stock.cashflow
                
                if df.empty:
                    st.info("No data available.")
                else:
                    st.dataframe(df.style.format("${:,.0f}"))

            # --- Valuation Tab ---
            with tab_valuation:
                st.subheader("Valuation Models")
                
                col_dcf, col_ddm = st.columns(2)
                
                with col_dcf:
                    st.markdown("### DCF Analysis")
                    dcf_val, future_fcf, term_val = perform_dcf_analysis(stock, dcf_growth, dcf_discount, dcf_terminal)
                    if dcf_val:
                        st.metric("Intrinsic Value (DCF)", f"${dcf_val:,.2f}", delta=f"{dcf_val-current_price:,.2f}")
                        if dcf_val > current_price:
                            st.success("Undervalued")
                        else:
                            st.error("Overvalued")
                    else:
                        st.info("Could not perform DCF.")

                with col_ddm:
                    st.markdown("### DDM Analysis")
                    ddm_val = calculate_ddm_value(stock, ddm_growth, ddm_return)
                    if ddm_val:
                        st.metric("Intrinsic Value (DDM)", f"${ddm_val:,.2f}", delta=f"{ddm_val-current_price:,.2f}")
                        if ddm_val > current_price:
                            st.success("Undervalued")
                        else:
                            st.error("Overvalued")
                    else:
                        st.info("Not applicable (No Dividends or Error)")

            # --- Technicals Tab ---
            with tab_technicals:
                st.subheader("Technical Analysis Signals")
                
                hist = stock.history(period="2y") # Need more data for SMA 200
                if len(hist) < 200:
                    st.warning("Not enough historical data for technical analysis.")
                else:
                    # Calculations
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
                    hist['RSI'] = calculate_rsi(hist)
                    fib_levels = calculate_fibonacci_levels(hist[-252:]) # Last 1 year for Fib
                    
                    current_sma_50 = hist['SMA_50'].iloc[-1]
                    current_sma_200 = hist['SMA_200'].iloc[-1]
                    current_rsi = hist['RSI'].iloc[-1]
                    
                    # Signals
                    col_sig1, col_sig2, col_sig3 = st.columns(3)
                    
                    # 1. Moving Averages
                    with col_sig1:
                        st.markdown("#### Moving Averages")
                        st.metric("SMA 50", f"${current_sma_50:,.2f}")
                        st.metric("SMA 200", f"${current_sma_200:,.2f}")
                        
                        if current_sma_50 > current_sma_200:
                            st.success("Signal: **GOLDEN CROSS (Bullish)**")
                        elif current_sma_50 < current_sma_200:
                            st.error("Signal: **DEATH CROSS (Bearish)**")
                        else:
                            st.info("Signal: Neutral")

                    # 2. RSI
                    with col_sig2:
                        st.markdown("#### RSI (14-day)")
                        st.metric("Current RSI", f"{current_rsi:.2f}")
                        
                        if current_rsi < 30:
                            st.success("Signal: **OVERSOLD (Buy)**")
                        elif current_rsi > 70:
                            st.error("Signal: **OVERBOUGHT (Sell)**")
                        else:
                            st.info("Signal: Neutral")

                    # 3. Fibonacci
                    with col_sig3:
                        st.markdown("#### Fibonacci Levels (1Y)")
                        closest_level = min(fib_levels.items(), key=lambda x: abs(x[1] - current_price))
                        st.metric("Nearest Level", f"{closest_level[0]}: ${closest_level[1]:,.2f}")
                        
                        if current_price > closest_level[1]:
                             st.info(f"Trading above {closest_level[0]} support/resistance")
                        else:
                             st.info(f"Trading below {closest_level[0]} support/resistance")

                    # Chart with Indicators
                    st.subheader("Technical Chart")
                    fig_tech = go.Figure()
                    fig_tech.add_trace(go.Candlestick(x=hist.index[-252:], open=hist['Open'][-252:], high=hist['High'][-252:], low=hist['Low'][-252:], close=hist['Close'][-252:], name='Price'))
                    fig_tech.add_trace(go.Scatter(x=hist.index[-252:], y=hist['SMA_50'][-252:], line=dict(color='orange', width=1), name='SMA 50'))
                    fig_tech.add_trace(go.Scatter(x=hist.index[-252:], y=hist['SMA_200'][-252:], line=dict(color='blue', width=1), name='SMA 200'))
                    
                    # Add Fib Lines
                    for level, price in fib_levels.items():
                        fig_tech.add_hline(y=price, line_dash="dot", annotation_text=level, annotation_position="top right")

                    fig_tech.update_layout(xaxis_rangeslider_visible=False, height=600)
                    st.plotly_chart(fig_tech, use_container_width=True)

            # --- News & Social Tab ---
            with tab_news:
                st.subheader("News Sentiment & Analyst Consensus")
                
                col_news, col_analyst = st.columns(2)
                
                with col_news:
                    st.markdown("### News Sentiment")
                    news = stock.news
                    avg_polarity, sentiment_label = analyze_sentiment(news)
                    
                    st.metric("Average Sentiment Polarity", f"{avg_polarity:.2f}")
                    if sentiment_label == "Positive":
                        st.success(f"Overall Sentiment: **{sentiment_label}**")
                    elif sentiment_label == "Negative":
                        st.error(f"Overall Sentiment: **{sentiment_label}**")
                    else:
                        st.info(f"Overall Sentiment: **{sentiment_label}**")
                        
                    st.markdown("#### Recent Headlines")
                    for item in news[:5]: # Show top 5
                        # Handle nested structure
                        if 'content' in item:
                            title = item['content'].get('title', 'No Title')
                            link_obj = item['content'].get('clickThroughUrl')
                            link = link_obj.get('url') if link_obj else '#'
                        else:
                            title = item.get('title', 'No Title')
                            link = item.get('link', '#')
                            
                        st.write(f"- [{title}]({link})")

                with col_analyst:
                    st.markdown("### Analyst Consensus")
                    target_mean = info.get('targetMeanPrice')
                    target_high = info.get('targetHighPrice')
                    target_low = info.get('targetLowPrice')
                    recommendation = info.get('recommendationKey', 'N/A').replace('_', ' ').title()
                    
                    st.metric("Analyst Recommendation", recommendation)
                    
                    if target_mean:
                        st.metric("Mean Target Price", f"${target_mean:,.2f}", delta=f"{target_mean-current_price:,.2f}")
                        st.write(f"**High Target:** ${target_high:,.2f}")
                        st.write(f"**Low Target:** ${target_low:,.2f}")
                        
                        # Gauge Chart for Target Price
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = current_price,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Current Price vs Target Range"},
                            delta = {'reference': target_mean},
                            gauge = {
                                'axis': {'range': [target_low * 0.9, target_high * 1.1]},
                                'bar': {'color': "black"},
                                'steps': [
                                    {'range': [target_low * 0.9, target_low], 'color': "red"},
                                    {'range': [target_low, target_high], 'color': "lightgreen"},
                                    {'range': [target_high, target_high * 1.1], 'color': "green"}],
                                'threshold': {
                                    'line': {'color': "blue", 'width': 4},
                                    'thickness': 0.75,
                                    'value': target_mean}}))
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    else:
                        st.info("No analyst target price data available.")

    except Exception as e:
        st.error(f"An error occurred: {e}")