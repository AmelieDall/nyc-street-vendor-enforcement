"""
Functions for building and cleaning address strings for geocoding
"""
import re
import pandas as pd

# ------- Building address strings -------

def clean_house(val):
    if pd.isna(val):
        return ''
    val = str(val).strip()
    val = re.sub(r'\.0$', '', val)
    return val


def clean_street(val):
    if pd.isna(val):
        return ''
    return str(val).strip().upper()


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


def build_nyc_address(house_val=None, street_val=None, borough_val=None,
                       city_val=None, state_val=None, zip_val=None):
    house = clean_house(house_val) if house_val is not None else ''
    street = clean_street(street_val) if street_val is not None else ''
    borough = clean_borough(borough_val)
    zip_code = clean_zip(zip_val)

    # Require at least a street name, or a borough+zip combo
    if not street and not (borough and zip_code):
        return None

    # House + street form ONE segment (space-joined internally)
    street_line = ' '.join(p for p in [house, street] if p)

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

    # Every remaining piece is its own comma-separated segment
    segments = [seg for seg in [street_line, city, state, zip_code] if seg]

    if not segments:
        return None

    return ', '.join(segments)


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
        house_val=row.get('respondent_address_house'),
        borough_val=row.get('respondent_address_borough'),
        zip_val=row.get('respondent_address_zip_code'),
    )



# ------- Cleaning Address Strings -------

#  Lookup tables
STREET_ABBREVIATIONS = {
    r'\bSTREET\b': 'ST', r'\bAVENUE\b': 'AVE', r'\bBOULEVARD\b': 'BLVD',
    r'\bROAD\b': 'RD', r'\bPLACE\b': 'PL', r'\bDRIVE\b': 'DR',
    r'\bLANE\b': 'LN', r'\bCOURT\b': 'CT', r'\bTERRACE\b': 'TER',
    r'\bPARKWAY\b': 'PKWY', r'\bHIGHWAY\b': 'HWY', r'\bEXPRESSWAY\b': 'EXPY',
}

DIRECTIONAL_ABBREVIATIONS = {
    r'\bEAST\b': 'E', r'\bWEST\b': 'W', r'\bNORTH\b': 'N', r'\bSOUTH\b': 'S',
    r'\bNORTHEAST\b': 'NE', r'\bNORTHWEST\b': 'NW',
    r'\bSOUTHEAST\b': 'SE', r'\bSOUTHWEST\b': 'SW',
}

CORNER_PREFIXES = re.compile(
    r'^(W\s+)?'
    r'(AT\s+)?'
    r'(N\.?\s*/?E\.?|N\.?\s*/?W\.?|'
    r'S\.?\s*/?E\.?|S\.?\s*/?W\.?|'
    r'NE|NW|SE|SW)?'
    r'\s*'
    r'(C\.?\s*[/P]?\s*O\.?|COR(NER)?\.?|CO)\s*'
    r'(OF\b|O\b)?'
    r'\s*',
    re.IGNORECASE
)

CORNER_WORD = re.compile(
    r'^(N\.?\s*E\.?|N\.?\s*W\.?|S\.?\s*E\.?|S\.?\s*W\.?|'
    r'NORTH|SOUTH|EAST|WEST)\s+(CORNER|COR)\.?\s*(OF\b)?\s*',
    re.IGNORECASE
)

CORNER_COMPOUND = re.compile(
    r'^[NSEW]\s+(N\.?\s*E\.?|N\.?\s*W\.?|S\.?\s*E\.?|S\.?\s*W\.?)\s+'
    r'(CORNER|COR)\.?\s*(OF\b)?\s*',
    re.IGNORECASE
)

INTERSECTION_CONNECTORS = re.compile(r'\s+AND\s+|\s*/\s*', re.IGNORECASE)

ORDINAL_SUFFIX = re.compile(r'(\d+)\s*(ST|ND|RD|TH)\b', re.IGNORECASE)

