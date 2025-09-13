# #!/usr/bin/env python3
# import json
# import time
# import random
# import threading
# import schedule
# from datetime import datetime, timedelta
# from typing import Dict, List, Any
# import paho.mqtt.client as mqtt
# import requests
#
# from config import THINGSBOARD_HOST, THINGSBOARD_ACCESS_TOKEN, THINGSBOARD_USE_SSL
#
# class EnergyDeviceSimulator:
#     """Simulates realistic energy consumption patterns for home devices"""
#
#     DEVICE_PROFILES = {
#         "Smart Fridge": {
#             "base_consumption": 0.15,  # kWh per hour baseline
#             "peak_multiplier": 1.8,    # Peak usage multiplier
#             "peak_hours": [7, 8, 18, 19, 20],  # Peak usage hours
#             "variance": 0.05,          # Random variance
#             "seasonal_factor": 1.1     # Winter usage increase
#         },
#         "HVAC System": {
#             "base_consumption": 2.5,
#             "peak_multiplier": 3.0,
#             "peak_hours": [6, 7, 8, 17, 18, 19, 20, 21],
#             "variance": 0.3,
#             "seasonal_factor": 2.0
#         },
#         "Water Heater": {
#             "base_consumption": 0.8,
#             "peak_multiplier": 2.2,
#             "peak_hours": [6, 7, 18, 19, 21, 22],
#             "variance": 0.15,
#             "seasonal_factor": 1.2
#         },
#         "Washing Machine": {
#             "base_consumption": 0.05,
#             "peak_multiplier": 4.0,
#             "peak_hours": [9, 10, 15, 16, 19],
#             "variance": 0.8,  # High variance for on/off cycles
#             "seasonal_factor": 1.0
#         },
#         "Living Room TV": {
#             "base_consumption": 0.08,
#             "peak_multiplier": 1.5,
#             "peak_hours": [18, 19, 20, 21, 22, 23],
#             "variance": 0.1,
#             "seasonal_factor": 1.1
#         },
#         "Kitchen Appliances": {
#             "base_consumption": 0.12,
#             "peak_multiplier": 2.5,
#             "peak_hours": [7, 8, 12, 13, 18, 19, 20],
#             "variance": 0.2,
#             "seasonal_factor": 1.0
#         },
#         "Home Office": {
#             "base_consumption": 0.25,
#             "peak_multiplier": 1.8,
#             "peak_hours": [8, 9, 10, 11, 13, 14, 15, 16, 17],
#             "variance": 0.1,
#             "seasonal_factor": 0.9
#         },
#         "Lighting System": {
#             "base_consumption": 0.06,
#             "peak_multiplier": 2.0,
#             "peak_hours": [6, 7, 8, 17, 18, 19, 20, 21, 22, 23],
#             "variance": 0.05,
#             "seasonal_factor": 1.3  # More lighting in winter
#         }
#     }
#
#     def __init__(self, device_name: str, access_token: str):
#         self.device_name = device_name
#         self.access_token = access_token
#         self.profile = self.DEVICE_PROFILES.get(device_name, self.DEVICE_PROFILES["Kitchen Appliances"])
#
#         # ThingsBoard connection settings
#         protocol = "https" if THINGSBOARD_USE_SSL else "http"
#         port = 443 if THINGSBOARD_USE_SSL else 80
#         self.base_url = f"{protocol}://{THINGSBOARD_HOST}:{port}"
#         self.telemetry_url = f"{self.base_url}/api/v1/{access_token}/telemetry"
#
#         # MQTT settings for alternative connection
#         self.mqtt_client = mqtt.Client()
#         self.mqtt_client.username_pw_set(access_token)
#         self.mqtt_client.connect(THINGSBOARD_HOST, 1883, 60)
#         self.mqtt_client.loop_start()
#
#         # Simulation state
#         self.is_running = False
#         self.last_consumption = 0.0
#         self.daily_total = 0.0
#         self.simulation_start = datetime.now()
#
#         print(f"Initialized {device_name} simulator")
#
#     def calculate_realistic_consumption(self) -> float:
#         """Calculate realistic energy consumption based on time and device profile"""
#         now = datetime.now()
#         hour = now.hour
#
#         # Base consumption
#         consumption = self.profile["base_consumption"]
#
#         # Peak hour adjustments
#         if hour in self.profile["peak_hours"]:
#             consumption *= self.profile["peak_multiplier"]
#
#         # Weekly patterns (weekends different)
#         if now.weekday() >= 5:  # Weekend
#             if "HVAC" in self.device_name or "Living Room" in self.device_name:
#                 consumption *= 1.2  # More home usage on weekends
#         else:  # Weekday
#             if "Home Office" in self.device_name and 9 <= hour <= 17:
#                 consumption *= 1.3  # Office hours
#
#         # Seasonal adjustments (assuming winter = higher consumption)
#         month = now.month
#         if month in [12, 1, 2]:  # Winter months
#             consumption *= self.profile["seasonal_factor"]
#         elif month in [6, 7, 8]:  # Summer months (AC usage)
#             if "HVAC" in self.device_name:
#                 consumption *= 1.5
#
#         # Random variance
#         variance = random.uniform(-self.profile["variance"], self.profile["variance"])
#         consumption = max(0, consumption * (1 + variance))
#
#         # Special device behaviors
#         if "Washing Machine" in self.device_name:
#             # Simulate washing cycles (2-3 hour cycles)
#             if random.random() < 0.1:  # 10% chance of cycle starting
#                 consumption *= 4.0
#             elif self.last_consumption > self.profile["base_consumption"] * 2:
#                 # Continue cycle for next hour
#                 consumption = self.last_consumption * random.uniform(0.8, 1.1)
#
#         return round(consumption, 3)
#
#     def generate_telemetry_data(self) -> Dict[str, Any]:
#         """Generate comprehensive telemetry data"""
#         consumption = self.calculate_realistic_consumption()
#         self.last_consumption = consumption
#         self.daily_total += consumption
#
#         # Reset daily total at midnight
#         if datetime.now().hour == 0 and datetime.now().minute < 5:
#             self.daily_total = 0.0
#
#         return {
#             "consumption": consumption,
#             "energy": consumption,  # Alternative key
#             "power": consumption * 1000,  # Convert to watts
#             "timestamp": int(datetime.now().timestamp() * 1000),
#             "device_type": "energy_meter",
#             "device_name": self.device_name,
#             "unit": "kWh",
#             "daily_total": round(self.daily_total, 3),
#             "status": "online",
#             "location": self._get_device_location(),
#             "efficiency_rating": random.uniform(0.8, 1.0),
#             "temperature": random.uniform(18, 24),  # Ambient temperature
#             "voltage": random.uniform(220, 240),    # Line voltage
#             "current": round(consumption * 1000 / 230, 2),  # Calculated current
#             "power_factor": random.uniform(0.85, 0.95)
#         }
#
#     def _get_device_location(self) -> str:
#         """Map device names to typical home locations"""
#         location_map = {
#             "Smart Fridge": "Kitchen",
#             "HVAC System": "Basement",
#             "Water Heater": "Basement",
#             "Washing Machine": "Laundry Room",
#             "Living Room TV": "Living Room",
#             "Kitchen Appliances": "Kitchen",
#             "Home Office": "Office",
#             "Lighting System": "General"
#         }
#         return location_map.get(self.device_name, "Unknown")
#
#     def send_to_thingsboard_http(self, data: Dict[str, Any]) -> bool:
#         """Send data to ThingsBoard via HTTP API"""
#         try:
#             headers = {
#                 'Content-Type': 'application/json',
#                 'Accept': 'application/json'
#             }
#
#             response = requests.post(
#                 self.telemetry_url,
#                 data=json.dumps(data),
#                 headers=headers,
#                 timeout=10
#             )
#
#             if response.status_code == 200:
#                 print(f"[{self.device_name}] HTTP: Sent {data['consumption']} kWh")
#                 return True
#             else:
#                 print(f"[{self.device_name}] HTTP Error: {response.status_code}")
#                 return False
#
#         except Exception as e:
#             print(f"[{self.device_name}] HTTP Exception: {e}")
#             return False
#
#     def send_to_thingsboard_mqtt(self, data: Dict[str, Any]) -> bool:
#         """Send data to ThingsBoard via MQTT"""
#         # try:
#         #     # Connect if not connected
#         #     if not self.mqtt_client.is_connected():
#         #         self.mqtt_client.connect(THINGSBOARD_HOST, 1883, 60)
#         #
#         #     # Publish telemetry
#         #     topic = "v1/devices/me/telemetry"
#         #     payload = json.dumps(data)
#         #
#         #     result = self.mqtt_client.publish(topic, payload)
#         #
#         #     if result.rc == 0:
#         #         print(f"[{self.device_name}] MQTT: Sent {data['consumption']} kWh")
#         #         return True
#         #     else:
#         #         print(f"[{self.device_name}] MQTT Error: {result.rc}")
#         #         return False
#         #
#         # except Exception as e:
#         #     print(f"[{self.device_name}] MQTT Exception: {e}")
#         #     return False
#         try:
#             topic = "v1/devices/me/telemetry"
#             payload = json.dumps(data)
#             result = self.mqtt_client.publish(topic, payload)
#
#             if result.rc == 0:
#                 print(f"[{self.device_name}] MQTT: Sent {data['consumption']} kWh")
#                 return True
#             else:
#                 print(f"[{self.device_name}] MQTT Error: {result.rc}")
#                 return False
#
#         except Exception as e:
#             print(f"[{self.device_name}] MQTT Exception: {e}")
#             return False
#
#
#
#     def simulate_data_point(self):
#         """Generate and send a single data point"""
#         data = self.generate_telemetry_data()
#         success = self.send_to_thingsboard_http(data)
#         if not success:
#             success = self.send_to_thingsboard_mqtt(data)
#
#         return success
#
#     def start_simulation(self, interval_seconds: int = 60):
#         """Start continuous simulation"""
#         self.is_running = True
#
#         def simulation_loop():
#             while self.is_running:
#                 try:
#                     self.simulate_data_point()
#                     time.sleep(interval_seconds)
#                 except KeyboardInterrupt:
#                     print(f"[{self.device_name}] Simulation stopped by user")
#                     break
#                 except Exception as e:
#                     print(f"[{self.device_name}] Error in simulation: {e}")
#                     time.sleep(5)  # Wait before retrying
#
#         # Run simulation in separate thread
#         thread = threading.Thread(target=simulation_loop, daemon=True)
#         thread.start()
#
#         print(f"[{self.device_name}] Simulation started (interval: {interval_seconds}s)")
#         return thread
#
#     def stop_simulation(self):
#         self.is_running = False
#         if self.mqtt_client.is_connected():
#             self.mqtt_client.loop_stop()
#             self.mqtt_client.disconnect()
#         print(f"[{self.device_name}] Simulation stopped")
#
#         # """Stop the simulation"""
#         # self.is_running = False
#         # if self.mqtt_client.is_connected():
#         #     self.mqtt_client.disconnect()
#         # print(f"[{self.device_name}] Simulation stopped")
#
# class MultiDeviceSimulator:
#     """Manages multiple device simulators"""
#
#     def __init__(self):
#         self.simulators = []
#         self.devices_config = {}
#
#     def add_device(self, device_name: str, access_token: str):
#         """Add a device to simulation"""
#         simulator = EnergyDeviceSimulator(device_name, access_token)
#         self.simulators.append(simulator)
#         self.devices_config[device_name] = access_token
#         return simulator
#
#     def start_all_simulations(self, interval_seconds: int = 60):
#         """Start simulation for all devices"""
#         threads = []
#         for simulator in self.simulators:
#             thread = simulator.start_simulation(interval_seconds)
#             threads.append(thread)
#
#         print(f"Started simulation for {len(self.simulators)} devices")
#         return threads
#
#     def stop_all_simulations(self):
#         """Stop all simulations"""
#         for simulator in self.simulators:
#             simulator.stop_simulation()
#
#     def generate_batch_historical_data(self, hours_back: int = 24):
#         """Generate historical data for all devices"""
#         print(f"Generating {hours_back} hours of historical data...")
#
#         end_time = datetime.now()
#         start_time = end_time - timedelta(hours=hours_back)
#
#         current_time = start_time
#
#         while current_time <= end_time:
#             for simulator in self.simulators:
#                 # Temporarily adjust time for realistic patterns
#                 original_time = datetime.now
#                 datetime.now = lambda: current_time
#
#                 # Generate and send data
#                 simulator.simulate_data_point()
#
#                 # Restore original time function
#                 datetime.now = original_time
#
#             current_time += timedelta(minutes=15)  # 15-minute intervals
#             time.sleep(0.1)  # Small delay to avoid rate limiting
#
#         print("Historical data generation completed")
#
# # Main execution
# if __name__ == "__main__":
#     print("Energy Device Hardware Simulator")
#     print("=" * 50)
#
#     # Check if access token is configured
#     if not THINGSBOARD_ACCESS_TOKEN:
#         print("ERROR: THINGSBOARD_ACCESS_TOKEN not configured")
#         print("Please set your ThingsBoard device access token in environment variables")
#         exit(1)
#
#     # Create multi-device simulator
#     simulator_manager = MultiDeviceSimulator()
#
#     # Add common home devices (using same token for demo)
#     devices = [
#         "Smart Fridge",
#         "HVAC System",
#         "Water Heater",
#         "Washing Machine",
#         "Living Room TV",
#         "Kitchen Appliances",
#         "Home Office",
#         "Lighting System"
#     ]
#
#     for device in devices:
#         simulator_manager.add_device(device, THINGSBOARD_ACCESS_TOKEN)
#
#     # Generate some historical data first
#     print("Generating historical data...")
#     simulator_manager.generate_batch_historical_data(hours_back=48)
#
#     # Start real-time simulation
#     print("Starting real-time simulation...")
#     threads = simulator_manager.start_all_simulations(interval_seconds=30)  # Every 30 seconds
#
#     try:
#         # Keep simulation running
#         while True:
#             time.sleep(60)
#             print(f"Simulation running... ({datetime.now()})")
#
#     except KeyboardInterrupt:
#         print("\nStopping all simulations...")
#         simulator_manager.stop_all_simulations()
#         print("Simulation stopped.")





