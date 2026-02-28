import requests
import pandas as pd
from datetime import datetime
import concurrent.futures


api_key = "48D44F07-81A8-4F31-BD3C-F596E84B2F6D"


def get_bea_tables(dataset='NIPA', key=api_key):
    url = "https://apps.bea.gov/api/data/"
    params = {
        'UserID': key,
        'Method': 'GetParameterValues',
        'datasetname': dataset,
        'ParameterName': 'TableName',
        'ResultFormat': 'JSON'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract the table list from the nested JSON
    print(data)
    tables = data['BEAAPI']['Results']['ParamValue']
    return pd.DataFrame(tables)


bea_tables = get_bea_tables()


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



all_NIPA = {}

def fetch_and_store(i, bea_tables, api_key):
    try:
        dataset_name = "NIPA"
        table_name = bea_tables.loc[i, 'TableName']
        frequency = "Q"
        year = "ALL"
        df = fetch_bea_data(api_key, dataset_name, table_name, frequency, year)
        return (f'{table_name}', df)
    except Exception as e:
        print(f"Error fetching data for {bea_tables.loc[i, 'TableName']}: {e}")
        return None

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(fetch_and_store, i, bea_tables, api_key) for i in bea_tables.index]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        if result:
            all_NIPA.update({result[0]: result[1]})

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

    # Validate the response structure before iterating
    if "Results" in data:
        results = data["Results"]
        # `series` can be missing if the API returned an error or empty results
        if not results or "series" not in results:
            status = data.get("status")
            message = data.get("message") or data.get("Errors") or results
            raise ValueError(f"BLS API returned no 'series' data. status={status}, message={message}")

        all_data = []
        for series_item in results["series"]:
            series_id = series_item.get("seriesID")
            for item in series_item.get("data", []):
                item["seriesID"] = series_id
                all_data.append(item)
        return pd.DataFrame(all_data)
    else:
        # Provide the raw response to make debugging easier
        raise ValueError(f"Unexpected BLS API response format: {data}")



# Replace with your API key
api_key = "14f9e85cd1d34b128fd2da56d209fc67"

MEASURE_CODE = '1100'

# Mapping of major NAICS sectors to their code ranges
# BLS provides productivity data for these major groups
sectors = {
    'Mining': ['21'],
    'Utilities': ['22'],
    'Manufacturing': ['31', '32', '33'],
    'Wholesale Trade': ['42'],
    'Retail Trade': ['44', '45'],
    'Transportation': ['48', '49'],
    'Information': ['51'],
    'Finance': ['52'],
    'Services': ['54', '56', '62', '71', '72']
}

def generate_ip_series_id(naics_code):
    """
    Constructs a BLS Series ID for Industry Productivity.
    Format: IP + U (Unadjusted) + 6-digit NAICS (padded with hyphens) + Measure Code
    """
    # BLS uses a 6-digit slot for NAICS. If shorter, it pads with hyphens.
    padded_naics = naics_code.ljust(6, '-')
    return f"IPU{padded_naics}{MEASURE_CODE}"

# Example: Generating IDs for top-level sectors
all_ids = []
for sector_name, codes in sectors.items():
    for code in codes:
        series_id = generate_ip_series_id(code)
        all_ids.append({'Sector': sector_name, 'NAICS': code, 'SeriesID': series_id})

labor_productivity_data = {}
for item in all_ids:
    start_year = str(datetime.now().year - 19)
    end_year = str(datetime.now().year)
    try:
        df = fetch_bls_data(api_key, [item['SeriesID']], start_year, end_year)
        labor_productivity_data.update({item['Sector']: df})
        # Save to CSV
    except Exception as e:
        print(f"Error fetching data: {e}")    


# CPI, Unemployment rate, Wage growth, Labor force participation rate, 
series_ids = ["CUUR0000SA0L1E", "LNS14000000", "WPSFD49116SA","LNS11300000","MPU4910012"]  
start_year = str(datetime.now().year - 19)
end_year = str(datetime.now().year)
try:
    df = fetch_bls_data(api_key, series_ids, start_year, end_year)
    print(df.head())
    # Save to CSV
    df.to_csv(path_or_buf="US CPI/bls_data.csv", index=False)
except Exception as e:
    print(f"Error fetching data: {e}")