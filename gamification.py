import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd

from config import POINTS_PER_KWH_SAVED, POINTS_MANUAL_INPUT, POINTS_DAILY_LOGIN
from database import DatabaseManager

class GamificationManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.username = 'default_user'  # In a real app, this would be dynamic
        
        # Initialize achievements and challenges
        self._initialize_achievements()
    
    def _initialize_achievements(self):
        """Initialize available achievements"""
        self.achievements = [
            {
                'id': 'first_login',
                'name': 'Welcome Aboard',
                'description': 'Log into the energy tracker for the first time',
                'points': 10,
                'type': 'milestone'
            },
            {
                'id': 'data_logger_7',
                'name': 'Data Logger',
                'description': 'Log energy data for 7 consecutive days',
                'points': 50,
                'type': 'streak'
            },
            {
                'id': 'energy_saver_10',
                'name': 'Energy Saver',
                'description': 'Reduce energy consumption by 10% compared to previous week',
                'points': 100,
                'type': 'improvement'
            },
            {
                'id': 'early_bird',
                'name': 'Early Bird',
                'description': 'Check the dashboard before 8 AM for 5 days',
                'points': 25,
                'type': 'habit'
            },
            {
                'id': 'night_owl',
                'name': 'Night Owl Saver',
                'description': 'Reduce energy consumption after 10 PM for a week',
                'points': 75,
                'type': 'habit'
            },
            {
                'id': 'recommendation_follower',
                'name': 'Recommendation Follower',
                'description': 'Apply 3 AI recommendations',
                'points': 150,
                'type': 'engagement'
            },
            {
                'id': 'community_leader',
                'name': 'Community Leader',
                'description': 'Reach top 3 in neighborhood leaderboard',
                'points': 200,
                'type': 'competitive'
            },
            {
                'id': 'streak_master',
                'name': 'Streak Master',
                'description': 'Maintain daily energy logging for 30 days',
                'points': 300,
                'type': 'streak'
            }
        ]
    
    def add_points(self, activity_type: str, points: int, description: str = '') -> bool:
        """Add points to user profile"""
        success = self.db_manager.update_user_points(
            username=self.username,
            points=points,
            activity_type=activity_type,
            description=description
        )
        
        if success:
            # Check for new achievements
            self._check_achievements()
            
            # Update user level
            self._update_user_level()
            
        return success
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get comprehensive user profile with gamification data"""
        profile = self.db_manager.get_user_profile(self.username)
        
        # Add additional gamification metrics
        profile['next_level_points'] = self._get_points_for_next_level(profile['level'])
        profile['current_level_progress'] = self._get_current_level_progress(profile['total_points'])
        profile['recent_activities'] = self._get_recent_activities()
        profile['current_streak'] = self._get_current_streak()
        
        return profile
    
    def get_points_breakdown(self) -> Dict[str, int]:
        """Get breakdown of points by activity type"""
        try:
            with self.db_manager.lock:
                conn = self.db_manager.db_path
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT activity_type, SUM(points) as total_points
                    FROM points_history
                    WHERE username = ?
                    GROUP BY activity_type
                """, (self.username,))
                
                results = cursor.fetchall()
                conn.close()
                
                return {activity: points for activity, points in results}
        except Exception as e:
            print(f"Error getting points breakdown: {e}")
            return {}
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user leaderboard"""
        return self.db_manager.get_leaderboard(limit)
    
    def get_available_achievements(self) -> List[Dict[str, Any]]:
        """Get all available achievements with earned status"""
        user_profile = self.get_user_profile()
        earned_achievements = set(user_profile['achievements'])
        
        achievements_with_status = []
        for achievement in self.achievements:
            achievement_copy = achievement.copy()
            achievement_copy['earned'] = achievement['id'] in earned_achievements
            achievements_with_status.append(achievement_copy)
        
        return achievements_with_status
    
    def get_active_challenges(self) -> List[Dict[str, Any]]:
        """Get active challenges"""
        try:
            with self.db_manager.lock:
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, challenge_type, target_value, reward_points, start_date, end_date
                    FROM challenges
                    WHERE active = TRUE AND end_date >= date('now')
                """)
                
                rows = cursor.fetchall()
                conn.close()
                
                challenges = []
                for row in rows:
                    challenges.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'challenge_type': row[3],
                        'target_value': row[4],
                        'reward_points': row[5],
                        'start_date': row[6],
                        'end_date': row[7]
                    })
                
                return challenges
        except Exception as e:
            print(f"Error getting active challenges: {e}")
            return []
    
    def get_challenge_progress(self, challenge_id: int) -> Dict[str, Any]:
        """Get user's progress on a specific challenge"""
        try:
            with self.db_manager.lock:
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Get challenge details
                cursor.execute("""
                    SELECT target_value, challenge_type
                    FROM challenges
                    WHERE id = ?
                """, (challenge_id,))
                
                challenge_row = cursor.fetchone()
                if not challenge_row:
                    return {'percentage': 0, 'completed': False}
                
                target_value, challenge_type = challenge_row
                
                # Get user progress
                cursor.execute("""
                    SELECT current_value, completed
                    FROM user_challenge_progress
                    WHERE username = ? AND challenge_id = ?
                """, (self.username, challenge_id))
                
                progress_row = cursor.fetchone()
                
                if progress_row:
                    current_value, completed = progress_row
                    percentage = min(100, (current_value / target_value) * 100) if target_value > 0 else 0
                else:
                    # Calculate progress based on challenge type
                    current_value = self._calculate_challenge_progress(challenge_type)
                    percentage = min(100, (current_value / target_value) * 100) if target_value > 0 else 0
                    completed = False
                    
                    # Insert/update progress
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_challenge_progress
                        (username, challenge_id, current_value, completed)
                        VALUES (?, ?, ?, ?)
                    """, (self.username, challenge_id, current_value, completed))
                
                conn.commit()
                conn.close()
                
                return {
                    'percentage': percentage,
                    'current_value': current_value,
                    'target_value': target_value,
                    'completed': completed
                }
        except Exception as e:
            print(f"Error getting challenge progress: {e}")
            return {'percentage': 0, 'completed': False}
    
    def complete_challenge(self, challenge_id: int) -> bool:
        """Mark a challenge as completed and award points"""
        try:
            with self.db_manager.lock:
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Get challenge reward points
                cursor.execute("""
                    SELECT reward_points, name
                    FROM challenges
                    WHERE id = ?
                """, (challenge_id,))
                
                challenge_row = cursor.fetchone()
                if not challenge_row:
                    return False
                
                reward_points, challenge_name = challenge_row
                
                # Mark as completed
                cursor.execute("""
                    UPDATE user_challenge_progress
                    SET completed = TRUE, completed_at = datetime('now')
                    WHERE username = ? AND challenge_id = ?
                """, (self.username, challenge_id))
                
                conn.commit()
                conn.close()
                
                # Award points
                return self.add_points('challenge_completed', reward_points, f'Completed challenge: {challenge_name}')
        except Exception as e:
            print(f"Error completing challenge: {e}")
            return False
    
    def _check_achievements(self):
        """Check and award new achievements"""
        user_profile = self.db_manager.get_user_profile(self.username)
        earned_achievements = set(user_profile['achievements'])
        
        # Check each achievement
        for achievement in self.achievements:
            if achievement['id'] in earned_achievements:
                continue  # Already earned
            
            if self._check_achievement_condition(achievement):
                self._award_achievement(achievement['id'], achievement['points'])
    
    def _check_achievement_condition(self, achievement: Dict[str, Any]) -> bool:
        """Check if achievement condition is met"""
        achievement_id = achievement['id']
        
        try:
            if achievement_id == 'first_login':
                return True  # Always award on first check
            
            elif achievement_id == 'data_logger_7':
                # Check for 7 consecutive days of data logging
                return self._check_consecutive_days(7)
            
            elif achievement_id == 'energy_saver_10':
                # Check for 10% energy reduction
                return self._check_energy_reduction(0.10)
            
            elif achievement_id == 'early_bird':
                # Check for early morning access (before 8 AM) for 5 days
                return self._check_early_access(5)
            
            elif achievement_id == 'streak_master':
                # Check for 30-day logging streak
                return self._check_consecutive_days(30)
            
            # Add more achievement conditions as needed
            
        except Exception as e:
            print(f"Error checking achievement condition for {achievement_id}: {e}")
        
        return False
    
    def _award_achievement(self, achievement_id: str, points: int) -> bool:
        """Award achievement to user"""
        try:
            # Get current achievements
            user_profile = self.db_manager.get_user_profile(self.username)
            achievements = user_profile['achievements']
            
            # Add new achievement
            achievements.append(achievement_id)
            
            with self.db_manager.lock:
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                # Update user profile
                cursor.execute("""
                    UPDATE user_profiles
                    SET achievements = ?
                    WHERE username = ?
                """, (json.dumps(achievements), self.username))
                
                conn.commit()
                conn.close()
            
            # Award points
            achievement_name = next((a['name'] for a in self.achievements if a['id'] == achievement_id), achievement_id)
            return self.add_points('achievement_unlocked', points, f'Achievement unlocked: {achievement_name}')
            
        except Exception as e:
            print(f"Error awarding achievement {achievement_id}: {e}")
            return False
    
    def _update_user_level(self):
        """Update user level based on total points"""
        user_profile = self.db_manager.get_user_profile(self.username)
        current_level = user_profile['level']
        total_points = user_profile['total_points']
        
        # Calculate new level (every 100 points = 1 level)
        new_level = max(1, total_points // 100)
        
        if new_level > current_level:
            try:
                with self.db_manager.lock:
                    import sqlite3
                    conn = sqlite3.connect(self.db_manager.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE user_profiles
                        SET level = ?
                        WHERE username = ?
                    """, (new_level, self.username))
                    
                    conn.commit()
                    conn.close()
                
                # Award bonus points for leveling up
                level_bonus = (new_level - current_level) * 50
                self.add_points('level_up', level_bonus, f'Leveled up to Level {new_level}')
                
            except Exception as e:
                print(f"Error updating user level: {e}")
    
    def _get_points_for_next_level(self, current_level: int) -> int:
        """Get points needed for next level"""
        return (current_level + 1) * 100
    
    def _get_current_level_progress(self, total_points: int) -> float:
        """Get progress toward next level (0-100)"""
        current_level = max(1, total_points // 100)
        points_in_current_level = total_points % 100
        return points_in_current_level
    
    def _get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent point-earning activities"""
        try:
            with self.db_manager.lock:
                import sqlite3
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT activity_type, points, description, timestamp
                    FROM points_history
                    WHERE username = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (self.username, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                activities = []
                for row in rows:
                    activities.append({
                        'activity_type': row[0],
                        'points': row[1],
                        'description': row[2],
                        'timestamp': row[3]
                    })
                
                return activities
        except Exception as e:
            print(f"Error getting recent activities: {e}")
            return []
    
    def _get_current_streak(self) -> int:
        """Get current daily login/activity streak"""
        try:
            # Get recent energy data entries
            recent_data = self.db_manager.get_recent_energy_data(hours=24*30)  # Last 30 days
            
            if recent_data.empty:
                return 0
            
            # Group by date
            daily_data = recent_data.groupby(recent_data['timestamp'].dt.date).size()
            
            # Count consecutive days from today backwards
            current_date = datetime.now().date()
            streak = 0
            
            while current_date in daily_data.index:
                streak += 1
                current_date -= timedelta(days=1)
            
            return streak
        except Exception as e:
            print(f"Error calculating current streak: {e}")
            return 0
    
    def _check_consecutive_days(self, required_days: int) -> bool:
        """Check if user has logged data for consecutive days"""
        return self._get_current_streak() >= required_days
    
    def _check_energy_reduction(self, target_percentage: float) -> bool:
        """Check if user has achieved energy reduction target"""
        try:
            # Compare this week to last week
            today = datetime.now().date()
            this_week_start = today - timedelta(days=7)
            last_week_start = today - timedelta(days=14)
            
            this_week_data = self.db_manager.get_energy_data_range(this_week_start, today)
            last_week_data = self.db_manager.get_energy_data_range(last_week_start, this_week_start)
            
            if this_week_data.empty or last_week_data.empty:
                return False
            
            this_week_total = this_week_data['consumption'].sum()
            last_week_total = last_week_data['consumption'].sum()
            
            if last_week_total == 0:
                return False
            
            reduction_percentage = (last_week_total - this_week_total) / last_week_total
            return reduction_percentage >= target_percentage
            
        except Exception as e:
            print(f"Error checking energy reduction: {e}")
            return False
    
    def _check_early_access(self, required_days: int) -> bool:
        """Check if user has accessed dashboard early morning for required days"""
        # This would need to be implemented with actual login tracking
        # For now, return a placeholder
        return False
    
    def _calculate_challenge_progress(self, challenge_type: str) -> float:
        """Calculate current progress for a challenge type"""
        try:
            if challenge_type == 'consumption_reduction':
                # Calculate percentage reduction compared to baseline
                baseline_data = self.db_manager.get_energy_data_range(
                    datetime.now().date() - timedelta(days=30),
                    datetime.now().date() - timedelta(days=23)
                )
                current_data = self.db_manager.get_recent_energy_data(hours=24*7)
                
                if baseline_data.empty or current_data.empty:
                    return 0.0
                
                baseline_avg = baseline_data['consumption'].mean()
                current_avg = current_data['consumption'].mean()
                
                if baseline_avg == 0:
                    return 0.0
                
                reduction = (baseline_avg - current_avg) / baseline_avg
                return max(0, reduction)
            
            elif challenge_type == 'daily_logging':
                # Count consecutive days of logging
                return float(self._get_current_streak())
            
            elif challenge_type == 'early_access':
                # Would need login time tracking
                return 0.0
            
        except Exception as e:
            print(f"Error calculating challenge progress: {e}")
        
        return 0.0
