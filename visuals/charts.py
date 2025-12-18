"""
Visualization Module
Executive-friendly charts for the routing optimization system.

Author: Principal Data Scientist
Purpose: Create clear, interpretable visualizations for decision-makers
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List


def create_comparison_chart(
    options: Dict[str, pd.DataFrame],
    metric: str = 'Cost_Score',
    title: str = 'Route Options Comparison'
) -> go.Figure:
    """
    Create comparison chart for route options.
    
    Args:
        options: Dictionary of option DataFrames
        metric: Metric to compare
        title: Chart title
        
    Returns:
        Plotly figure
    """
    data = []
    
    for option_name, df in options.items():
        if not df.empty:
            top_option = df.iloc[0]
            data.append({
                'Option': option_name.title(),
                'Value': top_option.get(metric, 0)
            })
    
    if not data:
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    df_plot = pd.DataFrame(data)
    
    fig = px.bar(
        df_plot,
        x='Option',
        y='Value',
        title=title,
        color='Option',
        text='Value'
    )
    
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(showlegend=False, height=400)
    
    return fig


def create_multi_objective_comparison(
    options: Dict[str, pd.DataFrame]
) -> go.Figure:
    """
    Create multi-objective comparison chart.
    
    Args:
        options: Dictionary of option DataFrames
        
    Returns:
        Plotly figure with subplots
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Delivery Time', 'Total Cost', 'CO₂ Emissions'),
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )
    
    option_names = []
    times = []
    costs = []
    emissions = []
    
    for option_name, df in options.items():
        if not df.empty:
            top = df.iloc[0]
            option_names.append(option_name.title())
            times.append(top.get('Total_Time_Hours', 0))
            costs.append(top.get('Cost_Score', 0))
            emissions.append(top.get('Emissions_Score', 0))
    
    # Time chart
    fig.add_trace(
        go.Bar(x=option_names, y=times, name='Time (hours)', marker_color='lightblue'),
        row=1, col=1
    )
    
    # Cost chart
    fig.add_trace(
        go.Bar(x=option_names, y=costs, name='Cost (₹)', marker_color='lightgreen'),
        row=1, col=2
    )
    
    # Emissions chart
    fig.add_trace(
        go.Bar(x=option_names, y=emissions, name='CO₂ (kg)', marker_color='lightcoral'),
        row=1, col=3
    )
    
    fig.update_layout(height=400, showlegend=False, title_text="Multi-Objective Comparison")
    fig.update_xaxes(title_text="Option")
    fig.update_yaxes(title_text="Hours", row=1, col=1)
    fig.update_yaxes(title_text="INR", row=1, col=2)
    fig.update_yaxes(title_text="kg CO₂", row=1, col=3)
    
    return fig


def create_trade_off_scatter(
    options_df: pd.DataFrame,
    x_metric: str = 'Cost_Score',
    y_metric: str = 'Time_Score',
    color_metric: str = 'Emissions_Score'
) -> go.Figure:
    """
    Create scatter plot showing trade-offs between metrics.
    
    Args:
        options_df: DataFrame with all options
        x_metric: Metric for x-axis
        y_metric: Metric for y-axis
        color_metric: Metric for color
        
    Returns:
        Plotly figure
    """
    fig = px.scatter(
        options_df,
        x=x_metric,
        y=y_metric,
        color=color_metric,
        hover_data=['Vehicle_ID', 'Vehicle_Type'],
        title=f'Trade-off Analysis: {y_metric} vs {x_metric}',
        labels={
            x_metric: x_metric.replace('_', ' '),
            y_metric: y_metric.replace('_', ' '),
            color_metric: color_metric.replace('_', ' ')
        }
    )
    
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(height=500)
    
    return fig


def create_cost_breakdown_pie(
    cost_breakdown: Dict[str, float]
) -> go.Figure:
    """
    Create pie chart for cost breakdown.
    
    Args:
        cost_breakdown: Dictionary of cost components
        
    Returns:
        Plotly figure
    """
    # Exclude total and subtotal
    exclude_keys = ['total_cost', 'subtotal']
    
    labels = []
    values = []
    
    for key, value in cost_breakdown.items():
        if key not in exclude_keys and value > 0:
            labels.append(key.replace('_', ' ').title())
            values.append(value)
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title_text="Cost Breakdown",
        height=400
    )
    
    return fig


def create_emissions_breakdown_chart(
    emission_breakdown: Dict[str, float]
) -> go.Figure:
    """
    Create bar chart for emissions breakdown.
    
    Args:
        emission_breakdown: Dictionary of emission components
        
    Returns:
        Plotly figure
    """
    labels = []
    values = []
    
    for key, value in emission_breakdown.items():
        if 'emissions' in key.lower():
            labels.append(key.replace('_', ' ').title())
            values.append(value)
    
    fig = go.Figure(data=[
        go.Bar(x=labels, y=values, marker_color='forestgreen')
    ])
    
    fig.update_layout(
        title="Emission Components",
        xaxis_title="Component",
        yaxis_title="CO₂ (kg)",
        height=400
    )
    
    return fig


