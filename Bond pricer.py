import numpy as np
import matplotlib.pyplot
import matplotlib.ticker as mtick
import random as rd
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def zero_bond_price(par, discount_rate,period, years):
    z_bond_value = par/(1+discount_rate/period)**(period*years)
    return z_bond_value
def zero_bond_yield(par, z_bond_value, years):
    discount_rate = (par/z_bond_value)**(1/years) - 1
    return discount_rate    
def Yield_to_Maturity(par, coupon_rate, price, years,compound): 
    coupon = par * coupon_rate
    ytm = (coupon + (par - price)/years)/((par+price)/compound)
    return ytm
def strip_constructor(bond):
    strip_number = bond['Tenor']* bond['Compound']
    strips = []
    Maturity_jumps = 1/bond['Compound']
    for i in range(int(strip_number)):
        strip = {}
        # Coupon STRIPS
        if Maturity_jumps < bond['Tenor']:
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = zero_bond_price((bond['Coupon']/bond['Compound'] * bond['Face']),
                                             bond['Yield'],
                                             bond['Compound'],
                                             strip['Maturity'])
            strip['Face'] = bond['Coupon']/bond['Compound'] * bond['Face']
            strip['Compound'] = 2
            strip['Yield'] = zero_bond_yield(strip['Face'],strip['Price'],strip['Maturity'])

            strips.append(strip)
        
        elif Maturity_jumps == bond['Tenor']:
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = zero_bond_price((bond['Coupon']/bond['Compound'] * bond['Face']),
                                             bond['Yield'],
                                             bond['Compound'],
                                             strip['Maturity'])
            strip['Face'] = bond['Coupon']/bond['Compound'] * bond['Face']
            strip['Compound'] = 2
            strip['Yield'] = zero_bond_yield(strip['Face'],strip['Price'],strip['Maturity'])

            strips.append(strip)
            
            #Principal STRIPS
            strip = {}
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = zero_bond_price((bond['Face']),
                                             bond['Yield'],
                                             bond['Compound'],
                                             strip['Maturity']) 
            strip['Face'] = bond['Face']
            strip['Compound'] = 2
            strip['Yield'] = zero_bond_yield(strip['Face'],strip['Price'],strip['Maturity'])

            strips.append(strip)
        Maturity_jumps += 1/bond['Compound']
    return strips
def replicate_bond(strip_set:list,bond_to_replicate):
    replicated_bond = bond_to_replicate
    replicators = strip_set 
    if isinstance(replicators, list):
        replicators = sorted(replicators, key=lambda x: x['Maturity Time'] )
    else:
        raise ValueError(f"Expected a list of dictionaries for replicators, but got {type(replicators)}")
    for i in replicators:

        try: 
            if i['Maturity Time'] == replicated_bond['Maturity Time']:
                cash_flow_replicated = replicated_bond['Face']+(replicated_bond['Face'] * replicated_bond['Coupon'] / replicated_bond['Compound'])
                bond_cash_flow =  i['Face']+(i['Face'] * i['Coupon'] / i['Compound'])
                x =  cash_flow_replicated/bond_cash_flow

                cost = i['Price']*x
                i['Cost to Replicate'] = cost
            
            elif i['Maturity Time'] < replicated_bond['Maturity Time']:
                cash_flow_replicated = (replicated_bond['Face'] * replicated_bond['Coupon'] / replicated_bond['Compound'])
                bond_cash_flow =  i['Face']+(i['Face'] * i['Coupon'] / i['Compound'])
                x =  cash_flow_replicated/bond_cash_flow

                cost = i['Price']*x
                i['Cost to Replicate'] = cost
                
        except Exception as e:
            print(f"Error while processing bond {i} for replication of {replicated_bond}: {e}")   

    new_bond = replicated_bond
    new_bond['Price'] =  sum([i['Cost to Replicate'] for i in replicators if 'Cost to Replicate' in i])
    return new_bond
def on_the_run(bonds):
    Tenors = {v['Tenor']: v['Tenor'] for v in bonds}.values()
    on_the_run = []
    for i in Tenors:
        sorted_bonds = sorted([x for x in bonds if x['Tenor']==i], key=lambda x: x['Tenor'] - x['Maturity'])
        on_the_run.append(sorted_bonds[0])
    return on_the_run

# Clean up DataFrame columns and rows
bonds = pd.read_excel('KSA Sukuk.xls')
bonds.columns = bonds.iloc[6]
bonds = bonds.iloc[7:].reset_index(drop=True)  # Use iloc for clarity

today = pd.to_datetime(date.today())
Treasuries = bonds[(bonds['Issuer'] == 'Saudi Arabia') & (bonds['Price [Latest]'] != '-') & (bonds['Offering Yield (%)'] != '-')].copy().reset_index(drop=True)

T_s = []
Zeros = []
Frns = []

