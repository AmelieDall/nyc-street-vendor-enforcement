"""
Functions to pull and visualize ACS data at the census0tract level
"""

import pandas as pd
import requests
import os
import time
import matplotlib.pyplot as plt
from dotenv import load_dotenv


# Setup
load_dotenv() 
CENSUS_API_KEY = os.environ["CENSUS_API_KEY"]


def fetch_acs_race(year, state_fips=36, api_key=CENSUS_API_KEY):
    """
    Pull tract-level race/ethnicity from B03002 (Hispanic origin × race)

    Categories returned are mutually exclusive at the race-by-ethnicity level:
      - nh_white, nh_black, nh_aian, nh_asian, nh_nhpi, nh_other,
        nh_two_or_more  (all "Not Hispanic or Latino, ___ alone/combo")
      - hispanic        (Hispanic or Latino, any race)
    """
    url = f'https://api.census.gov/data/{year}/acs/acs5'

    # B03002 — Hispanic or Latino Origin by Race
    race_vars = {
        'B03002_001E': 'total_pop',
        'B03002_003E': 'nh_white',
        'B03002_004E': 'nh_black',
        'B03002_005E': 'nh_aian',
        'B03002_006E': 'nh_asian',
        'B03002_007E': 'nh_nhpi',
        'B03002_008E': 'nh_other',
        'B03002_009E': 'nh_two_or_more',
        'B03002_012E': 'hispanic',  # Hispanic or Latino, any race
    }

    socioec_vars = {
        'B05002_013E': 'foreign_born',
        'B19013_001E': 'median_household_income'
    }

    vars_to_get = list(race_vars) + list(socioec_vars)

    params = {
        'get': ','.join(vars_to_get),
        'for': 'tract:*',
        'in': f'state:{state_fips} county:*',
        'key': api_key,
    }

    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    rows = r.json()

    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.rename(columns={**race_vars, **socioec_vars})

    # Numeric conversion
    for col in race_vars.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['year'] = year
    df['geoid'] = df['state'] + df['county'] + df['tract']

    return df[[
        'geoid', 'state', 'county', 'tract', 'year',
        'total_pop', 'nh_white', 'nh_black', 'nh_aian', 'nh_asian',
        'nh_nhpi', 'nh_other', 'nh_two_or_more',
        'hispanic', 'foreign_born', 'median_household_income'
    ]]


def compute_percentages(race_nyc):

    # Drop zero-population tracts (parks, cemeteries, airports)
    race_nyc = race_nyc[race_nyc['total_pop'] > 0].copy()

    # Compute percentages
    race_nyc['pct_white']       = race_nyc['nh_white']       / race_nyc['total_pop'] * 100
    race_nyc['pct_black']       = race_nyc['nh_black']       / race_nyc['total_pop'] * 100
    race_nyc['pct_aian']        = race_nyc['nh_aian']        / race_nyc['total_pop'] * 100
    race_nyc['pct_asian']       = race_nyc['nh_asian']       / race_nyc['total_pop'] * 100
    race_nyc['pct_nhpi']        = race_nyc['nh_nhpi']        / race_nyc['total_pop'] * 100
    race_nyc['pct_other']       = race_nyc['nh_other']       / race_nyc['total_pop'] * 100
    race_nyc['pct_two_or_more'] = race_nyc['nh_two_or_more'] / race_nyc['total_pop'] * 100
    race_nyc['pct_hispanic']    = race_nyc['hispanic']       / race_nyc['total_pop'] * 100
    race_nyc['pct_nonwhite']    = 100 - race_nyc['pct_white']
    race_nyc['pct_foreign_born'] = race_nyc['foreign_born'] / race_nyc['total_pop'] * 100

    return race_nyc



def plot_demographic_overlay(tracts_gdf, v_points_gdf, r_points_gdf, demo_col, demo_label,
                              cmap='Purples', point_color='black',
                              point_size=0.4, title_prefix=''):
    """
    Render a side-by-side figure: demographic surface alone (left),
    same surface with violation points overlaid (middle), and respondent
    points overlaid (right).

    Parameters
    ----------
    tracts_gdf : GeoDataFrame
        Tracts with demographic + count columns.
    v_points_gdf : GeoDataFrame
        Violation Points to overlay — should already be in matching CRS.
    r_points_gdf: GeoDataFrame
        Respondent Points to overlay - should already be in matching CRS.
    demo_col : str
        Column to color tracts by (e.g. 'pct_nonwhite').
    demo_label : str
        Human-readable label for colorbar and title.
    cmap : str
        Matplotlib colormap. Use sequential maps (Blues, Oranges, Purples, etc.)
        for proportions, not divergent ones.
    point_color, point_size : visual params for the dots
    title_prefix : str
        Prepended to subplot titles (e.g. '2024 ACS — ').
    """

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    #Left panel: Demographic surface
    tracts_gdf.plot(
        column=demo_col, ax=axes[0], cmap=cmap,
        edgecolor='white', linewidth=0.1,
        legend=True, legend_kwds={'label': demo_label, 'shrink': 0.6},
        missing_kwds={'color': 'lightgrey', 'label': 'No data'}
    )
    axes[0].set_title(f'{title_prefix}{demo_label} by Census Tract',
                       fontweight='bold', fontsize=13)
    axes[0].set_axis_off()

    #Middle panel: surface + violation points
    tracts_gdf.plot(
        column=demo_col, ax=axes[1], cmap=cmap,
        edgecolor='white', linewidth=0.1, alpha=0.75,
        missing_kwds={'color': 'lightgrey'}
    )
    v_points_gdf.plot(
        ax=axes[1], color=point_color,
        markersize=point_size, alpha = 0.1
    )
    axes[1].set_title(f'{title_prefix}{demo_label} + Violation Locations',
                       fontweight='bold', fontsize=10)
    axes[1].set_axis_off()

    #Right panel: surface + respondent points
    tracts_gdf.plot(
        column=demo_col, ax=axes[2], cmap=cmap,
        edgecolor='white', linewidth=0.1, alpha=0.75,
        missing_kwds={'color': 'lightgrey'}
    )
    r_points_gdf.plot(
        ax=axes[2], color=point_color,
        markersize=point_size, alpha=0.05 #Alpha is quite weak due to the density of points
    )
    axes[2].set_title(f'{title_prefix}{demo_label} + Respondent Locations',
                       fontweight='bold', fontsize=10)
    axes[2].set_axis_off()

    plt.tight_layout()
    return fig