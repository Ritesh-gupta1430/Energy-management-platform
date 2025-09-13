# ⚡ Energy Management Platform

Energy Management Platform is a Python-based web application that enables users to monitor, visualize, and analyze energy consumption data. It is built using **Streamlit**, **Pandas**, and **NumPy**, with optional integration to IoT platforms like **ThingsBoard** and communication protocols such as **MQTT**. This platform is ideal for both personal use and industrial applications, helping users make informed decisions to optimize energy usage.

---

## 📖 Project Overview

In today's world, energy consumption management plays a crucial role in reducing costs and environmental impact. This platform provides a user-friendly interface to:

✔ Track energy usage in real-time  
✔ Visualize consumption patterns with interactive graphs  
✔ Analyze data using mathematical tools  
✔ Detect anomalies and unusual spikes (future implementation)  
✔ Integrate with IoT devices using MQTT and ThingsBoard  
✔ Generate reports and insights for better decision-making

This tool is designed for homeowners, engineers, researchers, and developers working on smart energy solutions.

---

## 🚀 Installation Guide

### Step 1 – Clone the Repository

```bash
git clone https://github.com/Ritesh-gupta1430/Energy-management-platform.git
cd Energy-management-platform
```

### Step 2 – Create a Virtual Environment
```bash
venv\Scripts\activate
```

**Activate the environment:**

**On Windows:**
```bash
venv\Scripts\activate
```


**On Linux/MacOS:**
```bash
source venv/bin/activate
```

### Step 3 – Upgrade pip and Install Packages
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4 – Run the Application
```bash
streamlit run app.py
```
The app will open in your default web browser at http://localhost:8500.



### 📡 ThingsBoard & MQTT Integration (Optional)

You can enhance this platform by connecting it with IoT devices:

**ThingsBoard Setup**:

1. Create an account on ThingsBoard
2. Create devices like home1, home2, etc.
3. Get the Access Tokens for each device.
4. Add telemetry data for energy usage.

**MQTT Setup:**
1. Use MQTT to send data from devices to ThingsBoard or directly to this platform.
2. Configure MQTT client settings within the app to match your broker setup.
Note: These integrations allow real-time data collection and visualization.

### ✅ Features
✔ Real-time energy monitoring (with simulated or actual data)<br> 
✔ Interactive charts and graphs using Streamlit<br>
✔ User-friendly interface requiring no frontend knowledge<br>
✔ Easily extendable with IoT devices and APIs<br>
✔ Supports multiple homes or devices<br>
✔ Customizable thresholds and alerts (future scope)<br>
✔ Simple installation and setup process<br>

### 🚧 Known Issues
✔ Python version compatibility issues may arise — ensure you're using Python 3.10 or newer<br>
✔ Installation errors may occur on older operating systems due to missing build tools<br>
✔ IoT integration requires additional configuration and API tokens<br>
✔ Data upload validation is limited in the current version<br>

### 📦 Future Improvements
✔ Add user authentication and permissions<br>
✔ Implement machine learning for anomaly detection<br>
✔ Integrate with cloud storage and analytics platforms<br>
✔ Support automated alerts via email or SMS<br>
✔ Improve UI with advanced visualization tools<br>
✔ Enable role-based dashboards for multiple users<br>
