# Dash App for the visualization of the data
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import nbformat
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


# Create the Dash app
app = Dash(__name__)

# Load the data
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the file path
file_path = os.path.join(script_dir, "US CPI\\CPI 1913-2024.xlsx")

# Load the data
df = pd.read_excel(file_path, engine='openpyxl')

# Format the data
df.index = df['Year']

df.drop(columns=['HALF1','HALF2','Year'], 
        axis=1, 
        inplace=True)

# Calculate the MoM and YoY CPI
values_flat = pd.DataFrame(df.values.flatten())
MoMCPI = values_flat.pct_change(periods=1,fill_method=None) *100
YoYCPI = values_flat.pct_change(periods=12,fill_method=None)*100
months = df.columns
years = df.index
new_index = [f"{year}-{month}" for year in years for month in months]
MoMCPI.index = new_index
YoYCPI.index = new_index

#Start the Dash app
app.layout = html.Div(
    
    children=[html.H1(children='CPI Signals', 
                      
            style={'textAlign': 'center', 'color':'red','background-color':'black'}),

    dcc.Dropdown(id='dropdown',
                 options=[{'label': 'MoM Signals', 'value': 'MoM'},
                          {'label': 'YoY Signals', 'value': 'YoY'}],
                    multi=False,
                    value='MoM'),
                   
    html.Div(id='output_container', children=[],style={'background-color':'black'}),
    
    html.Br(style={'background-color':'black'}),

    dcc.Graph(id='CPI_Signals',
                figure={})
    ],
    style={'background-color':'black'}
) 

@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='CPI_Signals', component_property='figure')],
    [Input(component_id='dropdown', component_property='value')]
)
def update(option_selected):
    print(option_selected)
    print(type(option_selected))
    CPIHot = 0
    CPICold = 0
    container = "The number of Hot Signals for is {} and Cold Signals is {}.".format(CPIHot, CPICold)

    # Plotly
    if option_selected == 'MoM':
        ## Month Over Month Rolling Averagse
        CombinedMoM = pd.DataFrame()
        for x in [3, 6, 9, 12]:
            CombinedMoM[f'{x} Month Avg'] = MoMCPI.rolling(window=x).mean()
        print(CombinedMoM)

        ## MoM Graph
        Signal = px.line(CombinedMoM, x=CombinedMoM.index, y=CombinedMoM.columns, title='MoM CPI Rolling Averages')
        Signal.add_hrect(y0=0.166666,
                             y1=0.2083333,
                             line_width=0,
                             fillcolor='red',
                             opacity=0.2) # Monthly Target Inflation Rate based on Fed 2% Annual Target
        
        Signal.update_layout(title= 'MoM CPI Signals',
                         xaxis_title='Date',
                         yaxis_title='CPI Average (%)',
                         legend_title='Averages',
                         template='plotly_dark')
        ## Signal lines
        CPIHot = 0
        CPICold = 0
        for i in range(CombinedMoM.shape[0]):
            check1 = [CombinedMoM[f'{x}'].iloc[i] for x in CombinedMoM.columns[1:4]]
            if np.all([CombinedMoM[f'{x} Month Avg'].iloc[i] >= value for x in [3, 6] for value in check1]) and CombinedMoM['9 Month Avg'].iloc[i] >= CombinedMoM['12 Month Avg'].iloc[i]:
                Signal.add_vline(x=CombinedMoM.index[i], line_width=1.5,line_color='red')
                CPIHot += 1
            if np.all([CombinedMoM[f'{x} Month Avg'].iloc[i] <= value for x in [3, 6] for value in check1]) and CombinedMoM['9 Month Avg'].iloc[i] <= CombinedMoM['12 Month Avg'].iloc[i]:
                Signal.add_vline(x=CombinedMoM.index[i], line_width=1.5,line_color='blue') 
                CPICold += 1

    if option_selected == 'YoY':
         ## Year Over Year Rolling Averages
        CombinedYoY = pd.DataFrame()
        for x in [3, 6, 9, 12]:
            CombinedYoY[f'{x} Month Avg'] = YoYCPI.rolling(window=x).mean()
        print(CombinedYoY)
        ## YoY Graph
        Signal = px.line(CombinedYoY, x=CombinedYoY.index, y=CombinedYoY.columns, title='YoY CPI Rolling Averages')
        Signal.add_hrect(y0=1.5,
                             y1=2.5,line_width=0,
                             fillcolor='red',
                             opacity=0.2) # 2% (+- 0.5%) Fed Long-term Inflation Target
        
        Signal.update_layout(title= 'YoY CPI Signals',
                         xaxis_title='Date',
                         yaxis_title='CPI Average (%)',
                         legend_title='Averages',
                         template='plotly_dark')
        
        ## Signal lines
        for i in range(CombinedYoY.shape[0]):
            check1 = [CombinedYoY[f'{x}'].iloc[i] for x in CombinedYoY.columns[1:4]]
            if np.all([CombinedYoY[f'{x} Month Avg'].iloc[i] >= value for x in [3, 6] for value in check1]) and CombinedYoY['9 Month Avg'].iloc[i] <= CombinedYoY['12 Month Avg'].iloc[i]:
                Signal.add_vline(x=CombinedYoY.index[i], line_width=1.5,line_color='red')
                CPIHot += 1
            if np.all([CombinedYoY[f'{x} Month Avg'].iloc[i] <= value for x in [3, 6] for value in check1]) and CombinedYoY['9 Month Avg'].iloc[i] >= CombinedYoY['12 Month Avg'].iloc[i]:
                Signal.add_vline(x=CombinedYoY.index[i], line_width=1.5,line_color='blue') 
                CPICold += 1

    container = "The number of Hot Signals is {} and Cold Signals is {}.".format(CPIHot, CPICold)
    return container, Signal

#---------
if __name__ == '__main__':
    app.run_server(debug=True)
