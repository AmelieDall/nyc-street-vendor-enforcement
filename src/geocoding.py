"""
Functions for geocoding and to build and clean address strings for geocoding
"""
import re
import pandas as pd


def clean_house(val):
    if pd.isna(val):
        return ''
    val = str(val).strip()
    val = re.sub(r'\.0$', '', val)
    return val


def clean_street(val):
    if pd.isna(val):
        return ''
    val = str(val).strip().upper()
    val = re.sub(r'\bEAST\b', 'E', val)
    val = re.sub(r'\bWEST\b', 'W', val)
    val = re.sub(r'\bNORTH\b', 'N', val)
    val = re.sub(r'\bSOUTH\b', 'S', val)
    val = re.sub(r'\bSTREET\b', 'ST', val)
    val = re.sub(r'\bAVENUE\b', 'AVE', val)
    val = re.sub(r'\bBOULEVARD\b', 'BLVD', val)
    val = re.sub(r'\bROAD\b', 'RD', val)
    val = re.sub(r'\bPLACE\b', 'PL', val)
    val = re.sub(r'\s+', ' ', val).strip()
    return val


def clean_borough(val):
    if pd.isna(val):
        return ''
    val = str(val).strip().upper()
    mapping = {
        'MANHATTAN': 'Manhattan',
        'BROOKLYN': 'Brooklyn',
        'BRONX': 'Bronx',
        'QUEENS': 'Queens',
        'STATEN ISLAND': 'Staten Island',
        'MN': 'Manhattan',
        'BK': 'Brooklyn',
        'BX': 'Bronx',
        'QN': 'Queens',
        'QS': 'Queens',
        'SI': 'Staten Island',
    }
    return mapping.get(val, val.title())


def clean_zip(val):
    if pd.isna(val):
        return ''
    val = re.sub(r'\.0$', '', str(val).strip())
    return val if re.match(r'^\d{5}$', val) else ''


def build_nyc_address(house_val, street_val, borough_val, city_val, state_val, zip_val):
    house = clean_house(house_val)
    street = clean_street(street_val)

    if not street:
        return None

    parts = [p for p in [house, street] if p]
    address = ' '.join(parts)

    # Prefer borough-derived city name, fall back to city field, then zip
    borough = clean_borough(borough_val)
    borough_to_city = {
        'Manhattan': 'New York',
        'Brooklyn': 'Brooklyn',
        'Bronx': 'Bronx',
        'Queens': 'Queens',
        'Staten Island': 'Staten Island',
    }
    city = borough_to_city.get(borough, '')
    if not city:
        city = str(city_val).strip().title() if pd.notna(city_val) else ''

    state = str(state_val).strip().upper() if pd.notna(state_val) else 'NY'
    zip_code = clean_zip(zip_val)

    location_parts = [p for p in [city, state, zip_code] if p]
    if location_parts:
        address = f"{address}, {', '.join(location_parts)}"

    return address


def build_violation_address(row):
    return build_nyc_address(
        row['violation_location_house'],
        row['violation_location_street_name'],
        row['violation_location_borough'],
        row['violation_location_city'],
        row['violation_location_state_name'],
        row['violation_location_zip_code']
    )


def build_respondent_address(row):
    return build_nyc_address(
        row['respondent_address_house'],
        row['respondent_address_street_name'],
        row['respondent_address_borough'],
        row['respondent_address_city'],
        row['respondent_address_state_name'],
        row['respondent_address_zip_code']
    )





