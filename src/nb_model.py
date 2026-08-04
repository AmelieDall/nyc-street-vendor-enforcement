"""
Functions related to the variable selection and running of negative binomial regression models
"""

import statsmodels.api as sm
import numpy as np
import pandas as pd

def backward_selection_nb(df, y_col, candidate_vars, offset_col='total_pop',
                            p_threshold=0.05, standardize=True, verbose=True):
    """
    Backward feature selection for a Negative Binomial model using AIC.
    At each round, drops the single predictor whose removal produces the lowest AIC,
    provided that AIC improves (decreases). Stops when no removal improves AIC
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
    current_aic = current_model.aic

    while True:
        round_num += 1

        rounds.append({
            'round': round_num,
            'n_vars': len(vars_in_model),
            'vars': vars_in_model.copy(),
            'aic': current_aic,
            'log_likelihood': current_model.llf,
            'dropped_var': None,
            'dropped_aic': None
        })

        if verbose:
            print(f"Round {round_num}: {len(vars_in_model)} vars | "
                  f"AIC = {current_aic:.4f}")

        if len(vars_in_model) == 1:
            break

        # Try dropping each variable and record the resulting AIC
        candidate_drops = {}
        for var in vars_in_model:
            reduced_vars = [v for v in vars_in_model if v != var]
            X_reduced = sm.add_constant(df[reduced_vars])
            reduced_model = sm.NegativeBinomial(y, X_reduced, offset=offset).fit(
                maxiter=200, disp=False
            )
            candidate_drops[var] = (reduced_model.aic, reduced_model)

        # Variable whose removal yields the lowest AIC
        best_drop_var = min(candidate_drops, key=lambda v: candidate_drops[v][0])
        best_drop_aic, best_drop_model = candidate_drops[best_drop_var]

        if verbose:
            print(f"  Best drop: '{best_drop_var}' → AIC = {best_drop_aic:.4f} "
                  f"({'improvement' if best_drop_aic < current_aic else 'no improvement'})")

        # Only drop if AIC actually improves
        if best_drop_aic >= current_aic:
            if verbose:
                print(f"  No removal improves AIC. Stopping.")
            break

        rounds[-1]['dropped_var'] = best_drop_var
        rounds[-1]['dropped_aic'] = best_drop_aic

        vars_in_model.remove(best_drop_var)
        current_model = best_drop_model
        current_aic = best_drop_aic

    return current_model, rounds, vars_in_model