#!/usr/bin/env python3
"""
ThingsBoard Sync Service
Pulls telemetry data from ThingsBoard and syncs with local database
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import pandas as pd

from database import DatabaseManager
from thingsboard_client import ThingsBoardClient
from config import THINGSBOARD_HOST, THINGSBOARD_ACCESS_TOKEN, THINGSBOARD_USE_SSL

class ThingsBoardSyncService:
    """Service to sync data from ThingsBoard to local database"""
    
    def __init__(self, db_manager: DatabaseManager, tb_client: ThingsBoardClient = None):
        self.db_manager = db_manager
        self.tb_client = tb_client or ThingsBoardClient()
        
        # Device mapping (local name -> ThingsBoard device info)
        self.device_mapping = {
            "Smart Fridge": {"tb_device_id": "fridge_sensor", "keys": ["consumption", "energy", "power"]},
            "HVAC System": {"tb_device_id": "hvac_sensor", "keys": ["consumption", "energy", "power"]},
            "Water Heater": {"tb_device_id": "water_heater", "keys": ["consumption", "energy", "power"]},
            "Washing Machine": {"tb_device_id": "washer_sensor", "keys": ["consumption", "energy", "power"]},
            "Living Room TV": {"tb_device_id": "tv_sensor", "keys": ["consumption", "energy", "power"]},
            "Kitchen Appliances": {"tb_device_id": "kitchen_sensor", "keys": ["consumption", "energy", "power"]},
            "Home Office": {"tb_device_id": "office_sensor", "keys": ["consumption", "energy", "power"]},
            "Lighting System": {"tb_device_id": "lights_sensor", "keys": ["consumption", "energy", "power"]}
        }
        
        self.sync_running = False
        self.last_sync_time = None
        self.sync_thread = None
        
        print("ThingsBoard Sync Service initialized")
    
    def get_latest_telemetry_data(self, hours_back: int = 2) -> List[Dict[str, Any]]:
        """Fetch latest telemetry data from ThingsBoard"""
        try:
            end_ts = int(datetime.now().timestamp() * 1000)
            start_ts = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)
            
            # Get telemetry data using the client
            telemetry_data = self.tb_client.get_telemetry(
                keys=['consumption', 'energy', 'power', 'device_name', 'device'],
                start_ts=start_ts,
                end_ts=end_ts,
                limit=500
            )
            
            # Process and normalize the data
            processed_data = []
            
            for key, values in telemetry_data.items():
                if key in ['consumption', 'energy', 'power'] and values:
                    for entry in values:
                        try:
                            # Extract timestamp and value
                            timestamp_ms = entry.get('ts', 0)
                            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                            value = float(entry.get('value', 0))
                            
                            # Try to identify device from telemetry
                            device_name = 'Unknown Device'
                            
                            # Look for device information in the data
                            for device_key, device_values in telemetry_data.items():
                                if device_key in ['device_name', 'device']:
                                    for device_entry in device_values:
                                        if device_entry.get('ts') == timestamp_ms:
                                            device_name = str(device_entry.get('value', 'Unknown Device'))
                                            break
                            
                            processed_data.append({
                                'device_name': device_name,
                                'consumption': value if key == 'consumption' else value / 1000,  # Convert power to kWh estimate
                                'timestamp': timestamp,
                                'source': 'thingsboard',
                                'raw_key': key,
                                'raw_value': value
                            })
                            
                        except (ValueError, TypeError) as e:
                            print(f"Error processing telemetry entry {entry}: {e}")
                            continue
            
            print(f"Retrieved {len(processed_data)} data points from ThingsBoard")
            return processed_data
            
        except Exception as e:
            print(f"Error fetching telemetry data: {e}")
            return []
    
    def sync_to_local_database(self, data: List[Dict[str, Any]]) -> int:
        """Sync telemetry data to local database"""
        synced_count = 0
        duplicate_count = 0
        
        for entry in data:
            try:
                # Check if entry already exists (avoid duplicates)
                existing_data = self.db_manager.get_recent_energy_data(hours=1)
                
                duplicate = False
                if not existing_data.empty:
                    for _, row in existing_data.iterrows():
                        if (row['device_name'] == entry['device_name'] and 
                            abs((pd.to_datetime(row['timestamp']) - entry['timestamp']).total_seconds()) < 60):
                            duplicate = True
                            duplicate_count += 1
                            break
                
                if not duplicate:
                    success = self.db_manager.add_energy_data(
                        device_name=entry['device_name'],
                        consumption=entry['consumption'],
                        timestamp=entry['timestamp'],
                        source='thingsboard'
                    )
                    
                    if success:
                        synced_count += 1
                        
            except Exception as e:
                print(f"Error syncing entry {entry}: {e}")
                continue
        
        print(f"Synced {synced_count} new records, skipped {duplicate_count} duplicates")
        return synced_count
    
    def perform_sync(self) -> Dict[str, Any]:
        """Perform a complete sync operation"""
        sync_start = datetime.now()
        
        try:
            # Check ThingsBoard connection
            if not self.tb_client.check_connection():
                return {
                    'success': False,
                    'error': 'ThingsBoard connection failed',
                    'synced_count': 0,
                    'duration_seconds': 0
                }
            
            # Fetch latest data
            telemetry_data = self.get_latest_telemetry_data(hours_back=2)
            
            if not telemetry_data:
                return {
                    'success': True,
                    'message': 'No new data to sync',
                    'synced_count': 0,
                    'duration_seconds': (datetime.now() - sync_start).total_seconds()
                }
            
            # Sync to local database
            synced_count = self.sync_to_local_database(telemetry_data)
            
            duration = (datetime.now() - sync_start).total_seconds()
            self.last_sync_time = sync_start
            
            return {
                'success': True,
                'synced_count': synced_count,
                'total_fetched': len(telemetry_data),
                'duration_seconds': round(duration, 2),
                'last_sync': sync_start.isoformat()
            }
            
        except Exception as e:
            print(f"Error during sync operation: {e}")
            return {
                'success': False,
                'error': str(e),
                'synced_count': 0,
                'duration_seconds': (datetime.now() - sync_start).total_seconds()
            }
    
    def start_periodic_sync(self, interval_minutes: int = 5):
        """Start periodic background sync"""
        self.sync_running = True
        
        def sync_loop():
            while self.sync_running:
                try:
                    print(f"Starting ThingsBoard sync... ({datetime.now()})")
                    result = self.perform_sync()
                    
                    if result['success']:
                        print(f"Sync completed: {result['synced_count']} records in {result['duration_seconds']}s")
                    else:
                        print(f"Sync failed: {result.get('error', 'Unknown error')}")
                    
                    # Wait for next sync
                    time.sleep(interval_minutes * 60)
                    
                except Exception as e:
                    print(f"Error in sync loop: {e}")
                    time.sleep(30)  # Wait before retrying
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        
        print(f"Started periodic ThingsBoard sync (interval: {interval_minutes} minutes)")
    
    def stop_periodic_sync(self):
        """Stop periodic sync"""
        self.sync_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        print("Stopped ThingsBoard periodic sync")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            'sync_running': self.sync_running,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'tb_connected': self.tb_client.check_connection(),
            'device_mappings': len(self.device_mapping)
        }
    
    def update_device_mapping(self, local_device_name: str, tb_device_id: str, telemetry_keys: List[str]):
        """Update device mapping configuration"""
        self.device_mapping[local_device_name] = {
            'tb_device_id': tb_device_id,
            'keys': telemetry_keys
        }
        print(f"Updated device mapping: {local_device_name} -> {tb_device_id}")

# Usage example and testing
if __name__ == "__main__":
    print("ThingsBoard Sync Service Test")
    print("=" * 40)
    
    # Initialize components
    db_manager = DatabaseManager()
    tb_client = ThingsBoardClient()
    sync_service = ThingsBoardSyncService(db_manager, tb_client)
    
    # Test single sync
    print("Testing single sync operation...")
    result = sync_service.perform_sync()
    print(f"Sync result: {json.dumps(result, indent=2)}")
    
    # Test periodic sync (for demonstration)
    print("\nStarting periodic sync (press Ctrl+C to stop)...")
    sync_service.start_periodic_sync(interval_minutes=2)
    
    try:
        while True:
            time.sleep(10)
            status = sync_service.get_sync_status()
            print(f"Status: {json.dumps(status, indent=2)}")
            
    except KeyboardInterrupt:
        print("\nStopping sync service...")
        sync_service.stop_periodic_sync()
        print("Sync service stopped.")