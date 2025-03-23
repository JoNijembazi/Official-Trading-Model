import requests
import pandas as pd
from datetime import datetime
def fetch_bea_data(api_key, dataset_name, table_name, frequency, year):
    """
    Fetch data from the BEA API.

    Parameters:
        api_key (str): Your BEA API key.
        dataset_name (str): Dataset to fetch (e.g., 'NIPA').
        table_name (str): Table to retrieve data from (e.g., 'T10101').
        frequency (str): Data frequency (e.g., 'A' for annual, 'Q' for quarterly).
        year (str): Year or range of years (e.g., '2020' or 'ALL').

    Returns:
        pd.DataFrame: A DataFrame with the requested data.
    """
    base_url = "https://apps.bea.gov/api/data/"
    params = {
        "UserID": api_key,
        "method": "GetData",
        "datasetname": dataset_name,
        "TableName": table_name,
        "Frequency": frequency,
        "Year": year,
        "ResultFormat": "json",
    }
    
    # Make the API request
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    
    # Parse the JSON response
    data = response.json()
    
    if "BEAAPI" in data and "Results" in data["BEAAPI"]:
        result = data["BEAAPI"]["Results"]["Data"]
        # Convert to a DataFrame
        return pd.DataFrame(result)
    else:
        raise ValueError("Unexpected API response format. Check your parameters and API key.")

# Replace with your API key
api_key = "48D44F07-81A8-4F31-BD3C-F596E84B2F6D"

# Example: Fetch GDP data
dataset_name = "NIPA"
table_name = "T10101"  # GDP data
frequency = "A"  # Annual
year = "ALL"  # All available years

try:
    df = fetch_bea_data(api_key, dataset_name, table_name, frequency, year)
    print(df.head())
    # Save to CSV
    df.to_csv("bea_data.csv", index=False)
except Exception as e:
    print(f"Error fetching data: {e}")


def fetch_bls_data(api_key, series_ids, start_year, end_year):
    """
    Fetch data from the BLS API.

    Parameters:
        api_key (str): Your BLS API key.
        series_ids (list): List of series IDs to fetch data for.
        start_year (str): Start year for data retrieval.
        end_year (str): End year for data retrieval.

    Returns:
        pd.DataFrame: A DataFrame containing the retrieved data.
    """
    base_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    # Payload for the API request
    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": api_key,
    }
    
    # Make the API request
    response = requests.post(base_url, json=payload)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    
    # Parse the JSON response
    data = response.json()
    
    if "Results" in data:
        all_data = []
        for series in data["Results"]["series"]:
            series_id = series["seriesID"]
            for item in series["data"]:
                item["seriesID"] = series_id
                all_data.append(item)
        return pd.DataFrame(all_data)
    else:
        raise ValueError("Unexpected API response format. Check your parameters and API key.")

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