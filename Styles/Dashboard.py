
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

#%%

yf.set_tz_cache_location("C:/Users/Jleon/AppData/Local/yfinance_cache")

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
universe.index = universe.index.astype(str)  # Ensure index is string type

def fetch_and_store(value, tickers = universe):
    try:
        info = yf.Ticker(value).info  # Get the ticker symbol from the index
        price_history = yf.Ticker(value).history(period="max")  # Get the ticker symbol from the index
        tickers.at[value, 'info'] = info  # Store the info in the universe DataFrame
        tickers.at[value, 'price history'] = price_history  # Store the price history in the universe DataFrame
        return None
    except Exception as e:
        print(f"Error fetching data for {tickers.loc[i]} : {e}")
        time.sleep(1)  # Wait for 1 second before retrying
        return None


fetch_and_store('AAPL')  # Example for a single ticker

#%%
# Get the list of stocks

stock_info = pd.DataFrame(list(universe.at['AAPL', 'info'].items()), columns=['Key', 'Value'])
price_data = pd.DataFrame(universe.at['AAPL', 'price history'])

# app = Dash()
app = Dash()

app.layout = html.Div([
    html.H1("Stock Information Dashboard"), 
    html.Div([dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': html.Span(str(ticker), style={'color': "#575353"}), 'value': str(ticker)} for ticker in universe.index.tolist()],
        value='NVDA', # Default Stock
        style={'backgroundColor': '#1a1a1a', 'color': "#FFFFFF",'fontFamily': 'Arial, sans-serif','fontcolor': '#ffffff'}
    ),
        dcc.Graph(
            id='price-chart',
            style={'height': '100vh', 'width': '100%'}
        )
    ], style={'height': '100vh', 'width': '100%', 'backgroundColor': '#000000'}),
    html.Div(id='stock-info-table', style={'backgroundColor': '#000000', 'marginTop': '10px'})
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#000000', 'height': '100vh', })


@app.callback(
    Output('stock-info-table', 'children'),
    Input('stock-dropdown', 'value'),
)
def update_table(value):
    if value is None:
        return html.Div("Searching and Loading...", style={'color': '#ffffff', 'padding': '20px'})
    
    # Check if value exists in universe
    if value not in universe.index:
        return html.Div("Please select a valid stock.", style={'color': '#ffffff', 'padding': '20px'})
    
    if universe.at[value, 'info'] is None:
        fetch_and_store(value)  # Fetch data if not already fetched

    stock_info = pd.DataFrame(list(universe.at[value, 'info'].items()), columns=['Key', 'Value'])

    # Format values based on key
    def format_value(key, value):
        if value is None:
            return value
        percentage_keys = ['beta', 'dividendYield', 'trailingPE', 'forwardPE', 'profitMargins', 'operatingMargins', 'grossMargins', 'returnOnAssets', 'returnOnEquity']
        if isinstance(value, set):
            return ', '.join(map(str, sorted(value)))
        if any(pct_key.lower() in key.lower() for pct_key in percentage_keys):
            if isinstance(value, (int, float)):
                return f"{value * 100:.2f}%"
        elif isinstance(value, (int, float)):
            try:
                return f"{int(value):,}"
            except:
                return value
        return value
    business_summary_keys = {'longName':'Company Name','longBusinessSummary':'Business Summary','sector':'Sector','industry':'Industry','marketCap':'Market Cap','enterpriseValue':'Enterprise Value'}

    stock_info['Value'] = stock_info.apply(lambda row: format_value(row['Key'], row['Value']), axis=1)
    return html.Table(
        [html.Tr([
            html.Th("", style={'padding': '8px'}),
            html.Th("Description", style={'padding': '8px'})
        ])] +
        [
            html.Tr([
            html.Td(business_summary_keys[key],
                style={'padding': '8px'}),
            html.Td(
                stock_info.loc[stock_info['Key'] == key, 'Value'].iloc[0],
                style={
                'maxHeight': '100px',
                'overflowY': 'auto',
                'display': 'block',
                'cursor': 'pointer',
                'padding': '8px'
                },
                id={'type': 'cell', 'index': key},
                n_clicks=0
            )
            ]) for key in business_summary_keys
        ],
        style={
            'borderCollapse': 'separate',        # allow spacing between cells
            'borderSpacing': '0 10px',          # vertical space between rows
            'width': '100%',
            'backgroundColor': '#030000',
            'color': '#ffffff'
        }
        )

@app.callback(
    Output('price-chart', 'figure'),
    Input('stock-dropdown', 'value'),
)
def chart_price_history(value):
    if value is None:
        fig = go.Figure().add_annotation(text="Searching and Loading...", showarrow=False)
        fig.update_layout(template='plotly_dark', paper_bgcolor='#000000', plot_bgcolor='#030000', font=dict(color='#ffffff'))
        return fig 

    # Check if value exists in universe
    if value not in universe.index:
        fig = go.Figure().add_annotation(text="Please select a valid stock.", showarrow=False)
        fig.update_layout(template='plotly_dark', paper_bgcolor='#000000', plot_bgcolor='#030000', font=dict(color='#ffffff'))
        return fig 
    
    if universe.at[value, 'price history'] is None:
        fetch_and_store(value)  # Fetch data if not already fetched

    price_history = universe.at[value, 'price history']
    if price_history is not None:
        fig = go.Figure(data=[go.Candlestick(x=price_history.index,
                                             open=price_history['Open'],
                                             high=price_history['High'],
                                             low=price_history['Low'],
                                             close=price_history['Close'],
                                             yaxis='y',
                                             name='Price')])
        fig.add_trace(go.Bar(x=price_history.index, y=price_history['Volume'], name='Volume', yaxis='y2', marker=dict(color='rgba(100, 150, 200, 0.3)')))
        fig.update_layout(title=f'{value} Trading Chart',
                          xaxis_title='Date',
                          yaxis_title='Price',
                          yaxis2=dict(title='Volume', overlaying='y', side='right'),
                          xaxis_rangeslider_visible=False, 
                          template='plotly_dark',
                          paper_bgcolor='#000000',
                          plot_bgcolor='#030000',
                          font=dict(color='#ffffff'),
                          hovermode='x unified')
        return fig
    else:
        print(f"No price history available for {value}")

if __name__ == '__main__':
    app.run(debug=True)


# %%    
