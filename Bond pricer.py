import numpy as np
import matplotlib.pyplot
import matplotlib.ticker as mtick
import random as rd
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import calendar



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
    strip_number = bond['Term']* bond['Compound']
    strips = []
    Maturity_jumps = 1/bond['Compound']
    for i in range(int(strip_number)):
        strip = {}
        # Coupon STRIPS
        if Maturity_jumps < bond['Term']:
            strip['Maturity'] = Maturity_jumps
            strip['Coupon'] = 0
            strip['Price'] = (bond['Coupon']/bond['Compound'] * bond['Face']) - rd.randrange(0,10,1)/100
            strip['Face'] = bond['Coupon']/bond['Compound'] * bond['Face']
            strip['Compound'] = 1

            strips.append(strip)
        
        elif Maturity_jumps == bond['Term']:
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
    terms = {v['Term']: v['Term'] for v in bonds}.values()
    on_the_run = []
    for i in terms:
        sorted_bonds = sorted([x for x in bonds if x['Term']==i], key=lambda x: x['Term'] - x['Maturity'])
        on_the_run.append(sorted_bonds[0])
    return on_the_run


bonds = pd.read_excel('Govies.xls')
bonds.columns = bonds.iloc[6]
bonds = bonds[7:]

Treasuries = bonds[bonds['Issuer'] == 'United States Department of The Treasury']
today = pd.to_datetime(date.today())

T_s = []
Zeros = []
Frns = []

for i in range(len(Treasuries)):
    Maturity = pd.to_datetime(Treasuries['Maturity Date'].iloc[i]) - today
    Term = pd.to_datetime(Treasuries['Maturity Date'].iloc[i]) - pd.to_datetime(Treasuries['Offering Date'].iloc[i])
    Term_time = round(Term.days/365,1)
    Maturity_time = round(Maturity.days/365,2)
    
    #Zeros
    if Treasuries['Coupon Type'].iloc[i] == 'Zero':
        try:
            govy = {
                'Name':Treasuries['Security Name'].iloc[i],
                'Term':Term_time,
                'Maturity':Maturity_time,
                'Coupon':0,
                'Price':float(Treasuries['Price [Latest]'].iloc[i]),
                'Face':100,
                'Compound': 1}
            Zeros.append(govy)
        except ValueError:
            govy['Price'] = np.nan
            govy['Face'] = 100
            govy['Compound'] = 1
            Zeros.append(govy)
    #FRNs
    elif Treasuries['Coupon Type'].iloc[i] == 'Variable':
        try:
            govy = {
                'Name':Treasuries['Security Name'].iloc[i],
                'Term':round(Term_time,0),
                'Maturity':Maturity_time,
                'Coupon':'SOFR/Fed Funds',
                'Price':float(Treasuries['Price [Latest]'].iloc[i]),
                'Face':100,
                'Compound':4}
            Frns.append(govy)
        except ValueError:
            govy['Price'] = np.nan
            govy['Face'] = 100
            govy['Compound'] = 4
            Frns.append(govy)
            
    # T-bills, Notes, Bonds 
    else:
        try:
            govy = {
                'Name':Treasuries['Security Name'].iloc[i],
                'Term':round(Term_time,0),
                'Maturity':Maturity_time,
                'Coupon':float(Treasuries['Coupon Rate (%)'].iloc[i])/100,
                'Price':float(Treasuries['Price [Latest]'].iloc[i]),
                'Face':100,
                'Compound':2}
            T_s.append(govy)
        except ValueError:
            govy['Price'] = np.nan
            govy['Face'] = 100
            govy['Compound'] = 2
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

Curve = pd.DataFrame(Money_market_otr + Treasuries_otr).sort_values(by='Term')
Curve.drop_duplicates(subset=['Term'], keep='last', inplace=True)
    
fig = plt.figure(figsize=(10, 6));
ax = fig.add_subplot(111)
ax.plot(Curve['Term'], Curve['Yield']*100, marker=None, linestyle='-', color='blue')
ax.set_title('Yield Curve')
ax.set_xlabel('Term (Years)')
ax.set_ylabel('Yield (%)')

fig.show()
