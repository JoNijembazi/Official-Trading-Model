import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import yfinance as yf
from datetime import datetime

# Get the list of stocks
df = pd.read_csv('Stock_list.csv')
