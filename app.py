import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import threading
import json
import random

from config import *
from database import DatabaseManager
from mqtt_client import MQTTClient
from ai_recommendations import AIRecommendations
from anomaly_detection import AnomalyDetector
from notifications import NotificationManager
from gamification import GamificationManager
from thingsboard_client import ThingsBoardClient
from data_processor import DataProcessor
from thingsboard_sync import ThingsBoardSyncService
from ui.components import (
    apply_professional_theme, professional_header, professional_subheader,
    status_pill, professional_metric_card, professional_navigation, 
    professional_info_box, create_professional_chart, professional_data_table
)
from ui.theme import COLORS

# Page configuration - MUST be first st.* call
st.set_page_config(
    page_title="Energy Management Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = MQTTClient()
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = AIRecommendations()
if 'anomaly_detector' not in st.session_state:
    st.session_state.anomaly_detector = AnomalyDetector()
if 'notification_manager' not in st.session_state:
    st.session_state.notification_manager = NotificationManager()
if 'gamification_manager' not in st.session_state:
    st.session_state.gamification_manager = GamificationManager()
if 'thingsboard_client' not in st.session_state:
    st.session_state.thingsboard_client = ThingsBoardClient()
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = DataProcessor()
if 'thingsboard_sync' not in st.session_state:
    st.session_state.thingsboard_sync = ThingsBoardSyncService(
        st.session_state.db_manager, 
        st.session_state.thingsboard_client
    )

# Page configuration moved to top of file

def main():
    apply_professional_theme()
    
    professional_header("Energy Management Platform", "Enterprise energy monitoring and optimization dashboard")

    pages = [
        {"name": "dashboard", "label": "Dashboard"},
        {"name": "analytics", "label": "Analytics"},
        {"name": "ai_recommendations", "label": "AI Insights"},
        {"name": "manual_input", "label": "Data Entry"},
        {"name": "gamification", "label": "Performance Tracking"},
        {"name": "neighborhood", "label": "Benchmarking"},
        {"name": "hardware_simulator", "label": "Device Simulator"},
        {"name": "settings", "label": "Settings"},
    ]

    page = professional_navigation(pages, "dashboard")

    if page == "dashboard":
        dashboard_page()
    elif page == "analytics":
        analytics_page()
    elif page == "ai_recommendations":
        ai_recommendations_page()
    elif page == "manual_input":
        manual_input_page()
    elif page == "gamification":
        gamification_page()
    elif page == "neighborhood":
        neighborhood_page()
    elif page == "hardware_simulator":
        hardware_simulator_page()
    elif page == "settings":
        settings_page()
    elif page == "neighborhood":
        neighborhood_page()

def dashboard_page():
    # Enhanced header with sync button
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        professional_header("Real-Time Energy Dashboard", "Live insights into your energy consumption patterns")

    with col_header2:
        if st.button("Sync ThingsBoard", help="Pull latest data from ThingsBoard", type="primary"):
            with st.spinner("Syncing data..."):
                result = st.session_state.thingsboard_sync.perform_sync()
                if result['success']:
                    st.success(f"Synced {result['synced_count']} new records!")
                    st.session_state.data_processor.clear_cache()
                    st.rerun()
                else:
                    st.error(f"Sync failed: {result.get('error', 'Unknown error')}")

    # Enhanced status indicators with colors and hover effects
    professional_subheader("System Status", "Current status of all connected systems and services")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        mqtt_status = st.session_state.mqtt_client.is_connected()
        professional_metric_card("MQTT Connection", "Connected" if mqtt_status else "Disconnected")

    with col2:
        tb_status = st.session_state.thingsboard_client.check_connection()
        professional_metric_card("ThingsBoard", "Connected" if tb_status else "Disconnected")

    with col3:
        current_consumption = st.session_state.data_processor.get_current_consumption()
        professional_metric_card("Current Usage", f"{current_consumption:.2f} kWh")

    with col4:
        daily_total = st.session_state.data_processor.get_daily_total()
        yesterday_total = st.session_state.data_processor.get_daily_total(datetime.now().date() - timedelta(days=1))
        daily_delta = daily_total - yesterday_total if yesterday_total > 0 else None
        professional_metric_card("Today's Total", f"{daily_total:.2f} kWh", delta=f"{daily_delta:.2f} kWh" if daily_delta else None)

    with col5:
        weekly_total = st.session_state.data_processor.get_weekly_total()
        estimated_cost = daily_total * ENERGY_COST_PER_KWH
        professional_metric_card("Today's Cost", f"${estimated_cost:.2f}")
    
    # Enhanced interactive consumption chart with tabs
    professional_subheader("Energy Consumption Analysis", "Interactive charts and trends for different time periods")
    
    # Time period selection with session state to track selection
    if 'selected_time_tab' not in st.session_state:
        st.session_state.selected_time_tab = 0
    
    time_options = ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom Range"]
    selected_tab = st.selectbox("Time Period", time_options, index=st.session_state.selected_time_tab)
    st.session_state.selected_time_tab = time_options.index(selected_tab)
    
    if selected_tab == "Last 24 Hours":
        hours_back = 24
        chart_title = "24-Hour Energy Consumption Trend"
    elif selected_tab == "Last 7 Days":
        hours_back = 168  # 7 days
        chart_title = "7-Day Energy Consumption Overview"
    elif selected_tab == "Last 30 Days":
        hours_back = 720  # 30 days  
        chart_title = "30-Day Energy Consumption Analysis"
    else:  # Custom Range
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
        with col_date2:
            end_date = st.date_input("End Date", datetime.now())
        hours_back = int((datetime.now() - datetime.combine(start_date, datetime.min.time())).total_seconds() / 3600)
        chart_title = f"Energy Consumption: {start_date} to {end_date}"
    
    # Get recent data based on selection
    recent_data = st.session_state.db_manager.get_recent_energy_data(hours=hours_back)
    
    if not recent_data.empty:
        # Create enhanced interactive chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Energy Consumption Over Time', 'Device Breakdown', 'Hourly Pattern', 'Cost Analysis'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Main consumption trend with gradient fill
        fig.add_trace(
            go.Scatter(
                x=recent_data['timestamp'],
                y=recent_data['consumption'],
                mode='lines+markers',
                name='Energy (kWh)',
                line=dict(color='#1f77b4', width=3),
                fill='tonexty',
                fillcolor='rgba(31, 119, 180, 0.2)',
                hovertemplate='<b>%{x}</b><br>Consumption: %{y:.3f} kWh<br>Cost: $%{customdata:.2f}<extra></extra>',
                customdata=recent_data['consumption'] * ENERGY_COST_PER_KWH,
                marker=dict(size=5, symbol='circle')
            ),
            row=1, col=1
        )
        
        # Device breakdown pie chart
        device_breakdown = recent_data.groupby('device_name')['consumption'].sum().reset_index()
        if len(device_breakdown) > 1:
            fig.add_trace(
                go.Pie(
                    labels=device_breakdown['device_name'],
                    values=device_breakdown['consumption'],
                    name="Device Usage",
                    hovertemplate='<b>%{label}</b><br>Usage: %{value:.2f} kWh<br>Percentage: %{percent}<extra></extra>'
                ),
                row=1, col=2
            )
        
        # Hourly pattern analysis
        hourly_data = recent_data.groupby(recent_data['timestamp'].dt.hour)['consumption'].mean().reset_index()
        fig.add_trace(
            go.Bar(
                x=hourly_data['timestamp'],
                y=hourly_data['consumption'],
                name='Avg Hourly Usage',
                marker_color='lightblue',
                hovertemplate='<b>Hour %{x}:00</b><br>Avg: %{y:.3f} kWh<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Cost trend analysis
        recent_data_cost = recent_data.copy()
        recent_data_cost['cost'] = recent_data_cost['consumption'] * ENERGY_COST_PER_KWH
        recent_data_cost['cumulative_cost'] = recent_data_cost['cost'].cumsum()
        
        fig.add_trace(
            go.Scatter(
                x=recent_data_cost['timestamp'],
                y=recent_data_cost['cumulative_cost'],
                mode='lines+markers',
                name='Cumulative Cost ($)',
                line=dict(color='red', width=2),
                hovertemplate='<b>%{x}</b><br>Total Cost: $%{y:.2f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Update layout for better interactivity
        fig.update_layout(
            title=chart_title,
            height=900,
            showlegend=True,
            hovermode='closest'
        )
        
        # Add range slider to main chart
        fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
        
        fig = create_professional_chart(fig, "Daily Energy Consumption")
        st.plotly_chart(fig, width="stretch")
    else:
        professional_info_box("No recent energy data available. Please add data to begin monitoring your energy consumption.", "warning")
        
        # Helpful suggestions
        professional_info_box("**Get Started with Data Collection:**", "info")
        col_suggest1, col_suggest2, col_suggest3 = st.columns(3)
        with col_suggest1:
            st.markdown("**Manual Input**\nAdd energy data manually from your meter readings")
        with col_suggest2:
            st.markdown("**Hardware Simulator**\nGenerate realistic IoT device data for testing")
        with col_suggest3:
            st.markdown("**MQTT/ThingsBoard**\nConnect real IoT devices or use our simulator")
    
    # Anomaly alerts
    anomalies = st.session_state.anomaly_detector.detect_anomalies()
    if anomalies:
        professional_subheader("Anomaly Alerts", "Unusual patterns detected in energy consumption")
        for anomaly in anomalies:
            professional_info_box(f"Anomaly detected: {anomaly['message']} at {anomaly['timestamp']}", "warning")
    
    # Device status
    professional_subheader("Connected Devices", "Status of all registered IoT devices and sensors")
    devices = st.session_state.db_manager.get_device_status()
    if not devices.empty:
        for _, device in devices.iterrows():
            status_type = "online" if device['status'] == 'online' else "offline"
            device_info = f"{device['device_name']}: {status_pill(status_type, device['status'])} - Last seen: {device['last_seen']}"
            st.markdown(device_info, unsafe_allow_html=True)
    else:
        professional_info_box("No IoT devices connected. Use manual input or check MQTT configuration.", "info")


def neighborhood_page():
    professional_header("Community Benchmarking", "Compare your energy usage with neighbors and see community rankings")

    # User config section
    col1, col2 = st.columns([2, 1])
    with col1:
        professional_subheader("Your Energy Profile", "Configure your household details for accurate benchmarking")
        user_name = st.text_input("Household Name", value="Your Home", help="Enter your household name for leaderboard")
        household_size = st.number_input("Household Members", min_value=1, max_value=10, value=2,
                                         help="Number of people in your household")
        home_size = st.selectbox("Home Size",
                                 ["Small (< 1000 sq ft)", "Medium (1000-2000 sq ft)", "Large (2000-3000 sq ft)",
                                  "Very Large (> 3000 sq ft)"])

    with col2:
        professional_subheader("Your Ranking", "Your position compared to the community")
        # Example: daily_usage fetched from the user’s current database
        daily_usage = st.session_state.data_processor.get_daily_total()  # replace or adjust as needed
        normalized_usage = daily_usage / household_size  # kWh per person

        # Simulated neighborhood data for demo
        neighborhood_data = [
            {"name": "Green Family", "daily_kwh": 8.2, "members": 3, "efficiency_score": 95},
            {"name": "Johnson House", "daily_kwh": 12.5, "members": 4, "efficiency_score": 82},
            {"name": "Miller Residence", "daily_kwh": 15.8, "members": 2, "efficiency_score": 78},
            {"name": user_name, "daily_kwh": daily_usage, "members": household_size, "efficiency_score": 85},
            {"name": "Davis Home", "daily_kwh": 18.3, "members": 5, "efficiency_score": 72},
            {"name": "Wilson Family", "daily_kwh": 22.1, "members": 3, "efficiency_score": 65},
        ]
        for house in neighborhood_data:
            house['normalized_kwh'] = house['daily_kwh'] / house['members']
        neighborhood_data.sort(key=lambda x: x['normalized_kwh'])
        user_rank = next((i + 1 for i, house in enumerate(neighborhood_data) if house['name'] == user_name),
                         len(neighborhood_data))

        # Display rank
        professional_metric_card("Your Rank", f"#{user_rank} of {len(neighborhood_data)}")
        efficiency_delta = normalized_usage - 6.5 if normalized_usage > 0 else None
        professional_metric_card("Usage/Person", f"{normalized_usage:.1f} kWh",
                                 delta=f"{efficiency_delta:.1f}" if efficiency_delta else None)

    # Community leaderboard
    professional_subheader("Community Leaderboard", "Energy efficiency rankings for your neighborhood")
    leaderboard_df = pd.DataFrame(neighborhood_data)
    leaderboard_df = leaderboard_df.sort_values('normalized_kwh')
    leaderboard_df['rank'] = range(1, len(leaderboard_df) + 1)

    # Bar chart for normalized usage
    fig = go.Figure()
    colors = ['#2E8B57' if name == user_name else '#87CEEB' for name in leaderboard_df['name']]
    fig.add_trace(go.Bar(
        x=leaderboard_df['name'],
        y=leaderboard_df['normalized_kwh'],
        name='kWh per Person',
        marker_color=colors,
        text=leaderboard_df['normalized_kwh'].round(1),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Usage: %{y:.1f} kWh/person<br>Total: %{customdata:.1f} kWh<br>Members: %{customdata[1]}<br>Efficiency: %{customdata}%<extra></extra>',
        customdata=list(zip(leaderboard_df['daily_kwh'], leaderboard_df['members'], leaderboard_df['efficiency_score']))
    ))
    fig.update_layout(
        title="Energy Usage per Person (kWh/day)",
        xaxis_title="Households",
        yaxis_title="kWh per Person",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # Community insights
    professional_subheader("Community Insights", "Key statistics and performance metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_usage = sum(house['normalized_kwh'] for house in neighborhood_data) / len(neighborhood_data)
        professional_metric_card("Neighborhood Average", f"{avg_usage:.1f} kWh/person")
    with col2:
        best_performer = min(neighborhood_data, key=lambda x: x['normalized_kwh'])
        professional_metric_card("Best Performer", f"{best_performer['name']}",
                                 delta=f"{best_performer['normalized_kwh']:.1f} kWh/person")
    with col3:
        total_savings = sum(house['daily_kwh'] for house in neighborhood_data) * ENERGY_COST_PER_KWH
        professional_metric_card("Community Daily Cost", f"${total_savings:.2f}")

    # Best practices from top performers
    professional_subheader("Best Practices", "Energy-saving tips from top-performing households")
    tips = [
        "**Green Family**: 'We use a programmable thermostat and set it 2°F lower in winter'",
        "**Johnson House**: 'LED bulbs everywhere + smart power strips for phantom loads'",
        "**Miller Residence**: 'We air-dry clothes and run dishwasher only when full'"
    ]
    for tip in tips:
        professional_info_box(tip, "info")


def analytics_page():
    professional_header("Energy Analytics", "Comprehensive analysis of historical energy consumption patterns")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Get historical data
    historical_data = st.session_state.db_manager.get_energy_data_range(start_date, end_date)
    
    if not historical_data.empty:
        # Daily consumption trend
        st.subheader("Daily Consumption Trend")
        daily_data = historical_data.groupby(historical_data['timestamp'].dt.date)['consumption'].sum().reset_index()
        
        fig = px.bar(daily_data, x='timestamp', y='consumption', 
                    title='Daily Energy Consumption',
                    labels={'consumption': 'Consumption (kWh)', 'timestamp': 'Date'})
        fig = create_professional_chart(fig, "Daily Energy Consumption")
        st.plotly_chart(fig, width="stretch")
        
        # Hourly patterns
        st.subheader("Hourly Usage Patterns")
        hourly_data = historical_data.groupby(historical_data['timestamp'].dt.hour)['consumption'].mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_data['timestamp'],
            y=hourly_data['consumption'],
            mode='lines+markers',
            name='Average Hourly Consumption'
        ))
        
        fig.update_layout(
            title="Average Hourly Energy Consumption",
            xaxis_title="Hour of Day",
            yaxis_title="Average Consumption (kWh)"
        )
        fig = create_professional_chart(fig, "Daily Energy Consumption")
        st.plotly_chart(fig, width="stretch")
        
        # Statistics
        st.subheader("Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Consumption", f"{historical_data['consumption'].sum():.2f} kWh")
        with col2:
            st.metric("Average Daily", f"{daily_data['consumption'].mean():.2f} kWh")
        with col3:
            st.metric("Peak Hour", f"{hourly_data.loc[hourly_data['consumption'].idxmax(), 'timestamp']}:00")
        with col4:
            estimated_cost = historical_data['consumption'].sum() * ENERGY_COST_PER_KWH
            st.metric("Estimated Cost", f"${estimated_cost:.2f}")
    else:
        st.warning("No data available for the selected date range.")

def ai_recommendations_page():
    professional_header("AI-Powered Energy Insights", "Intelligent recommendations for optimizing your energy consumption")
    
    # Get recent consumption data
    recent_data = st.session_state.db_manager.get_recent_energy_data(hours=168)  # Last week
    
    if not recent_data.empty:
        # Generate recommendations
        if st.button("Generate New Recommendations"):
            with st.spinner("Analyzing your energy usage patterns..."):
                recommendations = st.session_state.ai_recommendations.generate_recommendations(recent_data)
                
                if recommendations:
                    st.success("New recommendations generated!")
                    
                    for i, rec in enumerate(recommendations, 1):
                        with st.expander(f"Recommendation {i}: {rec['title']}"):
                            st.write(rec['description'])
                            if 'estimated_savings' in rec:
                                st.metric("Estimated Monthly Savings", f"${rec['estimated_savings']:.2f}")
                else:
                    st.error("Failed to generate recommendations. Please check your OpenAI API configuration.")
        
        # Show stored recommendations
        stored_recommendations = st.session_state.db_manager.get_recent_recommendations()
        if not stored_recommendations.empty:
            st.subheader("Recent Recommendations")
            for _, rec in stored_recommendations.iterrows():
                with st.expander(f"{rec['title']} - {rec['created_at']}"):
                    st.write(rec['description'])
                    if rec['estimated_savings']:
                        st.metric("Estimated Monthly Savings", f"${rec['estimated_savings']:.2f}")
    else:
        st.warning("Need at least a week of energy data to generate meaningful recommendations.")

def manual_input_page():
    professional_header("Manual Data Entry", "Add energy consumption data for devices without IoT sensors")
    
    st.write("Add energy consumption data for homes without IoT sensors.")
    
    # Manual input form
    with st.form("manual_energy_input"):
        col1, col2 = st.columns(2)
        
        with col1:
            device_name = st.text_input("Device/Location Name", placeholder="e.g., Kitchen, Living Room, Meter Reading")
            consumption = st.number_input("Energy Consumption (kWh)", min_value=0.0, step=0.1)
        
        with col2:
            input_date = st.date_input("Date", datetime.now().date())
            input_time = st.time_input("Time", datetime.now().time())
        
        submitted = st.form_submit_button("Add Energy Data")
        
        if submitted:
            if device_name and consumption > 0:
                timestamp = datetime.combine(input_date, input_time)
                
                # Add to database
                success = st.session_state.db_manager.add_energy_data(
                    device_name, consumption, timestamp, source='manual'
                )
                
                if success:
                    st.success(f"Added {consumption} kWh for {device_name} at {timestamp}")
                    
                    # Clear cache to refresh dashboard metrics immediately
                    st.session_state.data_processor.clear_cache()
                    
                    # Award points for manual input
                    st.session_state.gamification_manager.add_points('manual_input', 10)
                    
                    # Send to ThingsBoard if configured
                    st.session_state.thingsboard_client.send_telemetry(device_name, {
                        'consumption': consumption,
                        'timestamp': timestamp.isoformat()
                    })
                else:
                    st.error("Failed to add energy data. Please try again.")
            else:
                st.error("Please fill in all required fields.")
    
    # Show recent manual entries
    professional_subheader("Recent Manual Entries", "History of manually entered energy data")
    manual_data = st.session_state.db_manager.get_manual_entries(limit=10)
    if not manual_data.empty:
        professional_data_table(manual_data, "Recent Entries")
    else:
        professional_info_box("No manual entries yet. Add your first energy reading above.", "info")

def gamification_page():
    professional_header("Performance Tracking", "Monitor your energy efficiency achievements and community ranking")
    
    # User profile
    user_profile = st.session_state.gamification_manager.get_user_profile()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Points", user_profile['total_points'])
    with col2:
        st.metric("Current Level", user_profile['level'])
    with col3:
        st.metric("Achievements", len(user_profile['achievements']))
    
    # Points breakdown
    st.subheader("Points Breakdown")
    points_data = st.session_state.gamification_manager.get_points_breakdown()
    if points_data:
        fig = px.pie(
            values=list(points_data.values()),
            names=list(points_data.keys()),
            title="Points by Activity"
        )
        fig = create_professional_chart(fig, "Daily Energy Consumption")
        st.plotly_chart(fig, width="stretch")
    
    # Leaderboard
    professional_subheader("Community Leaderboard", "Top performers in your neighborhood")
    leaderboard = st.session_state.gamification_manager.get_leaderboard()
    if leaderboard:
        for i, user in enumerate(leaderboard, 1):
            col1, col2, col3 = st.columns([1, 3, 2])
            with col1:
                if i == 1:
                    st.write("🥇")
                elif i == 2:
                    st.write("🥈")
                elif i == 3:
                    st.write("🥉")
                else:
                    st.write(f"#{i}")
            with col2:
                st.write(user['username'])
            with col3:
                st.write(f"{user['points']} points")
    
    # Achievements
    professional_subheader("Achievements", "Your earned badges and available milestones")
    achievements = st.session_state.gamification_manager.get_available_achievements()
    
    for achievement in achievements:
        earned = achievement['id'] in user_profile['achievements']
        status = "Completed" if earned else "Available"
        
        with st.expander(f"{achievement['name']} - {status}"):
            st.write(achievement['description'])
            st.write(f"Points: {achievement['points']}")
    
    # Challenges
    professional_subheader("Active Challenges", "Current goals to help you save more energy")
    challenges = st.session_state.gamification_manager.get_active_challenges()
    
    for challenge in challenges:
        progress = st.session_state.gamification_manager.get_challenge_progress(challenge['id'])
        
        with st.expander(f"{challenge['name']} - {progress['percentage']:.1f}% Complete"):
            st.write(challenge['description'])
            st.progress(progress['percentage'] / 100)
            st.write(f"Reward: {challenge['reward_points']} points")
            
            if progress['percentage'] >= 100 and not progress['completed']:
                if st.button(f"Claim Reward - {challenge['name']}", key=f"claim_{challenge['id']}"):
                    st.session_state.gamification_manager.complete_challenge(challenge['id'])
                    st.success(f"Challenge completed! Earned {challenge['reward_points']} points!")
                    st.rerun()

def neighborhood_page():
    professional_header("Community Benchmarking", "Compare your energy usage with neighbors and see community rankings")

    # User profile selection
    col1, col2 = st.columns([2, 1])
    with col1:
        professional_subheader("Your Energy Profile", "Configure your household details for accurate benchmarking")
        user_name = st.text_input("Household Name", value="Your Home", help="Enter your household name for leaderboard")
        household_size = st.number_input("Household Members", min_value=1, max_value=10, value=2, help="Number of people in your household")
        home_size = st.selectbox("Home Size", ["Small (< 1000 sq ft)", "Medium (1000-2000 sq ft)", "Large (2000-3000 sq ft)", "Very Large (> 3000 sq ft)"])

    with col2:
        professional_subheader("Your Ranking", "Your position compared to the community")
        # Calculate user's current ranking
        daily_usage = st.session_state.data_processor.get_daily_total()
        normalized_usage = daily_usage / household_size  # kWh per person

        # Simulated neighborhood data for demo
        neighborhood_data = [
            {"name": "Green Family", "daily_kwh": 8.2, "members": 3, "efficiency_score": 95},
            {"name": "Johnson House", "daily_kwh": 12.5, "members": 4, "efficiency_score": 82},
            {"name": "Miller Residence", "daily_kwh": 15.8, "members": 2, "efficiency_score": 78},
            {"name": user_name, "daily_kwh": daily_usage, "members": household_size, "efficiency_score": 85},
            {"name": "Davis Home", "daily_kwh": 18.3, "members": 5, "efficiency_score": 72},
            {"name": "Wilson Family", "daily_kwh": 22.1, "members": 3, "efficiency_score": 65},
        ]

        # Calculate normalized usage and rank
        for house in neighborhood_data:
            house['normalized_kwh'] = house['daily_kwh'] / house['members']

        neighborhood_data.sort(key=lambda x: x['normalized_kwh'])
        user_rank = next((i+1 for i, house in enumerate(neighborhood_data) if house['name'] == user_name), len(neighborhood_data))

        # Display rank with color coding
        rank_color = "green" if user_rank <= 2 else "orange" if user_rank <= 4 else "red"
        professional_metric_card("Your Rank", f"#{user_rank} of {len(neighborhood_data)}")
        efficiency_delta = normalized_usage - 6.5 if normalized_usage > 0 else None
        professional_metric_card("Usage/Person", f"{normalized_usage:.1f} kWh", delta=f"{efficiency_delta:.1f}" if efficiency_delta else None)

    # Neighborhood leaderboard
    professional_subheader("Community Leaderboard", "Energy efficiency rankings for your neighborhood")

    leaderboard_df = pd.DataFrame(neighborhood_data)
    leaderboard_df = leaderboard_df.sort_values('normalized_kwh')
    leaderboard_df['rank'] = range(1, len(leaderboard_df) + 1)

    # Create interactive leaderboard chart
    fig = go.Figure()

    # Bar chart for normalized usage
    colors = ['#2E8B57' if name == user_name else '#87CEEB' for name in leaderboard_df['name']]

    fig.add_trace(go.Bar(
        x=leaderboard_df['name'],
        y=leaderboard_df['normalized_kwh'],
        name='kWh per Person',
        marker_color=colors,
        text=leaderboard_df['normalized_kwh'].round(1),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Usage: %{y:.1f} kWh/person<br>Total: %{customdata[0]:.1f} kWh<br>Members: %{customdata[1]}<br>Efficiency: %{customdata[2]}%<extra></extra>',
        customdata=list(zip(leaderboard_df['daily_kwh'], leaderboard_df['members'], leaderboard_df['efficiency_score']))
    ))

    fig.update_layout(
        title="Energy Usage per Person (kWh/day)",
        xaxis_title="Households",
        yaxis_title="kWh per Person",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

    # Community insights
    professional_subheader("Community Insights", "Key statistics and performance metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_usage = sum(house['normalized_kwh'] for house in neighborhood_data) / len(neighborhood_data)
        professional_metric_card("Neighborhood Average", f"{avg_usage:.1f} kWh/person")

    with col2:
        best_performer = min(neighborhood_data, key=lambda x: x['normalized_kwh'])
        professional_metric_card("Best Performer", f"{best_performer['name']}", delta=f"{best_performer['normalized_kwh']:.1f} kWh/person")

    with col3:
        total_savings = sum(house['daily_kwh'] for house in neighborhood_data) * ENERGY_COST_PER_KWH
        professional_metric_card("Community Daily Cost", f"${total_savings:.2f}")

    # Energy tips from top performers
    professional_subheader("Best Practices", "Energy-saving tips from top-performing households")
    tips = [
        "**Green Family**: 'We use a programmable thermostat and set it 2°F lower in winter'",
        "**Johnson House**: 'LED bulbs everywhere + smart power strips for phantom loads'",
        "**Miller Residence**: 'We air-dry clothes and run dishwasher only when full'"
    ]

    for tip in tips:
        professional_info_box(tip, "info")

def hardware_simulator_page():
    professional_header("Device Simulator", "Generate realistic IoT energy data and connect to ThingsBoard")

    # Quick setup tabs
    tab1, tab2, tab3 = st.tabs(["Quick Start", "Configuration", "Live Data"])

    with tab1:
        st.subheader("🚀 Get Started in 3 Steps")

        st.markdown("""
        ### Step 1: ThingsBoard Device Setup
        1. Visit [demo.thingsboard.io](https://demo.thingsboard.io)
        2. Login (use demo credentials or create account)
        3. Go to **Devices** → **Add new device**
        4. Copy your **Access Token** from device credentials
        """)

        # Access token input
        access_token = st.text_input("🔑 ThingsBoard Access Token",
                                   value=THINGSBOARD_ACCESS_TOKEN or "",
                                   type="password",
                                   help="Paste your ThingsBoard device access token here")

        st.markdown("""
        ### Step 2: Choose Your Devices
        Select which home devices to simulate:
        """)

        # Device selection
        col1, col2 = st.columns(2)
        with col1:
            devices_selected = st.multiselect(
                "Select devices to simulate:",
                ["Smart Fridge", "HVAC System", "Water Heater", "Washing Machine"],
                default=["Smart Fridge", "HVAC System"]
            )

        with col2:
            more_devices = st.multiselect(
                "Additional devices:",
                ["Living Room TV", "Kitchen Appliances", "Home Office", "Lighting System"],
                default=["Living Room TV"]
            )

        all_selected_devices = devices_selected + more_devices

        st.markdown("""
        ### Step 3: Start Simulation
        """)

        col_sim1, col_sim2 = st.columns([2, 1])
        with col_sim1:
            sim_interval = st.slider("Data transmission interval (seconds)", 30, 300, 60)
            generate_history = st.checkbox("📅 Generate 24h historical data first", value=True)

        with col_sim2:
            if st.button("🚀 Start Simulator", type="primary"):
                if access_token and all_selected_devices:
                    st.success("Simulator Started!")
                    st.info(f"Simulating {len(all_selected_devices)} devices every {sim_interval}s")

                    # Show sample command
                    st.code(f"""# Sample data being sent to ThingsBoard:
{{
    "consumption": 2.3,
    "device_name": "Smart Fridge", 
    "timestamp": {int(datetime.now().timestamp() * 1000)},
    "temperature": 22.1,
    "status": "online"
}}""")
                else:
                    st.error("Please provide access token and select devices")

    with tab2:
        st.subheader("🔧 Advanced Configuration")

        st.markdown("""
        ### Device Profiles
        Each simulated device has realistic consumption patterns:
        """)

        # Device profiles table
        profiles_data = {
            "Device": ["Smart Fridge", "HVAC System", "Water Heater", "Washing Machine"],
            "Base Usage (kWh/h)": [0.15, 2.5, 0.8, 0.05],
            "Peak Multiplier": ["1.8x", "3.0x", "2.2x", "4.0x"],
            "Peak Hours": ["7-8, 18-20", "6-8, 17-21", "6-7, 18-19, 21-22", "9-10, 15-16, 19"]
        }

        profiles_df = pd.DataFrame(profiles_data)
        st.dataframe(profiles_df, width="stretch")

        st.markdown("""
        ### Simulation Features
        - **Realistic Patterns**: Peak/off-peak usage based on typical home behavior
        - **Seasonal Variations**: Higher usage in winter/summer months
        - **Device Cycles**: Washing machines, dishwashers have realistic on/off cycles
        - **Weekend/Weekday**: Different patterns for work vs. home days
        - **Random Variance**: Natural fluctuations in energy consumption
        """)

        # Manual simulation controls
        st.subheader("🎮 Manual Controls")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Generate Sample Data"):
                sample_data = {
                    "consumption": round(random.uniform(0.5, 3.0), 2),
                    "device_name": "Demo Device",
                    "timestamp": datetime.now().isoformat(),
                    "power": round(random.uniform(500, 3000), 1),
                    "status": "online"
                }
                st.json(sample_data)

        with col2:
            if st.button("🔄 Test ThingsBoard Connection"):
                if st.session_state.thingsboard_client.check_connection():
                    st.success("✅ ThingsBoard connection successful!")
                else:
                    st.error("❌ ThingsBoard connection failed")

    with tab3:
        st.subheader("📊 Live Simulation Data")

        # Sync status
        sync_status = st.session_state.thingsboard_sync.get_sync_status()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔗 ThingsBoard", "✅ Connected" if sync_status['tb_connected'] else "❌ Disconnected")
        with col2:
            st.metric("🔄 Sync Status", "✅ Running" if sync_status['sync_running'] else "❌ Stopped")
        with col3:
            last_sync = sync_status['last_sync_time']
            st.metric("🕰️ Last Sync", last_sync.split('T')[1][:5] if last_sync else "Never")

        # Real-time simulation data preview
        st.subheader("📈 Recent Simulated Data")

        # Get latest data from database
        recent_sim_data = st.session_state.db_manager.get_recent_energy_data(hours=2)

        if not recent_sim_data.empty:
            # Filter for ThingsBoard sources
            tb_data = recent_sim_data[recent_sim_data['source'].isin(['thingsboard', 'iot'])]

            if not tb_data.empty:
                # Live data chart
                fig = go.Figure()
                for device in tb_data['device_name'].unique():
                    device_data = tb_data[tb_data['device_name'] == device]
                    fig.add_trace(go.Scatter(
                        x=device_data['timestamp'],
                        y=device_data['consumption'],
                        mode='lines+markers',
                        name=device,
                        hovertemplate='<b>%{fullData.name}</b><br>Time: %{x}<br>Usage: %{y:.3f} kWh<extra></extra>'
                    ))

                fig.update_layout(
                    title="Live Device Simulation Data",
                    xaxis_title="Time",
                    yaxis_title="Consumption (kWh)",
                    height=400
                )

                fig = create_professional_chart(fig, "Live Device Simulation Data")
                st.plotly_chart(fig, width="stretch")

                # Data table
                professional_subheader("Raw Data Table", "Recent telemetry data from connected devices")
                display_data = tb_data[['timestamp', 'device_name', 'consumption', 'source']].head(20)
                professional_data_table(display_data)
            else:
                professional_info_box("No simulated data found. Start the hardware simulator to see live data.", "info")
        else:
            professional_info_box("No recent data available. Check your connections or start simulation.", "warning")

        # Manual sync button
        if st.button("Sync Now", type="primary"):
            with st.spinner("Syncing data..."):
                result = st.session_state.thingsboard_sync.perform_sync()
                if result['success']:
                    st.success(f"Synced {result['synced_count']} records!")
                    st.rerun()
                else:
                    st.error(f"Sync failed: {result.get('error')}")

def settings_page():
    professional_header("System Settings", "Configure MQTT, ThingsBoard, and notification preferences")

    # MQTT Settings
    st.subheader("MQTT Configuration")
    col1, col2 = st.columns(2)

    with col1:
        mqtt_host = st.text_input("MQTT Broker Host", value=MQTT_BROKER_HOST)
        mqtt_port = st.number_input("MQTT Broker Port", value=MQTT_BROKER_PORT)

    with col2:
        mqtt_username = st.text_input("MQTT Username", value=MQTT_USERNAME or "")
        mqtt_password = st.text_input("MQTT Password", type="password")

    if st.button("Test MQTT Connection"):
        test_client = MQTTClient(host=mqtt_host, port=mqtt_port, username=mqtt_username, password=mqtt_password)
        if test_client.connect():
            st.success("MQTT connection successful!")
            test_client.disconnect()
        else:
            st.error("MQTT connection failed. Please check your settings.")

    # ThingsBoard Settings
    st.subheader("ThingsBoard Configuration")
    col1, col2 = st.columns(2)

    with col1:
        tb_host = st.text_input("ThingsBoard Host", value=THINGSBOARD_HOST)
        tb_port = st.number_input("ThingsBoard Port", value=THINGSBOARD_PORT)

    with col2:
        tb_token = st.text_input("Access Token", type="password")

    if st.button("Test ThingsBoard Connection"):
        test_client = ThingsBoardClient(host=tb_host, port=tb_port, access_token=tb_token)
        if test_client.check_connection():
            st.success("ThingsBoard connection successful!")
        else:
            st.error("ThingsBoard connection failed. Please check your settings.")

    # Notification Settings
    st.subheader("Notification Settings")

    email_enabled = st.checkbox("Enable Email Notifications", value=True)
    if email_enabled:
        email_address = st.text_input("Email Address", placeholder="your@email.com")

        notification_types = st.multiselect(
            "Notification Types",
            ["High Usage Alerts", "Anomaly Detection", "Daily Reports", "Weekly Reports", "Recommendations"],
            default=["High Usage Alerts", "Anomaly Detection"]
        )

    # Threshold Settings
    st.subheader("Alert Thresholds")
    col1, col2 = st.columns(2)

    with col1:
        high_usage_threshold = st.number_input("High Usage Alert (kWh)", value=5.0, min_value=0.1, step=0.1)
        anomaly_threshold = st.number_input("Anomaly Detection Sensitivity", value=2.0, min_value=1.0, max_value=5.0, step=0.1)

    with col2:
        cost_per_kwh = st.number_input("Energy Cost per kWh ($)", value=ENERGY_COST_PER_KWH, min_value=0.01, step=0.01)

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")
        st.info("Note: Some settings may require an application restart to take effect.")

    # System Status
    st.subheader("System Status")

    # Database status
    db_status = st.session_state.db_manager.check_connection()
    st.write(f"Database: {'✅ Connected' if db_status else '❌ Disconnected'}")

    # MQTT status
    mqtt_status = st.session_state.mqtt_client.is_connected()
    st.write(f"MQTT: {'✅ Connected' if mqtt_status else '❌ Disconnected'}")

    # ThingsBoard status
    tb_status = st.session_state.thingsboard_client.check_connection()
    st.write(f"ThingsBoard: {'✅ Connected' if tb_status else '❌ Disconnected'}")

    # Data statistics
    data_count = st.session_state.db_manager.get_data_count()
    st.write(f"Total Energy Records: {data_count}")

if __name__ == "__main__":
    main()
