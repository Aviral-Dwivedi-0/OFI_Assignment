"""
Routing Engine Module - STEP 4 (CORE LOGIC)
Multi-objective route optimization with explicit trade-off analysis.

Author: Principal Data Scientist
Purpose: Generate ranked route options (fastest, cheapest, greenest)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Core routing optimization engine.
    
    Philosophy:
    - Multi-objective optimization (time, cost, emissions)
    - Return RANKED OPTIONS, not single answer
    - Explicit trade-off communication
    - Rule-based for interpretability
    
    Optimization Objectives:
    1. Minimize delivery time
    2. Minimize operational cost
    3. Minimize CO₂ emissions
    """
    
    def __init__(self, processed_data: Dict[str, pd.DataFrame]):
        """
        Initialize routing engine with preprocessed data.
        
        Args:
            processed_data: Dictionary of processed DataFrames from preprocessing
        """
        self.data = processed_data
        self.routes_df = processed_data['routes']
        self.vehicles_df = processed_data['vehicles']
        self.costs_df = processed_data['costs']
        
    def optimize_route(
        self,
        origin: str,
        destination: str,
        order_weight_kg: float,
        priority: str = 'Standard',
        show_top_n: int = 3
    ) -> Dict:
        """
        Generate optimal route options for a specific order.
        
        Args:
            origin: Origin warehouse/city
            destination: Destination city
            order_weight_kg: Order weight in kilograms
            priority: Delivery priority (Express/Standard/Economy)
            show_top_n: Number of route options to return
            
        Returns:
            Dictionary containing:
            - ranked_options: Top route-vehicle combinations
            - trade_off_analysis: Comparison metrics
            - recommendations: Business-friendly interpretation
        """
        logger.info(f"\n🔍 Optimizing route: {origin} → {destination}")
        logger.info(f"   Order weight: {order_weight_kg} kg | Priority: {priority}")
        
        # Step 1: Filter feasible routes
        feasible_routes = self._filter_feasible_routes(origin, destination)
        
        if feasible_routes.empty:
            return self._handle_no_routes(origin, destination)
        
        # Step 2: Filter feasible vehicles
        feasible_vehicles = self._filter_feasible_vehicles(
            origin, order_weight_kg
        )
        
        if feasible_vehicles.empty:
            return self._handle_no_vehicles(order_weight_kg)
        
        # Step 3: Generate all route-vehicle combinations
        combinations = self._generate_combinations(
            feasible_routes, feasible_vehicles
        )
        
        # Step 4: Score combinations across objectives
        scored_combinations = self._score_combinations(
            combinations, priority, order_weight_kg
        )
        
        # Step 5: Rank by each objective
        ranked_options = self._rank_options(scored_combinations, show_top_n)
        
        # Step 6: Generate trade-off analysis
        trade_offs = self._analyze_trade_offs(ranked_options)
        
        # Step 7: Create business recommendations
        recommendations = self._generate_recommendations(
            ranked_options, trade_offs, priority
        )
        
        return {
            'ranked_options': ranked_options,
            'trade_off_analysis': trade_offs,
            'recommendations': recommendations,
            'total_combinations_evaluated': len(scored_combinations)
        }
    
    def _filter_feasible_routes(
        self,
        origin: str,
        destination: str
    ) -> pd.DataFrame:
        """
        Filter routes matching origin-destination.
        
        Args:
            origin: Origin location
            destination: Destination location
            
        Returns:
            DataFrame of matching routes
        """
        # Match routes (handle case variations)
        mask = (
            (self.routes_df['Origin'].str.lower() == origin.lower()) &
            (self.routes_df['Destination'].str.lower() == destination.lower())
        )
        
        feasible = self.routes_df[mask].copy()
        
        logger.info(f"   Found {len(feasible)} matching routes")
        
        return feasible
    
    def _filter_feasible_vehicles(
        self,
        origin: str,
        order_weight_kg: float
    ) -> pd.DataFrame:
        """
        Filter vehicles by capacity and availability.
        
        Args:
            origin: Origin location
            order_weight_kg: Required capacity
            
        Returns:
            DataFrame of feasible vehicles
        """
        # Filter criteria:
        # 1. Sufficient capacity
        # 2. Available or In_Transit (not Maintenance)
        # 3. Preferably at origin location
        
        vehicles = self.vehicles_df.copy()
        
        # Capacity filter
        vehicles = vehicles[vehicles['Capacity_KG'] >= order_weight_kg]
        
        # Status filter
        vehicles = vehicles[vehicles['Status'].isin(['Available', 'In_Transit'])]
        
        # Location scoring (prefer vehicles at origin)
        vehicles['Location_Match'] = (
            vehicles['Current_Location'].str.lower() == origin.lower()
        ).astype(int)
        
        # Sort by location match and quality score
        vehicles = vehicles.sort_values(
            ['Location_Match', 'Vehicle_Quality_Score'],
            ascending=[False, False]
        )
        
        logger.info(f"   Found {len(vehicles)} feasible vehicles")
        
        return vehicles
    
    def _generate_combinations(
        self,
        routes: pd.DataFrame,
        vehicles: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate all route-vehicle combinations.
        
        Args:
            routes: Feasible routes
            vehicles: Feasible vehicles
            
        Returns:
            DataFrame with all combinations
        """
        # Use assign for cleaner cross-join without modifying originals
        combinations = routes.assign(_key=1).merge(
            vehicles.assign(_key=1),
            on='_key',
            suffixes=('_route', '_vehicle')
        ).drop('_key', axis=1)
        
        return combinations
    
    def _score_combinations(
        self,
        combinations: pd.DataFrame,
        priority: str,
        order_weight_kg: float
    ) -> pd.DataFrame:
        """
        Score each combination across time, cost, and emissions objectives.
        
        Args:
            combinations: Route-vehicle combinations
            priority: Delivery priority
            order_weight_kg: Order weight
            
        Returns:
            DataFrame with scores
        """
        df = combinations.copy()
        
        # Import cost and sustainability models
        from cost_model import CostModel
        from sustainability_model import SustainabilityModel
        
        cost_model = CostModel()
        sustainability_model = SustainabilityModel()
        
        # Score 1: TIME SCORE (lower is better)
        priority_weight = {
            'Express': 2.0,
            'Standard': 1.0,
            'Economy': 0.5
        }.get(priority, 1.0)
        
        df['Time_Score'] = (
            df['Total_Time_Hours'] * priority_weight
        )
        
        # Score 2: COST SCORE (lower is better)
        df['Cost_Score'] = df.apply(
            lambda row: cost_model.estimate_delivery_cost(
                distance_km=row['Distance_KM'],
                vehicle_type=row['Vehicle_Type'],
                fuel_efficiency=row['Fuel_Efficiency_KM_per_L'],
                traffic_delay_min=row['Traffic_Delay_Minutes'],
                weather_impact=row['Weather_Impact'],
                order_weight_kg=order_weight_kg
            ),
            axis=1
        )
        
        # Score 3: EMISSIONS SCORE (lower is better) - Vectorized for performance
        df['Emissions_Score'] = (df['Distance_KM'] * df['CO2_Emissions_Kg_per_KM']).round(2)
        
        # Normalize scores to 0-1 range for comparison
        for score_col in ['Time_Score', 'Cost_Score', 'Emissions_Score']:
            min_val = df[score_col].min()
            max_val = df[score_col].max()
            if max_val > min_val:
                df[f'{score_col}_Normalized'] = (df[score_col] - min_val) / (max_val - min_val)
            else:
                df[f'{score_col}_Normalized'] = 0.5
        
        # Composite score (equal weighting for now)
        df['Composite_Score'] = (
            df['Time_Score_Normalized'] * 0.33 +
            df['Cost_Score_Normalized'] * 0.33 +
            df['Emissions_Score_Normalized'] * 0.34
        )
        
        return df
    
    def _rank_options(
        self,
        scored_df: pd.DataFrame,
        top_n: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Rank options by each objective.
        
        Args:
            scored_df: Scored combinations
            top_n: Number of top options per objective
            
        Returns:
            Dictionary with top options for each objective
        """
        ranked = {}
        
        # Fastest option (minimize time)
        ranked['fastest'] = scored_df.nsmallest(
            top_n, 'Time_Score'
        )[self._get_output_columns()].reset_index(drop=True)
        
        # Cheapest option (minimize cost)
        ranked['cheapest'] = scored_df.nsmallest(
            top_n, 'Cost_Score'
        )[self._get_output_columns()].reset_index(drop=True)
        
        # Greenest option (minimize emissions)
        ranked['greenest'] = scored_df.nsmallest(
            top_n, 'Emissions_Score'
        )[self._get_output_columns()].reset_index(drop=True)
        
        # Best balanced option (minimize composite)
        ranked['balanced'] = scored_df.nsmallest(
            top_n, 'Composite_Score'
        )[self._get_output_columns()].reset_index(drop=True)
        
        return ranked
    
    def _get_output_columns(self) -> List[str]:
        """Get relevant columns for output."""
        return [
            'Order_ID', 'Route', 'Origin', 'Destination',
            'Distance_KM', 'Total_Time_Hours',
            'Vehicle_ID', 'Vehicle_Type', 'Capacity_KG',
            'Fuel_Efficiency_KM_per_L', 'CO2_Emissions_Kg_per_KM',
            'Time_Score', 'Cost_Score', 'Emissions_Score',
            'Composite_Score', 'Weather_Impact', 'Traffic_Delay_Minutes'
        ]
    
    def _analyze_trade_offs(
        self,
        ranked_options: Dict[str, pd.DataFrame]
    ) -> Dict:
        """
        Analyze trade-offs between options.
        
        Args:
            ranked_options: Ranked options by objective
            
        Returns:
            Trade-off analysis metrics
        """
        analysis = {}
        
        # Get top option for each objective
        fastest = ranked_options['fastest'].iloc[0]
        cheapest = ranked_options['cheapest'].iloc[0]
        greenest = ranked_options['greenest'].iloc[0]
        
        # Compare metrics
        analysis['fastest_vs_cheapest'] = {
            'time_saved_hours': cheapest['Total_Time_Hours'] - fastest['Total_Time_Hours'],
            'cost_difference_inr': fastest['Cost_Score'] - cheapest['Cost_Score'],
            'message': f"Fastest route saves {abs(cheapest['Total_Time_Hours'] - fastest['Total_Time_Hours']):.1f} hours but costs ₹{abs(fastest['Cost_Score'] - cheapest['Cost_Score']):.0f} more"
        }
        
        analysis['cheapest_vs_greenest'] = {
            'cost_saved_inr': greenest['Cost_Score'] - cheapest['Cost_Score'],
            'co2_saved_kg': cheapest['Emissions_Score'] - greenest['Emissions_Score'],
            'message': f"Greenest route reduces CO₂ by {abs(cheapest['Emissions_Score'] - greenest['Emissions_Score']):.1f} kg but costs ₹{abs(greenest['Cost_Score'] - cheapest['Cost_Score']):.0f} more"
        }
        
        return analysis
    
    def _generate_recommendations(
        self,
        ranked_options: Dict[str, pd.DataFrame],
        trade_offs: Dict,
        priority: str
    ) -> Dict:
        """
        Generate business-friendly recommendations.
        
        Args:
            ranked_options: Ranked options
            trade_offs: Trade-off analysis
            priority: Order priority
            
        Returns:
            Recommendation dictionary
        """
        recommendations = {}
        
        # Priority-based recommendation
        if priority == 'Express':
            recommendations['primary'] = {
                'option': 'fastest',
                'rationale': 'Express priority requires fastest delivery despite higher cost'
            }
        elif priority == 'Economy':
            recommendations['primary'] = {
                'option': 'cheapest',
                'rationale': 'Economy priority prioritizes cost savings over speed'
            }
        else:
            recommendations['primary'] = {
                'option': 'balanced',
                'rationale': 'Standard priority balances time, cost, and environmental impact'
            }
        
        # Alternative consideration
        recommendations['alternative'] = {
            'option': 'greenest',
            'rationale': 'Consider greenest option for corporate sustainability goals'
        }
        
        return recommendations
    
    def _handle_no_routes(self, origin: str, destination: str) -> Dict:
        """Handle case where no routes are found."""
        logger.warning(f"⚠ No routes found for {origin} → {destination}")
        
        return {
            'error': 'NO_ROUTES_FOUND',
            'message': f'No routes available for {origin} to {destination}',
            'ranked_options': {},
            'trade_off_analysis': {},
            'recommendations': {
                'primary': {
                    'option': 'none',
                    'rationale': 'Route not in current network. Consider external logistics partner.'
                }
            }
        }
    
    def _handle_no_vehicles(self, order_weight_kg: float) -> Dict:
        """Handle case where no vehicles are available."""
        logger.warning(f"⚠ No vehicles available for {order_weight_kg} kg order")
        
        return {
            'error': 'NO_VEHICLES_AVAILABLE',
            'message': f'No vehicles with sufficient capacity ({order_weight_kg} kg) are currently available',
            'ranked_options': {},
            'trade_off_analysis': {},
            'recommendations': {
                'primary': {
                    'option': 'wait',
                    'rationale': 'Wait for vehicle availability or split shipment'
                }
            }
        }


if __name__ == "__main__":
    # Test routing engine
    from data_loader import load_data
    from preprocessing import preprocess_data
    
    print("\n" + "="*60)
    print("ROUTING ENGINE - STANDALONE TEST")
    print("="*60)
    
    data, _ = load_data()
    processed = preprocess_data(data)
    
    engine = RoutingEngine(processed)
    
    # Test optimization
    result = engine.optimize_route(
        origin='Mumbai',
        destination='Delhi',
        order_weight_kg=500,
        priority='Express',
        show_top_n=3
    )
    
    print("\n📊 OPTIMIZATION RESULT:")
    print(f"Total combinations evaluated: {result['total_combinations_evaluated']}")
    
    for option_name, option_df in result['ranked_options'].items():
        print(f"\n{option_name.upper()} Option:")
        if not option_df.empty:
            print(f"  Vehicle: {option_df.iloc[0]['Vehicle_ID']}")
            print(f"  Time: {option_df.iloc[0]['Total_Time_Hours']:.1f} hours")
            print(f"  Cost: ₹{option_df.iloc[0]['Cost_Score']:.0f}")
    
    print("\n✅ Routing engine test complete!")
