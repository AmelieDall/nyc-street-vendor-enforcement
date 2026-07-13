"""
Function pulls raw NYC OATH street vending violation data.
"""
import time
import requests
import pandas as pd

BASE_URL = "https://data.cityofnewyork.us/resource/jz4z-kudi.json"

def fetch_data(year, limit=1000):
    """Pull all vending violations for a given year from NYC Open Data (OATH)."""
    offset = 0
    rows = []
    while True:
        soql_query = f"""
            SELECT *
            WHERE violation_date BETWEEN '{year}-01-01T00:00:00'::floating_timestamp
            AND '{year}-12-31T23:59:59'::floating_timestamp
            AND upper(charge_1_code_description) LIKE '%VENDING%'
            ORDER BY violation_date ASC
            LIMIT {limit} OFFSET {offset}
        """
        response = requests.get(BASE_URL, params={"$query": soql_query})
        data = response.json()
        if not data:
            break
        rows.extend(data)
        print(f"Year {year} offset {offset}: fetched {len(data)} records")
        offset += limit
        time.sleep(0.5)  # be gentle to the API
    return rows
