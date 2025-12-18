"""
Data Preprocessing Module - STEP 3
Clean, standardize, and engineer features for routing optimization.

Author: Principal Data Scientist
Purpose: Create derived features for time, cost, distance, and emission proxies
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Handles data cleaning, standardization, and feature engineering.
    
    Core Responsibilities:
    - Clean and standardize data
    - Engineer derived features (distance proxy, cost proxy, time proxy, emission proxy)
    - Handle missing data with explicit strategies
    - Create route-vehicle compatibility matrices
    """
    
    # Weather impact multipliers for time estimation
    WEATHER_TIME_MULTIPLIER = {
        'None': 1.0,
        'Light_Rain': 1.15,
        'Heavy_Rain': 1.35,
        'Fog': 1.25
    }
    
    # Priority time sensitivity weights
    PRIORITY_TIME_WEIGHT = {
        'Express': 1.5,      # Express orders prioritize speed
        'Standard': 1.0,     # Standard baseline
        'Economy': 0.7       # Economy tolerates longer times
    }
    
    # Vehicle status availability scoring
    STATUS_AVAILABILITY = {
        'Available': 1.0,
        'In_Transit': 0.3,   # Could be reallocated but not ideal
        'Maintenance': 0.0   # Cannot be used
    }
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        """
        Initialize preprocessor with loaded data.
        
        Args:
            data: Dictionary of DataFrames from DataLoader
        """
        self.data = data
        self.processed_data = {}
        
    def preprocess_all(self) -> Dict[str, pd.DataFrame]:
        """
        Execute full preprocessing pipeline.
        
        Returns:
            Dictionary of processed DataFrames
        """
        logger.info("\n" + "=" * 60)
        logger.info("INITIATING DATA PREPROCESSING")
        logger.info("=" * 60)
        
        # Process each dataset
        self.processed_data['routes'] = self._process_routes()
        self.processed_data['vehicles'] = self._process_vehicles()
        self.processed_data['costs'] = self._process_costs()
        self.processed_data['warehouses'] = self._process_warehouses()
        self.processed_data['orders'] = self._process_orders()
        
        # Create derived datasets
        self.processed_data['route_vehicle_matrix'] = self._create_route_vehicle_matrix()
        
        logger.info("=" * 60)
        logger.info("PREPROCESSING COMPLETE")
        logger.info("=" * 60)
        
        return self.processed_data
    
    def _process_routes(self) -> pd.DataFrame:
        """
        Process route distance data with feature engineering.
        
        Features Created:
        - Normalized distance
        - Total time estimate (distance + traffic + weather)
        - Weather risk score
        - Route efficiency score
        """
        logger.info("\n📍 Processing Routes Data...")
        
        df = self.data['routes_distance'].copy()
        
        # Parse route into origin-destination
        df[['Origin', 'Destination']] = df['Route'].str.split('-', expand=True)
        
        # Handle missing values with business logic
        df['Traffic_Delay_Minutes'] = df['Traffic_Delay_Minutes'].fillna(0)
        df['Weather_Impact'] = df['Weather_Impact'].fillna('None')
        df['Toll_Charges_INR'] = df['Toll_Charges_INR'].fillna(0)
        
        # Feature: Weather time multiplier
        df['Weather_Multiplier'] = df['Weather_Impact'].map(self.WEATHER_TIME_MULTIPLIER).fillna(1.0)
        
        # Feature: Total estimated time (hours)
        # Assume average speed 60 km/h base, adjusted for traffic and weather
        df['Base_Travel_Time_Hours'] = df['Distance_KM'] / 60.0
        df['Traffic_Delay_Hours'] = df['Traffic_Delay_Minutes'] / 60.0
        df['Total_Time_Hours'] = (
            df['Base_Travel_Time_Hours'] + df['Traffic_Delay_Hours']
        ) * df['Weather_Multiplier']
        
        # Feature: Route efficiency (distance per hour)
        df['Route_Efficiency'] = df['Distance_KM'] / df['Total_Time_Hours']
        
        # Feature: Weather risk score (binary for now)
        df['Has_Weather_Risk'] = (df['Weather_Impact'] != 'None').astype(int)
        
        # Feature: High traffic flag
        df['High_Traffic'] = (df['Traffic_Delay_Minutes'] > df['Traffic_Delay_Minutes'].median()).astype(int)
        
        # Distance normalization (for scoring)
        df['Distance_Normalized'] = (
            (df['Distance_KM'] - df['Distance_KM'].min()) / 
            (df['Distance_KM'].max() - df['Distance_KM'].min())
        )
        
        logger.info(f"✓ Processed {len(df)} routes with {len(df.columns)} features")
        
        return df
    
    def _process_vehicles(self) -> pd.DataFrame:
        """
        Process vehicle fleet data with derived features.
        
        Features Created:
        - Availability score
        - Cost efficiency score
        - Environmental efficiency score
        - Age penalty factor
        """
        logger.info("\n🚛 Processing Vehicle Fleet Data...")
        
        df = self.data['vehicle_fleet'].copy()
        
        # Feature: Availability score (based on status)
        df['Availability_Score'] = df['Status'].map(self.STATUS_AVAILABILITY)
        
        # Feature: Cost efficiency (higher is better - km per liter)
        df['Cost_Efficiency'] = df['Fuel_Efficiency_KM_per_L']
        
        # Feature: Environmental efficiency (lower CO2 is better, invert for scoring)
        max_co2 = df['CO2_Emissions_Kg_per_KM'].max()
        df['Env_Efficiency'] = max_co2 - df['CO2_Emissions_Kg_per_KM']
        
        # Feature: Age penalty (older vehicles less desirable)
        # Normalize age to 0-1 scale, then invert (1 = new, 0 = old)
        df['Age_Penalty'] = 1 - (df['Age_Years'] / df['Age_Years'].max())
        
        # Feature: Overall vehicle score (composite)
        df['Vehicle_Quality_Score'] = (
            df['Availability_Score'] * 0.4 +
            (df['Cost_Efficiency'] / df['Cost_Efficiency'].max()) * 0.3 +
            (df['Env_Efficiency'] / df['Env_Efficiency'].max()) * 0.2 +
            df['Age_Penalty'] * 0.1
        )
        
        # Feature: Capacity class (for quick filtering)
        df['Capacity_Class'] = pd.cut(
            df['Capacity_KG'],
            bins=[0, 1000, 3000, 7000, np.inf],
            labels=['Small', 'Medium', 'Large', 'XLarge']
        )
        
        logger.info(f"✓ Processed {len(df)} vehicles with {len(df.columns)} features")
        
        return df
    
    def _process_costs(self) -> pd.DataFrame:
        """
        Process cost breakdown data.
        
        Features Created:
        - Total cost
        - Cost components breakdown
        - Cost per km estimates
        """
        logger.info("\n💰 Processing Cost Data...")
        
        df = self.data['cost_breakdown'].copy()
        
        # Feature: Total operational cost
        cost_columns = [
            'Fuel_Cost', 'Labor_Cost', 'Vehicle_Maintenance',
            'Insurance', 'Packaging_Cost', 'Technology_Platform_Fee', 'Other_Overhead'
        ]
        
        df['Total_Cost'] = df[cost_columns].sum(axis=1)
        
        # Feature: Cost component percentages
        for col in cost_columns:
            df[f'{col}_Pct'] = (df[col] / df['Total_Cost'] * 100).round(2)
        
        # Merge with routes to get distance
        routes_df = self.data['routes_distance'][['Order_ID', 'Distance_KM']]
        df = df.merge(routes_df, on='Order_ID', how='left')
        
        # Feature: Cost per km
        df['Cost_Per_KM'] = (df['Total_Cost'] / df['Distance_KM']).replace([np.inf, -np.inf], np.nan)
        
        logger.info(f"✓ Processed {len(df)} cost records with {len(df.columns)} features")
        
        return df
    
    def _process_warehouses(self) -> pd.DataFrame:
        """
        Process warehouse inventory data.
        
        Features Created:
        - Stock health indicators
        - Location summaries
        """
        logger.info("\n🏭 Processing Warehouse Data...")
        
        df = self.data['warehouse_inventory'].copy()
        
        # Feature: Stock health (above/below reorder level)
        df['Stock_Health'] = np.where(
            df['Current_Stock_Units'] > df['Reorder_Level'],
            'Healthy',
            'Low'
        )
        
        # Feature: Stock days (rough estimate, assuming reorder = 7 days supply)
        df['Estimated_Days_Supply'] = (
            df['Current_Stock_Units'] / df['Reorder_Level'] * 7
        ).round(1)
        
        # Create location summary
        location_summary = df.groupby('Location').agg({
            'Current_Stock_Units': 'sum',
            'Product_Category': 'count',
            'Storage_Cost_per_Unit': 'mean'
        }).reset_index()
        
        location_summary.columns = ['Location', 'Total_Stock', 'Categories', 'Avg_Storage_Cost']
        
        logger.info(f"✓ Processed {len(df)} inventory records across {len(location_summary)} warehouses")
        
        return df
    
    def _process_orders(self) -> pd.DataFrame:
        """
        Process orders data (if detailed information exists).
        
        Note: The orders.csv might be minimal. This handles that gracefully.
        """
        logger.info("\n📦 Processing Orders Data...")
        
        df = self.data['orders'].copy()
        
        # If orders only have IDs, create a minimal processed version
        if len(df.columns) == 1:
            logger.info("ℹ Orders data contains only IDs - creating minimal structure")
            
            # Enrich from routes and costs
            df = df.merge(
                self.data['routes_distance'][['Order_ID', 'Route', 'Distance_KM']],
                on='Order_ID',
                how='left'
            )
            
            df = df.merge(
                self.data['cost_breakdown'][['Order_ID', 'Fuel_Cost', 'Labor_Cost']],
                on='Order_ID',
                how='left'
            )
        
        logger.info(f"✓ Processed {len(df)} orders")
        
        return df
    
    def _create_route_vehicle_matrix(self) -> pd.DataFrame:
        """
        Create compatibility matrix for route-vehicle combinations.
        
        This is the core dataset for optimization, combining:
        - Route characteristics
        - Vehicle capabilities
        - Estimated costs
        - Time estimates
        - Environmental impact
        
        Returns:
            DataFrame with all possible route-vehicle combinations and scores
        """
        logger.info("\n🔗 Creating Route-Vehicle Compatibility Matrix...")
        
        routes = self.processed_data['routes']
        vehicles = self.processed_data['vehicles']
        
        # Cross join to get all combinations (assign method avoids in-place modification)
        matrix = routes.assign(_merge_key=1).merge(
            vehicles.assign(_merge_key=1),
            on='_merge_key',
            suffixes=('_route', '_vehicle')
        ).drop('_merge_key', axis=1)
        
        logger.info(f"✓ Created {len(matrix)} route-vehicle combinations")
        
        return matrix
    
    def get_feature_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of engineered features by dataset.
        
        Returns:
            Dictionary mapping dataset names to list of key features
        """
        summary = {}
        
        for name, df in self.processed_data.items():
            # Identify engineered features (exclude original columns)
            all_cols = df.columns.tolist()
            summary[name] = {
                'total_features': len(all_cols),
                'sample_features': all_cols[:10]  # First 10 for brevity
            }
        
        return summary


def preprocess_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to preprocess all data.
    
    Args:
        data: Dictionary of raw DataFrames
        
    Returns:
        Dictionary of processed DataFrames
    """
    preprocessor = DataPreprocessor(data)
    return preprocessor.preprocess_all()


if __name__ == "__main__":
    # Test preprocessing
    from data_loader import load_data
    
    print("\n" + "="*60)
    print("PREPROCESSING MODULE - STANDALONE TEST")
    print("="*60)
    
    data, _ = load_data()
    processed = preprocess_data(data)
    
    print("\n📊 PROCESSED DATASETS:")
    for name, df in processed.items():
        print(f"  {name}: {df.shape[0]} rows × {df.shape[1]} columns")
    
    print("\n✅ Preprocessing test complete!")