#!/usr/bin/env python3
import json
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
import paho.mqtt.client as mqtt
import requests

from config import THINGSBOARD_HOST, THINGSBOARD_ACCESS_TOKEN, THINGSBOARD_USE_SSL

class EnergyDeviceSimulator:
    """Simulates realistic energy consumption patterns for home devices"""

    DEVICE_PROFILES = {
        "Smart Fridge": {"base_consumption": 0.15, "peak_multiplier": 1.8, "peak_hours": [7, 8, 18, 19, 20], "variance": 0.05, "seasonal_factor": 1.1},
        "HVAC System": {"base_consumption": 2.5, "peak_multiplier": 3.0, "peak_hours": [6, 7, 8, 17, 18, 19, 20, 21], "variance": 0.3, "seasonal_factor": 2.0},
        "Water Heater": {"base_consumption": 0.8, "peak_multiplier": 2.2, "peak_hours": [6, 7, 18, 19, 21, 22], "variance": 0.15, "seasonal_factor": 1.2},
        "Washing Machine": {"base_consumption": 0.05, "peak_multiplier": 4.0, "peak_hours": [9, 10, 15, 16, 19], "variance": 0.8, "seasonal_factor": 1.0},
        "Living Room TV": {"base_consumption": 0.08, "peak_multiplier": 1.5, "peak_hours": [18, 19, 20, 21, 22, 23], "variance": 0.1, "seasonal_factor": 1.1},
        "Kitchen Appliances": {"base_consumption": 0.12, "peak_multiplier": 2.5, "peak_hours": [7, 8, 12, 13, 18, 19, 20], "variance": 0.2, "seasonal_factor": 1.0},
        "Home Office": {"base_consumption": 0.25, "peak_multiplier": 1.8, "peak_hours": [8, 9, 10, 11, 13, 14, 15, 16, 17], "variance": 0.1, "seasonal_factor": 0.9},
        "Lighting System": {"base_consumption": 0.06, "peak_multiplier": 2.0, "peak_hours": [6, 7, 8, 17, 18, 19, 20, 21, 22, 23], "variance": 0.05, "seasonal_factor": 1.3}
    }

    def __init__(self, device_name: str, access_token: str):
        self.device_name = device_name
        self.access_token = access_token
        self.profile = self.DEVICE_PROFILES.get(device_name, self.DEVICE_PROFILES["Kitchen Appliances"])

        protocol = "https" if THINGSBOARD_USE_SSL else "http"
        port = 443 if THINGSBOARD_USE_SSL else 80
        self.base_url = f"{protocol}://{THINGSBOARD_HOST}:{port}"
        self.telemetry_url = f"{self.base_url}/api/v1/{access_token}/telemetry"

        # MQTT client setup
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(access_token)
        self.mqtt_client.connect(THINGSBOARD_HOST, 1883, 60)
        self.mqtt_client.loop_start()

        self.is_running = False
        self.last_consumption = 0.0
        self.daily_total = 0.0
        self.simulation_start = datetime.now()

        print(f"Initialized {device_name} simulator")

    def calculate_realistic_consumption(self) -> float:
        now = datetime.now()
        hour = now.hour

        consumption = self.profile["base_consumption"]
        if hour in self.profile["peak_hours"]:
            consumption *= self.profile["peak_multiplier"]

        if now.weekday() >= 5:
            if "HVAC" in self.device_name or "Living Room" in self.device_name:
                consumption *= 1.2
        else:
            if "Home Office" in self.device_name and 9 <= hour <= 17:
                consumption *= 1.3

        month = now.month
        if month in [12, 1, 2]:
            consumption *= self.profile["seasonal_factor"]
        elif month in [6, 7, 8]:
            if "HVAC" in self.device_name:
                consumption *= 1.5

        variance = random.uniform(-self.profile["variance"], self.profile["variance"])
        consumption = max(0, consumption * (1 + variance))

        if "Washing Machine" in self.device_name:
            if random.random() < 0.1:
                consumption *= 4.0
            elif self.last_consumption > self.profile["base_consumption"] * 2:
                consumption = self.last_consumption * random.uniform(0.8, 1.1)

        return round(consumption, 3)

    def generate_telemetry_data(self) -> Dict[str, Any]:
        consumption = self.calculate_realistic_consumption()
        self.last_consumption = consumption
        self.daily_total += consumption

        if datetime.now().hour == 0 and datetime.now().minute < 5:
            self.daily_total = 0.0

        return {
            "consumption": consumption,
            "energy": consumption,
            "power": consumption * 1000,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "device_type": "energy_meter",
            "device_name": self.device_name,
            "unit": "kWh",
            "daily_total": round(self.daily_total, 3),
            "status": "online",
            "location": self._get_device_location(),
            "efficiency_rating": random.uniform(0.8, 1.0),
            "temperature": random.uniform(18, 24),
            "voltage": random.uniform(220, 240),
            "current": round(consumption * 1000 / 230, 2),
            "power_factor": random.uniform(0.85, 0.95)
        }

    def _get_device_location(self) -> str:
        location_map = {
            "Smart Fridge": "Kitchen",
            "HVAC System": "Basement",
            "Water Heater": "Basement",
            "Washing Machine": "Laundry Room",
            "Living Room TV": "Living Room",
            "Kitchen Appliances": "Kitchen",
            "Home Office": "Office",
            "Lighting System": "General"
        }
        return location_map.get(self.device_name, "Unknown")

    def send_to_thingsboard_http(self, data: Dict[str, Any]) -> bool:
        try:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            response = requests.post(self.telemetry_url, data=json.dumps(data), headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"[{self.device_name}] HTTP: Sent {data['consumption']} kWh")
                return True
            else:
                print(f"[{self.device_name}] HTTP Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{self.device_name}] HTTP Exception: {e}")
            return False

    def send_to_thingsboard_mqtt(self, data: Dict[str, Any]) -> bool:
        try:
            topic = "v1/devices/me/telemetry"
            payload = json.dumps(data)
            result = self.mqtt_client.publish(topic, payload)
            if result.rc == 0:
                print(f"[{self.device_name}] MQTT: Sent {data['consumption']} kWh")
                return True
            else:
                print(f"[{self.device_name}] MQTT Error: {result.rc}")
                return False
        except Exception as e:
            print(f"[{self.device_name}] MQTT Exception: {e}")
            return False

    def simulate_data_point(self):
        data = self.generate_telemetry_data()
        success = self.send_to_thingsboard_http(data)
        if not success:
            success = self.send_to_thingsboard_mqtt(data)
        return success

    def start_simulation(self, interval_seconds=60):
        self.is_running = True

        def simulation_loop():
            while self.is_running:
                try:
                    self.simulate_data_point()
                    time.sleep(interval_seconds)
                except KeyboardInterrupt:
                    print(f"[{self.device_name}] Simulation stopped by user")
                    break
                except Exception as e:
                    print(f"[{self.device_name}] Error in simulation: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=simulation_loop, daemon=True)
        thread.start()
        print(f"[{self.device_name}] Simulation started (interval: {interval_seconds}s)")
        return thread

    def stop_simulation(self):
        self.is_running = False
        if self.mqtt_client.is_connected():
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        print(f"[{self.device_name}] Simulation stopped")

class MultiDeviceSimulator:
    def __init__(self):
        self.simulators = []
        self.devices_config = {}

    def add_device(self, device_name: str, access_token: str):
        simulator = EnergyDeviceSimulator(device_name, access_token)
        self.simulators.append(simulator)
        self.devices_config[device_name] = access_token
        return simulator

    def start_all_simulations(self, interval_seconds=60):
        threads = []
        for simulator in self.simulators:
            threads.append(simulator.start_simulation(interval_seconds))
        print(f"Started simulation for {len(self.simulators)} devices")
        return threads

    def stop_all_simulations(self):
        for simulator in self.simulators:
            simulator.stop_simulation()

    def generate_batch_historical_data(self, hours_back=24):
        print(f"Generating {hours_back} hours of historical data...")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        current_time = start_time
        while current_time <= end_time:
            for simulator in self.simulators:
                original_datetime_now = datetime.now
                datetime.now = lambda: current_time
                simulator.simulate_data_point()
                datetime.now = original_datetime_now
            current_time += timedelta(minutes=15)
            time.sleep(0.1)
        print("Historical data generation completed")

if __name__ == "__main__":
    print("Energy Device Hardware Simulator")
    print("=" * 50)

    if not THINGSBOARD_ACCESS_TOKEN:
        print("ERROR: THINGSBOARD_ACCESS_TOKEN not configured")
        exit(1)

    simulator_manager = MultiDeviceSimulator()

    devices = [
        "Smart Fridge",
        "HVAC System",
        "Water Heater",
        "Washing Machine",
        "Living Room TV",
        "Kitchen Appliances",
        "Home Office",
        "Lighting System"
    ]

    for device in devices:
        simulator_manager.add_device(device, THINGSBOARD_ACCESS_TOKEN)

    print("Generating historical data...")
    simulator_manager.generate_batch_historical_data(hours_back=48)

    print("Starting real-time simulation...")
    threads = simulator_manager.start_all_simulations(interval_seconds=30)

    try:
        while True:
            time.sleep(60)
            print(f"Simulation running... ({datetime.now()})")
    except KeyboardInterrupt:
        print("\nStopping all simulations...")
        simulator_manager.stop_all_simulations()
        print("Simulation stopped.")
