"""
Utility Functions Module
Helper functions for the routing optimization system.

Author: Principal Data Scientist
Purpose: Reusable utilities for formatting, validation, and calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def format_currency(amount: float, currency: str = '₹') -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage string.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def format_time_hours(hours: float) -> str:
    """
    Format hours in human-readable format.
    
    Args:
        hours: Time in hours
        
    Returns:
        Formatted time string (e.g., "2h 30m")
    """
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"


def format_weight(weight_kg: float) -> str:
    """
    Format weight with appropriate unit.
    
    Args:
        weight_kg: Weight in kilograms
        
    Returns:
        Formatted weight string
    """
    if weight_kg >= 1000:
        return f"{weight_kg / 1000:.1f} tons"
    else:
        return f"{weight_kg:.0f} kg"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 0
    return ((new_value - old_value) / old_value) * 100


def calculate_savings(baseline: float, optimized: float) -> Dict[str, float]:
    """
    Calculate savings metrics.
    
    Args:
        baseline: Baseline value
        optimized: Optimized value
        
    Returns:
        Dictionary with savings metrics
    """
    absolute_savings = baseline - optimized
    percentage_savings = calculate_percentage_change(baseline, optimized) * -1  # Invert for savings
    
    return {
        'absolute_savings': round(absolute_savings, 2),
        'percentage_savings': round(percentage_savings, 2),
        'improvement': absolute_savings > 0
    }


def validate_route_input(
    origin: str,
    destination: str,
    order_weight_kg: float,
    valid_locations: List[str]
) -> Dict[str, Any]:
    """
    Validate route optimization input parameters.
    
    Args:
        origin: Origin location
        destination: Destination location
        order_weight_kg: Order weight
        valid_locations: List of valid location names
        
    Returns:
        Validation result dictionary
    """
    errors = []
    warnings = []
    
    # Check origin
    if origin not in valid_locations:
        errors.append(f"Invalid origin: {origin}. Must be one of {valid_locations}")
    
    # Check destination
    if destination not in valid_locations:
        errors.append(f"Invalid destination: {destination}. Must be one of {valid_locations}")
    
    # Check same origin-destination
    if origin == destination:
        errors.append("Origin and destination cannot be the same")
    
    # Check weight
    if order_weight_kg <= 0:
        errors.append("Order weight must be positive")
    elif order_weight_kg > 10000:
        warnings.append(f"Large order weight ({order_weight_kg} kg) may require multiple vehicles")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def create_summary_metrics(results: Dict) -> Dict[str, Any]:
    """
    Create summary metrics from optimization results.
    
    Args:
        results: Optimization results dictionary
        
    Returns:
        Summary metrics dictionary
    """
    if 'ranked_options' not in results or not results['ranked_options']:
        return {
            'status': 'No options available',
            'metrics': {}
        }
    
    metrics = {}
    
    # Extract top option from each category
    for category in ['fastest', 'cheapest', 'greenest', 'balanced']:
        if category in results['ranked_options'] and not results['ranked_options'][category].empty:
            option = results['ranked_options'][category].iloc[0]
            
            metrics[category] = {
                'time_hours': round(option.get('Total_Time_Hours', 0), 2),
                'cost_inr': round(option.get('Cost_Score', 0), 2),
                'emissions_kg': round(option.get('Emissions_Score', 0), 2),
                'vehicle': option.get('Vehicle_ID', 'N/A'),
                'distance_km': round(option.get('Distance_KM', 0), 1)
            }
    
    return {
        'status': 'Success',
        'metrics': metrics,
        'combinations_evaluated': results.get('total_combinations_evaluated', 0)
    }


def generate_baseline_comparison(
    optimized_metrics: Dict,
    baseline_avg_cost: float,
    baseline_avg_time: float,
    baseline_avg_emissions: float
) -> pd.DataFrame:
    """
    Generate baseline vs optimized comparison table.
    
    Args:
        optimized_metrics: Optimized route metrics
        baseline_avg_cost: Baseline average cost
        baseline_avg_time: Baseline average time
        baseline_avg_emissions: Baseline average emissions
        
    Returns:
        Comparison DataFrame
    """
    comparisons = []
    
    for option_name, metrics in optimized_metrics.items():
        if option_name == 'status' or option_name == 'combinations_evaluated':
            continue
            
        cost_savings = calculate_savings(baseline_avg_cost, metrics['cost_inr'])
        time_savings = calculate_savings(baseline_avg_time, metrics['time_hours'])
        emission_savings = calculate_savings(baseline_avg_emissions, metrics['emissions_kg'])
        
        comparisons.append({
            'Option': option_name.title(),
            'Cost Savings': format_percentage(cost_savings['percentage_savings']),
            'Time Savings': format_percentage(time_savings['percentage_savings']),
            'Emission Savings': format_percentage(emission_savings['percentage_savings']),
            'Vehicle': metrics['vehicle']
        })
    
    return pd.DataFrame(comparisons)


def extract_location_from_route(route_str: str) -> tuple:
    """
    Extract origin and destination from route string.
    
    Args:
        route_str: Route string (e.g., "Mumbai-Delhi")
        
    Returns:
        Tuple of (origin, destination)
    """
    parts = route_str.split('-')
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, None


def calculate_fleet_utilization(vehicles_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate fleet utilization metrics.
    
    Args:
        vehicles_df: Vehicle fleet DataFrame
        
    Returns:
        Utilization metrics
    """
    total_vehicles = len(vehicles_df)
    
    status_counts = vehicles_df['Status'].value_counts().to_dict()
    
    available = status_counts.get('Available', 0)
    in_transit = status_counts.get('In_Transit', 0)
    maintenance = status_counts.get('Maintenance', 0)
    
    utilization_rate = ((in_transit / total_vehicles) * 100) if total_vehicles > 0 else 0
    availability_rate = ((available / total_vehicles) * 100) if total_vehicles > 0 else 0
    
    return {
        'total_vehicles': total_vehicles,
        'available': available,
        'in_transit': in_transit,
        'maintenance': maintenance,
        'utilization_rate': round(utilization_rate, 1),
        'availability_rate': round(availability_rate, 1)
    }


