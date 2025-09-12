import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

from config import ANOMALY_DETECTION_THRESHOLD, HIGH_USAGE_THRESHOLD
from database import DatabaseManager

class AnomalyDetector:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.threshold_multiplier = ANOMALY_DETECTION_THRESHOLD
        self.high_usage_threshold = HIGH_USAGE_THRESHOLD
    
    def detect_anomalies(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Detect anomalies in recent energy consumption data"""
        # Get recent energy data
        recent_data = self.db_manager.get_recent_energy_data(hours=hours_back * 7)  # Get more data for better baseline
        
        if recent_data.empty:
            return []
        
        anomalies = []
        
        # Statistical anomaly detection
        stat_anomalies = self._detect_statistical_anomalies(recent_data, hours_back)
        anomalies.extend(stat_anomalies)
        
        # High usage detection
        high_usage_anomalies = self._detect_high_usage(recent_data, hours_back)
        anomalies.extend(high_usage_anomalies)
        
        # Device-specific anomalies
        device_anomalies = self._detect_device_anomalies(recent_data, hours_back)
        anomalies.extend(device_anomalies)
        
        # Time-based pattern anomalies
        pattern_anomalies = self._detect_pattern_anomalies(recent_data, hours_back)
        anomalies.extend(pattern_anomalies)
        
        # Store anomalies in database
        for anomaly in anomalies:
            self.db_manager.add_anomaly(
                device_name=anomaly['device_name'],
                anomaly_type=anomaly['type'],
                message=anomaly['message'],
                timestamp=anomaly['timestamp'],
                severity=anomaly['severity']
            )
        
        return anomalies
    
    def _detect_statistical_anomalies(self, data: pd.DataFrame, hours_back: int) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        
        if len(data) < 10:  # Need minimum data points
            return anomalies
        
        # Get recent data for comparison
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_data = data[data['timestamp'] >= cutoff_time]
        
        # Z-score based anomaly detection
        try:
            # Group by device for device-specific analysis
            for device_name in data['device_name'].unique():
                device_data = data[data['device_name'] == device_name]
                recent_device_data = recent_data[recent_data['device_name'] == device_name]
                
                if len(device_data) < 10 or recent_device_data.empty:
                    continue
                
                # Calculate statistics from historical data
                mean_consumption = device_data['consumption'].mean()
                std_consumption = device_data['consumption'].std()
                
                if std_consumption == 0:  # Avoid division by zero
                    continue
                
                # Check recent data for anomalies
                for _, row in recent_device_data.iterrows():
                    z_score = abs((row['consumption'] - mean_consumption) / std_consumption)
                    
                    if z_score > self.threshold_multiplier:
                        severity = 'high' if z_score > self.threshold_multiplier * 1.5 else 'medium'
                        
                        anomalies.append({
                            'device_name': device_name,
                            'type': 'statistical_outlier',
                            'message': f"Unusual consumption detected: {row['consumption']:.2f} kWh (Z-score: {z_score:.2f})",
                            'timestamp': row['timestamp'],
                            'severity': severity,
                            'value': row['consumption'],
                            'expected': mean_consumption,
                            'z_score': z_score
                        })
        
        except Exception as e:
            print(f"Error in statistical anomaly detection: {e}")
        
        return anomalies
    
    def _detect_high_usage(self, data: pd.DataFrame, hours_back: int) -> List[Dict[str, Any]]:
        """Detect periods of unusually high energy usage"""
        anomalies = []
        
        # Get recent data
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_data = data[data['timestamp'] >= cutoff_time]
        
        # Check for high usage periods
        for _, row in recent_data.iterrows():
            if row['consumption'] > self.high_usage_threshold:
                severity = 'high' if row['consumption'] > self.high_usage_threshold * 2 else 'medium'
                
                anomalies.append({
                    'device_name': row['device_name'],
                    'type': 'high_usage',
                    'message': f"High energy usage detected: {row['consumption']:.2f} kWh (threshold: {self.high_usage_threshold} kWh)",
                    'timestamp': row['timestamp'],
                    'severity': severity,
                    'value': row['consumption'],
                    'threshold': self.high_usage_threshold
                })
        
        return anomalies
    
    def _detect_device_anomalies(self, data: pd.DataFrame, hours_back: int) -> List[Dict[str, Any]]:
        """Detect device-specific anomalies"""
        anomalies = []
        
        try:
            # Get recent data
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_data = data[data['timestamp'] >= cutoff_time]
            
            # Check for devices that haven't reported recently
            device_last_seen = data.groupby('device_name')['timestamp'].max()
            inactive_threshold = datetime.now() - timedelta(hours=2)  # 2 hours without data
            
            for device_name, last_seen in device_last_seen.items():
                if last_seen < inactive_threshold:
                    hours_inactive = (datetime.now() - last_seen).total_seconds() / 3600
                    
                    anomalies.append({
                        'device_name': device_name,
                        'type': 'device_inactive',
                        'message': f"Device hasn't reported data for {hours_inactive:.1f} hours",
                        'timestamp': datetime.now(),
                        'severity': 'medium',
                        'last_seen': last_seen
                    })
            
            # Check for sudden consumption drops (might indicate device failure)
            for device_name in recent_data['device_name'].unique():
                device_data = data[data['device_name'] == device_name].sort_values('timestamp')
                recent_device_data = recent_data[recent_data['device_name'] == device_name]
                
                if len(device_data) < 5 or recent_device_data.empty:
                    continue
                
                # Calculate recent average vs historical average
                historical_avg = device_data[device_data['timestamp'] < cutoff_time]['consumption'].mean()
                recent_avg = recent_device_data['consumption'].mean()
                
                if not pd.isna(historical_avg) and not pd.isna(recent_avg):
                    if recent_avg < historical_avg * 0.3 and historical_avg > 0.1:  # Significant drop
                        anomalies.append({
                            'device_name': device_name,
                            'type': 'consumption_drop',
                            'message': f"Significant consumption drop detected. Recent: {recent_avg:.2f} kWh, Historical: {historical_avg:.2f} kWh",
                            'timestamp': recent_device_data['timestamp'].iloc[-1],
                            'severity': 'medium',
                            'recent_avg': recent_avg,
                            'historical_avg': historical_avg
                        })
        
        except Exception as e:
            print(f"Error in device anomaly detection: {e}")
        
        return anomalies
    
    def _detect_pattern_anomalies(self, data: pd.DataFrame, hours_back: int) -> List[Dict[str, Any]]:
        """Detect anomalies in consumption patterns"""
        anomalies = []
        
        try:
            if len(data) < 24:  # Need at least 24 hours of data
                return anomalies
            
            # Get recent data
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_data = data[data['timestamp'] >= cutoff_time]
            historical_data = data[data['timestamp'] < cutoff_time]
            
            if recent_data.empty or historical_data.empty:
                return anomalies
            
            # Analyze hourly patterns
            recent_hourly = recent_data.groupby(recent_data['timestamp'].dt.hour)['consumption'].mean()
            historical_hourly = historical_data.groupby(historical_data['timestamp'].dt.hour)['consumption'].mean()
            
            # Find hours with significant pattern deviations
            for hour in recent_hourly.index:
                if hour in historical_hourly.index:
                    recent_val = recent_hourly[hour]
                    historical_val = historical_hourly[hour]
                    
                    if historical_val > 0:
                        ratio = recent_val / historical_val
                        
                        # Check for significant deviations
                        if ratio > 2.0 or ratio < 0.5:
                            severity = 'high' if ratio > 3.0 or ratio < 0.3 else 'medium'
                            
                            anomalies.append({
                                'device_name': 'system',
                                'type': 'pattern_deviation',
                                'message': f"Unusual consumption pattern at hour {hour}:00. Recent: {recent_val:.2f} kWh, Expected: {historical_val:.2f} kWh",
                                'timestamp': datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0),
                                'severity': severity,
                                'ratio': ratio,
                                'hour': hour
                            })
        
        except Exception as e:
            print(f"Error in pattern anomaly detection: {e}")
        
        return anomalies
    
    def _detect_ml_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using machine learning (Isolation Forest)"""
        anomalies = []
        
        try:
            if len(data) < 50:  # Need sufficient data for ML
                return anomalies
            
            # Prepare features
            features_data = data.copy()
            features_data['hour'] = features_data['timestamp'].dt.hour
            features_data['day_of_week'] = features_data['timestamp'].dt.dayofweek
            features_data['month'] = features_data['timestamp'].dt.month
            
            # Select numerical features
            feature_columns = ['consumption', 'hour', 'day_of_week', 'month']
            X = features_data[feature_columns]
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply Isolation Forest
            clf = IsolationForest(contamination=0.1, random_state=42)
            outliers = clf.fit_predict(X_scaled)
            
            # Get recent anomalies
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_mask = features_data['timestamp'] >= cutoff_time
            
            for idx, is_outlier in enumerate(outliers):
                if is_outlier == -1 and recent_mask.iloc[idx]:
                    row = features_data.iloc[idx]
                    
                    anomalies.append({
                        'device_name': row['device_name'],
                        'type': 'ml_anomaly',
                        'message': f"Machine learning model detected unusual consumption pattern: {row['consumption']:.2f} kWh",
                        'timestamp': row['timestamp'],
                        'severity': 'medium',
                        'value': row['consumption']
                    })
        
        except Exception as e:
            print(f"Error in ML anomaly detection: {e}")
        
        return anomalies
    
    def get_anomaly_summary(self, days_back: int = 7) -> Dict[str, Any]:
        """Get summary of recent anomalies"""
        recent_anomalies = self.db_manager.get_recent_anomalies(hours=days_back * 24)
        
        if recent_anomalies.empty:
            return {
                'total_anomalies': 0,
                'by_severity': {},
                'by_type': {},
                'devices_affected': []
            }
        
        return {
            'total_anomalies': len(recent_anomalies),
            'by_severity': recent_anomalies['severity'].value_counts().to_dict(),
            'by_type': recent_anomalies['anomaly_type'].value_counts().to_dict(),
            'devices_affected': recent_anomalies['device_name'].unique().tolist()
        }
