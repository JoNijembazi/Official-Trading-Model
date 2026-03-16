import sys
import os
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import yfinance as yf
from datetime import datetime
import ftplib as FTP
import tickerlookup.Ticker_list as tl  
import concurrent.futures
import time
from dash import Dash, html, dcc, callback, Output, Input
import scipy.stats as stats
import matplotlib.pyplot as plt
import fredapi as fa

def process_options(ticker):
    options = yf.Ticker(ticker).options  # Fetch expirations dynamically here
    results = []
    
    for opt in range(len(options)):
        opt_chain = yf.Ticker(ticker).option_chain(options[opt])  # Renamed 'opt' to 'opt_chain' for clarity
        results.append(opt_chain)

    options_data = pd.DataFrame()
    for opt in results:
        df_calls = pd.DataFrame(opt.calls)
        df_puts = pd.DataFrame(opt.puts)
        df_puts.fillna(0, inplace=True) 
        df_calls.fillna(0, inplace=True)
        options_data = pd.concat([options_data, df_calls], ignore_index=True)
        options_data = pd.concat([options_data, df_puts], ignore_index=True)
    
    options_data['Expiry'] = pd.to_datetime(options_data['contractSymbol'].str[4:10], format='%y%m%d').dt.strftime('%Y-%m-%d')
    options_data['All'] = 'All Contracts'
    options_data['Type'] = options_data['contractSymbol'].str.contains('C').map({True: 'Call', False: 'Put'})

    return options_data

def fetch_and_store(ticker):
    price_history = yf.Ticker(ticker).history(period="max")  # Get the ticker symbol from the index
    return price_history

df = process_options('NVDA')
price_history = fetch_and_store('NVDA')
price_history['logchange'] = np.log(price_history['Close'] / price_history['Close'].shift(1))-1

print(price_history['Close'].iloc[-1])
options = df[(df['strike'] > price_history['Close'].iloc[-1]*0.8)&(df['strike'] < price_history['Close'].iloc[-1]*1.2)].sort_values(by='openInterest', ascending=False).head(10)

results = []
for index, row in options.iterrows():
    option_hist = fetch_and_store(row['contractSymbol'])
    print(f"Fetched history for {row['contractSymbol']}")
    option_hist['contractSymbol'] = row['contractSymbol']  # Add contract symbol to the history DataFrame
    results.append(option_hist)

fig = go.Figure()

for opt in results: 
    opt['logchange'] = np.log(opt['Close'] / opt['Close'].shift(1))-1
    fig.add_trace(go.Scatter(x=opt.index,
                                   y=opt['logchange'] * 100, 
                                   name=opt['contractSymbol'][0]))
fig.add_trace(go.Scatter(x=price_history.index, 
                        y=price_history['logchange'] * 100,
                        name='Underlying'))

fig.update_layout(title='Option and Underlying Price Changes', xaxis_title='Date', yaxis_title='Percentage Change (%)')
fig.show()


fred = fa.Fred('eaa358a70c1b9ce981ac8b39975d8eb5')

SOFR_data = fred.get_series('SOFR')

for opt in results:
    opt['logchange'] = np.log(opt['Close'] / opt['Close'].shift(1))
    correlation = price_history['logchange'].corr(opt['logchange'])
    print(f"Correlation between {opt['contractSymbol'][0]} and Underlying: {correlation:.4f}")
    stats.probplot(opt['logchange'].dropna(), dist="norm", plot=plt)
    plt.title(f'QQ Plot of Log Returns of {opt["contractSymbol"][0]}') 
    plt.show()

stats.probplot(price_history['logchange'].dropna(), dist="norm", plot=plt)
plt.show()
plt.title('QQ Plot of Log Returns')

