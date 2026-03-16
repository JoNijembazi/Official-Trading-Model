from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import valet.BocValet as bv


usd_cad = bv.BoCValet().get_series('FXUSDCAD')
series = bv.BoCValet().list_series()

print(usd_cad.head())
print(series)