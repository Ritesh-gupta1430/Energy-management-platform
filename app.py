import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import threading
import json

from config import *
from database import DatabaseManager
from mqtt_client import MQTTClient
from ai_recommendations import AIRecommendations
from anomaly_detection import AnomalyDetector
from notifications import NotificationManager
from gamification import GamificationManager
from thingsboard_client import ThingsBoardClient
from data_processor import DataProcessor

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

# Page configuration
st.set_page_config(
    page_title="Neighborhood Energy Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("⚡ Neighborhood Energy Tracker")
    st.markdown("Python-Powered Insights, Notifications & Sustainable Living")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Dashboard", "📊 Analytics", "🤖 AI Recommendations", "📱 Manual Input", "🎮 Gamification", "⚙️ Settings"]
    )
    
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "📊 Analytics":
        analytics_page()
    elif page == "🤖 AI Recommendations":
        ai_recommendations_page()
    elif page == "📱 Manual Input":
        manual_input_page()
    elif page == "🎮 Gamification":
        gamification_page()
    elif page == "⚙️ Settings":
        settings_page()

def dashboard_page():
    st.header("Real-Time Energy Dashboard")
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        mqtt_status = st.session_state.mqtt_client.is_connected()
        st.metric("MQTT Status", "Connected" if mqtt_status else "Disconnected")
    
    with col2:
        tb_status = st.session_state.thingsboard_client.check_connection()
        st.metric("ThingsBoard", "Connected" if tb_status else "Disconnected")
    
    with col3:
        current_consumption = st.session_state.data_processor.get_current_consumption()
        st.metric("Current Usage", f"{current_consumption:.2f} kWh")
    
    with col4:
        daily_total = st.session_state.data_processor.get_daily_total()
        st.metric("Today's Total", f"{daily_total:.2f} kWh")
    
    # Real-time consumption chart
    st.subheader("Real-Time Energy Consumption")
    
    # Get recent data
    recent_data = st.session_state.db_manager.get_recent_energy_data(hours=24)
    
    if not recent_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_data['timestamp'],
            y=recent_data['consumption'],
            mode='lines+markers',
            name='Energy Consumption (kWh)',
            line=dict(color='#00ff00', width=2)
        ))
        
        fig.update_layout(
            title="24-Hour Energy Consumption",
            xaxis_title="Time",
            yaxis_title="Consumption (kWh)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No recent energy data available. Check your IoT connections or add manual data.")
    
    # Anomaly alerts
    anomalies = st.session_state.anomaly_detector.detect_anomalies()
    if anomalies:
        st.subheader("⚠️ Anomaly Alerts")
        for anomaly in anomalies:
            st.warning(f"Anomaly detected: {anomaly['message']} at {anomaly['timestamp']}")
    
    # Device status
    st.subheader("Connected Devices")
    devices = st.session_state.db_manager.get_device_status()
    if not devices.empty:
        for _, device in devices.iterrows():
            status_color = "green" if device['status'] == 'online' else "red"
            st.write(f"🔌 {device['device_name']}: :color[{status_color}][{device['status']}] - Last seen: {device['last_seen']}")
    else:
        st.info("No IoT devices connected. Use manual input or check MQTT configuration.")

def analytics_page():
    st.header("Energy Analytics")
    
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
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
    st.header("🤖 AI-Powered Energy Recommendations")
    
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
    st.header("📱 Manual Energy Input")
    
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
    st.subheader("Recent Manual Entries")
    manual_data = st.session_state.db_manager.get_manual_entries(limit=10)
    if not manual_data.empty:
        st.dataframe(manual_data, use_container_width=True)
    else:
        st.info("No manual entries yet.")

def gamification_page():
    st.header("🎮 Energy Saving Game")
    
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
        st.plotly_chart(fig, use_container_width=True)
    
    # Leaderboard
    st.subheader("🏆 Neighborhood Leaderboard")
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
                    st.write(f"{i}.")
            with col2:
                st.write(user['username'])
            with col3:
                st.write(f"{user['points']} points")
    
    # Achievements
    st.subheader("🏅 Achievements")
    achievements = st.session_state.gamification_manager.get_available_achievements()
    
    for achievement in achievements:
        earned = achievement['id'] in user_profile['achievements']
        icon = "✅" if earned else "⏳"
        status = "Earned" if earned else "Not Earned"
        
        with st.expander(f"{icon} {achievement['name']} - {status}"):
            st.write(achievement['description'])
            st.write(f"Points: {achievement['points']}")
    
    # Challenges
    st.subheader("🎯 Current Challenges")
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

def settings_page():
    st.header("⚙️ Settings")
    
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
