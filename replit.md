# Overview

The Neighborhood Energy Tracker is a comprehensive Python-based application that monitors real-time energy consumption from IoT devices and provides AI-powered recommendations for sustainable energy usage. The system integrates multiple data sources (MQTT sensors, manual input), processes consumption patterns, and delivers actionable insights through a Streamlit web interface. Core features include anomaly detection, gamification elements, automated notifications, and integration with ThingsBoard for IoT device management.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Streamlit Web Interface**: Single-page application serving as the primary user interface
- **Interactive Dashboards**: Built using Plotly for real-time energy consumption visualization
- **Session Management**: Streamlit session state for maintaining application components and user data
- **Component-based Structure**: Modular UI components for different functionality areas

## Backend Architecture
- **SQLite Database**: Lightweight file-based database for local data storage with thread-safe operations
- **MQTT Integration**: Real-time IoT data collection using Paho MQTT client with automatic reconnection
- **AI Processing Pipeline**: OpenAI GPT-5 integration for intelligent energy recommendations with fallback to rule-based logic
- **Background Services**: Threaded schedulers for notifications, data processing, and anomaly detection
- **Caching Layer**: In-memory caching with timeout-based invalidation for performance optimization

## Data Processing & Analytics
- **Anomaly Detection**: Multi-layered approach using statistical analysis, isolation forests, and pattern recognition
- **Data Aggregation**: Time-series processing for daily, weekly, and monthly consumption summaries
- **Predictive Analytics**: Consumption forecasting and trend analysis using pandas and scikit-learn
- **Gamification Engine**: Points-based reward system with achievements and streak tracking

## Authentication & Security
- **Environment-based Configuration**: Sensitive credentials managed through .env files
- **API Key Management**: Secure storage and validation of third-party service credentials
- **Database Security**: SQLite with connection pooling and transaction management

# External Dependencies

## IoT & Communication Services
- **MQTT Broker**: Configurable MQTT broker (defaults to test.mosquitto.org) for real-time sensor data
- **ThingsBoard CE**: Optional IoT platform integration for device management and telemetry
- **Email Services**: SMTP integration (Gmail by default) for notification delivery
- **Twilio SMS**: Optional SMS notifications for critical alerts

## AI & Machine Learning
- **OpenAI API**: GPT-5 integration for intelligent energy recommendations and analysis
- **Scikit-learn**: Machine learning algorithms for anomaly detection and pattern analysis
- **SciPy**: Statistical analysis tools for consumption pattern evaluation

## Data & Visualization
- **Pandas**: Data manipulation and time-series analysis
- **Plotly**: Interactive chart generation and dashboard visualizations
- **NumPy**: Numerical computations and array operations

## Web Framework & UI
- **Streamlit**: Primary web application framework for the user interface
- **Threading**: Background task management for real-time data processing
- **Schedule**: Automated task scheduling for periodic notifications and reports