import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from plotly.subplots import make_subplots

#Set up Alpha vantage API for Statements
api_key = "UDY0JA4KTIKXBA93"

def fetch_statements(symbol, api_key, f1="INCOME_STATEMENT",f2="BALANCE_SHEET",f3="CASH_FLOW"):
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": f1,
        "symbol": symbol,
        "apikey": api_key,
        "datatype": "json"
    }
    
    r = requests.get(base_url, params=params)
    if r.status_code == 200:       
        
        data = r.json()
        print(data)
        income_statement = data["quarterlyReports"]
        inc_st = pd.DataFrame.from_dict(income_statement)     
        inc_st.set_index('fiscalDateEnding',drop=True, inplace=True)
        inc_st.iloc[:, 1:] = inc_st.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        inc_st.fillna(0,inplace=True)

        time.sleep(3)  # Alpha Vantage allows 5 requests per minute for free tier
        params["function"] = f2
        
        r = requests.get(base_url, params=params)
        data = r.json()
        balance_sheet = data["quarterlyReports"]
        bal_st = pd.DataFrame.from_dict(balance_sheet)
        bal_st.set_index('fiscalDateEnding',drop=True, inplace=True)
        bal_st.iloc[:, 1:] = bal_st.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        inc_st.fillna(0,inplace=True)

        time.sleep(3)
        params["function"] = f3

        r = requests.get(base_url, params=params)
        data = r.json()
        cash_flow = data["quarterlyReports"]
        cf_st = pd.DataFrame.from_dict(cash_flow)
        cf_st.set_index('fiscalDateEnding',drop=True, inplace=True)
        cf_st.iloc[:, 1:] = cf_st.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')

    else:
        print(r)
        print(data)
        raise ValueError("Unexpected API response format. Check your parameters and API key.")
    return inc_st, bal_st, cf_st

income, balance, cash_flow = fetch_statements("AAPL", api_key)

# Calulate TTM EPS
Q_dirty_EPS = income['netIncome'] / balance['commonStockSharesOutstanding']
Ttm_EPS = Q_dirty_EPS.rolling(window=4).sum().shift(-3) 
Ttm_EPS = Ttm_EPS.dropna()
Ttm_EPS.index = pd.to_datetime(Ttm_EPS.index,utc=True) + pd.DateOffset(hours=4)  # Adjust to market close time

# Lookup Stocks
def ticker_info_lookup(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="5y", interval="1d")
        price_t = stock.analyst_price_targets
        return info, history, price_t
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}. Please wait a moment and try again.")
        return None


# Example usage
ticker = "AAPL"
info, history, targets = ticker_info_lookup(ticker)
targets.pop('current',None)
profile = pd.DataFrame.from_dict(info, orient='index', columns=[ticker])


history['TTM EPS'] = np.nan
history.index = pd.to_datetime(history.index,utc=True)
history.sort_index(inplace=True, ascending=False)


for date, eps in Ttm_EPS.items():
    if date in history.index:
        print(date, eps)
        history.at[date, 'TTM EPS'] = eps
    if date not in history.index:
        # Find the closest earlier date in history
        earlier_dates = history.index[history.index < date]
        if not earlier_dates.empty:
            closest_date = earlier_dates.max()
            print(f"Mapping EPS for {date} to closest earlier date {closest_date} in history.")
            history.at[closest_date, 'TTM EPS'] = eps


history['TTM EPS'] = history['TTM EPS'].bfill()
history['TTM P/E'] = history['Close'] / history['TTM EPS']

# Multi-panel plot with subplots
fig = make_subplots(rows=2,
                    cols=2, 
                    specs=[[{"colspan": 2,"secondary_y":True}, None],
                           [{"colspan": 2},None]]
                           )


fig.add_trace(go.Candlestick(x=history.index,
                open=history['Open'],
                high=history['High'],
                low=history['Low'],
                close=history['Close']),
                secondary_y=False,
                name='Price',
                row=1,
                col='all',)

fig.add_trace(go.Bar(x=history.index, 
                     y=history['Volume'],
                     name='Volume',),
                     secondary_y=True,
                     row=1,
                     col='all')

for y,x in targets.items():
    if x >= history['Close'][1]:
        fig.add_hline(y=x, line_dash="dot", line_color="green",annotation_text=y, annotation=dict(font_size=9, font_family="Arial"),annotation_position="top left",line_width=1)
    if x < history['Close'][1]:
        fig.add_hline(y=x, line_dash="dot", line_color="red", annotation_text=y, annotation=dict(font_size=9, font_family="Arial"),annotation_position="top left",line_width=1)

fig.add_trace(go.Scatter(x=history.index, 
                         y=history['TTM P/E'], 
                         name='TTM P/E', 
                         line=dict(color='orange')),
                         row=2,col='all')

fig.update_layout(title_text=f'{ticker} Price History & P/E',
                  hovermode='x unified',
                  xaxis=dict(rangeslider=dict(visible=False)))               

fig.show()


