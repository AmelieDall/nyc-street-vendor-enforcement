"""
Functions related to BID analysis
"""

import geopandas as gpd
import pandas as pd

def assign_in_bid(violations_gdf, bids_gdf, bid_name_col='BID_NAME', 
                   year_col='year', year_founded_col='year_founded'):
    """
    Adds an 'in_bid' column to violations_gdf: the BID_NAME if the violation
    falls within a BID's polygon AND occurred in or after that BID's founding
    year, otherwise NaN.

    Parameters
    ----------
    violations_gdf : GeoDataFrame
        Point geometries, must have a `year_col` column.
    bids_gdf : GeoDataFrame
        Polygon geometries, must have `bid_name_col` and `year_founded_col`.
    bid_name_col : str
        Column in bids_gdf holding the BID name.
    year_col : str
        Column in violations_gdf holding the violation year.
    year_founded_col : str
        Column in bids_gdf holding the year the BID was founded.

    Returns
    -------
    GeoDataFrame
        Copy of violations_gdf with a new 'in_bid' column.
    """
    # Work off copies so we don't mutate the originals
    violations = violations_gdf.copy()
    bids = bids_gdf.copy()

    # Make sure CRSs match — reproject BIDs to violations' CRS if needed
    if bids.crs != violations.crs:
        bids = bids.to_crs(violations.crs)

    # Preserve original index so we can map results back cleanly
    violations = violations.reset_index(drop=False).rename(columns={'index': '_orig_idx'})

    violations['in_bid'] = pd.NA

    # Loop year by year: only BIDs founded on/before that year are eligible
    for yr in violations[year_col].dropna().unique():
        eligible_bids = bids[bids[year_founded_col] <= yr]
        if eligible_bids.empty:
            continue

        yr_violations = violations[violations[year_col] == yr]

        joined = gpd.sjoin(
            yr_violations[['_orig_idx', 'geometry']],
            eligible_bids[[bid_name_col, 'geometry']],
            how='left',
            predicate='within'
        )

        # If a point falls in multiple overlapping BIDs, keep the first match
        joined = joined.drop_duplicates(subset='_orig_idx', keep='first')

        # Map matched BID names back onto the main violations frame
        match_map = joined.set_index('_orig_idx')[bid_name_col]
        violations.loc[violations['_orig_idx'].isin(match_map.index), 'in_bid'] = (
            violations['_orig_idx'].map(match_map)
        )

    violations = violations.drop(columns='_orig_idx').set_index(violations_gdf.index)

    # Re-wrap as GeoDataFrame in case dtype got lost along the way
    violations = gpd.GeoDataFrame(violations, geometry='geometry', crs=violations_gdf.crs)

    return violations