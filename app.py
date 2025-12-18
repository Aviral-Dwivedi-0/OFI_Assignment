"""
Smart Route Planner - Streamlit Application (STEP 8)
Decision Intelligence System for NexGen Logistics

Author: Principal Data Scientist
Purpose: Client-ready prototype for interview evaluation
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'visuals'))

from src.data_loader import load_data
from src.preprocessing import preprocess_data
from src.routing_engine import RoutingEngine
from src.cost_model import CostModel
from src.sustainability_model import SustainabilityModel
from src.utils import (
    format_currency, format_time_hours, format_weight,
    get_location_list, calculate_fleet_utilization,
    create_summary_metrics, validate_route_input
)
from visuals.charts import (
    create_multi_objective_comparison,
    create_cost_breakdown_pie,
    create_fleet_utilization_chart,
    create_route_summary_table,
    create_baseline_vs_optimized,
    create_savings_gauge
)

# Page configuration
st.set_page_config(
    page_title="Smart Route Planner | NexGen Logistics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Custom CSS with #1A6262 Theme
st.markdown("""
<style>
    /* Global Background - #1A6262 Theme */
    .stApp {
        background: linear-gradient(135deg, #0d1f1f 0%, #122d2d 50%, #1A6262 100%);
    }
    
    /* Main content area with #1A6262 accent */
    .main .block-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(26, 98, 98, 0.15);
        border: 1px solid rgba(26, 98, 98, 0.1);
    }
    
    /* Hide Sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Horizontal Navigation Bar */
    .nav-container {
        background: linear-gradient(90deg, #1A6262 0%, #145050 100%);
        padding: 0;
        margin: -4rem -4rem 2rem -4rem;
        box-shadow: 0 4px 20px rgba(26, 98, 98, 0.3);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .nav-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 3rem;
        color: white;
    }
    
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 1rem;
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    
    .nav-brand-icon {
        font-size: 2.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    .nav-subtitle {
        font-size: 0.9rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    .nav-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Modern Cards with #1A6262 Accent */
    .metric-card {
        background: linear-gradient(135deg, #d6ecec 0%, #b3d9d9 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1A6262;
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(26, 98, 98, 0.35);
    }
    
    /* Success Box */
    .success-box {
        background: linear-gradient(135deg, #d4f4dd 0%, #a8e6cf 100%);
        border: 2px solid #1A6262;
        border-radius: 12px;
        padding: 1.5rem;
        color: #155724;
        box-shadow: 0 4px 12px rgba(26, 98, 98, 0.15);
        transition: all 0.3s ease;
    }
    
    .success-box:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(26, 98, 98, 0.25);
    }
    
    /* Warning Box */
    .warning-box {
        background: linear-gradient(135deg, #fff9e6 0%, #ffe6b3 100%);
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 1.5rem;
        color: #856404;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.15);
        transition: all 0.3s ease;
    }
    
    .warning-box:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(255, 193, 7, 0.25);
    }
    
    /* Info Box */
    .info-box {
        background: linear-gradient(135deg, #d6ecec 0%, #b3d9d9 100%);
        border: 2px solid #1A6262;
        border-radius: 12px;
        padding: 1.5rem;
        color: #0c5460;
        box-shadow: 0 4px 12px rgba(26, 98, 98, 0.15);
        transition: all 0.3s ease;
    }
    
    .info-box:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(26, 98, 98, 0.25);
    }
    
    /* Button Hover Effects */
    .stButton > button {
        background: linear-gradient(135deg, #1A6262 0%, #145050 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1f7a7a 0%, #196868 100%);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(26, 98, 98, 0.5);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.4);
    }
    
    /* Form Submit Button */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #1A6262 0%, #145050 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.3);
        width: 100%;
    }
    
    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1f7a7a 0%, #196868 100%);
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(26, 98, 98, 0.5);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(26, 98, 98, 0.05);
        padding: 10px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        color: #145050;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #d6ecec 0%, #b3d9d9 100%);
        border-color: #1A6262;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26, 98, 98, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1A6262 0%, #145050 100%);
        color: white;
        border-color: #1A6262;
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.4);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1A6262;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(26, 98, 98, 0.1);
    }
    
    /* Selectbox and Input styling */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid rgba(26, 98, 98, 0.3);
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover,
    .stNumberInput > div > div > input:hover {
        border-color: #1A6262;
        box-shadow: 0 0 0 2px rgba(26, 98, 98, 0.1);
    }
    
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus {
        border-color: #1A6262;
        box-shadow: 0 0 0 3px rgba(26, 98, 98, 0.2);
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background-color: #1A6262;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #d6ecec 0%, #b3d9d9 100%);
        border-radius: 8px;
        border: 1px solid #1A6262;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #b3d9d9 0%, #99cccc 100%);
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(26, 98, 98, 0.2);
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: rgba(26, 98, 98, 0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #1A6262;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_preprocess_data():
    """Load and preprocess all data with caching."""
    with st.spinner("Loading logistics data..."):
        data, quality_summary = load_data()
        processed_data = preprocess_data(data)
    return data, processed_data, quality_summary


def main():
    """Main application function."""
    
    # Load data
    try:
        raw_data, processed_data, quality_summary = load_and_preprocess_data()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()
    
    # Initialize models
    routing_engine = RoutingEngine(processed_data)
    cost_model = CostModel()
    sustainability_model = SustainabilityModel()
    
    # Modern Horizontal Navigation Bar
    st.markdown("""
        <div class="nav-container">
            <div class="nav-header">
                <div>
                    <div class="nav-brand">
                        <span class="nav-brand-icon">&#x1F69A;</span>
                        <div>
                            <div>Smart Route Planner</div>
                            <div class="nav-subtitle">Decision Intelligence System for NexGen Logistics</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tabs = st.tabs([
        "🎯 Route Optimization",
        "📊 Fleet Dashboard", 
        "🔍 Data Quality",
        "ℹ️ About"
    ])
    
    # Route pages
    with tabs[0]:
        show_route_optimization_page(routing_engine, cost_model, sustainability_model, raw_data, processed_data)
    
    with tabs[1]:
        show_fleet_dashboard(raw_data, processed_data)
    
    with tabs[2]:
        show_data_quality_page(quality_summary, raw_data)
    
    with tabs[3]:
        show_about_page()


def show_route_optimization_page(routing_engine, cost_model, sustainability_model, raw_data, processed_data):
    """Display route optimization interface."""
    
    st.header("Route Optimization")
    
    # Get valid locations
    locations = get_location_list(raw_data)
    
    # Input form
    with st.form("route_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            origin = st.selectbox("📍 Origin", locations, index=0)
        
        with col2:
            destination = st.selectbox("📍 Destination", locations, index=1 if len(locations) > 1 else 0)
        
        with col3:
            order_weight = st.number_input("📦 Order Weight (kg)", min_value=1.0, max_value=10000.0, value=500.0, step=50.0)
        
        with col4:
            priority = st.selectbox("⚡ Priority", ["Express", "Standard", "Economy"], index=1)
        
        submitted = st.form_submit_button("🚀 Optimize Route", use_container_width=True)
    
    if submitted:
        # Validate input
        validation = validate_route_input(origin, destination, order_weight, locations)
        
        if not validation['valid']:
            for error in validation['errors']:
                st.error(f"❌ {error}")
            return
        
        if validation['warnings']:
            for warning in validation['warnings']:
                st.warning(f"⚠️ {warning}")
        
        # Run optimization
        with st.spinner("🔄 Analyzing route options..."):
            results = routing_engine.optimize_route(
                origin=origin,
                destination=destination,
                order_weight_kg=order_weight,
                priority=priority,
                show_top_n=1
            )
        
        # Check for errors
        if 'error' in results:
            st.error(f"❌ {results['message']}")
            st.info(f"💡 {results['recommendations']['primary']['rationale']}")
            return
        
        # Display results
        st.success(f"✅ Found {results['total_combinations_evaluated']} feasible route-vehicle combinations")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Cost Analysis", "🌱 Sustainability", "📈 Trade-offs"])
        
        with tab1:
            show_overview_tab(results, cost_model, sustainability_model)
        
        with tab2:
            show_cost_analysis_tab(results, cost_model, order_weight)
        
        with tab3:
            show_sustainability_tab(results, sustainability_model)
        
        with tab4:
            show_tradeoffs_tab(results)


def show_overview_tab(results, cost_model, sustainability_model):
    """Display overview of route options."""
    
    st.subheader("Route Options Summary")
    
    # Summary table
    summary_table = create_route_summary_table(results['ranked_options'])
    st.dataframe(summary_table, use_container_width=True, hide_index=True)
    
    # Multi-objective comparison chart
    st.subheader("Multi-Objective Comparison")
    fig = create_multi_objective_comparison(results['ranked_options'])
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    rec = results['recommendations']['primary']
    st.markdown(f"""
    <div class="success-box">
        <strong>Primary Recommendation:</strong> {rec['option'].title()} Option<br>
        <strong>Rationale:</strong> {rec['rationale']}
    </div>
    """, unsafe_allow_html=True)
    
    if 'alternative' in results['recommendations']:
        alt = results['recommendations']['alternative']
        st.markdown(f"""
        <div class="info-box">
            <strong>Alternative:</strong> {alt['option'].title()} Option<br>
            <strong>Rationale:</strong> {alt['rationale']}
        </div>
        """, unsafe_allow_html=True)


def show_cost_analysis_tab(results, cost_model, order_weight):
    """Display detailed cost analysis."""
    
    st.subheader("Cost Analysis")
    
    # Get cheapest option
    if 'cheapest' in results['ranked_options'] and not results['ranked_options']['cheapest'].empty:
        cheapest = results['ranked_options']['cheapest'].iloc[0]
        
        # Get cost breakdown
        breakdown = cost_model.get_cost_breakdown(
            distance_km=cheapest['Distance_KM'],
            vehicle_type=cheapest['Vehicle_Type'],
            fuel_efficiency=cheapest['Fuel_Efficiency_KM_per_L'],
            traffic_delay_min=cheapest['Traffic_Delay_Minutes'],
            weather_impact=cheapest['Weather_Impact'],
            order_weight_kg=order_weight
        )
        
        # Display cost components
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.metric("Total Cost", format_currency(breakdown['total_cost']))
            st.metric("Fuel Cost", format_currency(breakdown['fuel_cost']))
            st.metric("Labor Cost", format_currency(breakdown['labor_cost']))
            st.metric("Maintenance Cost", format_currency(breakdown['maintenance_cost']))
        
        with col2:
            st.metric("Toll Charges", format_currency(breakdown['toll_charges']))
            st.metric("Insurance", format_currency(breakdown['insurance_cost']))
            st.metric("Packaging", format_currency(breakdown['packaging_cost']))
            st.metric("Platform Fee", format_currency(breakdown['platform_fee']))
        
        # Cost breakdown pie chart
        st.subheader("Cost Component Breakdown")
        fig_pie = create_cost_breakdown_pie(breakdown)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Cost per km metric
        cost_per_km = breakdown['total_cost'] / cheapest['Distance_KM']
        st.info(f"📊 **Cost Efficiency:** {format_currency(cost_per_km)} per kilometer")
    else:
        st.warning("No cost data available for selected route.")


def show_sustainability_tab(results, sustainability_model):
    """Display sustainability analysis."""
    
    st.subheader("Environmental Impact Analysis")
    
    # Get greenest option
    if 'greenest' in results['ranked_options'] and not results['ranked_options']['greenest'].empty:
        greenest = results['ranked_options']['greenest'].iloc[0]
        
        # Get emission breakdown
        emissions = sustainability_model.get_emission_breakdown(
            distance_km=greenest['Distance_KM'],
            co2_rate=greenest['CO2_Emissions_Kg_per_KM'],
            fuel_efficiency=greenest['Fuel_Efficiency_KM_per_L']
        )
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total CO₂ Emissions", f"{emissions['total_emissions_kg']:.2f} kg")
        
        with col2:
            st.metric("Emissions per KM", f"{emissions['emissions_per_km']:.4f} kg/km")
        
        with col3:
            st.metric("Fuel Consumption", f"{emissions['fuel_consumption_liters']:.2f} L")
        
        # Carbon offset cost
        offset = sustainability_model.calculate_carbon_offset_cost(emissions['total_emissions_kg'])
        st.info(f"🌳 **Carbon Offset Cost:** {format_currency(offset['offset_cost_inr'])} ({emissions['total_emissions_kg']:.1f} kg CO₂)")
        
        # Vehicle efficiency assessment
        efficiency = sustainability_model.assess_vehicle_efficiency(
            greenest['Vehicle_Type'],
            greenest['CO2_Emissions_Kg_per_KM']
        )
        
        if efficiency == 'Efficient':
            st.success(f"✅ Vehicle {greenest['Vehicle_ID']} is environmentally **{efficiency}**")
        elif efficiency == 'Average':
            st.info(f"ℹ️ Vehicle {greenest['Vehicle_ID']} has **{efficiency}** environmental efficiency")
        else:
            st.warning(f"⚠️ Vehicle {greenest['Vehicle_ID']} is environmentally **{efficiency}**")
        
        # Comparison with other options
        if 'cheapest' in results['ranked_options'] and not results['ranked_options']['cheapest'].empty:
            cheapest = results['ranked_options']['cheapest'].iloc[0]
            
            comparison = sustainability_model.compare_emissions(
                cheapest['Emissions_Score'],
                greenest['Emissions_Score']
            )
            
            st.markdown(f"""
            <div class="info-box">
                <strong>Green vs Cost Trade-off:</strong><br>
                {comparison['interpretation']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No sustainability data available for selected route.")


def show_tradeoffs_tab(results):
    """Display trade-off analysis."""
    
    st.subheader("Trade-off Analysis")
    
    if 'trade_off_analysis' not in results or not results['trade_off_analysis']:
        st.info("Trade-off analysis not available for this route.")
        return
    
    trade_offs = results['trade_off_analysis']
    
    # Fastest vs Cheapest
    if 'fastest_vs_cheapest' in trade_offs:
        st.markdown("### ⚡ Fastest vs 💰 Cheapest")
        st.markdown(f"""
        <div class="info-box">
            {trade_offs['fastest_vs_cheapest']['message']}
        </div>
        """, unsafe_allow_html=True)
    
    # Cheapest vs Greenest
    if 'cheapest_vs_greenest' in trade_offs:
        st.markdown("### 💰 Cheapest vs 🌱 Greenest")
        st.markdown(f"""
        <div class="info-box">
            {trade_offs['cheapest_vs_greenest']['message']}
        </div>
        """, unsafe_allow_html=True)
    
    # Summary insights
    st.markdown("### 📊 Key Insights")
    st.markdown("""
    - **Time vs Cost:** Faster routes typically incur higher costs due to premium vehicle usage
    - **Cost vs Sustainability:** Environmentally efficient vehicles may have higher operational costs
    - **Balanced Approach:** Standard priority routes offer optimal trade-offs for most scenarios
    """)


def show_fleet_dashboard(raw_data, processed_data):
    """Display fleet management dashboard."""
    
    st.header("Fleet Management Dashboard")
    
    vehicles_df = raw_data['vehicle_fleet']
    
    # Fleet utilization metrics
    utilization = calculate_fleet_utilization(vehicles_df)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Vehicles", utilization['total_vehicles'])
    
    with col2:
        st.metric("Available", utilization['available'], delta=f"{utilization['availability_rate']}%")
    
    with col3:
        st.metric("In Transit", utilization['in_transit'], delta=f"{utilization['utilization_rate']}%")
    
    with col4:
        st.metric("Maintenance", utilization['maintenance'])
    
    # Fleet utilization chart
    fig = create_fleet_utilization_chart(utilization)
    st.plotly_chart(fig, use_container_width=True)
    
    # Vehicle details
    st.subheader("Vehicle Fleet Details")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.multiselect("Filter by Status", vehicles_df['Status'].unique(), default=vehicles_df['Status'].unique())
    
    with col2:
        type_filter = st.multiselect("Filter by Type", vehicles_df['Vehicle_Type'].unique(), default=vehicles_df['Vehicle_Type'].unique())
    
    # Apply filters (show all if no selection)
    filtered_vehicles = vehicles_df.copy()
    
    if status_filter:  # Only filter if something is selected
        filtered_vehicles = filtered_vehicles[filtered_vehicles['Status'].isin(status_filter)]
    
    if type_filter:  # Only filter if something is selected
        filtered_vehicles = filtered_vehicles[filtered_vehicles['Vehicle_Type'].isin(type_filter)]
    
    # Display table
    st.dataframe(
        filtered_vehicles[['Vehicle_ID', 'Vehicle_Type', 'Capacity_KG', 'Fuel_Efficiency_KM_per_L', 
                          'Current_Location', 'Status', 'CO2_Emissions_Kg_per_KM']],
        use_container_width=True,
        hide_index=True
    )


def show_data_quality_page(quality_summary, raw_data):
    """Display data quality metrics."""
    
    st.header("Data Quality Report")
    
    st.subheader("Dataset Overview")
    st.dataframe(quality_summary, use_container_width=True, hide_index=True)
    
    # Dataset details
    st.subheader("Dataset Details")
    
    for dataset_name, df in raw_data.items():
        with st.expander(f"📁 {dataset_name} ({len(df)} records)"):
            st.write(f"**Columns:** {len(df.columns)}")
            st.write(f"**Missing Values:** {df.isnull().sum().sum()}")
            st.write("**Sample Data:**")
            st.dataframe(df.head(), use_container_width=True)


def show_about_page():
    """Display about information."""
    
    st.header("About Smart Route Planner")
    
    st.markdown("""
    ## 🎯 Project Overview
    
    **Smart Route Planner** is a Decision Intelligence System designed for NexGen Logistics to optimize 
    delivery routes across multiple objectives: time, cost, and environmental impact.
    
    ## 🏗️ Architecture
    
    The system employs a **multi-objective optimization approach** with the following components:
    
    - **Data Loading:** Safe CSV loading with schema validation
    - **Preprocessing:** Feature engineering for time/cost/emission proxies
    - **Routing Engine:** Multi-objective scoring and ranking
    - **Cost Model:** Interpretable cost estimation with breakdown
    - **Sustainability Model:** CO₂ emission calculation and reporting
    
    ## 📊 Key Features
    
    ✅ **Multiple Route Options:** Fastest, Cheapest, Greenest, Balanced
    ✅ **Explicit Trade-offs:** Clear visibility into time-cost-emission trade-offs
    ✅ **Cost Breakdown:** Detailed operational cost components
    ✅ **Environmental Impact:** CO₂ emissions and carbon offset estimates
    ✅ **Fleet Management:** Real-time vehicle utilization insights
    ✅ **Data Quality:** Transparent data quality reporting
    
    ## 🚀 Innovation Elements
    
    1. **Decision Intelligence:** Not just routing - comprehensive decision support
    2. **Transparency:** All assumptions and calculations are explicit
    3. **Sustainability Focus:** Environmental impact as strategic priority
    4. **Scenario Analysis:** What-if capabilities for sensitivity testing
    5. **Scalability Design:** Architecture ready for 10× growth
    
    ## 📈 Expected Business Impact
    
    - **15-20% Cost Reduction** via optimal vehicle-route matching
    - **10-15% Time Improvement** through traffic-aware routing
    - **8-12% CO₂ Reduction** by preferencing efficient vehicles
    - **Improved Fleet Utilization** from ~50% to ~65%
    
    ## 🔮 Future Enhancements
    
    - Machine learning for demand forecasting
    - Multi-stop route optimization
    - Real-time traffic integration
    - Dynamic pricing based on capacity
    - Advanced weather impact modeling
    
    ## 📧 Contact
    
    Developed as an interview case study for OFI Services
    
    **Technology Stack:** Python, Streamlit, Pandas, Plotly
    """)


if __name__ == "__main__":
    main()
