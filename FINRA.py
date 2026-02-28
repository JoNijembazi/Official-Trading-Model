# -*- coding: utf-8 -*-
"""
reg SHO Daily Short Sale Volume FINRA
@author: adam getbags
"""

# import modules
import pandas as pd
import requests
from datetime import timedelta
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import datetime as dt

import plotly.express as px
import plotly.graph_objects as go

def get_token(api_key, api_secret):

    bearer_token = requests.post(
        "https://ews.fip.finra.org/fip/rest/ews/oauth2/access_token?grant_type=client_credentials",
        auth=(api_key, api_secret),
    )
    return bearer_token.json()["access_token"]

# assign dataset to request
groupName = 'fixedIncomeMarket'
datasetName = 'treasuryDailyAggregates'
token = get_token('71fbd3fd719e409b9eb9','')


# assign ticker
ticker = 'IEF'

# build URL
url = f'https://api.finra.org/data/group/{groupName}/name/{datasetName}'

# create headers
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}'
    }

# create custom filter
customFilter = {
    "limit" : 5000,
    # "compareFilters": [
    #     {"compareType": "equal", 
    #       "fieldName": "securitiesInformationProcessorSymbolIdentifier", 
    #       "fieldValue" : "IEF"}
    # ]
    }

# make POST request
request = requests.post(url, headers=headers, json=customFilter)

# format to dataframe
response_json = request.json()
print(response_json)

if isinstance(response_json, dict) and 'data' in response_json:
    data = pd.DataFrame.from_records(response_json['data'])
else:
    data = pd.DataFrame()  # Create an empty DataFrame if the expected data is not present
# format date
# data.tradeReportDate = pd.to_datetime(data.tradeReportDate).astype('datetime64[ns]')


# define aggregate functions to apply 
aggFunc = {'declines' : 'sum',
    'totalTrades': 'sum', 
    'advances': 'sum'}

aggData = data.groupby(['tradeReportDate']).agg(aggFunc)
aggData.index.names = ['Date']
aggData.index =  pd.DatetimeIndex(aggData.index).astype('datetime64[ns]')
aggData.columns = ['TotalTrades', 'ChangeUp', 'ChangeDown']

# get dates for volume request
startDate = aggData.index[-1] - timedelta(days=365)
endDate = aggData.index[-1] + timedelta(days=1)


# request techincal data from Yahoo
technicalData = yf.Ticker(ticker).history(start = startDate,
                            end = endDate)


# add total volume column // integer formatting
technicalData.index = pd.to_datetime(technicalData.index)


# Merge technicalData's Volume with aggData on date index for explicit matching
aggData.index

# Ensure both indices are timezone-naive
aggData.index = aggData.index.tz_localize(None)
technicalData.index = technicalData.index.tz_localize(None)

# aggData = aggData.merge(technicalData['Volume'], left_index=True, right_index=True, how='left')
# aggData.rename(columns={'Volume': 'yahooTotalVolume'}, inplace=True)

# short volume from FINRA over total volume from FINRA 
aggData['Advance/Decline'] = aggData['ChangeUp']/aggData['ChangeDown']

# short volume from FINRA over total volume 
aggData['Advance/Total'] = aggData['ChangeUp']/aggData['TotalTrades']

# short exempt volume from FINRA over short volume from FINRA 
aggData['Decline/Total'] = aggData['ChangeDown']/aggData['TotalTrades']

# short exempt volume from FINRA over total volume from FINRA
aggData['shortExemptVolOverTVFINRA'] = aggData['shortExemptVolumeFINRA'
                                        ]/aggData['volumeFINRA']

# short exempt volume from FINRA over total volume 
aggData['shortExemptVolOverTV'] = aggData['shortExemptVolumeFINRA'
                                   ]/aggData['yahooTotalVolume']

# line charts
px.line(aggData, y=['Advance/Decline', 'Advance/Total', 'Decline/Total'], x =aggData.index,
        title=f'Short Volume Ratios for {ticker}').show()

