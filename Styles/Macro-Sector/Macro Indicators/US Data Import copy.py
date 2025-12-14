import requests
import pandas as pd
from datetime import datetime
import bls_data

data = BlsData(["CUUR0000SA0L1E","LNS14000000"],2008,2025)

# Replace with your API key
api_key = "80a61ff034c741c9863afb334ed31fbc"

# Example: Fetch data for the unemployment rate (series ID "LNS14000000")
series_ids = ["CUUR0000SA0L1E","LNS14000000"]  # CPI & Unemployment rate
start_year = str(datetime.now().year - 19)
end_year = str(datetime.now().year)
try:
    df = fetch_bls_data(api_key, series_ids, start_year, end_year)
    print(df.head())
    # Save to CSV
    df.to_csv(path_or_buf="US CPI/bls_data.csv", index=False)
except Exception as e:
    print(f"Error fetching data: {e}")