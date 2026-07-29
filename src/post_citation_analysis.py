"""
Functions to visualize post-citation treatment of violations
"""

import pandas as pd


PENALTY_CATEGORY_ORDER = [
    'Full Amount Imposed',
    'Three Quarters to Full Amount Imposed',
    'Half to Three Quarters Imposed',
    'A Quarter to Half Imposed',
    'Less than a Quarter Imposed',
    'No Penalty Imposed'
]

PENALTY_CATEGORY_COLORS = ['#D32F2F', '#F57C00', '#FBC02D', '#AFB42B', '#7CB342', '#388E3C']


def classify_penalty_ratio(row):
    """Classify a violation's penalty-to-total ratio into a category bucket."""
    total = row['total_violation_amount']
    penalty = row['penalty_imposed']

    if pd.isna(penalty) or pd.isna(total):
        return 'No Penalty Imposed'
    if total == 0:
        return 'No Penalty Imposed'

    ratio = penalty / total

    if ratio == 1.0:
        return 'Full Amount Imposed'
    elif ratio >= 0.75:
        return 'Three Quarters to Full Amount Imposed'
    elif ratio >= 0.5:
        return 'Half to Three Quarters Imposed'
    elif ratio >= 0.25:
        return 'A Quarter to Half Imposed'
    else:
        return 'Less than a Quarter Imposed'


def build_penalty_proportion_table(violations_df_full, boroughs=None):
    """
    Classify violations by penalty ratio and return a borough x category
    proportion table (percentages), plus a dict of n per borough.
    """
    violations_df_full['penalty_ratio_cat'] = violations_df_full.apply(classify_penalty_ratio, axis=1)

    valid_boroughs = ['MANHATTAN', 'BRONX', 'QUEENS', 'BROOKLYN', 'STATEN IS']

    if boroughs is None:
        boroughs = valid_boroughs
    else:
        boroughs = [b.upper() for b in boroughs]

    boroughs = [b for b in boroughs if b in violations_df_full['violation_location_borough'].unique()]

    prop_table = pd.DataFrame(index=boroughs, columns=PENALTY_CATEGORY_ORDER, dtype=float)
    counts_n = {}

    for borough in boroughs:
        sub = violations_df_full[violations_df_full['violation_location_borough'] == borough]
        counts = (
            sub['penalty_ratio_cat']
            .value_counts(normalize=True)
            .reindex(PENALTY_CATEGORY_ORDER)
            .fillna(0) * 100
        )
        prop_table.loc[borough] = counts
        counts_n[borough] = len(sub)

    return prop_table, counts_n, boroughs