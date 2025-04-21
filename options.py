import pandas as pd
import numpy as np
import scipy.stats as scis
import random
import plotly.express as px 
import yfinance as yf
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import vega

def implied_vol(S0,K,T,r,market_price,flag='c',tol=0.00001):
    # Calculating the implied vol of a euro option
    # S0: Stock Price
    # K: Stike Price
    # T: Time to maturity
    # r: risk free rate
    # market_price: option price in market
    max_iter = 200 #max iterations
    vol_old = 0.3 #initial guess

    for k in range(max_iter):
        bs_price = bs(flag='c',S=S0,K=K,t=T,r=r,sigma=vol_old)
        Cprice = vega(flag='c',S=S0,K=K,t=T,r=r,sigma=vol_old)*100
        C = bs_price - market_price
        
        vol_new = vol_old - C/Cprice
        new_bs_price = bs(flag='c',S=S0,K=K,t=T,r=r,sigma=vol_new)
        
        if abs(vol_old-vol_new) < tol or abs(new_bs_price-market_price) < tol:
            break

        vol_old = vol_new
    
    implied_vol = vol_new
    return implied_vol

S0,K,T,r = 30, 28, 1/52, 0.025
market_price = 20
print(implied_vol(S0,K,T,r, market_price)*100)



# Tickers = ['OKLO', 'INTC']
# dic = {}

# # for x in Tickers:
# #     data = yf.Ticker(x)
# #     data = data.history(period='5d',interval='5m')
# #     dic[x]= data


# def stop_loss(K, Price, trading_time, opt_pos):
#     S_i = Price
#     inventory = 0
#     profit = opt_pos * 300
#     covered = opt_pos * 100
#     Price_time = []
#     Profit_time = []
#     time = []
#     for t in trading_time:
#         if S_i > K:
#             buy = covered
#             inventory = max(inventory + buy,inventory)
#             if inventory < buy:
#                 trading_cost =  buy * 0.05
#             else:
#                 trading_cost = 0
#             profit -= trading_cost
#             Profit_time.append(profit)
#             Price_time.append(S_i)
#             time.append(t)
#             S_i = S_i * (1+ random.randrange(-5,5,)/100)

#         if S_i < K:
#             sell = covered
#             inventory = max(inventory,inventory-sell)
#             if inventory > sell:
#                 trading_cost =  sell * 0.05
#             else:
#                 trading_cost = 0
#             profit -= trading_cost
#             Profit_time.append(profit)
#             Price_time.append(S_i)
#             time.append(t)
#             S_i = S_i * (1+ random.randrange(-5,5,)/100)      
        
#     return  Profit_time, Price_time, time


# Stock_price_0 = 32
# Strike_price = 33 
# trading_minutes = range(390)


# fig = go.Figure()
# for i in range(100):
#     Gain, Stock, tick = stop_loss(Strike_price,Stock_price_0, trading_minutes, 300 )
#     df = pd.DataFrame([Gain,Stock,tick]).transpose()
#     df.columns =['Profit','Price','Time']
#     fig.add_trace(go.Line(x=df['Time'], y=df['Profit']))

# fig.update_layout(showlegend=False)
# fig.show()