for i in range(len(Treasuries)):
    try:
        Maturity = pd.to_datetime(Treasuries.loc[i, 'Maturity Date']) - today
        Tenor = pd.to_datetime(Treasuries.loc[i, 'Maturity Date']) - pd.to_datetime(Treasuries.loc[i, 'Offering Date'])
        Tenor_time = round(Tenor.days/365, 1)
        Maturity_time = round(Maturity.days/365, 2)
    except Exception as e:
        print(1, i, e, f"Name:{Treasuries.loc[i, 'Security Name']}")

    # Zeros
    if Treasuries.loc[i, 'Coupon Type'] == 'Zero':
        govy = {
            'Name': Treasuries.loc[i, 'Security Name'],
            'Tenor': Tenor_time,
            'Maturity': Maturity_time,
            'Coupon': 0,
            'Price': pd.to_numeric(Treasuries.loc[i, 'Price [Latest]'], errors='coerce'),
            'Face': 100,
            'Compound': 1
        }
        Zeros.append(govy)
    # FRNs
    elif Treasuries.loc[i, 'Coupon Type'] == 'Variable':
        govy = {
            'Name': Treasuries.loc[i, 'Security Name'],
            'Tenor': round(Tenor_time, 0),
            'Maturity': Maturity_time,
            'Coupon': 'SOFR/Fed Funds',
            'Price': pd.to_numeric(Treasuries.loc[i, 'Price [Latest]'], errors='coerce'),
            'Face': 100,
            'Compound': 4
        }
        Frns.append(govy)
    # T-bills, Notes, Bonds
    else:
        govy = {
            'Name': Treasuries.loc[i, 'Security Name'],
            'Tenor': round(Tenor_time, 0),
            'Maturity': Maturity_time,
            'Coupon': pd.to_numeric(Treasuries.loc[i, 'Coupon Rate (%)'], errors='coerce') / 100,
            'Price': pd.to_numeric(Treasuries.loc[i, 'Price [Latest]'], errors='coerce'),
            'Face': 100,
            'Compound': 2
        }
        T_s.append(govy)

for i in Zeros:
    try:
        if pd.notnull(i['Price']) and pd.notnull(i['Maturity']):
            i['Yield'] = zero_bond_yield(par=i['Face'], z_bond_value=i['Price'], years=i['Maturity'])
        else:
            i['Yield'] = np.nan
    except Exception:
        i['Yield'] = np.nan

for i in T_s:
    try:
        if pd.notnull(i['Price']) and pd.notnull(i['Maturity']) and pd.notnull(i['Coupon']):
            i['Yield'] = Yield_to_Maturity(par=i['Face'], coupon_rate=i['Coupon'], price=i['Price'], years=i['Maturity'], compound=i['Compound'])
        else:
            i['Yield'] = np.nan
    except Exception:
        i['Yield'] = np.nan

Money_market_otr = on_the_run(Zeros)
Treasuries_otr = on_the_run(T_s)
Treasuries_to_zeros =[]
for i in Treasuries_otr:
    zeros = strip_constructor(i)
    Treasuries_to_zeros.append(zeros)


Curve = pd.DataFrame(Money_market_otr + Treasuries_otr).sort_values(by='Tenor').reset_index(drop=True)
Curve = Curve.drop_duplicates(subset=['Tenor'], keep='last').reset_index(drop=True)
Curve.set_index('Tenor', inplace=True)  # Use column name directly


for x in Curve.index:
    forward = x
    previous_tenor = forward
    Curve[f'Implied Spot Rates {forward} Year Forward'] = np.nan
    for i in range(len(Curve)):
        try:
            tenor_val = Curve.index[i]
            if tenor_val < forward:
                Curve.at[tenor_val, f'Implied Spot Rates {forward} Year Forward'] = np.nan
            elif tenor_val == forward:
                Curve.at[tenor_val, f'Implied Spot Rates {forward} Year Forward'] = np.nan
                Curve.at[forward, 'Forward Yield Curve'] = Curve.at[forward, f'Implied Spot Rates {previous_tenor} Year Forward']
            else:
                Curve.at[tenor_val, f'Implied Spot Rates {forward} Year Forward'] = (
                    ((1 + Curve.at[tenor_val, 'Yield']) ** tenor_val) /
                    ((1 + Curve.at[forward, 'Yield']) ** forward)
                ) ** (1 / (tenor_val - forward)) - 1
        except Exception as e:
            Curve.at[tenor_val, f'Implied Spot Rates {forward} Year Forward'] = np.nan


def visual_curves(Forwards_curves):
    fig = make_subplots(rows=1,cols=1,
                        specs=[[{"type":'scatter'}],
]
                            )
    fig.add_trace(
        go.Scatter(
            x=Curve.index, 
            y=Curve['Yield'], 
            mode='lines+markers', 
            name='Yield Curve'
            ),
            row=1,
            col=1)

    
    # table_headers = ['Tenor', 'Yield', 'Forward Yield Curve']
    # table_values = [Curve.index.tolist(),round(Curve['Yield']*100,3).tolist()]
    
    for x in Forwards_curves.index:
        try:
            fig.add_trace(go.Scatter(x=Forwards_curves.index, 
                                    y=Forwards_curves[f'Implied Spot Rates {x} Year Forward'],
                                    name = f'{x} Year Forward Curve',
                                    mode='lines+markers'),                                
                                    row=1,
                                    col=1
            )
            # table_headers.append(f'Implied Spot Rates {x} Year Forward')
            # table_values.append(round(Forwards_curves[f'Implied Spot Rates {x} Year Forward']*100,3).tolist())
        except:
            continue

    fig.update_yaxes(tickformat=".4%", title="Rate (%)",row=1,col=1)  # Format y-axis as percentages with 2 decimals
    fig.update_xaxes(tickformat='Year', tickmode='array', tickvals=Curve.index,row=1,col=1)
    fig.update_layout()
    # fig.add_trace(
    #     go.Table(
    #                 header=dict(values=table_headers
    #             ),
    #                 cells=dict(values=table_values)
    #             ),
    #             row=2,
    #             col= 1
    #             )
    # fig.add_trace(
    #     go.Table(
    #                 header=dict(values=Forwards_curves.columns[:8]
    #             ),
    #                 cells=dict(values=[(Forwards_curves[col]).to_list() for col in Forwards_curves.columns[:8]])
    #             ),
    #             row=3,
    #             col=1
    #             )
    return fig

Forwards = visual_curves(Curve)

Forwards.show()
