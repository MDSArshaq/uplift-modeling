"""
The Persuadable Hunter - Uplift Model Auditor
Streamlit app for evaluating uplift targeting strategies with human-in-the-loop decile selection.
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Import utilities
from utils.calculations import (
    load_and_prepare_data,
    calculate_decile_stats,
    calculate_portfolio_profit,
    calculate_spray_and_pray,
    calculate_profit_curve,
    calculate_decile_profits
)
from utils.charts import build_roi_curve, build_decile_bars

# Page config
st.set_page_config(
    page_title="The Persuadable Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .toggle-impact {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid #3498db;
    }
    .profit-positive { color: #27ae60; }
    .profit-negative { color: #e74c3c; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache the data."""
    # Try relative paths only (portable)
    paths = [
        Path("data/test_results_with_uplift.csv"),
        Path("../data/test_results_with_uplift.csv")
    ]
    
    for path in paths:
        if path.exists():
            return load_and_prepare_data(str(path))
    
    st.error("Data file not found! Please ensure test_results_with_uplift.csv is in the data folder.")
    st.stop()


def main():
    # Load data
    df = load_data()
    decile_stats = calculate_decile_stats(df)
    
    # ========== SIDEBAR ==========
    st.sidebar.title("🎯 Model Auditor")
    
    # Business Parameters
    st.sidebar.header("💰 Business Parameters")
    email_cost = st.sidebar.slider(
        "Email Cost ($)",
        min_value=0.01,
        max_value=1.00,
        value=0.10,
        step=0.01,
        format="$%.2f"
    )
    
    profit_per_conversion = st.sidebar.slider(
        "Profit per Conversion ($)",
        min_value=5.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
        format="$%.0f"
    )
    
    # Targeting
    st.sidebar.header("🎯 Targeting")
    target_pct = st.sidebar.slider(
        "Target % of Selected Pool",
        min_value=10,
        max_value=100,
        value=90,
        step=5,
        format="%d%%"
    ) / 100
    
    # Decile Audit
    st.sidebar.header("🔧 Decile Audit")
    
    # Initialize session state for deciles (before buttons)
    for i in range(1, 11):
        if f'decile_{i}' not in st.session_state:
            st.session_state[f'decile_{i}'] = True
    
    # Quick action buttons (one-shot actions)
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Exclude D9", type="secondary"):
        # One-shot: just set D9 to False, don't create sticky state
        st.session_state['decile_9'] = False
    if col2.button("Reset All", type="secondary"):
        for i in range(1, 11):
            st.session_state[f'decile_{i}'] = True
    
    # Decile checkboxes in two columns
    st.sidebar.write("Select deciles to include:")
    dcol1, dcol2 = st.sidebar.columns(2)
    
    selected_deciles = []
    for i in range(10, 0, -1):
        col = dcol1 if i > 5 else dcol2
        label = f"D{i}"
        if i == 9:
            label += " (!)"  # ASCII warning for portability
        
        checked = col.checkbox(
            label,
            value=st.session_state.get(f'decile_{i}', True),
            key=f'decile_{i}'
        )
        if checked:
            selected_deciles.append(i)
    
    # Pool size badge
    pool_df = df[df['decile'].isin(selected_deciles)]
    st.sidebar.metric("Selected Pool", f"{len(pool_df):,} customers")
    
    # Narrative expanders
    st.sidebar.markdown("---")
    with st.sidebar.expander("❓ What is Decile 9?"):
        st.markdown("""
        **Decile 9** contains "Sure Things" — customers with **high baseline conversion** 
        but **low incremental lift**. They buy regardless of email.
        
        The T-Learner over-indexes on them because it sees high treatment conversion, 
        not realizing these customers convert anyway.
        """)
    
    with st.sidebar.expander("🔪 Portfolio Surgery"):
        st.markdown("""
        Instead of using a strict ranking cutoff, we can **surgically exclude** 
        unprofitable segments like Decile 9.
        
        This demonstrates the value of **human-in-the-loop auditing** of ML models.
        """)
    
    with st.sidebar.expander("🛡️ Production Guardrails"):
        st.markdown("""
        In production, implement:
        - **Safety Cap**: Limit targeting of high-loyalty segments
        - **Exploration Group**: 5% holdout to monitor if excluded segments become persuadable
        """)
    
    # ========== MAIN PANEL ==========
    st.title("🎯 The Persuadable Hunter")
    st.markdown("### Uplift Model Auditor — Human-in-the-Loop Targeting")
    
    # Calculate all metrics
    all_deciles = list(range(1, 11))
    
    # Before (all deciles)
    before_result = calculate_portfolio_profit(
        df, all_deciles, target_pct, email_cost, profit_per_conversion
    )
    
    # After (selected deciles)
    after_result = calculate_portfolio_profit(
        df, selected_deciles, target_pct, email_cost, profit_per_conversion
    )
    
    # Spray & Pray baseline
    spray_result = calculate_spray_and_pray(df, email_cost, profit_per_conversion)
    
    # ========== TOGGLE IMPACT PANEL (THE "AHA!" MOMENT) ==========
    delta = after_result['profit'] - before_result['profit']
    delta_pct = (delta / abs(before_result['profit']) * 100) if before_result['profit'] != 0 else 0
    
    excluded = [d for d in all_deciles if d not in selected_deciles]
    excluded_str = ", ".join([f"D{d}" for d in sorted(excluded)]) if excluded else "None"
    
    st.markdown("---")
    
    # Toggle Impact Panel
    impact_cols = st.columns([2, 2, 2, 1])
    
    with impact_cols[0]:
        st.markdown("##### 📊 Before (All Deciles)")
        st.markdown(f"### ${before_result['profit']:,.0f}")
    
    with impact_cols[1]:
        st.markdown("##### ✂️ After (Portfolio Surgery)")
        color = "profit-positive" if after_result['profit'] >= before_result['profit'] else "profit-negative"
        st.markdown(f"### ${after_result['profit']:,.0f}")
    
    with impact_cols[2]:
        st.markdown("##### 💰 Delta")
        if delta >= 0:
            st.markdown(f"### <span style='color:#27ae60'>+${delta:,.0f}</span> ({delta_pct:+.1f}%)", unsafe_allow_html=True)
        else:
            st.markdown(f"### <span style='color:#e74c3c'>${delta:,.0f}</span> ({delta_pct:.1f}%)", unsafe_allow_html=True)
    
    with impact_cols[3]:
        st.markdown("##### Excluded")
        st.markdown(f"**{excluded_str}**")
    
    st.markdown("---")
    
    # ========== KPI CARDS ==========
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.metric(
            "🎯 Target %",
            f"{target_pct * 100:.0f}%",
            help="Percentage of selected pool to target"
        )
    
    with kpi_cols[1]:
        delta_vs_spray = after_result['profit'] - spray_result['profit']
        st.metric(
            "💰 Profit",
            f"${after_result['profit']:,.0f}",
            delta=f"${delta_vs_spray:+,.0f} vs S&P",
            help="Projected profit with current selection"
        )
    
    with kpi_cols[2]:
        st.metric(
            "📧 Emails Sent",
            f"{after_result['emails_sent']:,}",
            help="Number of customers targeted"
        )
    
    with kpi_cols[3]:
        st.metric(
            "📈 Incremental Conv.",
            f"{after_result['incremental_conversions']:.1f}",
            help="Projected incremental conversions"
        )
    
    st.markdown("---")
    
    # ========== CHARTS ==========
    chart_cols = st.columns([3, 2])
    
    with chart_cols[0]:
        # ROI Curve
        st.markdown("#### ROI Curve: Strict Ranking vs Portfolio Surgery")
        
        strict_curve = calculate_profit_curve(
            df, all_deciles, email_cost, profit_per_conversion
        )
        filtered_curve = calculate_profit_curve(
            df, selected_deciles, email_cost, profit_per_conversion
        )
        
        fig_roi = build_roi_curve(strict_curve, filtered_curve, spray_result['profit'])
        st.plotly_chart(fig_roi, width='stretch')
    
    with chart_cols[1]:
        # Decile profitability
        st.markdown("#### Decile Profitability")
        
        decile_profits = calculate_decile_profits(decile_stats, email_cost, profit_per_conversion)
        fig_bars = build_decile_bars(decile_profits, selected_deciles)
        st.plotly_chart(fig_bars, width='stretch')
    
    # ========== DECILE SUMMARY TABLE ==========
    st.markdown("---")
    st.markdown("#### Decile Summary")
    
    # Add status column
    decile_profits['status'] = decile_profits.apply(
        lambda row: "✅ Included" if row['decile'] in selected_deciles else "❌ Excluded",
        axis=1
    )
    
    # Format for display
    display_df = decile_profits[['decile', 'n_customers', 'control_rate', 'treatment_rate', 
                                  'observed_lift', 'profit', 'status']].copy()
    display_df.columns = ['Decile', 'Customers', 'Control %', 'Treatment %', 
                          'Lift (pp)', 'Profit ($)', 'Status']
    
    # Style the dataframe
    def highlight_d9(row):
        if row['Decile'] == 9:
            return ['background-color: #f8d7da'] * len(row)
        elif row['Decile'] in selected_deciles and row['Profit ($)'] > 0:
            return ['background-color: #d4edda'] * len(row)
        return [''] * len(row)
    
    styled_df = display_df.style.apply(highlight_d9, axis=1).format({
        'Control %': '{:.2f}',
        'Treatment %': '{:.2f}',
        'Lift (pp)': '{:+.2f}',
        'Profit ($)': '${:,.0f}'
    })
    
    st.dataframe(styled_df, width='stretch', hide_index=True)
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <strong>The Persuadable Hunter</strong> — Uplift Modeling Portfolio Project<br>
        Built with Streamlit | T-Learner on Hillstrom Dataset
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
