import pandas as pd
import numpy as np
import scipy.stats as stats
import plotly.express as px
import plotly.graph_objects as go
import dash 
from dash import dcc, html
from dash.dependencies import Input, Output


funds = pd.read_excel('PIMCO_CANADART_Canadian_Core_Bond_Fund_HLD_Data.xlsx',skiprows=9)

funds.groupby('SECTOR/STATE/TYPE').sum()['(CAD)'].sort_values(ascending=False)/funds['(CAD)'].sum()