import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import threading

from config import THINGSBOARD_HOST, THINGSBOARD_PORT, THINGSBOARD_ACCESS_TOKEN, THINGSBOARD_USE_SSL

class ThingsBoardClient:
    def __init__(self, host: str = None, port: int = None, access_token: str = None, use_ssl: bool = None):
        self.host = host or THINGSBOARD_HOST
        self.port = port or THINGSBOARD_PORT
        self.access_token = access_token or THINGSBOARD_ACCESS_TOKEN
        self.use_ssl = use_ssl if use_ssl is not None else THINGSBOARD_USE_SSL
        
        # Construct base URL
        protocol = "https" if self.use_ssl else "http"
        self.base_url = f"{protocol}://{self.host}:{self.port}"
        self.api_url = f"{self.base_url}/api/v1"
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Connection status
        self.connected = False
        self.last_connection_check = None
        
        print(f"ThingsBoard client initialized for {self.base_url}")
    
    def check_connection(self) -> bool:
        """Check if connection to ThingsBoard is working"""
        # Cache connection check for 30 seconds
        if (self.last_connection_check and 
            datetime.now() - self.last_connection_check < timedelta(seconds=30)):
            return self.connected
        
        try:
            if not self.access_token:
                print("ThingsBoard access token not configured")
                self.connected = False
                return False
            
            # Test connection by sending a simple telemetry test
            url = f"{self.api_url}/{self.access_token}/telemetry"
            test_data = {"test_connection": True, "timestamp": int(datetime.now().timestamp() * 1000)}
            
            response = self.session.post(
                url, 
                data=json.dumps(test_data),
                timeout=5
            )
            
            self.connected = response.status_code == 200
            self.last_connection_check = datetime.now()
            
            if self.connected:
                print("ThingsBoard connection successful")
            else:
                print(f"ThingsBoard connection failed: HTTP {response.status_code} - {response.text}")
            
            return self.connected
            
        except requests.exceptions.RequestException as e:
            print(f"ThingsBoard connection error: {e}")
            self.connected = False
            self.last_connection_check = datetime.now()
            return False
    
    def send_telemetry(self, device_name: str, telemetry_data: Dict[str, Any]) -> bool:
        """Send telemetry data to ThingsBoard"""
        if not self.access_token:
            print("ThingsBoard access token not configured")
            return False
        
        try:
            # Prepare telemetry payload
            if 'timestamp' not in telemetry_data:
                telemetry_data['timestamp'] = int(datetime.now().timestamp() * 1000)
            elif isinstance(telemetry_data['timestamp'], str):
                # Convert ISO string to timestamp
                dt = datetime.fromisoformat(telemetry_data['timestamp'].replace('Z', '+00:00'))
                telemetry_data['timestamp'] = int(dt.timestamp() * 1000)
            
            # Add device identifier
            telemetry_data['device'] = device_name
            
            # Send to ThingsBoard telemetry endpoint
            url = f"{self.api_url}/{self.access_token}/telemetry"
            
            response = self.session.post(
                url,
                data=json.dumps(telemetry_data),
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Sent telemetry to ThingsBoard: {device_name} - {telemetry_data}")
                return True
            else:
                print(f"Failed to send telemetry to ThingsBoard: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending telemetry to ThingsBoard: {e}")
            return False
    
    def send_attributes(self, device_name: str, attributes: Dict[str, Any]) -> bool:
        """Send device attributes to ThingsBoard"""
        if not self.access_token:
            print("ThingsBoard access token not configured")
            return False
        
        try:
            # Add device identifier
            attributes['device'] = device_name
            
            # Send to ThingsBoard attributes endpoint
            url = f"{self.api_url}/{self.access_token}/attributes"
            
            response = self.session.post(
                url,
                data=json.dumps(attributes),
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Sent attributes to ThingsBoard: {device_name} - {attributes}")
                return True
            else:
                print(f"Failed to send attributes to ThingsBoard: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending attributes to ThingsBoard: {e}")
            return False
    
    def get_telemetry(self, keys: List[str] = None, start_ts: int = None, end_ts: int = None, limit: int = 100) -> Dict[str, List]:
        """Get telemetry data from ThingsBoard"""
        if not self.access_token:
            print("ThingsBoard access token not configured")
            return {}
        
        try:
            url = f"{self.api_url}/{self.access_token}/telemetry"
            params = {}
            
            if keys:
                params['keys'] = ','.join(keys)
            
            if start_ts:
                params['startTs'] = start_ts
            
            if end_ts:
                params['endTs'] = end_ts
            
            if limit:
                params['limit'] = limit
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved telemetry from ThingsBoard: {len(data) if isinstance(data, dict) else 0} keys")
                return data
            else:
                print(f"Failed to get telemetry from ThingsBoard: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting telemetry from ThingsBoard: {e}")
            return {}
    
    def get_latest_telemetry(self, keys: List[str] = None) -> Dict[str, Any]:
        """Get latest telemetry values from ThingsBoard"""
        if not self.access_token:
            print("ThingsBoard access token not configured")
            return {}
        
        try:
            url = f"{self.api_url}/{self.access_token}/telemetry"
            params = {}
            
            if keys:
                params['keys'] = ','.join(keys)
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract latest values
                latest_values = {}
                if isinstance(data, dict):
                    for key, values in data.items():
                        if values and isinstance(values, list) and len(values) > 0:
                            # Get the most recent value
                            latest_values[key] = values[0]['value']
                
                print(f"Retrieved latest telemetry from ThingsBoard: {latest_values}")
                return latest_values
            else:
                print(f"Failed to get latest telemetry from ThingsBoard: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting latest telemetry from ThingsBoard: {e}")
            return {}
    
    def get_attributes(self, client_keys: List[str] = None, server_keys: List[str] = None, shared_keys: List[str] = None) -> Dict[str, Any]:
        """Get device attributes from ThingsBoard"""
        if not self.access_token:
            print("ThingsBoard access token not configured")
            return {}
        
        try:
            url = f"{self.api_url}/{self.access_token}/attributes"
            params = {}
            
            if client_keys:
                params['clientKeys'] = ','.join(client_keys)
            
            if server_keys:
                params['serverKeys'] = ','.join(server_keys)
            
            if shared_keys:
                params['sharedKeys'] = ','.join(shared_keys)
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Retrieved attributes from ThingsBoard: {data}")
                return data
            else:
                print(f"Failed to get attributes from ThingsBoard: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting attributes from ThingsBoard: {e}")
            return {}
    
    def send_energy_consumption(self, device_name: str, consumption: float, timestamp: datetime = None) -> bool:
        """Send energy consumption data to ThingsBoard"""
        if timestamp is None:
            timestamp = datetime.now()
        
        telemetry_data = {
            'consumption': consumption,
            'energy': consumption,  # Alternative key name
            'timestamp': int(timestamp.timestamp() * 1000),
            'device_type': 'energy_meter',
            'unit': 'kWh'
        }
        
        return self.send_telemetry(device_name, telemetry_data)
    
    def get_energy_consumption_history(self, device_name: str = None, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get energy consumption history from ThingsBoard"""
        end_ts = int(datetime.now().timestamp() * 1000)
        start_ts = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
        
        # Get telemetry for energy consumption keys
        telemetry_keys = ['consumption', 'energy', 'power']
        telemetry_data = self.get_telemetry(
            keys=telemetry_keys,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=1000
        )
        
        # Process and format the data
        energy_history = []
        
        for key, values in telemetry_data.items():
            if key in telemetry_keys and values:
                for entry in values:
                    energy_history.append({
                        'device_name': device_name or 'unknown',
                        'consumption': entry.get('value', 0),
                        'timestamp': datetime.fromtimestamp(entry.get('ts', 0) / 1000),
                        'key': key
                    })
        
        # Sort by timestamp
        energy_history.sort(key=lambda x: x['timestamp'])
        
        return energy_history
    
    def sync_with_database(self, db_manager) -> bool:
        """Sync local database with ThingsBoard data"""
        try:
            print("Syncing data with ThingsBoard...")
            
            # Get recent energy data from ThingsBoard
            energy_history = self.get_energy_consumption_history(hours_back=24)
            
            if not energy_history:
                print("No energy history retrieved from ThingsBoard")
                return True
            
            # Add data to local database
            synced_count = 0
            for entry in energy_history:
                success = db_manager.add_energy_data(
                    device_name=entry['device_name'],
                    consumption=entry['consumption'],
                    timestamp=entry['timestamp'],
                    source='thingsboard'
                )
                
                if success:
                    synced_count += 1
            
            print(f"Synced {synced_count} records from ThingsBoard")
            return True
            
        except Exception as e:
            print(f"Error syncing with ThingsBoard: {e}")
            return False
    
    def send_device_status(self, device_name: str, status: str, metadata: Dict[str, Any] = None) -> bool:
        """Send device status as attributes to ThingsBoard"""
        attributes = {
            'status': status,
            'last_seen': datetime.now().isoformat(),
            'device_name': device_name
        }
        
        if metadata:
            attributes.update(metadata)
        
        return self.send_attributes(device_name, attributes)
    
    def get_dashboard_url(self, dashboard_id: str = None) -> str:
        """Get ThingsBoard dashboard URL"""
        if dashboard_id:
            return f"{self.base_url}/dashboard/{dashboard_id}"
        else:
            return f"{self.base_url}/dashboards"
    
    def create_alarm(self, alarm_type: str, severity: str, message: str, device_name: str = None) -> bool:
        """Create an alarm in ThingsBoard (if supported by the REST API)"""
        # Note: This might require additional ThingsBoard configuration
        # and may not be available in all ThingsBoard CE versions
        try:
            alarm_data = {
                'type': alarm_type,
                'severity': severity.upper(),
                'status': 'ACTIVE_UNACK',
                'details': {
                    'message': message,
                    'device': device_name or 'system',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # This would require authentication with ThingsBoard's main API
            # For now, we'll send it as telemetry with alarm prefix
            alarm_telemetry = {
                'alarm_type': alarm_type,
                'alarm_severity': severity,
                'alarm_message': message,
                'alarm_timestamp': datetime.now().isoformat(),
                'alarm_status': 'ACTIVE'
            }
            
            return self.send_telemetry(device_name or 'system', alarm_telemetry)
            
        except Exception as e:
            print(f"Error creating alarm in ThingsBoard: {e}")
            return False
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session'):
            self.session.close()
