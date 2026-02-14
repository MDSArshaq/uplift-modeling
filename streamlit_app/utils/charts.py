"""
Chart utilities for the Model Auditor Streamlit app.
Creates Plotly charts for ROI curves and decile profitability.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def build_roi_curve(
    strict_curve: dict,
    filtered_curve: dict,
    spray_and_pray_profit: float
) -> go.Figure:
    """
    Build ROI curve comparing strict ranking vs filtered portfolio.
    
    Args:
        strict_curve: dict with percentages, profits, optimal_pct, optimal_profit
        filtered_curve: dict with same structure for selected deciles
        spray_and_pray_profit: Baseline profit for reference line
    """
    fig = go.Figure()
    
    # Strict ranking line (all deciles)
    fig.add_trace(go.Scatter(
        x=strict_curve['percentages'],
        y=strict_curve['profits'],
        mode='lines',
        name='Strict Ranking (All Deciles)',
        line=dict(color='#3498db', width=2.5),
        hovertemplate='%{x}% targeted<br>Profit: $%{y:,.0f}<extra></extra>'
    ))
    
    # Filtered portfolio line
    fig.add_trace(go.Scatter(
        x=filtered_curve['percentages'],
        y=filtered_curve['profits'],
        mode='lines',
        name='Portfolio Filtered',
        line=dict(color='#27ae60', width=2.5, dash='dash'),
        hovertemplate='%{x}% targeted<br>Profit: $%{y:,.0f}<extra></extra>'
    ))
    
    # Optimal point for strict
    fig.add_trace(go.Scatter(
        x=[strict_curve['optimal_pct']],
        y=[strict_curve['optimal_profit']],
        mode='markers',
        name=f"Optimal Strict ({strict_curve['optimal_pct']}%)",
        marker=dict(color='#3498db', size=12, symbol='star'),
        hovertemplate=f"Optimal: {strict_curve['optimal_pct']}%<br>Profit: ${strict_curve['optimal_profit']:,.0f}<extra></extra>"
    ))
    
    # Optimal point for filtered
    fig.add_trace(go.Scatter(
        x=[filtered_curve['optimal_pct']],
        y=[filtered_curve['optimal_profit']],
        mode='markers',
        name=f"Optimal Filtered ({filtered_curve['optimal_pct']}%)",
        marker=dict(color='#27ae60', size=12, symbol='star'),
        hovertemplate=f"Optimal: {filtered_curve['optimal_pct']}%<br>Profit: ${filtered_curve['optimal_profit']:,.0f}<extra></extra>"
    ))
    
    # Spray & Pray reference
    fig.add_hline(
        y=spray_and_pray_profit,
        line_dash="dot",
        line_color="gray",
        annotation_text=f"Spray & Pray: ${spray_and_pray_profit:,.0f}",
        annotation_position="bottom right"
    )
    
    # Break-even line
    fig.add_hline(y=0, line_color="black", line_width=0.5)
    
    fig.update_layout(
        title=dict(
            text='ROI Curve: Strict Ranking vs Portfolio Surgery',
            font=dict(size=18)
        ),
        xaxis_title='% of Selected Pool Targeted',
        yaxis_title='Profit ($)',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(t=80, b=60),
        height=450
    )
    
    return fig


def build_decile_bars(
    decile_profits: pd.DataFrame,
    selected_deciles: list
) -> go.Figure:
    """
    Build decile profitability bar chart with color coding.
    
    Colors:
    - Green: Profitable and selected
    - Red: Decile 9 (highlighted as the "Loyalty Tax")
    - Gray: Unprofitable
    - Faded: Excluded deciles
    """
    df = decile_profits.copy()
    
    # Assign colors
    colors = []
    opacities = []
    patterns = []
    
    for _, row in df.iterrows():
        decile = row['decile']
        profit = row['profit']
        is_selected = decile in selected_deciles
        
        if not is_selected:
            colors.append('#bdc3c7')  # Light gray for excluded
            opacities.append(0.4)
            patterns.append('/')
        elif decile == 9:
            colors.append('#e74c3c')  # Red for D9
            opacities.append(0.9)
            patterns.append('')
        elif profit > 0:
            colors.append('#27ae60')  # Green for profitable
            opacities.append(0.9)
            patterns.append('')
        else:
            colors.append('#95a5a6')  # Gray for unprofitable
            opacities.append(0.9)
            patterns.append('')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['decile'],
        y=df['profit'],
        marker=dict(
            color=colors,
            opacity=opacities,
            line=dict(color='white', width=1.5),
            pattern_shape=patterns
        ),
        text=[f"${p:,.0f}" for p in df['profit']],
        textposition='outside',
        textfont=dict(size=10, color='black'),
        hovertemplate=(
            'Decile %{x}<br>'
            'Profit: $%{y:,.0f}<br>'
            'Lift: %{customdata[0]:.2f}pp<br>'
            'Customers: %{customdata[1]:,}<extra></extra>'
        ),
        customdata=df[['observed_lift', 'n_customers']].values
    ))
    
    # Break-even line
    fig.add_hline(y=0, line_color="black", line_width=1)
    
    # Annotations for D8 and D9
    d8_row = df[df['decile'] == 8].iloc[0]
    d9_row = df[df['decile'] == 9].iloc[0]
    
    if 8 in selected_deciles and d8_row['profit'] > 0:
        fig.add_annotation(
            x=8, y=d8_row['profit'],
            text="Persuadables",
            showarrow=True,
            arrowhead=2,
            arrowcolor='#27ae60',
            font=dict(color='#27ae60', size=10),
            yshift=30
        )
    
    if 9 in selected_deciles:
        fig.add_annotation(
            x=9, y=d9_row['profit'],
            text="Loyalty Tax",
            showarrow=True,
            arrowhead=2,
            arrowcolor='#e74c3c',
            font=dict(color='#e74c3c', size=10),
            yshift=-30 if d9_row['profit'] < 0 else 30
        )
    
    fig.update_layout(
        title=dict(
            text='Decile Profitability - The Loyalty Tax',
            font=dict(size=18)
        ),
        xaxis_title='Uplift Decile (1=Lowest, 10=Highest)',
        yaxis_title='Profit ($)',
        xaxis=dict(tickmode='linear', dtick=1),
        height=400,
        margin=dict(t=60, b=60)
    )
    
    return fig


def build_cumulative_chart(
    decile_profits: pd.DataFrame,
    selected_deciles: list
) -> go.Figure:
    """Build cumulative profit chart showing impact of adding each decile."""
    df = decile_profits.copy()
    
    # Filter to selected and sort by decile descending
    df = df[df['decile'].isin(selected_deciles)].sort_values('decile', ascending=False)
    df['cumulative_profit'] = df['profit'].cumsum()
    df['cumulative_pct'] = df['n_customers'].cumsum() / df['n_customers'].sum() * 100
    
    fig = go.Figure()
    
    # Line
    fig.add_trace(go.Scatter(
        x=df['cumulative_pct'],
        y=df['cumulative_profit'],
        mode='lines+markers',
        name='Cumulative Profit',
        line=dict(color='#3498db', width=2),
        marker=dict(size=10),
        hovertemplate='%{x:.0f}% targeted<br>Cumulative Profit: $%{y:,.0f}<extra></extra>'
    ))
    
    # Annotate deciles
    for _, row in df.iterrows():
        color = '#e74c3c' if row['decile'] == 9 else '#3498db'
        fig.add_annotation(
            x=row['cumulative_pct'],
            y=row['cumulative_profit'],
            text=f"D{int(row['decile'])}",
            font=dict(size=9, color=color),
            showarrow=False,
            xshift=15
        )
    
    fig.add_hline(y=0, line_color="black", line_width=0.5)
    
    fig.update_layout(
        title='Cumulative Profit (High to Low Uplift)',
        xaxis_title='% of Selected Pool',
        yaxis_title='Cumulative Profit ($)',
        height=350
    )
    
    return fig
