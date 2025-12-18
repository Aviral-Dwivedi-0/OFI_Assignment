"""
Data Loading Module - STEP 2
Safe CSV loading with schema validation and missing data awareness.

Author: Principal Data Scientist
Purpose: Interview Case Study - NexGen Logistics Smart Route Planner
"""

import pandas as pd
import os
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles safe loading and validation of all logistics datasets.
    
    Responsibilities:
    - Load CSV files with error handling
    - Validate schema integrity
    - Report missing data patterns
    - Provide data quality metrics
    """
    
    # Expected schema definitions (column names we need)
    EXPECTED_SCHEMAS = {
        'orders': ['Order_ID'],
        'routes_distance': ['Order_ID', 'Route', 'Distance_KM', 'Fuel_Consumption_L', 
                           'Toll_Charges_INR', 'Traffic_Delay_Minutes', 'Weather_Impact'],
        'vehicle_fleet': ['Vehicle_ID', 'Vehicle_Type', 'Capacity_KG', 'Fuel_Efficiency_KM_per_L',
                         'Current_Location', 'Status', 'Age_Years', 'CO2_Emissions_Kg_per_KM'],
        'warehouse_inventory': ['Warehouse_ID', 'Location', 'Product_Category', 
                               'Current_Stock_Units', 'Reorder_Level'],
        'cost_breakdown': ['Order_ID', 'Fuel_Cost', 'Labor_Cost', 'Vehicle_Maintenance',
                          'Insurance', 'Packaging_Cost', 'Technology_Platform_Fee', 'Other_Overhead'],
        'customer_feedback': ['Order_ID', 'Feedback_Date', 'Rating', 'Would_Recommend']
    }
    
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = data_dir
        self.data: Dict[str, pd.DataFrame] = {}
        self.quality_report: Dict[str, Dict] = {}
        
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Load all required datasets.
        
        Returns:
            Dictionary of DataFrames keyed by dataset name
            
        Raises:
            FileNotFoundError: If critical files are missing
            ValueError: If schema validation fails
        """
        logger.info("=" * 60)
        logger.info("INITIATING DATA LOADING PROCESS")
        logger.info("=" * 60)
        
        datasets = {
            'orders': 'orders.csv',
            'routes_distance': 'routes_distance.csv',
            'vehicle_fleet': 'vehicle_fleet.csv',
            'warehouse_inventory': 'warehouse_inventory.csv',
            'cost_breakdown': 'cost_breakdown.csv',
            'customer_feedback': 'customer_feedback.csv'
        }
        
        for name, filename in datasets.items():
            try:
                self.data[name] = self._load_single_file(name, filename)
            except Exception as e:
                logger.error(f"Failed to load {filename}: {str(e)}")
                raise
                
        logger.info("=" * 60)
        logger.info("DATA LOADING COMPLETE")
        logger.info("=" * 60)
        
        return self.data
    
    def _load_single_file(self, dataset_name: str, filename: str) -> pd.DataFrame:
        """
        Load and validate a single CSV file.
        
        Args:
            dataset_name: Logical name of the dataset
            filename: CSV filename
            
        Returns:
            Loaded and validated DataFrame
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Required file not found: {filepath}")
        
        logger.info(f"\n📂 Loading: {filename}")
        
        # Load CSV
        df = pd.read_csv(filepath)
        
        # Validate schema
        self._validate_schema(df, dataset_name, filename)
        
        # Generate quality report
        self._assess_quality(df, dataset_name)
        
        logger.info(f"✅ Loaded {len(df)} records from {filename}")
        
        return df
    
    def _validate_schema(self, df: pd.DataFrame, dataset_name: str, filename: str) -> None:
        """
        Validate DataFrame has expected columns.
        
        Args:
            df: DataFrame to validate
            dataset_name: Name of dataset
            filename: Source filename
            
        Raises:
            ValueError: If critical columns are missing
        """
        if dataset_name not in self.EXPECTED_SCHEMAS:
            logger.warning(f"No schema validation defined for {dataset_name}")
            return
        
        expected_cols = self.EXPECTED_SCHEMAS[dataset_name]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(
                f"Schema validation failed for {filename}. "
                f"Missing columns: {missing_cols}"
            )
        
        logger.info(f"✓ Schema validated for {dataset_name}")
    
    def _assess_quality(self, df: pd.DataFrame, dataset_name: str) -> None:
        """
        Assess data quality and missing data patterns.
        
        Args:
            df: DataFrame to assess
            dataset_name: Name of dataset
        """
        total_rows = len(df)
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0
        
        # Columns with missing data
        cols_with_missing = df.columns[df.isnull().any()].tolist()
        
        quality_metrics = {
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'missing_cells': missing_cells,
            'missing_percentage': round(missing_pct, 2),
            'columns_with_missing': cols_with_missing,
            'duplicate_rows': df.duplicated().sum()
        }
        
        self.quality_report[dataset_name] = quality_metrics
        
        # Log quality issues
        if missing_pct > 0:
            logger.warning(f"⚠ Missing data: {missing_pct:.2f}% of cells in {dataset_name}")
            logger.warning(f"  Affected columns: {cols_with_missing}")
        
        if quality_metrics['duplicate_rows'] > 0:
            logger.warning(f"⚠ Found {quality_metrics['duplicate_rows']} duplicate rows")
    
    def get_quality_summary(self) -> pd.DataFrame:
        """
        Get comprehensive data quality summary.
        
        Returns:
            DataFrame with quality metrics for all datasets
        """
        if not self.quality_report:
            logger.warning("No quality report available. Load data first.")
            return pd.DataFrame()
        
        summary_data = []
        for dataset, metrics in self.quality_report.items():
            summary_data.append({
                'Dataset': dataset,
                'Rows': metrics['total_rows'],
                'Columns': metrics['total_columns'],
                'Missing %': metrics['missing_percentage'],
                'Duplicates': metrics['duplicate_rows'],
                'Columns w/ Missing': ', '.join(metrics['columns_with_missing']) if metrics['columns_with_missing'] else 'None'
            })
        
        return pd.DataFrame(summary_data)
    
    def validate_data_relationships(self) -> Dict[str, any]:
        """
        Validate referential integrity between datasets.
        
        Returns:
            Dictionary with validation results
        """
        if not self.data:
            raise ValueError("No data loaded. Call load_all_data() first.")
        
        logger.info("\n🔍 VALIDATING DATA RELATIONSHIPS")
        logger.info("-" * 60)
        
        validation_results = {}
        
        # Check 1: Orders in routes_distance should exist in orders (if orders has detailed data)
        if 'Order_ID' in self.data['orders'].columns:
            orders_set = set(self.data['orders']['Order_ID'].dropna())
            routes_orders_set = set(self.data['routes_distance']['Order_ID'].dropna())
            
            missing_orders = routes_orders_set - orders_set
            if missing_orders:
                logger.warning(f"⚠ {len(missing_orders)} orders in routes not found in orders table")
            else:
                logger.info("✓ All route orders exist in orders table")
            
            validation_results['orders_route_consistency'] = len(missing_orders) == 0
        
        # Check 2: Warehouse locations should match vehicle locations
        warehouse_locations = set(self.data['warehouse_inventory']['Location'].unique())
        vehicle_locations = set(self.data['vehicle_fleet']['Current_Location'].unique())
        
        unmatched_vehicle_locs = vehicle_locations - warehouse_locations
        if unmatched_vehicle_locs:
            logger.warning(f"⚠ Vehicles at non-warehouse locations: {unmatched_vehicle_locs}")
        else:
            logger.info("✓ All vehicles at valid warehouse locations")
        
        validation_results['location_consistency'] = len(unmatched_vehicle_locs) == 0
        
        # Check 3: Cost breakdown should align with routes
        routes_orders = set(self.data['routes_distance']['Order_ID'].dropna())
        cost_orders = set(self.data['cost_breakdown']['Order_ID'].dropna())
        
        orders_without_costs = routes_orders - cost_orders
        if orders_without_costs:
            logger.warning(f"⚠ {len(orders_without_costs)} orders have routes but no cost data")
            validation_results['routes_without_costs'] = list(orders_without_costs)[:5]  # Sample
        else:
            logger.info("✓ All orders with routes have cost data")
        
        validation_results['cost_coverage'] = (len(routes_orders) - len(orders_without_costs)) / len(routes_orders) * 100 if routes_orders else 0
        
        logger.info("-" * 60)
        
        return validation_results


def load_data(data_dir: str = 'data') -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Convenience function to load all data and get quality report.
    
    Args:
        data_dir: Directory containing CSV files
        
    Returns:
        Tuple of (data dictionary, quality summary DataFrame)
    """
    loader = DataLoader(data_dir)
    data = loader.load_all_data()
    loader.validate_data_relationships()
    quality_summary = loader.get_quality_summary()
    
    return data, quality_summary


if __name__ == "__main__":
    # Test the loader
    print("\n" + "="*60)
    print("DATA LOADER MODULE - STANDALONE TEST")
    print("="*60)
    
    data, quality = load_data()
    
    print("\n📊 DATA QUALITY SUMMARY:")
    print(quality.to_string(index=False))
    
    print("\n✅ Data loader test complete!")
