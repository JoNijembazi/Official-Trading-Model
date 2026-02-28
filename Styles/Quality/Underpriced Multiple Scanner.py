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

ticker = "TFII"

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

income, balance, cash_flow = fetch_statements(ticker, api_key)

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
        history = stock.history(period="max", interval="1d")
        price_t = stock.analyst_price_targets
        return info, history, price_t
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}. Please wait a moment and try again.")
        return None

# Example usage

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
def interface_plots():
    fig = make_subplots(rows=3,
                        cols=2, 
                        specs=[[{"colspan": 2,"secondary_y":True}, None],
                            [{"colspan": 1, 'type': 'indicator'},{"colspan": 1, 'type': 'indicator'}],
                            [{"colspan": 2, 'type': 'table'},None]
                            ]
                            )

    fig.add_trace(go.Bar(x=history.index,                      
                        y=history['Volume'],
                        name='Volume'),
                        secondary_y=True,
                        row=1,
                        col='all')

    fig.add_trace(go.Candlestick(x=history.index,
                    open=history['Open'],
                    high=history['High'],
                    low=history['Low'],
                    close=history['Close'],name='OCHL',zorder=1),
                    secondary_y=False,
                    row=1,
                    col='all',)


    fig.add_trace(go.Indicator(
        mode = "number+delta+gauge",
        value = targets['mean'],
        number = {'prefix':'$'},
        delta={'reference': history['Close'].iloc[0], 
            'relative': True,
            "valueformat": ".00%"},
        title = {"text": "Street Consensus"},
        domain={'x': [0.5, 0.5], 'y': [0.5, 0.5]}),
        row=2,
        col=1)

    fig.add_trace(go.Indicator(
        mode = "delta",
        value = history['Close'].iloc[0],
        delta={'reference': history.loc[history[(history.index.year == 2025)].index.min(),'Close'],
            'relative': True,
            "valueformat": ".00%"},
        title = {"text": "YTD Performance"},
        domain={'x': [0.5, 0.5], 'y': [0.5, 0.5]}),
        row=2,
        col=2) 
    
    fig.add_trace(go.Table(
        header=dict(values=['Metric', 'Value'],
                    fill_color='rgb(0,0,0)',
                    align='center',
                    font=dict(color='red', size=12)
                    ),
        cells=dict(values=[profile.index, profile[ticker]],
                fill_color='rgb(0,0,0)',
                align='left',
                font=dict(color='red', size=8)
                )),
                row = 3, 
                col=1,
        )
    
    fig.update_layout(title_text=f'{profile.loc['longName',ticker]} ({ticker})',
                  hovermode='x unified',
                  xaxis=dict(rangeslider=dict(visible=False),
                             rangeselector=dict(buttons=list([
                                 dict(count=1, label="1m", step="month", stepmode="backward"),
                                 dict(count=3, label="3m", step="month", stepmode="backward"),
                                 dict(count=6, label="6m", step="month", stepmode="backward"),
                                 dict(count=1, label="YTD", step="year", stepmode="todate"),
                                 dict(count=1, label="1y", step="year", stepmode="backward"),
                                 dict(count=3, label="3y", step="year", stepmode="backward"),
                                 dict(count=5,label="5y", step="year", stepmode="backward"),
                                 dict(step="all"),
                                 ]),
                                 activecolor='red',
                                 font=dict(size=10, color='white'),
                                 )                               
                                 ),
                  yaxis = dict(title='Price', side='left',fixedrange=False,autorange=True),
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                  height=800,
                  width=1000,
                  template='plotly_dark'
                  )        
    fig.show()


    # fig.add_trace(go.Scatter(x=history.index, 
    #                         y=history['TTM P/E'], 
    #                         name='TTM P/E', 
    #                         line=dict(color='orange')),
    #                         row=2,col='all',
    #                         )

fig3 = go.Figure(data=go.Table(columnwidth=[250*len(balance.columns) for col in balance.columns],
    header=dict(values=['Item'] + balance.index.tolist(),
                align='center',
                fill_color='goldenrod',
                font=dict(color='white', size=12)
                ),
    cells=dict(values=[balance.columns.tolist()] + [balance[col].tolist() for col in balance.columns],
               align='left',
               fill_color='black',
               font=dict(color='orange', size=8),
               format=[None] + [".0f"] * len(balance.index)),),
    layout=go.Layout(title_text=f'{ticker} Balance Sheet'),
)

fig3.update_layout(
    height=800,
    width=1400,
    template='plotly_dark',
    margin=dict(l=300)
)

fig3.update_layout(height=800, width=1000, template='plotly_dark')

interface_plots()
