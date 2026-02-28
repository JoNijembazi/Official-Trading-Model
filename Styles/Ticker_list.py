import io
import pandas as pd
from ftplib import FTP

def get_clean_stock_list():
    ftp = FTP('ftp.nasdaqtrader.com')
    ftp.login()
    
    def download_ftp_file(filename):
        buffer = io.BytesIO()
        ftp.retrbinary(f'RETR SymbolDirectory/{filename}', buffer.write)
        buffer.seek(0)
        # Nasdaq files use '|' as a delimiter
        return pd.read_csv(buffer, sep='|')

    # 1. Pull Nasdaq-listed and Other-listed (NYSE/AMEX) files
    nasdaq_df = download_ftp_file('nasdaqlisted.txt')
    print('nasdaqlisted.txt columns:', nasdaq_df.columns.tolist())
    other_df = download_ftp_file('otherlisted.txt')
    print('otherlisted.txt columns:', other_df.columns.tolist())
    ftp.quit()

    # 2. Clean Nasdaq-listed data
    # Filter: Not an ETF, Not a Test Issue, and is a Common Stock
    # Note: 'Financial Status' == 'N' usually indicates normal/primary
    nasdaq_clean = nasdaq_df[
        (nasdaq_df['ETF'] == 'N') & 
        (nasdaq_df['Test Issue'] == 'N')
    ].copy()
    
    # 3. Clean Other-listed (NYSE/AMEX) data
    # Filter: Not an ETF, Not a Test Issue
    other_clean = other_df[
        (other_df['ETF'] == 'N') & 
        (other_df['Test Issue'] == 'N')
    ].copy()

    # 4. Filter for Common Stocks & Primary Shares
    # We exclude tickers with dots/suffixes (e.g., BRK.B) which are usually secondary
    def is_primary_common(row, symbol_col, name_col):
        symbol = str(row[symbol_col])
        name = str(row[name_col]).upper()
        if '.' in symbol or '-' in symbol or '$' in symbol:
            return False
        if 'COMMON STOCK' in name and 'PREFERRED' not in name:
            return True
        return False

    nasdaq_final = nasdaq_clean[nasdaq_clean.apply(lambda row: is_primary_common(row, 'Symbol', 'Security Name'), axis=1)]
    other_final = other_clean[other_clean.apply(lambda row: is_primary_common(row, 'ACT Symbol', 'Security Name'), axis=1)]

    # Standardize columns for concatenation
    nasdaq_final = nasdaq_final.rename(columns={'Symbol': 'Symbol', 'Security Name': 'Security Name'})
    other_final = other_final.rename(columns={'ACT Symbol': 'Symbol', 'Security Name': 'Security Name'})

    full_list = pd.concat([nasdaq_final[['Symbol', 'Security Name']],
                           other_final[['Symbol', 'Security Name']]])
    return full_list.drop_duplicates(subset=['Symbol']).sort_values('Symbol')

# Execute
stocks_df = get_clean_stock_list()
