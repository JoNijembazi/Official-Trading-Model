
import sys
import os
# Add the absolute path to the project root to sys.path
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

#Key Functions
universe = pd.DataFrame(tl.TickerLookup.get_clean_stock_list()['Symbol'])
universe['info'] = None  # Add a new column to store the info data
universe['price history'] = None  # Add a new column to store the info data
universe.set_index('Symbol', inplace=True)  # Set the index to 'Symbol' for easier access

def fetch_and_store(i, tickers):
    try:
        info = yf.Ticker(i).info  # Get the ticker symbol from the index
        price_history = yf.Ticker(i).history(period="max")  # Get the ticker symbol from the index
        tickers.at[i, 'info'] = info  # Store the info in the universe DataFrame
        tickers.at[i, 'price history'] = price_history  # Store the price history in the universe DataFrame
        return None
    except Exception as e:
        print(f"Error fetching data for {tickers.loc[i]} : {e}")
        time.sleep(1)  # Wait for 1 second before retrying
        return None

#%%
# Get the list of stocks

fetch_and_store('AAPL', universe)

stock_info = pd.DataFrame(list(universe.at['AAPL', 'info'].items()), columns=['Key', 'Value'])
# app = Dash()
app = Dash()

app.layout = html.Div([
    html.H1("Stock Information Dashboard"),
    html.Div([
        html.Table([
                html.Tr([
                    html.Th("Key"),
                    html.Th("Value")
                ])] + [
                    html.Tr([
                        html.Td(row['Key']),
                        html.Td(str(row['Value']))
                    ]) for _, row in stock_info.iterrows()
                ], style={'borderCollapse': 'collapse', 'width': '100%', 'backgroundColor': '#f2f2f2',}
        )
    ])
],style={'borderCollapse': 'collapse', 'width': '100%', 'backgroundColor': '#f2f2f2',})

if __name__ == '__main__':
    app.run(debug=True)

# # App layout
# app.layout = html.Div()

# @app.callback(
#     [Output('output_container', 'children')],
#     [Input('dropdown', 'value')],
# )

# def update(option):
    # return None