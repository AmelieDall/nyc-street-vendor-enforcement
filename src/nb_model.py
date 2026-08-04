"""
Functions related to the variable selection and running of negative binomial regression models
"""

import statsmodels.api as sm
import numpy as np
import pandas as pd
from IPython.display import HTML


def backward_selection_nb(df, y_col, candidate_vars, offset_col='total_pop',
                            p_threshold=0.05, standardize=True, verbose=True):
    """
    Backward feature selection for a Negative Binomial model using BIC.
    At each round, drops the single predictor whose removal produces the lowest BIC,
    provided that BIC improves (decreases). Stops when no removal improves BIC
    or only one predictor remains.

    Returns: final fitted model, list of rounds with details, final variable list
    """
    vars_in_model = list(candidate_vars)

    offset = np.log(df[offset_col])
    y = df[y_col]

    rounds = []
    round_num = 0

    # Fit the full model first
    X = sm.add_constant(df[vars_in_model])
    current_model = sm.NegativeBinomial(y, X, offset=offset).fit(maxiter=200, disp=False)
    current_bic = current_model.bic

    while True:
        round_num += 1

        rounds.append({
            'round': round_num,
            'n_vars': len(vars_in_model),
            'vars': vars_in_model.copy(),
            'bic': current_bic,
            'log_likelihood': current_model.llf,
            'dropped_var': None,
            'dropped_bic': None
        })

        if verbose:
            print(f"Round {round_num}: {len(vars_in_model)} vars | "
                  f"BIC = {current_bic:.4f}")

        if len(vars_in_model) == 1:
            break

        # Try dropping each variable and record the resulting BIC
        candidate_drops = {}
        for var in vars_in_model:
            reduced_vars = [v for v in vars_in_model if v != var]
            X_reduced = sm.add_constant(df[reduced_vars])
            reduced_model = sm.NegativeBinomial(y, X_reduced, offset=offset).fit(
                maxiter=200, disp=False
            )
            candidate_drops[var] = (reduced_model.bic, reduced_model)

        # Variable whose removal yields the lowest BIC
        best_drop_var = min(candidate_drops, key=lambda v: candidate_drops[v][0])
        best_drop_bic, best_drop_model = candidate_drops[best_drop_var]

        if verbose:
            print(f"  Best drop: '{best_drop_var}' → BIC = {best_drop_bic:.4f} "
                  f"({'improvement' if best_drop_bic < current_bic else 'no improvement'})")

        # Only drop if BIC actually improves
        if best_drop_bic >= current_bic:
            if verbose:
                print(f"  No removal improves BIC. Stopping.")
            break

        rounds[-1]['dropped_var'] = best_drop_var
        rounds[-1]['dropped_bic'] = best_drop_bic

        vars_in_model.remove(best_drop_var)
        current_model = best_drop_model
        current_bic = best_drop_bic

    return current_model, rounds, vars_in_model


VAR_COLORS = {
    'pct_comarea_z':                ('background:#E3F2F4;color:#0B4A52'),
    'pct_in_bid_z':                 ('background:#EEEDFE;color:#3C3489'),
    'NYPD_share_z':                 ('background:#E5EAF5;color:#223A66'),
    'dist_mi_z':                    ('background:#FAECE7;color:#712B13'),
    'mean_severity_ratio_z':        ('background:#FDEBDD;color:#7A3B0A'),
    'mean_collection_rate_z':       ('background:#E2F4E9;color:#1D5C34'),
    'median_household_income_z':    ('background:#FBEAF0;color:#72243E'),
    'pct_nonwhite_z':               ('background:#EAF3DE;color:#27500A'),
    'pct_foreign_born_z':           ('background:#D3D1C7;color:#2C2C2A'),
    'n_311_requests_z':             ('background:#E1F5EE;color:#085041'),
    'pro_vendor_score_overall_z':   ('background:#E6F1FB;color:#0C447C'),
}

PILL = (
    'display:inline-block;padding:2px 8px;border-radius:999px;'
    'font-family:monospace;font-size:12px;font-weight:500;'
    'margin:2px 2px;white-space:nowrap;'
)

def render_vars(var_list):
    pills = []
    for v in var_list:
        style = PILL + VAR_COLORS.get(v, 'background:#eee;color:#333')
        pills.append(f'<span style="{style}">{v}</span>')
    return ' '.join(pills)

def styled_results(df, n=10):
    rows = ['<table style="border-collapse:collapse;width:100%;font-size:13px;">']
    rows.append(
        '<thead><tr>'
        + ''.join(
            f'<th style="text-align:left;padding:6px 10px;border-bottom:1px solid #ddd;white-space:nowrap">{c}</th>'
            for c in ['rank', 'bic', 'n_vars', 'variables']
        )
        + '</tr></thead><tbody>'
    )
    for i, row in df.head(n).iterrows():
        rows.append(
            f'<tr style="border-bottom:0.5px solid #eee">'
            f'<td style="padding:6px 10px;color:#888">{i+1}</td>'
            f'<td style="padding:6px 10px;text-align:center">{row["n_vars"]}</td>'
            f'<td style="padding:6px 10px">{render_vars(row["vars"])}</td>'
            f'</tr>'
        )
    rows.append('</tbody></table>')
    return HTML(''.join(rows))
