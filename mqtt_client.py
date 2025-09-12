import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from typing import Callable, Optional
import time

from config import *
from database import DatabaseManager

class MQTTClient:
    def __init__(self, host: str = None, port: int = None, username: str = None, password: str = None):
        self.host = host or MQTT_BROKER_HOST
        self.port = port or MQTT_BROKER_PORT
        self.username = username or MQTT_USERNAME
        self.password = password or MQTT_PASSWORD
        self.topic_prefix = MQTT_TOPIC_PREFIX
        
        self.client = mqtt.Client()
        self.connected = False
        self.db_manager = DatabaseManager()
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # Set credentials if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Start connection in a separate thread
        self.connect_thread = threading.Thread(target=self._connect_with_retry, daemon=True)
        self.connect_thread.start()
    
    def _connect_with_retry(self):
        """Connect to MQTT broker with retry logic"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries and not self.connected:
            try:
                print(f"Attempting to connect to MQTT broker at {self.host}:{self.port}")
                result = self.client.connect(self.host, self.port, 60)
                
                if result == 0:
                    self.client.loop_start()
                    break
                else:
                    print(f"MQTT connection failed with code {result}")
                    retry_count += 1
                    time.sleep(5 * retry_count)  # Exponential backoff
                    
            except Exception as e:
                print(f"MQTT connection error: {e}")
                retry_count += 1
                time.sleep(5 * retry_count)
        
        if retry_count >= max_retries:
            print("Failed to connect to MQTT broker after maximum retries")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            self.connected = True
            print("Connected to MQTT broker successfully")
            
            # Subscribe to energy topics
            topics = [
                f"{self.topic_prefix}/+/consumption",
                f"{self.topic_prefix}/+/status",
                f"{self.topic_prefix}/+/telemetry"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                print(f"Subscribed to topic: {topic}")
                
        else:
            self.connected = False
            print(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        self.connected = False
        print(f"Disconnected from MQTT broker with return code {rc}")
        
        # Try to reconnect
        if rc != 0:
            threading.Thread(target=self._connect_with_retry, daemon=True).start()
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic_parts = msg.topic.split('/')
            device_name = topic_parts[1] if len(topic_parts) > 1 else "unknown"
            message_type = topic_parts[2] if len(topic_parts) > 2 else "unknown"
            
            # Decode message payload
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except json.JSONDecodeError:
                # Try to parse as float for simple consumption values
                try:
                    payload = {"value": float(msg.payload.decode('utf-8'))}
                except ValueError:
                    print(f"Could not parse MQTT message payload: {msg.payload.decode('utf-8')}")
                    return
            
            print(f"Received MQTT message from {device_name}: {payload}")
            
            # Handle different message types
            if message_type == "consumption":
                self._handle_consumption_message(device_name, payload)
            elif message_type == "status":
                self._handle_status_message(device_name, payload)
            elif message_type == "telemetry":
                self._handle_telemetry_message(device_name, payload)
                
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def _handle_consumption_message(self, device_name: str, payload: dict):
        """Handle energy consumption messages"""
        try:
            # Extract consumption value
            consumption = payload.get('value') or payload.get('consumption') or payload.get('energy')
            
            if consumption is not None:
                timestamp = datetime.now()
                if 'timestamp' in payload:
                    try:
                        timestamp = datetime.fromisoformat(payload['timestamp'].replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # Store in database
                success = self.db_manager.add_energy_data(
                    device_name=device_name,
                    consumption=float(consumption),
                    timestamp=timestamp,
                    source='iot'
                )
                
                if success:
                    print(f"Stored energy data: {device_name} - {consumption} kWh")
                else:
                    print(f"Failed to store energy data for {device_name}")
                    
        except Exception as e:
            print(f"Error handling consumption message: {e}")
    
    def _handle_status_message(self, device_name: str, payload: dict):
        """Handle device status messages"""
        try:
            status = payload.get('status', 'unknown')
            print(f"Device {device_name} status: {status}")
            
            # Update device status in database could be implemented here
            
        except Exception as e:
            print(f"Error handling status message: {e}")
    
    def _handle_telemetry_message(self, device_name: str, payload: dict):
        """Handle general telemetry messages"""
        try:
            # Handle multiple telemetry values
            for key, value in payload.items():
                if key in ['consumption', 'energy', 'power']:
                    self._handle_consumption_message(device_name, {'value': value})
                    
        except Exception as e:
            print(f"Error handling telemetry message: {e}")
    
    def publish(self, topic: str, payload: dict) -> bool:
        """Publish a message to MQTT broker"""
        if not self.connected:
            print("MQTT client not connected")
            return False
        
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published to {topic}: {message}")
                return True
            else:
                print(f"Failed to publish to {topic}")
                return False
                
        except Exception as e:
            print(f"Error publishing MQTT message: {e}")
            return False
    
    def publish_consumption(self, device_name: str, consumption: float) -> bool:
        """Publish energy consumption data"""
        topic = f"{self.topic_prefix}/{device_name}/consumption"
        payload = {
            "consumption": consumption,
            "timestamp": datetime.now().isoformat(),
            "device": device_name
        }
        
        return self.publish(topic, payload)
    
    def is_connected(self) -> bool:
        """Check if client is connected to broker"""
        return self.connected
    
    def connect(self) -> bool:
        """Manually connect to MQTT broker"""
        try:
            result = self.client.connect(self.host, self.port, 60)
            if result == 0:
                self.client.loop_start()
                # Wait a bit for connection to establish
                time.sleep(1)
                return self.connected
            return False
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            print("Disconnected from MQTT broker")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.disconnect()
