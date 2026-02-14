"""
Calculation utilities for the Model Auditor Streamlit app.
Handles profit calculations with counterfactual projection.
"""
import pandas as pd
import numpy as np


def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    """Load data and create robust decile assignment."""
    df = pd.read_csv(filepath)
    
    # Robust decile assignment using rank (Codex fix)
    # Forces exactly 10 bins even with ties
    df['decile'] = pd.qcut(
        df['uplift_score'].rank(method='first'),
        q=10, labels=False
    ) + 1
    
    return df


def calculate_decile_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate per-decile statistics."""
    stats = []
    
    for decile in range(1, 11):
        subset = df[df['decile'] == decile]
        treated = subset[subset['treatment'] == 1]
        control = subset[subset['treatment'] == 0]
        
        n_total = len(subset)
        n_treated = len(treated)
        n_control = len(control)
        
        if n_treated > 0 and n_control > 0:
            treat_rate = treated['y_true'].mean()
            ctrl_rate = control['y_true'].mean()
            uplift_rate = treat_rate - ctrl_rate
        else:
            treat_rate = ctrl_rate = uplift_rate = 0
        
        stats.append({
            'decile': decile,
            'n_customers': n_total,
            'n_treated': n_treated,
            'n_control': n_control,
            'treatment_rate': treat_rate * 100,
            'control_rate': ctrl_rate * 100,
            'observed_lift': uplift_rate * 100,
            'uplift_rate': uplift_rate  # Keep raw for calculations
        })
    
    return pd.DataFrame(stats)


def calculate_portfolio_profit(
    df: pd.DataFrame,
    selected_deciles: list,
    target_pct: float,
    email_cost: float,
    profit_per_conversion: float
) -> dict:
    """
    Calculate profit for a portfolio of selected deciles.
    
    Uses counterfactual projection: estimate uplift rate from RCT,
    then project to ALL targeted customers.
    
    Args:
        df: DataFrame with decile, treatment, y_true columns
        selected_deciles: List of deciles to include (1-10)
        target_pct: Percentage of selected pool to target (0-1)
        email_cost: Cost per email
        profit_per_conversion: Profit per conversion
    
    Returns:
        dict with profit metrics
    """
    # Filter to selected deciles
    pool = df[df['decile'].isin(selected_deciles)].copy()
    pool_size = len(pool)
    
    if pool_size == 0:
        return {
            'profit': 0,
            'revenue': 0,
            'cost': 0,
            'incremental_conversions': 0,
            'emails_sent': 0,
            'pool_size': 0
        }
    
    # Sort by uplift score within selected pool
    pool = pool.sort_values('uplift_score', ascending=False)
    
    # Target top X% of selected pool
    n_target = int(pool_size * target_pct)
    if n_target == 0:
        n_target = 1
    
    targeted = pool.head(n_target)
    
    # Calculate uplift rate from targeted subset
    treated = targeted[targeted['treatment'] == 1]
    control = targeted[targeted['treatment'] == 0]
    
    n_treated = len(treated)
    n_control = len(control)
    
    if n_treated > 0 and n_control > 0:
        treat_rate = treated['y_true'].mean()
        ctrl_rate = control['y_true'].mean()
        uplift_rate = treat_rate - ctrl_rate
        incr_conv = uplift_rate * n_target  # Project to all targeted
    else:
        incr_conv = 0
    
    cost = n_target * email_cost
    revenue = incr_conv * profit_per_conversion
    profit = revenue - cost
    
    return {
        'profit': profit,
        'revenue': revenue,
        'cost': cost,
        'incremental_conversions': incr_conv,
        'emails_sent': n_target,
        'pool_size': pool_size
    }


def calculate_spray_and_pray(
    df: pd.DataFrame,
    email_cost: float,
    profit_per_conversion: float
) -> dict:
    """
    Calculate profit for Spray & Pray (email everyone).
    This is the baseline: all deciles, 100% of population.
    """
    n_total = len(df)
    
    treated = df[df['treatment'] == 1]
    control = df[df['treatment'] == 0]
    
    treat_rate = treated['y_true'].mean()
    ctrl_rate = control['y_true'].mean()
    uplift_rate = treat_rate - ctrl_rate
    
    incr_conv = uplift_rate * n_total
    cost = n_total * email_cost
    revenue = incr_conv * profit_per_conversion
    profit = revenue - cost
    
    return {
        'profit': profit,
        'revenue': revenue,
        'cost': cost,
        'incremental_conversions': incr_conv,
        'emails_sent': n_total
    }


def calculate_profit_curve(
    df: pd.DataFrame,
    selected_deciles: list,
    email_cost: float,
    profit_per_conversion: float,
    n_points: int = 20
) -> dict:
    """
    Calculate profit at different targeting percentages for selected deciles.
    Returns data for ROI curve chart.
    """
    percentages = []
    profits = []
    
    for pct_int in range(5, 105, 5):
        pct = pct_int / 100
        result = calculate_portfolio_profit(
            df, selected_deciles, pct, email_cost, profit_per_conversion
        )
        percentages.append(pct_int)
        profits.append(result['profit'])
    
    # Find optimal
    optimal_idx = np.argmax(profits)
    
    return {
        'percentages': percentages,
        'profits': profits,
        'optimal_pct': percentages[optimal_idx],
        'optimal_profit': profits[optimal_idx]
    }


def calculate_decile_profits(
    decile_stats: pd.DataFrame,
    email_cost: float,
    profit_per_conversion: float
) -> pd.DataFrame:
    """Calculate profit for each decile individually."""
    df = decile_stats.copy()
    
    # Project uplift to all customers in decile
    df['incremental_conv'] = df['uplift_rate'] * df['n_customers']
    df['cost'] = df['n_customers'] * email_cost
    df['revenue'] = df['incremental_conv'] * profit_per_conversion
    df['profit'] = df['revenue'] - df['cost']
    
    return df