def prioritize_routes_by_urgency(orders_df: pd.DataFrame, routes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prioritize routes based on urgency factors.
    
    Args:
        orders_df: Orders DataFrame
        routes_df: Routes DataFrame
        
    Returns:
        Prioritized routes DataFrame
    """
    # Combine orders and routes
    combined = routes_df.copy()
    
    # Calculate urgency score
    # Higher traffic delay = more urgent (plan ahead)
    # Weather impact = more urgent (needs special handling)
    combined['Urgency_Score'] = 0
    
    if 'Traffic_Delay_Minutes' in combined.columns:
        # Normalize traffic delay
        max_delay = combined['Traffic_Delay_Minutes'].max()
        if max_delay > 0:
            combined['Urgency_Score'] += (combined['Traffic_Delay_Minutes'] / max_delay) * 50
    
    if 'Weather_Impact' in combined.columns:
        weather_urgency = {
            'None': 0,
            'Light_Rain': 20,
            'Heavy_Rain': 40,
            'Fog': 30
        }
        combined['Urgency_Score'] += combined['Weather_Impact'].map(weather_urgency).fillna(0)
    
    # Sort by urgency
    combined = combined.sort_values('Urgency_Score', ascending=False)
    
    return combined


def get_location_list(data: Dict[str, pd.DataFrame]) -> List[str]:
    """
    Extract unique list of valid locations from datasets.
    
    Args:
        data: Dictionary of DataFrames
        
    Returns:
        Sorted list of unique locations
    """
    locations = set()
    
    # From warehouses
    if 'warehouse_inventory' in data:
        locations.update(data['warehouse_inventory']['Location'].unique())
    
    # From vehicles
    if 'vehicle_fleet' in data:
        locations.update(data['vehicle_fleet']['Current_Location'].unique())
    
    # From routes (origins and destinations)
    if 'routes_distance' in data:
        routes_df = data['routes_distance']
        if 'Route' in routes_df.columns:
            for route in routes_df['Route']:
                origin, dest = extract_location_from_route(route)
                if origin:
                    locations.add(origin)
                if dest:
                    locations.add(dest)
    
    return sorted(list(locations))


def log_optimization_attempt(
    origin: str,
    destination: str,
    weight: float,
    priority: str,
    result_status: str
) -> None:
    """
    Log optimization attempt for audit trail.
    
    Args:
        origin: Origin location
        destination: Destination location
        weight: Order weight
        priority: Priority level
        result_status: Result status
    """
    logger.info(
        f"OPTIMIZATION: {origin}->{destination} | "
        f"Weight: {weight}kg | Priority: {priority} | "
        f"Status: {result_status}"
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("UTILITIES MODULE - STANDALONE TEST")
    print("="*60)
    
    # Test formatting functions
    print("\n🔧 Testing Formatting Functions:")
    print(f"  Currency: {format_currency(12500.50)}")
    print(f"  Percentage: {format_percentage(15.75)}")
    print(f"  Time: {format_time_hours(2.5)}")
    print(f"  Weight: {format_weight(1500)}")
    
    # Test calculations
    print("\n📊 Testing Calculations:")
    savings = calculate_savings(1000, 850)
    print(f"  Savings: {savings}")
    
    print("\n✅ Utilities test complete!")
