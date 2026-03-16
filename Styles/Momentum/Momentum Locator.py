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

yf.set_tz_cache_location("C:/Users/Jleon/AppData/Local/yfinance_cache")

universe = pd.DataFrame(tl.TickerLookup.get_clean_stock_list()['Symbol'])
universe.set_index('Symbol', inplace=True)  # Set the index to 'Symbol' for easier access
universe.index = universe.index.astype(str)  # Ensure index is string type


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

# build treemap
def build_treemap(ticker):
    if ticker is None:
        fig = px.treemap(title="Select a stock to view its options")
        fig.update_layout(xaxis_title="Date", yaxis_title="Close price", template='plotly_dark')
        return fig
    
    options_data = process_options(ticker)
    data_cols = [col for col in options_data.columns
                if col not in ["openInterest", "Expiry"]]
    
    fig_treemap = px.treemap(
        options_data,
        path=['All', 'Expiry', 'strike', 'contractSymbol'],
        values="openInterest",
        title="Option Contracts Treemap by Expiry and Open Interest",
        hover_data={col: True for col in options_data.columns
                    if col not in ["contractSymbol", "openInterest", "Expiry"]},
        color="percentChange",
        color_continuous_scale="edge",
        labels={
            "openInterest": "Open Interest",
            "Expiry": "Expiration Date",
            "strike": "Strike Price",
            "bid": "Bid Price",
            "ask": "Ask Price",
            "volume": "Volume",
            "impliedVolatility": "Implied Volatility",
            "percentChange": "Percent Change (%)",
        },
        custom_data=data_cols,
    )
        
    # compute indexes for the hovertemplate
    type_idx    = data_cols.index('Type')
    bid_idx     = data_cols.index('bid')
    ask_idx     = data_cols.index('ask')
    vol_idx     = data_cols.index('volume')
    iv_idx      = data_cols.index('impliedVolatility')

    fig_treemap.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            f"Type: %{{customdata[{type_idx}]}}<br>"
            "Open Interest: %{value:,.0f}<br>"
            "Percent Change: %{color:.2f}%<br>"
            f"Bid: %{{customdata[{bid_idx}]:.2f}}<br>"
            f"Ask: %{{customdata[{ask_idx}]:.2f}}<br>"
            f"Volume: %{{customdata[{vol_idx}]:,.0f}}<br>"
            f"Implied Volatility: %{{customdata[{iv_idx}]:.4f}}<br>"
            "<extra></extra>"
        )
    )
    fig_treemap.update_layout(template='plotly_dark')
    return fig_treemap

# helper to produce a history figure
def create_history_figure(symbol: str | None = None):
    if symbol is None:
        fig = px.line(title="Select a contract in the treemap")
        fig.update_layout(xaxis_title="Date", yaxis_title="Close price", template='plotly_dark')
        return fig
    hist = yf.Ticker(symbol).history(period="max")
    fig = go.Figure()
    
    # Add closing price line on primary y-axis
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close Price", yaxis="y"))
    
    # Add volume bars on secondary y-axis
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume", yaxis="y2", opacity=0.3))
    
    fig.update_layout(
        title=f"Price history for {symbol}",
        xaxis_title="Date",
        yaxis=dict(title="Close price"),
        yaxis2=dict(title="Volume", overlaying="y", side="right"),
        hovermode="x unified",
        template='plotly_dark'
    )
    return fig

# Dash app layout
app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': html.Span(str(ticker), style={'color': "#575353"}), 'value': str(ticker)} for ticker in universe.index.tolist()],
        value='NVDA', # Default Stock
        style={'backgroundColor': '#1a1a1a', 'color': "#FFFFFF",'fontFamily': 'Arial, sans-serif','fontcolor': '#ffffff'}
    ),
    dcc.Loading(dcc.Graph(id="treemap", style={'marginBottom': '10px'})), 
    dcc.Loading(dcc.Graph(id="history", figure=create_history_figure(), style={'marginTop': '10px'})),
], style={'margin': '0px', 'padding': '0px'})

# callback that fires when the user clicks on the treemap
@app.callback(
    Output("treemap", "figure"),
    Input("stock-dropdown", "value"),
)
def update_treemap(value):
    options_data = process_options(value)
    try:
        return build_treemap(value)
    except Exception as e:
        fig = px.treemap(title=f"Error loading options for {value}: {str(e)}")
        fig.update_layout(template='plotly_dark')
        return fig
            
@app.callback(
    Output("history", "figure"),
    Input("treemap", "clickData"),
    Input("stock-dropdown", "value")
)
def update_history(clickData, value):
    options_data = process_options(value)
    if not clickData:
        return create_history_figure()
    # the deepest-level label is the contract symbol
    label = clickData["points"][0].get("label", "")
    if label in options_data["contractSymbol"].values:
        return create_history_figure(label)
    return create_history_figure()

if __name__ == "__main__":
    app.run(debug=True)
