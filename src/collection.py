"""
Functions to pull and clean raw NYC OATH street vending violation data.
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


def normalize_agency_name(name):
    if pd.isna(name):
        return 'Unknown'

    name = str(name).upper().strip()

    # NYPD / Police
    if 'NYPD' in name or 'TRANSPORT INTELLIGENCE' in name:
        if 'TRANSPORT INTELLIGENCE' in name:
            return 'NYPD Transit'
        return 'Police'
    if 'POLICE DEPARTMENT' in name or 'POLICE DEPT' in name:
        return 'Police'

    # Parks
    if any(x in name for x in ['PARKS DEPARTMENT', 'PARKS AND RECR', 'PARKS - CAPITAL']):
        return 'Parks'

    # Health / Mental Health
    if any(x in name for x in ['DOH MENTAL HEALTH', 'DOH/MENTAL HEALTH', 'DOHMH',
                                'DEPT OF HEALTH', 'COOLING TOWERS']):
        return 'Health/Mental Health'

    # Sanitation — specific before general
    if 'SANITATION VENDOR ENFORCEMENT' in name:
        return 'Sanitation Vendor Enforcement'
    if any(x in name for x in ['SANITATION POLICE', 'SANITATION RECYCLING',
                                'SANITATION OTHERS', 'SANITATION DEPT']):
        return 'Sanitation'
    if 'DOS' in name and 'ENFORCEMENT' in name:
        return 'Sanitation'

    # Consumer Affairs
    if any(x in name for x in ['CONSUMER AFFAIRS', 'CONSUMER AFF', 'DCA -', 'TICKET SELLER']):
        return 'Consumer Affairs'

    # Transportation
    if 'TRANSPORTATION' in name or 'DEPT OF TRAN' in name:
        return 'Transportation'

    # Environmental Protection
    if any(x in name for x in ['DEP -', 'DEP.', 'BUREAU OF ENV', 'ENV PROTECT']):
        return 'Environmental Protection'

    # Buildings
    if 'BUILDINGS' in name:
        return 'Buildings'

    # Sheriff
    if 'SHERIFF' in name:
        return 'Sheriff'

    # Ports
    if 'PORTS AND TERMINALS' in name:
        return 'Ports & Terminals'

    # Technology
    if 'DOITT' in name:
        return 'Technology'

    # Missing / Invalid
    if any(x in name for x in ['AGENCY CODE MISSING', 'INVALID']):
        return 'Missing/Invalid Agency'

    # Miscellaneous
    if 'MISCELLANEOUS' in name or 'CSTDL AGY' in name:
        return 'Miscellaneous'

    return name

