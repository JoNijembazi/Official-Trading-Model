import sys
import os
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import yfinance as yf
from datetime import datetime
import ftplib as FTP
import tickerlookup.Ticker_list as tl  
import concurrent.futures
import time
from dash import Dash, html, dcc, callback, Output, Input