def create_baseline_vs_optimized(
    baseline_metrics: Dict,
    optimized_metrics: Dict
) -> go.Figure:
    """
    Create comparison chart: baseline vs optimized.
    
    Args:
        baseline_metrics: Baseline metrics
        optimized_metrics: Optimized metrics
        
    Returns:
        Plotly figure
    """
    categories = ['Cost (₹)', 'Time (hours)', 'CO₂ (kg)']
    
    baseline_values = [
        baseline_metrics.get('cost', 0),
        baseline_metrics.get('time', 0),
        baseline_metrics.get('emissions', 0)
    ]
    
    optimized_values = [
        optimized_metrics.get('cost', 0),
        optimized_metrics.get('time', 0),
        optimized_metrics.get('emissions', 0)
    ]
    
    fig = go.Figure(data=[
        go.Bar(name='Baseline', x=categories, y=baseline_values, marker_color='lightcoral'),
        go.Bar(name='Optimized', x=categories, y=optimized_values, marker_color='lightgreen')
    ])
    
    fig.update_layout(
        title="Baseline vs Optimized Performance",
        xaxis_title="Metric",
        yaxis_title="Value",
        barmode='group',
        height=400
    )
    
    return fig


def create_fleet_utilization_chart(
    utilization_metrics: Dict
) -> go.Figure:
    """
    Create fleet utilization donut chart.
    
    Args:
        utilization_metrics: Fleet utilization metrics
        
    Returns:
        Plotly figure
    """
    labels = ['Available', 'In Transit', 'Maintenance']
    values = [
        utilization_metrics.get('available', 0),
        utilization_metrics.get('in_transit', 0),
        utilization_metrics.get('maintenance', 0)
    ]
    
    colors = ['lightblue', 'lightgreen', 'lightcoral']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title=f"Fleet Utilization ({utilization_metrics.get('total_vehicles', 0)} vehicles)",
        height=400
    )
    
    return fig


def create_savings_gauge(
    savings_percentage: float,
    title: str = "Cost Savings"
) -> go.Figure:
    """
    Create gauge chart for savings visualization.
    
    Args:
        savings_percentage: Savings percentage (0-100)
        title: Chart title
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=savings_percentage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 15, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 30]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 10], 'color': "lightgray"},
                {'range': [10, 20], 'color': "lightgreen"},
                {'range': [20, 30], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 20
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig


def create_route_summary_table(
    options: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Create summary table for route options.
    
    Args:
        options: Dictionary of option DataFrames
        
    Returns:
        Summary DataFrame
    """
    summary_data = []
    
    for option_name, df in options.items():
        if not df.empty:
            top = df.iloc[0]
            summary_data.append({
                'Option': option_name.title(),
                'Vehicle': top.get('Vehicle_ID', 'N/A'),
                'Type': top.get('Vehicle_Type', 'N/A'),
                'Distance (km)': round(top.get('Distance_KM', 0), 1),
                'Time (hours)': round(top.get('Total_Time_Hours', 0), 2),
                'Cost (₹)': round(top.get('Cost_Score', 0), 2),
                'CO₂ (kg)': round(top.get('Emissions_Score', 0), 2),
                'Weather': top.get('Weather_Impact', 'None')
            })
    
    return pd.DataFrame(summary_data)


def create_sensitivity_chart(
    sensitivity_results: Dict
) -> go.Figure:
    """
    Create sensitivity analysis chart.
    
    Args:
        sensitivity_results: Sensitivity analysis results
        
    Returns:
        Plotly figure
    """
    scenarios = ['Low (-20%)', 'Baseline', 'High (+20%)']
    costs = [
        sensitivity_results.get('low_scenario', 0),
        sensitivity_results.get('baseline_cost', 0),
        sensitivity_results.get('high_scenario', 0)
    ]
    
    fig = go.Figure(data=[
        go.Scatter(x=scenarios, y=costs, mode='lines+markers', line=dict(width=3))
    ])
    
    fig.update_layout(
        title="Sensitivity Analysis: Fuel Price Impact",
        xaxis_title="Scenario",
        yaxis_title="Total Cost (₹)",
        height=400
    )
    
    return fig


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VISUALIZATION MODULE - STANDALONE TEST")
    print("="*60)
    
    # Test with dummy data
    dummy_options = {
        'fastest': pd.DataFrame([{
            'Vehicle_ID': 'VEH001',
            'Vehicle_Type': 'Express_Bike',
            'Distance_KM': 150,
            'Total_Time_Hours': 2.5,
            'Cost_Score': 1200,
            'Emissions_Score': 25,
            'Weather_Impact': 'None'
        }]),
        'cheapest': pd.DataFrame([{
            'Vehicle_ID': 'VEH002',
            'Vehicle_Type': 'Large_Truck',
            'Distance_KM': 150,
            'Total_Time_Hours': 3.0,
            'Cost_Score': 900,
            'Emissions_Score': 45,
            'Weather_Impact': 'None'
        }])
    }
    
    fig = create_comparison_chart(dummy_options, 'Cost_Score', 'Cost Comparison')
    print(f"✓ Created comparison chart")
    
    table = create_route_summary_table(dummy_options)
    print(f"✓ Created summary table with {len(table)} rows")
    
    print("\n✅ Visualization module test complete!")