AVE_AMERICAS = re.compile(r'\bAVE(NUE)?\s+OF\s+THE\s+AMERICAS\b', re.IGNORECASE)

UNIT_SUFFIX = re.compile(
    r'\s+(\d+\s*)?(APT|UNIT|FL|FLOOR|RM|ROOM|STE|SUITE|#)\s*[\w-]*$',
    re.IGNORECASE
)

PO_BOX = re.compile(r'^\s*P\.?\s*O\.?\s*BOX\b', re.IGNORECASE)

BWAY = re.compile(r'\bBWAY\b', re.IGNORECASE)
AV_STANDALONE = re.compile(r'\bAV\b', re.IGNORECASE)

# Trailing ellipsis from pandas truncation
TRAILING_ELLIPSIS = re.compile(r',?\s*\.\.\.\s*$')

# Repeated street type: "ST ST" → "ST", "AVE AVE" → "AVE"
DOUBLED_SUFFIX = re.compile(
    r'\b(ST|AVE|BLVD|RD|PL|DR|LN|CT|TER|PKWY|HWY|EXPY)\s+\1\b',
    re.IGNORECASE
)

# Between/BETW truncation artifacts
BETWEEN_TRUNC = re.compile(r'\s+BETW\s+.*$', re.IGNORECASE)

# No house number
NO_HOUSENUMBER = re.compile(r'^\d+(-\d+)?\s')

# Other
APPROX_DESCRIPTOR = re.compile(
    r'\s+APPROX\s+[\w\s]+?(OF\s+|E\s+OF\s+|W\s+OF\s+|N\s+OF\s+|S\s+OF\s+)?',
    re.IGNORECASE
)

GATE_DESCRIPTOR = re.compile(r'^GATE\s+[A-Z]\b', re.IGNORECASE)



def clean_address(val):
    if pd.isna(val) or val is None:
        return None

    val = str(val).strip()

    if not val or val.lower() == 'none':
        return None

    # P.O. Box — ungeodable
    if PO_BOX.match(val):
        return None

    if GATE_DESCRIPTOR.match(val):
      return None

    # Strip trailing ellipsis before anything else
    val = TRAILING_ELLIPSIS.sub('', val).strip()

    # Strip compound corner prefixes (most specific first)
    val = CORNER_COMPOUND.sub('', val).strip()
    val = CORNER_WORD.sub('', val).strip()
    val = CORNER_PREFIXES.sub('', val).strip()

    # Expand BWAY → BROADWAY
    val = BWAY.sub('BROADWAY', val)

    # Strip truncated "BETW X Y" intersection suffixes
    val = BETWEEN_TRUNC.sub('', val).strip()

    val = APPROX_DESCRIPTOR.sub(' ', val).strip()

    # Normalize intersections
    val = INTERSECTION_CONNECTORS.sub(' & ', val)

    # Avenue of the Americas → 6 AVE
    val = AVE_AMERICAS.sub('6 AVE', val)

    # Abbreviate ordinals
    val = ORDINAL_SUFFIX.sub(r'\1', val)

    # Apply street type and directional abbreviations
    for pattern, replacement in {**DIRECTIONAL_ABBREVIATIONS, **STREET_ABBREVIATIONS}.items():
        val = re.sub(pattern, replacement, val, flags=re.IGNORECASE)

    # AV → AVE standalone
    val = AV_STANDALONE.sub('AVE', val)

    # Remove doubled street suffixes
    val = DOUBLED_SUFFIX.sub(r'\1', val)

    # Remove unit suffixes
    val = UNIT_SUFFIX.sub('', val).strip()

    # Remove stray punctuation except & , and -
    val = re.sub(r"['.]", '', val)

    # Collapse whitespace
    val = re.sub(r'\s+', ' ', val).strip()

    # Strip zip from landmarks (no leading house number)
    if not NO_HOUSENUMBER.match(val):
        val = re.sub(r',\s*\d{5}\s*$', '', val).strip()

    return val if val else None


