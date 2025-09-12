import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import threading
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = "energy_tracker.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Energy data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS energy_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL,
                    consumption REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    source TEXT DEFAULT 'iot',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Device status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT UNIQUE NOT NULL,
                    device_type TEXT,
                    status TEXT DEFAULT 'offline',
                    last_seen DATETIME,
                    metadata TEXT
                )
            """)
            
            # AI recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    estimated_savings REAL,
                    category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    applied BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Anomalies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    total_points INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    achievements TEXT DEFAULT '[]',
                    preferences TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            """)
            
            # Points history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS points_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Challenges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    challenge_type TEXT NOT NULL,
                    target_value REAL NOT NULL,
                    reward_points INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # User challenge progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_challenge_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    challenge_id INTEGER NOT NULL,
                    current_value REAL DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    completed_at DATETIME,
                    FOREIGN KEY (challenge_id) REFERENCES challenges (id)
                )
            """)
            
            # Create indices for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_timestamp ON energy_data(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_energy_device ON energy_data(device_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(timestamp)")
            
            # Insert default user profile if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO user_profiles (username, email)
                VALUES ('default_user', 'user@example.com')
            """)
            
            # Insert sample challenges
            cursor.execute("""
                INSERT OR IGNORE INTO challenges (name, description, challenge_type, target_value, reward_points, start_date, end_date)
                VALUES 
                ('Energy Saver', 'Reduce daily consumption by 10%', 'consumption_reduction', 0.1, 100, date('now'), date('now', '+30 days')),
                ('Data Logger', 'Log energy data for 7 consecutive days', 'daily_logging', 7, 50, date('now'), date('now', '+30 days')),
                ('Early Bird', 'Check dashboard before 8 AM for 5 days', 'early_access', 5, 75, date('now'), date('now', '+30 days'))
            """)
            
            conn.commit()
            conn.close()
    
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def add_energy_data(self, device_name: str, consumption: float, timestamp: datetime = None, source: str = 'iot') -> bool:
        """Add energy consumption data"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO energy_data (device_name, consumption, timestamp, source)
                    VALUES (?, ?, ?, ?)
                """, (device_name, consumption, timestamp, source))
                
                # Update device status
                cursor.execute("""
                    INSERT OR REPLACE INTO devices (device_name, status, last_seen)
                    VALUES (?, 'online', ?)
                """, (device_name, timestamp))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error adding energy data: {e}")
            return False
    
    def get_recent_energy_data(self, hours: int = 24) -> pd.DataFrame:
        """Get recent energy data"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT device_name, consumption, timestamp, source
                    FROM energy_data
                    WHERE timestamp >= datetime('now', '-{} hours')
                    ORDER BY timestamp DESC
                """.format(hours)
                
                df = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
        except Exception as e:
            print(f"Error getting recent energy data: {e}")
            return pd.DataFrame()
    
    def get_energy_data_range(self, start_date, end_date) -> pd.DataFrame:
        """Get energy data for a date range"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT device_name, consumption, timestamp, source
                    FROM energy_data
                    WHERE date(timestamp) BETWEEN ? AND ?
                    ORDER BY timestamp
                """
                
                df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                conn.close()
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
        except Exception as e:
            print(f"Error getting energy data range: {e}")
            return pd.DataFrame()
    
    def get_device_status(self) -> pd.DataFrame:
        """Get status of all devices"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT device_name, status, last_seen
                    FROM devices
                    ORDER BY last_seen DESC
                """
                
                df = pd.read_sql_query(query, conn)
                conn.close()
                
                return df
        except Exception as e:
            print(f"Error getting device status: {e}")
            return pd.DataFrame()
    
    def get_manual_entries(self, limit: int = 10) -> pd.DataFrame:
        """Get recent manual entries"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT device_name, consumption, timestamp
                    FROM energy_data
                    WHERE source = 'manual'
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                conn.close()
                
                return df
        except Exception as e:
            print(f"Error getting manual entries: {e}")
            return pd.DataFrame()
    
    def add_recommendation(self, title: str, description: str, estimated_savings: float = None, category: str = None) -> bool:
        """Add AI recommendation"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO recommendations (title, description, estimated_savings, category)
                    VALUES (?, ?, ?, ?)
                """, (title, description, estimated_savings, category))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error adding recommendation: {e}")
            return False
    
    def get_recent_recommendations(self, limit: int = 10) -> pd.DataFrame:
        """Get recent recommendations"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT title, description, estimated_savings, category, created_at
                    FROM recommendations
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                conn.close()
                
                return df
        except Exception as e:
            print(f"Error getting recent recommendations: {e}")
            return pd.DataFrame()
    
    def add_anomaly(self, device_name: str, anomaly_type: str, message: str, timestamp: datetime = None, severity: str = 'medium') -> bool:
        """Add anomaly detection result"""
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO anomalies (device_name, anomaly_type, message, timestamp, severity)
                    VALUES (?, ?, ?, ?, ?)
                """, (device_name, anomaly_type, message, timestamp, severity))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error adding anomaly: {e}")
            return False
    
    def get_recent_anomalies(self, hours: int = 24) -> pd.DataFrame:
        """Get recent anomalies"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                
                query = """
                    SELECT device_name, anomaly_type, message, timestamp, severity
                    FROM anomalies
                    WHERE timestamp >= datetime('now', '-{} hours')
                    AND resolved = FALSE
                    ORDER BY timestamp DESC
                """.format(hours)
                
                df = pd.read_sql_query(query, conn)
                conn.close()
                
                return df
        except Exception as e:
            print(f"Error getting recent anomalies: {e}")
            return pd.DataFrame()
    
    def get_user_profile(self, username: str = 'default_user') -> Dict[str, Any]:
        """Get user profile"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT username, email, total_points, level, achievements, preferences
                    FROM user_profiles
                    WHERE username = ?
                """, (username,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        'username': row[0],
                        'email': row[1],
                        'total_points': row[2],
                        'level': row[3],
                        'achievements': json.loads(row[4]),
                        'preferences': json.loads(row[5])
                    }
                else:
                    return {
                        'username': username,
                        'email': '',
                        'total_points': 0,
                        'level': 1,
                        'achievements': [],
                        'preferences': {}
                    }
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}
    
    def update_user_points(self, username: str, points: int, activity_type: str, description: str = '') -> bool:
        """Update user points and add to history"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Update total points
                cursor.execute("""
                    UPDATE user_profiles
                    SET total_points = total_points + ?
                    WHERE username = ?
                """, (points, username))
                
                # Add to points history
                cursor.execute("""
                    INSERT INTO points_history (username, activity_type, points, description)
                    VALUES (?, ?, ?, ?)
                """, (username, activity_type, points, description))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"Error updating user points: {e}")
            return False
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user leaderboard"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT username, total_points, level
                    FROM user_profiles
                    ORDER BY total_points DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                return [
                    {
                        'username': row[0],
                        'points': row[1],
                        'level': row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_data_count(self) -> int:
        """Get total count of energy data records"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM energy_data")
                count = cursor.fetchone()[0]
                
                conn.close()
                return count
        except Exception as e:
            print(f"Error getting data count: {e}")
            return 0
