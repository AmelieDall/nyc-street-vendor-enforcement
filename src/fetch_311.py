"""
Functions to pull NYC Open Gov 311 Request Data
"""

import time
import requests
import pandas as pd
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import contextily as cx
import matplotlib.pyplot as plt


COMPLAINT_TYPES = "'Vendor Enforcement', 'Mobile Food Vendor', 'Violation of Park Rules'"

SELECT_FIELDS = """
    unique_key, created_date, agency, agency_name,
    complaint_type, descriptor, descriptor_2, location_type,
    incident_zip, incident_address, street_name,
    council_district, bbl, borough,
    latitude, longitude
"""


def _make_session(
    total_retries: int = 5,
    backoff_factor: float = 1.0,
    status_forcelist: tuple = (429, 500, 502, 503, 504),
) -> requests.Session:
    """
    Session with exponential backoff retry.
    Wait times roughly: 1s, 2s, 4s, 8s, 16s (backoff_factor * 2^(retry_count - 1)).
    Honors Retry-After header if Socrata sends one (common on 429s).
    """
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET"]),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_311_requests(
    resource_id: str,
    date_filter: str | None = None,
    limit: int = 50000,
    max_retries: int = 5,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Pull 311 vendor/park-enforcement complaints from a Socrata resource,
    paginating until exhausted. Retries transient errors with exponential backoff.

    Parameters
    ----------
    resource_id : str
        Socrata resource id, e.g. 'erm2-nwe9' (2020+) or '76ig-c548' (2010-2019).
    date_filter : str, optional
        Extra SoQL clause appended to $where, e.g. "created_date < '2026-01-01T00:00:00'".
    """
    base_url = f"https://data.cityofnewyork.us/resource/{resource_id}.json"

    where_clause = f"complaint_type IN({COMPLAINT_TYPES})"
    if date_filter:
        where_clause += f" AND {date_filter}"

    params = {
        "$select": SELECT_FIELDS,
        "$where": where_clause,
        "$order": "created_date DESC",
        "$limit": limit,
        "$offset": 0,
    }

    session = _make_session(total_retries=max_retries)
    all_rows = []

    while True:
        try:
            response = session.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Retries via Session are already exhausted at this point — this is a hard failure.
            print(f"[{resource_id}] Failed at offset {params['$offset']} after retries: {e}")
            raise

        batch = response.json()
        if not batch:
            break
        all_rows.extend(batch)
        print(f"[{resource_id}] Fetched {len(all_rows)} rows so far...")
        params["$offset"] += limit

    df = pd.DataFrame(all_rows)
    print(f"[{resource_id}] Done. Total rows: {len(df)}")
    return df


def fetch_and_save(
    resource_id: str,
    date_filter: str | None,
    out_path: str,
    max_retries: int = 5,
) -> pd.DataFrame:
    df = fetch_311_requests(resource_id, date_filter, max_retries=max_retries)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df




COLOR_MAP = {
    'DPR': 'tab:blue',
    'DOHMH': 'tab:orange',
    'DSNY': 'tab:green',
}

def plot_all_maps(gdf, agencies):

    fig, axes = plt.subplots(1, 3, figsize=(18, 8))

    for ax, agency in zip(axes, agencies):
        subset = gdf[gdf['agency'] == agency]
        subset = subset[subset.geometry.notna() & ~subset.geometry.is_empty]

        if not subset.empty:
            subset.plot(ax=ax, color=COLOR_MAP[agency], markersize=6, alpha=0.7)
            cx.add_basemap(ax, crs=subset.crs, source=cx.providers.CartoDB.Positron)

        ax.set_title(f'311 Requests — {agency}', fontweight='bold')
        ax.set_axis_off()

    plt.tight_layout()
    plt.show()