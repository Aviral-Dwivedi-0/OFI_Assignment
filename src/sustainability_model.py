"""
Sustainability Model Module - STEP 6
CO₂ emission estimation and environmental impact analysis.

Author: Principal Data Scientist
Purpose: Calculate and report environmental impact (CO₂ proxy)
"""

import logging
from typing import Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


class SustainabilityModel:
    """
    Environmental sustainability assessment model.
    
    Focus: CO₂ emissions as primary proxy for environmental impact
    
    Emission Sources:
    1. Direct vehicle emissions (distance × CO₂ rate)
    2. Fuel combustion emissions
    
    Note: This is a PROXY model. Production version would include:
    - Scope 1, 2, 3 emissions
    - Warehouse energy consumption
    - Packaging materials
    - End-of-life disposal
    """
    
    # CO₂ emission factors (kg CO₂ per liter of diesel)
    CO2_PER_LITER_DIESEL = 2.68
    
    # Emission benchmarks (for comparison)
    EMISSION_BENCHMARKS = {
        'Express_Bike': {'low': 0.05, 'high': 0.12},
        'Small_Van': {'low': 0.20, 'high': 0.35},
        'Medium_Truck': {'low': 0.30, 'high': 0.45},
        'Large_Truck': {'low': 0.40, 'high': 0.65},
        'Refrigerated': {'low': 0.45, 'high': 0.60}
    }
    
    def __init__(self):
        """Initialize sustainability model."""
        pass
    
    def calculate_co2_emissions(
        self,
        distance_km: float,
        co2_rate: float
    ) -> float:
        """
        Calculate total CO₂ emissions for a route.
        
        Args:
            distance_km: Route distance
            co2_rate: Vehicle CO₂ emission rate (kg CO₂ per km)
            
        Returns:
            Total CO₂ emissions in kg
        """
        total_emissions = distance_km * co2_rate
        return round(total_emissions, 2)
    
    def calculate_emissions_from_fuel(
        self,
        fuel_consumption_liters: float
    ) -> float:
        """
        Calculate CO₂ emissions from fuel combustion.
        
        Args:
            fuel_consumption_liters: Fuel consumed in liters
            
        Returns:
            CO₂ emissions in kg
        """
        emissions = fuel_consumption_liters * self.CO2_PER_LITER_DIESEL
        return round(emissions, 2)
    
    def get_emission_breakdown(
        self,
        distance_km: float,
        co2_rate: float,
        fuel_efficiency: float
    ) -> Dict[str, float]:
        """
        Get detailed emission breakdown.
        
        Args:
            distance_km: Route distance
            co2_rate: Vehicle CO₂ rate
            fuel_efficiency: Fuel efficiency (km/liter)
            
        Returns:
            Dictionary with emission components
        """
        # Method 1: Direct vehicle emissions
        direct_emissions = self.calculate_co2_emissions(distance_km, co2_rate)
        
        # Method 2: Fuel-based emissions (cross-validation)
        fuel_consumption = distance_km / fuel_efficiency
        fuel_emissions = self.calculate_emissions_from_fuel(fuel_consumption)
        
        # Average (for robustness)
        total_emissions = (direct_emissions + fuel_emissions) / 2
        
        return {
            'direct_vehicle_emissions_kg': round(direct_emissions, 2),
            'fuel_based_emissions_kg': round(fuel_emissions, 2),
            'total_emissions_kg': round(total_emissions, 2),
            'emissions_per_km': round(total_emissions / distance_km, 4),
            'fuel_consumption_liters': round(fuel_consumption, 2)
        }
    
    def compare_emissions(
        self,
        option_a_emissions: float,
        option_b_emissions: float
    ) -> Dict:
        """
        Compare emissions between two options.
        
        Args:
            option_a_emissions: Emissions for option A (kg)
            option_b_emissions: Emissions for option B (kg)
            
        Returns:
            Comparison metrics
        """
        diff = option_a_emissions - option_b_emissions
        pct_diff = (diff / option_b_emissions * 100) if option_b_emissions > 0 else 0
        
        # Contextual comparison
        # Average car emits ~0.15 kg CO₂ per km
        car_equivalent_km = diff / 0.15
        
        return {
            'emission_difference_kg': round(diff, 2),
            'percentage_difference': round(pct_diff, 2),
            'greener_option': 'A' if diff > 0 else 'B',
            'car_equivalent_km': round(car_equivalent_km, 1),
            'interpretation': f"Choosing greener option saves {abs(diff):.1f} kg CO₂ (equivalent to {abs(car_equivalent_km):.0f} km of car travel)"
        }
    
    def assess_vehicle_efficiency(
        self,
        vehicle_type: str,
        co2_rate: float
    ) -> str:
        """
        Assess if vehicle emission rate is within acceptable range.
        
        Args:
            vehicle_type: Type of vehicle
            co2_rate: Vehicle CO₂ emission rate
            
        Returns:
            Assessment string ('Efficient', 'Average', 'Inefficient')
        """
        if vehicle_type not in self.EMISSION_BENCHMARKS:
            return 'Unknown'
        
        benchmark = self.EMISSION_BENCHMARKS[vehicle_type]
        
        if co2_rate <= benchmark['low']:
            return 'Efficient'
        elif co2_rate <= benchmark['high']:
            return 'Average'
        else:
            return 'Inefficient'
    
    def calculate_carbon_offset_cost(
        self,
        emissions_kg: float,
        offset_price_per_ton: float = 15.0  # USD per ton CO₂
    ) -> Dict:
        """
        Calculate cost to offset emissions via carbon credits.
        
        Args:
            emissions_kg: Total emissions in kg
            offset_price_per_ton: Price per ton CO₂ (default: $15)
            
        Returns:
            Offset cost details
        """
        emissions_tons = emissions_kg / 1000
        cost_usd = emissions_tons * offset_price_per_ton
        cost_inr = cost_usd * 83.0  # Approximate USD to INR conversion
        
        return {
            'emissions_tons': round(emissions_tons, 3),
            'offset_cost_usd': round(cost_usd, 2),
            'offset_cost_inr': round(cost_inr, 2),
            'interpretation': f"Carbon offset would cost ₹{cost_inr:.2f} ({emissions_tons:.3f} tons @ ${offset_price_per_ton}/ton)"
        }
    
    def generate_sustainability_report(
        self,
        routes_df: pd.DataFrame
    ) -> Dict:
        """
        Generate fleet-wide sustainability report.
        
        Args:
            routes_df: DataFrame with route and emission data
            
        Returns:
            Sustainability metrics
        """
        if 'Emissions_Score' not in routes_df.columns:
            logger.warning("Emissions_Score column not found")
            return {}
        
        total_emissions = routes_df['Emissions_Score'].sum()
        avg_emissions = routes_df['Emissions_Score'].mean()
        
        # Top emitters
        top_emitters = routes_df.nlargest(5, 'Emissions_Score')[
            ['Order_ID', 'Route', 'Emissions_Score']
        ].to_dict('records')
        
        # Efficiency distribution
        if 'Distance_KM' in routes_df.columns:
            routes_df['Emissions_Per_KM'] = routes_df['Emissions_Score'] / routes_df['Distance_KM']
            avg_emissions_per_km = routes_df['Emissions_Per_KM'].mean()
        else:
            avg_emissions_per_km = 0
        
        report = {
            'total_fleet_emissions_kg': round(total_emissions, 2),
            'total_fleet_emissions_tons': round(total_emissions / 1000, 2),
            'average_emissions_per_route_kg': round(avg_emissions, 2),
            'average_emissions_per_km': round(avg_emissions_per_km, 4),
            'top_5_emitters': top_emitters,
            'carbon_offset_cost': self.calculate_carbon_offset_cost(total_emissions)
        }
        
        return report
    
    def recommend_green_alternatives(
        self,
        current_emissions: float,
        current_vehicle_type: str,
        alternative_vehicles: List[Dict]
    ) -> List[Dict]:
        """
        Recommend greener vehicle alternatives.
        
        Args:
            current_emissions: Current route emissions (kg)
            current_vehicle_type: Current vehicle type
            alternative_vehicles: List of alternative vehicle options
            
        Returns:
            List of recommendations with emission savings
        """
        recommendations = []
        
        for vehicle in alternative_vehicles:
            if vehicle['co2_rate'] < current_emissions:
                savings = current_emissions - vehicle['co2_rate']
                savings_pct = (savings / current_emissions * 100)
                
                recommendations.append({
                    'vehicle_id': vehicle['vehicle_id'],
                    'vehicle_type': vehicle['vehicle_type'],
                    'emission_savings_kg': round(savings, 2),
                    'emission_savings_pct': round(savings_pct, 2),
                    'recommendation': f"Switch to {vehicle['vehicle_type']} to save {savings:.1f} kg CO₂ ({savings_pct:.1f}%)"
                })
        
        # Sort by savings
        recommendations.sort(key=lambda x: x['emission_savings_kg'], reverse=True)
        
        return recommendations


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SUSTAINABILITY MODEL - STANDALONE TEST")
    print("="*60)
    
    model = SustainabilityModel()
    
    # Test emission calculation
    breakdown = model.get_emission_breakdown(
        distance_km=500,
        co2_rate=0.45,
        fuel_efficiency=6.0
    )
    
    print("\n🌱 EMISSION BREAKDOWN (500 km route):")
    for component, value in breakdown.items():
        print(f"  {component:.<40} {value}")
    
    # Test carbon offset
    offset = model.calculate_carbon_offset_cost(breakdown['total_emissions_kg'])
    print(f"\n💚 Carbon Offset Cost:")
    print(f"  {offset['interpretation']}")
    
    # Test efficiency assessment
    assessment = model.assess_vehicle_efficiency('Large_Truck', 0.45)
    print(f"\n📊 Vehicle Efficiency: {assessment}")
    
    print("\n✅ Sustainability model test complete!")
