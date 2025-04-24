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

def zero_bond_price(par, discount_rate, years):
    z_bond_value = par/(1+discount_rate/years)**(years)
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
            strip['Price'] = (bond['Coupon']/bond['Compound'] * bond['Face']) - rd.randrange(0,10,1)/100
            strip['Face'] = bond['Coupon']/bond['Compound'] * bond['Face']
            strip['Compound'] = 1

            strips.append(strip)
        
        elif Maturity_jumps == bond['Tenor']:
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = (bond['Coupon']/bond['Compound'] * bond['Face']) - rd.randrange(0,10,1)/100
            strip['Face'] = bond['Coupon']/bond['Compound'] * bond['Face']
            strip['Compound'] = 1

            strips.append(strip)
            
            #Principal STRIPS
            strip = {}
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = bond['Face'] - rd.randrange(1,3,1)
            strip['Face'] = bond['Face']
            strip['Compound'] = 1

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


bonds = pd.read_excel('Govies.xls')
bonds.columns = bonds.iloc[6]
bonds = bonds[7:]


today = pd.to_datetime(date.today())
Treasuries = bonds[(bonds['Issuer'] == 'United States Department of The Treasury') & (bonds['Price [Latest]'] != '-') & (bonds['Offering Yield (%)'] != '-')]

T_s = []
Zeros = []
Frns = []

for i in range(len(Treasuries)):
    try:
        Maturity = pd.to_datetime(Treasuries['Maturity Date'].iloc[i]) - today
        Tenor = pd.to_datetime(Treasuries['Maturity Date'].iloc[i]) - pd.to_datetime(Treasuries['Offering Date'].iloc[i])
        Tenor_time = round(Tenor.days/365,1)
        Maturity_time = round(Maturity.days/365,2)
    except Exception as e:
        print(1, i, e, f'Name:{Treasuries['Security Name'].iloc[i]}' )  
    
    #Zeros
   
    if Treasuries['Coupon Type'].iloc[i] == 'Zero':
        govy = {
            'Name':Treasuries['Security Name'].iloc[i],
            'Tenor':Tenor_time,
            'Maturity':Maturity_time,
            'Coupon':0,
            'Price':pd.to_numeric(Treasuries['Price [Latest]'].iloc[i],errors='coerce'),
            'Face':100,
            'Compound': 1}

        Zeros.append(govy)
    #FRNs
    elif Treasuries['Coupon Type'].iloc[i] == 'Variable':
        govy = {
                'Name':Treasuries['Security Name'].iloc[i],
                'Tenor':round(Tenor_time,0),
                'Maturity':Maturity_time,
                'Coupon':'SOFR/Fed Funds',
                'Price':pd.to_numeric(Treasuries['Price [Latest]'].iloc[i],errors='coerce'),
                'Face':100,
                'Compound':4}
        Frns.append(govy)
       
    
    # T-bills, Notes, Bonds 
    else:
        govy = {
                'Name':Treasuries['Security Name'].iloc[i],
                'Tenor':round(Tenor_time,0),
                'Maturity':Maturity_time,
                'Coupon':pd.to_numeric(Treasuries['Coupon Rate (%)'].iloc[i])/100,
                'Price':pd.to_numeric(Treasuries['Price [Latest]'].iloc[i],errors='coerce'),
                'Face':100,
                'Compound':2}
        T_s.append(govy)
    
for i in Zeros:
    try:
        i['Yield'] = zero_bond_yield(par=i['Face'], z_bond_value=i['Price'], years=i['Maturity']) 
    except Exception:
        i['Yield'] = np.nan

for i in T_s:
    i['Yield'] = Yield_to_Maturity(par=i['Face'],coupon_rate=i['Coupon'], price=i['Price'], years=i['Maturity'], compound=i['Compound'])

Money_market_otr = on_the_run(Zeros)
Treasuries_otr = on_the_run(T_s)
Treasuries_to_zeros =[]
for i in Treasuries_otr:
    zeros = strip_constructor(i)
    Treasuries_to_zeros.append(zeros)

Curve = pd.DataFrame(Money_market_otr + Treasuries_otr).sort_values(by='Tenor').reset_index(drop=True)
Curve.drop_duplicates(subset=['Tenor'], keep='last', inplace=True)
Curve.set_index(Curve['Tenor'],inplace=True)

forward = 1
Curve[f'{forward} Year Forward Rates'] = np.nan
for i in range(len(Curve)):
    try: # Forward rate at T-t
        if Curve.iloc[i]['Tenor'] <= forward:
            Curve[f'{forward} Year Forward Rates'].iat[i] = Curve['Yield'].iat[i]
        else:

            Curve[f'{forward} Year Forward Rates'].iat[i] = ( # Spot rate at T
                                                    ((1+Curve.iloc[i]['Yield'])**(Curve.iloc[i]['Tenor']))/
                                                    # Divided by Spot rate at time t
                                                    ((1+Curve.loc[forward,'Yield'])**(Curve.loc[forward,'Tenor']))
                                                    # to the inverse power of T-t
                                                      )**(1/(Curve.iloc[i]['Tenor']-forward))-1

    except Exception as e:
        Curve.iloc[i][f'{forward} Year Forward Rates'] = Curve.iloc[i]['Yield']
        print(e)

Curve[f'Implied Spot Rates {forward} Year Forward'] = np.nan

for count,value in enumerate(Curve['Tenor'].unique()):
    try: # Forward rate at T-t
            Curve[f'Implied Spot Rates {forward} Year Forward'].iat[count] = ( # Spot rate at T
                                                    ((1+Curve.iloc[count]['Yield'])**(Curve.iloc[count]['Tenor']))/
                                                    # Divided by Spot rate at time t
                                                    ((1+Curve.iat[count,'Yield'])**(Curve.iat[count-(count-1),'Tenor']))
                                                    # to the inverse power of T-t
                                                      )**(1/(Curve.iloc[i]['Tenor']-forward))-1
    except Exception as e:
        print(e)

fig = go.Figure(go.Scatter(x=Curve['Tenor'], 
                          y=Curve[f'{forward} Year Forward Rates'],
                          mode='lines+markers')
)
fig.update_yaxes(tickformat=".2%", title="Yield (%)")  # Format y-axis as percentages with 2 decimals
fig.update_xaxes(tickformat='Year', tickmode='array', tickvals=Curve['Tenor'].unique())
fig.add_trace(go.Scatter(x=Curve['Tenor'], y=Curve['Yield'], mode='lines+markers', name='Yield Curve',))
fig.add_table(header=Curve['Tenor'],
              cells=[Curve['Yield'],
                     Curve[f'{forward} Year Forward Rates']
                     ])
fig.show()


