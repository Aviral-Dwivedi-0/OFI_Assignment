"""
Cost Model Module - STEP 5
Interpretable cost estimation for route-vehicle combinations.

Author: Principal Data Scientist
Purpose: Calculate operational costs with business-readable breakdown
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CostModel:
    """
    Operational cost estimation model.
    
    Cost Components:
    1. Fuel cost (distance × fuel consumption × fuel price)
    2. Labor cost (time-based with complexity factors)
    3. Vehicle maintenance (distance-based wear)
    4. Toll charges (route-specific)
    5. Insurance allocation
    6. Packaging costs
    7. Technology platform fees
    8. Other overhead
    
    Philosophy: Rule-based, interpretable, auditable
    """
    
    # Cost parameters (INR) - Based on industry averages
    FUEL_PRICE_PER_LITER = 102.0  # Diesel price in INR
    
    LABOR_COST_PER_HOUR = {
        'Express_Bike': 150.0,
        'Small_Van': 200.0,
        'Medium_Truck': 250.0,
        'Large_Truck': 300.0,
        'Refrigerated': 350.0  # Higher due to specialized handling
    }
    
    MAINTENANCE_COST_PER_KM = {
        'Express_Bike': 2.0,
        'Small_Van': 3.5,
        'Medium_Truck': 5.0,
        'Large_Truck': 7.0,
        'Refrigerated': 8.0
    }
    
    # Base costs
    BASE_INSURANCE_PER_TRIP = 50.0
    BASE_PACKAGING_COST = 30.0
    PLATFORM_FEE_PERCENTAGE = 3.0  # 3% of subtotal
    OVERHEAD_PERCENTAGE = 5.0     # 5% of subtotal
    
    # Multipliers for complexity
    WEATHER_COST_MULTIPLIER = {
        'None': 1.0,
        'Light_Rain': 1.1,
        'Heavy_Rain': 1.25,
        'Fog': 1.15
    }
    
    WEIGHT_COST_FACTOR = 0.01  # Cost increase per kg
    
    def __init__(self):
        """Initialize cost model."""
        self.fuel_price = self.FUEL_PRICE_PER_LITER
        
    def estimate_delivery_cost(
        self,
        distance_km: float,
        vehicle_type: str,
        fuel_efficiency: float,
        traffic_delay_min: float = 0,
        weather_impact: str = 'None',
        order_weight_kg: float = 0,
        toll_charges: float = 0
    ) -> float:
        """
        Estimate total delivery cost.
        
        Args:
            distance_km: Route distance
            vehicle_type: Type of vehicle
            fuel_efficiency: Fuel efficiency (km/liter)
            traffic_delay_min: Traffic delay in minutes
            weather_impact: Weather condition
            order_weight_kg: Order weight
            toll_charges: Toll charges if known
            
        Returns:
            Estimated total cost in INR
        """
        breakdown = self.get_cost_breakdown(
            distance_km, vehicle_type, fuel_efficiency,
            traffic_delay_min, weather_impact, order_weight_kg, toll_charges
        )
        
        return breakdown['total_cost']
    
    def get_cost_breakdown(
        self,
        distance_km: float,
        vehicle_type: str,
        fuel_efficiency: float,
        traffic_delay_min: float = 0,
        weather_impact: str = 'None',
        order_weight_kg: float = 0,
        toll_charges: float = 0
    ) -> Dict[str, float]:
        """
        Get detailed cost breakdown.
        
        Args:
            distance_km: Route distance
            vehicle_type: Type of vehicle
            fuel_efficiency: Fuel efficiency (km/liter)
            traffic_delay_min: Traffic delay in minutes
            weather_impact: Weather condition
            order_weight_kg: Order weight
            toll_charges: Toll charges if known
            
        Returns:
            Dictionary with cost components
        """
        # 1. Fuel Cost
        fuel_consumption_liters = distance_km / fuel_efficiency
        fuel_cost = fuel_consumption_liters * self.fuel_price
        
        # 2. Labor Cost (time-based)
        avg_speed_kmh = 60.0  # Base average speed
        base_time_hours = distance_km / avg_speed_kmh
        traffic_delay_hours = traffic_delay_min / 60.0
        total_time_hours = base_time_hours + traffic_delay_hours
        
        hourly_rate = self.LABOR_COST_PER_HOUR.get(vehicle_type, 250.0)
        labor_cost = total_time_hours * hourly_rate
        
        # Weather adjustment
        weather_multiplier = self.WEATHER_COST_MULTIPLIER.get(weather_impact, 1.0)
        labor_cost *= weather_multiplier
        
        # 3. Vehicle Maintenance
        maintenance_rate = self.MAINTENANCE_COST_PER_KM.get(vehicle_type, 5.0)
        maintenance_cost = distance_km * maintenance_rate
        
        # 4. Toll Charges (use provided or estimate)
        if toll_charges > 0:
            toll_cost = toll_charges
        else:
            # Estimate: ~0.80 INR per km for highways
            toll_cost = distance_km * 0.80
        
        # 5. Insurance
        insurance_cost = self.BASE_INSURANCE_PER_TRIP
        
        # 6. Packaging Cost (weight-based)
        packaging_cost = self.BASE_PACKAGING_COST + (order_weight_kg * self.WEIGHT_COST_FACTOR)
        
        # Calculate subtotal
        subtotal = (
            fuel_cost + labor_cost + maintenance_cost +
            toll_cost + insurance_cost + packaging_cost
        )
        
        # 7. Platform Fee (% of subtotal)
        platform_fee = subtotal * (self.PLATFORM_FEE_PERCENTAGE / 100)
        
        # 8. Overhead (% of subtotal)
        overhead = subtotal * (self.OVERHEAD_PERCENTAGE / 100)
        
        # Total cost
        total_cost = subtotal + platform_fee + overhead
        
        return {
            'fuel_cost': round(fuel_cost, 2),
            'labor_cost': round(labor_cost, 2),
            'maintenance_cost': round(maintenance_cost, 2),
            'toll_charges': round(toll_cost, 2),
            'insurance_cost': round(insurance_cost, 2),
            'packaging_cost': round(packaging_cost, 2),
            'platform_fee': round(platform_fee, 2),
            'overhead': round(overhead, 2),
            'subtotal': round(subtotal, 2),
            'total_cost': round(total_cost, 2)
        }
    
    def compare_costs(
        self,
        option_a: Dict[str, float],
        option_b: Dict[str, float]
    ) -> Dict:
        """
        Compare two cost options.
        
        Args:
            option_a: Cost breakdown for option A
            option_b: Cost breakdown for option B
            
        Returns:
            Comparison analysis
        """
        diff = option_a['total_cost'] - option_b['total_cost']
        pct_diff = (diff / option_b['total_cost'] * 100) if option_b['total_cost'] > 0 else 0
        
        # Identify biggest cost driver difference
        component_diffs = {}
        for key in ['fuel_cost', 'labor_cost', 'maintenance_cost', 'toll_charges']:
            if key in option_a and key in option_b:
                component_diffs[key] = option_a[key] - option_b[key]
        
        biggest_driver = max(component_diffs.items(), key=lambda x: abs(x[1]))
        
        return {
            'cost_difference': round(diff, 2),
            'percentage_difference': round(pct_diff, 2),
            'cheaper_option': 'A' if diff > 0 else 'B',
            'biggest_cost_driver': biggest_driver[0],
            'driver_difference': round(biggest_driver[1], 2)
        }
    
    def sensitivity_analysis(
        self,
        distance_km: float,
        vehicle_type: str,
        fuel_efficiency: float,
        parameter: str = 'fuel_price',
        variation_pct: float = 20.0
    ) -> Dict:
        """
        Perform sensitivity analysis on cost parameters.
        
        Args:
            distance_km: Route distance
            vehicle_type: Vehicle type
            fuel_efficiency: Fuel efficiency
            parameter: Parameter to vary ('fuel_price', 'labor_cost')
            variation_pct: Percentage variation (+/-)
            
        Returns:
            Sensitivity analysis results
        """
        # Baseline cost
        baseline = self.estimate_delivery_cost(
            distance_km, vehicle_type, fuel_efficiency
        )
        
        # Vary parameter
        if parameter == 'fuel_price':
            original_price = self.fuel_price
            
            # Increase
            self.fuel_price = original_price * (1 + variation_pct / 100)
            high_cost = self.estimate_delivery_cost(
                distance_km, vehicle_type, fuel_efficiency
            )
            
            # Decrease
            self.fuel_price = original_price * (1 - variation_pct / 100)
            low_cost = self.estimate_delivery_cost(
                distance_km, vehicle_type, fuel_efficiency
            )
            
            # Reset
            self.fuel_price = original_price
        
        return {
            'baseline_cost': round(baseline, 2),
            'high_scenario': round(high_cost, 2),
            'low_scenario': round(low_cost, 2),
            'high_impact': round((high_cost - baseline) / baseline * 100, 2),
            'low_impact': round((baseline - low_cost) / baseline * 100, 2)
        }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("COST MODEL - STANDALONE TEST")
    print("="*60)
    
    model = CostModel()
    
    # Test cost estimation
    breakdown = model.get_cost_breakdown(
        distance_km=500,
        vehicle_type='Large_Truck',
        fuel_efficiency=6.0,
        traffic_delay_min=30,
        weather_impact='Light_Rain',
        order_weight_kg=2000,
        toll_charges=400
    )
    
    print("\n💰 COST BREAKDOWN (500 km, Large Truck):")
    for component, value in breakdown.items():
        print(f"  {component:.<30} ₹{value:>10,.2f}")
    
    print("\n✅ Cost model test complete!")
