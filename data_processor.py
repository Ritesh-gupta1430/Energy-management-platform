import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import statistics
from collections import defaultdict

from database import DatabaseManager
from config import ENERGY_COST_PER_KWH

class DataProcessor:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self._cache = {}
        self._cache_timeout = timedelta(minutes=5)  # Cache data for 5 minutes
        self._last_cache_update = {}
    
    def get_current_consumption(self) -> float:
        """Get current energy consumption (most recent reading)"""
        try:
            # Check cache first
            cache_key = 'current_consumption'
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]
            
            # Get most recent energy data
            recent_data = self.db_manager.get_recent_energy_data(hours=1)
            
            if recent_data.empty:
                current_consumption = 0.0
            else:
                # Get the most recent consumption value
                current_consumption = recent_data.iloc[0]['consumption']
            
            # Cache the result
            self._cache[cache_key] = current_consumption
            self._last_cache_update[cache_key] = datetime.now()
            
            return current_consumption
            
        except Exception as e:
            print(f"Error getting current consumption: {e}")
            return 0.0
    
    def get_daily_total(self, date: datetime.date = None) -> float:
        """Get total energy consumption for a specific date (default: today)"""
        if date is None:
            date = datetime.now().date()
        
        try:
            cache_key = f'daily_total_{date}'
            if self._is_cache_valid(cache_key):
                return self._cache[cache_key]
            
            # Get data for the specific date
            data = self.db_manager.get_energy_data_range(date, date)
            
            if data.empty:
                daily_total = 0.0
            else:
                daily_total = data['consumption'].sum()
            
            # Cache the result
            self._cache[cache_key] = daily_total
            self._last_cache_update[cache_key] = datetime.now()
            
            return daily_total
            
        except Exception as e:
            print(f"Error getting daily total: {e}")
            return 0.0
    
    def get_weekly_total(self, week_start: datetime.date = None) -> float:
        """Get total energy consumption for a week"""
        if week_start is None:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())  # Monday of current week
        
        week_end = week_start + timedelta(days=6)
        
        try:
            data = self.db_manager.get_energy_data_range(week_start, week_end)
            
            if data.empty:
                return 0.0
            
            return data['consumption'].sum()
            
        except Exception as e:
            print(f"Error getting weekly total: {e}")
            return 0.0
    
    def get_monthly_total(self, year: int = None, month: int = None) -> float:
        """Get total energy consumption for a month"""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        # Get first and last day of the month
        month_start = datetime(year, month, 1).date()
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        try:
            data = self.db_manager.get_energy_data_range(month_start, month_end)
            
            if data.empty:
                return 0.0
            
            return data['consumption'].sum()
            
        except Exception as e:
            print(f"Error getting monthly total: {e}")
            return 0.0
    
    def get_consumption_statistics(self, days_back: int = 30) -> Dict[str, float]:
        """Get comprehensive consumption statistics"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return {
                    'total_consumption': 0.0,
                    'average_daily': 0.0,
                    'min_daily': 0.0,
                    'max_daily': 0.0,
                    'median_daily': 0.0,
                    'std_deviation': 0.0,
                    'total_cost': 0.0
                }
            
            # Daily consumption totals
            daily_totals = data.groupby(data['timestamp'].dt.date)['consumption'].sum()
            
            total_consumption = data['consumption'].sum()
            total_cost = total_consumption * ENERGY_COST_PER_KWH
            
            return {
                'total_consumption': total_consumption,
                'average_daily': daily_totals.mean() if not daily_totals.empty else 0.0,
                'min_daily': daily_totals.min() if not daily_totals.empty else 0.0,
                'max_daily': daily_totals.max() if not daily_totals.empty else 0.0,
                'median_daily': daily_totals.median() if not daily_totals.empty else 0.0,
                'std_deviation': daily_totals.std() if not daily_totals.empty else 0.0,
                'total_cost': total_cost,
                'days_with_data': len(daily_totals),
                'average_hourly': data['consumption'].mean() if not data.empty else 0.0
            }
            
        except Exception as e:
            print(f"Error getting consumption statistics: {e}")
            return {}
    
    def get_device_consumption_breakdown(self, days_back: int = 30) -> pd.DataFrame:
        """Get consumption breakdown by device"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # Group by device and calculate statistics
            device_stats = data.groupby('device_name').agg({
                'consumption': ['sum', 'mean', 'count', 'std']
            }).round(3)
            
            # Flatten column names
            device_stats.columns = ['total_consumption', 'avg_consumption', 'reading_count', 'std_deviation']
            
            # Calculate percentage and cost
            total_consumption = device_stats['total_consumption'].sum()
            device_stats['percentage'] = (device_stats['total_consumption'] / total_consumption * 100).round(1)
            device_stats['total_cost'] = (device_stats['total_consumption'] * ENERGY_COST_PER_KWH).round(2)
            
            # Sort by total consumption
            device_stats = device_stats.sort_values('total_consumption', ascending=False)
            
            return device_stats.reset_index()
            
        except Exception as e:
            print(f"Error getting device consumption breakdown: {e}")
            return pd.DataFrame()
    
    def get_hourly_consumption_pattern(self, days_back: int = 30) -> pd.DataFrame:
        """Get average consumption pattern by hour of day"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # Group by hour and calculate average consumption
            hourly_pattern = data.groupby(data['timestamp'].dt.hour).agg({
                'consumption': ['mean', 'std', 'count']
            }).round(3)
            
            # Flatten column names
            hourly_pattern.columns = ['avg_consumption', 'std_deviation', 'data_points']
            
            return hourly_pattern.reset_index()
            
        except Exception as e:
            print(f"Error getting hourly consumption pattern: {e}")
            return pd.DataFrame()
    
    def get_weekly_consumption_pattern(self, weeks_back: int = 8) -> pd.DataFrame:
        """Get consumption pattern by day of week"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(weeks=weeks_back)
            
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return pd.DataFrame()
            
            # Add day of week
            data['day_of_week'] = data['timestamp'].dt.day_name()
            data['weekday_num'] = data['timestamp'].dt.weekday
            
            # Group by day of week
            weekly_pattern = data.groupby(['weekday_num', 'day_of_week']).agg({
                'consumption': ['mean', 'sum', 'count']
            }).round(3)
            
            # Flatten column names
            weekly_pattern.columns = ['avg_consumption', 'total_consumption', 'data_points']
            
            return weekly_pattern.reset_index()
            
        except Exception as e:
            print(f"Error getting weekly consumption pattern: {e}")
            return pd.DataFrame()
    
    def calculate_energy_efficiency_score(self, days_back: int = 30) -> Dict[str, Any]:
        """Calculate an energy efficiency score based on various factors"""
        try:
            stats = self.get_consumption_statistics(days_back)
            
            if not stats or stats['total_consumption'] == 0:
                return {
                    'score': 0,
                    'grade': 'N/A',
                    'factors': {},
                    'recommendations': ['Start monitoring energy consumption to get your efficiency score']
                }
            
            # Scoring factors (0-100 scale)
            factors = {}
            
            # Consistency factor (lower std deviation is better)
            if stats['std_deviation'] > 0 and stats['average_daily'] > 0:
                cv = stats['std_deviation'] / stats['average_daily']  # Coefficient of variation
                factors['consistency'] = max(0, 100 - (cv * 50))  # Lower CV = higher score
            else:
                factors['consistency'] = 50  # Neutral score
            
            # Usage level factor (compare to typical household)
            typical_daily_usage = 25  # kWh per day for average household
            if stats['average_daily'] <= typical_daily_usage:
                factors['usage_level'] = 100 - (stats['average_daily'] / typical_daily_usage * 50)
            else:
                factors['usage_level'] = max(0, 50 - ((stats['average_daily'] - typical_daily_usage) / typical_daily_usage * 50))
            
            # Peak usage management (based on hourly patterns)
            hourly_pattern = self.get_hourly_consumption_pattern(days_back)
            if not hourly_pattern.empty:
                peak_hours = hourly_pattern[(hourly_pattern.index >= 17) & (hourly_pattern.index <= 21)]  # 5-9 PM
                off_peak_hours = hourly_pattern[(hourly_pattern.index >= 23) | (hourly_pattern.index <= 6)]  # 11PM-6AM
                
                if not peak_hours.empty and not off_peak_hours.empty:
                    peak_avg = peak_hours['avg_consumption'].mean()
                    off_peak_avg = off_peak_hours['avg_consumption'].mean()
                    
                    if peak_avg > 0:
                        peak_ratio = off_peak_avg / peak_avg
                        factors['peak_management'] = min(100, peak_ratio * 100)  # Better if more off-peak usage
                    else:
                        factors['peak_management'] = 50
                else:
                    factors['peak_management'] = 50
            else:
                factors['peak_management'] = 50
            
            # Data completeness factor
            expected_readings = days_back * 24  # Assuming hourly readings
            actual_readings = stats.get('days_with_data', 0) * 24
            factors['data_completeness'] = min(100, (actual_readings / expected_readings) * 100)
            
            # Calculate overall score (weighted average)
            weights = {
                'usage_level': 0.4,
                'consistency': 0.2,
                'peak_management': 0.3,
                'data_completeness': 0.1
            }
            
            weighted_score = sum(factors[factor] * weights[factor] for factor in factors)
            
            # Determine grade
            if weighted_score >= 90:
                grade = 'A+'
            elif weighted_score >= 80:
                grade = 'A'
            elif weighted_score >= 70:
                grade = 'B'
            elif weighted_score >= 60:
                grade = 'C'
            elif weighted_score >= 50:
                grade = 'D'
            else:
                grade = 'F'
            
            # Generate recommendations
            recommendations = []
            if factors['usage_level'] < 50:
                recommendations.append("Consider reducing overall energy consumption")
            if factors['consistency'] < 50:
                recommendations.append("Try to maintain more consistent daily usage patterns")
            if factors['peak_management'] < 50:
                recommendations.append("Shift energy usage away from peak hours (5-9 PM)")
            if factors['data_completeness'] < 80:
                recommendations.append("Improve data collection for better analysis")
            
            if not recommendations:
                recommendations.append("Great job! Keep maintaining your energy efficiency practices")
            
            return {
                'score': round(weighted_score, 1),
                'grade': grade,
                'factors': {k: round(v, 1) for k, v in factors.items()},
                'recommendations': recommendations,
                'stats_summary': stats
            }
            
        except Exception as e:
            print(f"Error calculating efficiency score: {e}")
            return {
                'score': 0,
                'grade': 'N/A',
                'factors': {},
                'recommendations': ['Error calculating efficiency score']
            }
    
    def detect_usage_trends(self, days_back: int = 60) -> Dict[str, Any]:
        """Detect trends in energy usage over time"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return {'trends': [], 'summary': 'No data available for trend analysis'}
            
            # Daily consumption totals
            daily_totals = data.groupby(data['timestamp'].dt.date)['consumption'].sum()
            
            if len(daily_totals) < 7:  # Need at least a week of data
                return {'trends': [], 'summary': 'Insufficient data for trend analysis'}
            
            trends = []
            
            # Overall trend (linear regression)
            x = np.arange(len(daily_totals))
            coeffs = np.polyfit(x, daily_totals.values, 1)
            slope = coeffs[0]
            
            if slope > 0.1:
                trends.append({
                    'type': 'increasing_consumption',
                    'description': f'Energy consumption is increasing by approximately {slope:.2f} kWh per day',
                    'severity': 'medium' if slope < 1 else 'high'
                })
            elif slope < -0.1:
                trends.append({
                    'type': 'decreasing_consumption',
                    'description': f'Energy consumption is decreasing by approximately {abs(slope):.2f} kWh per day',
                    'severity': 'positive'
                })
            else:
                trends.append({
                    'type': 'stable_consumption',
                    'description': 'Energy consumption is relatively stable',
                    'severity': 'low'
                })
            
            # Volatility analysis
            volatility = daily_totals.std() / daily_totals.mean() if daily_totals.mean() > 0 else 0
            
            if volatility > 0.3:
                trends.append({
                    'type': 'high_volatility',
                    'description': f'Energy consumption varies significantly (CV: {volatility:.2f})',
                    'severity': 'medium'
                })
            elif volatility < 0.1:
                trends.append({
                    'type': 'low_volatility',
                    'description': 'Energy consumption is very consistent',
                    'severity': 'positive'
                })
            
            # Weekly pattern analysis
            if len(daily_totals) >= 14:  # At least 2 weeks
                weekly_pattern = self.get_weekly_consumption_pattern(weeks_back=days_back//7)
                
                if not weekly_pattern.empty:
                    weekend_avg = weekly_pattern[weekly_pattern['weekday_num'].isin([5, 6])]['avg_consumption'].mean()
                    weekday_avg = weekly_pattern[~weekly_pattern['weekday_num'].isin([5, 6])]['avg_consumption'].mean()
                    
                    if weekend_avg > weekday_avg * 1.2:
                        trends.append({
                            'type': 'weekend_spike',
                            'description': f'Weekend consumption is {((weekend_avg/weekday_avg-1)*100):.1f}% higher than weekdays',
                            'severity': 'medium'
                        })
                    elif weekend_avg < weekday_avg * 0.8:
                        trends.append({
                            'type': 'weekend_drop',
                            'description': f'Weekend consumption is {((1-weekend_avg/weekday_avg)*100):.1f}% lower than weekdays',
                            'severity': 'low'
                        })
            
            # Recent changes (last week vs previous weeks)
            if len(daily_totals) >= 14:
                recent_week = daily_totals.tail(7).mean()
                previous_weeks = daily_totals.head(-7).mean()
                
                change_percent = ((recent_week - previous_weeks) / previous_weeks * 100) if previous_weeks > 0 else 0
                
                if abs(change_percent) > 15:
                    direction = 'increased' if change_percent > 0 else 'decreased'
                    trends.append({
                        'type': 'recent_change',
                        'description': f'Energy consumption has {direction} by {abs(change_percent):.1f}% in the last week',
                        'severity': 'high' if abs(change_percent) > 30 else 'medium'
                    })
            
            # Summary
            positive_trends = len([t for t in trends if t['severity'] == 'positive'])
            concerning_trends = len([t for t in trends if t['severity'] in ['medium', 'high']])
            
            if positive_trends > concerning_trends:
                summary = "Overall energy usage patterns look good"
            elif concerning_trends > positive_trends:
                summary = "Some concerning trends detected in energy usage"
            else:
                summary = "Mixed trends in energy usage patterns"
            
            return {
                'trends': trends,
                'summary': summary,
                'analysis_period': f"{start_date} to {end_date}",
                'data_points': len(daily_totals)
            }
            
        except Exception as e:
            print(f"Error detecting usage trends: {e}")
            return {'trends': [], 'summary': 'Error analyzing usage trends'}
    
    def get_cost_analysis(self, days_back: int = 30) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        try:
            stats = self.get_consumption_statistics(days_back)
            
            if not stats or stats['total_consumption'] == 0:
                return {
                    'total_cost': 0.0,
                    'daily_average_cost': 0.0,
                    'projected_monthly_cost': 0.0,
                    'projected_annual_cost': 0.0,
                    'cost_breakdown': {},
                    'savings_opportunities': []
                }
            
            # Basic cost calculations
            total_cost = stats['total_cost']
            daily_average_cost = total_cost / stats['days_with_data'] if stats['days_with_data'] > 0 else 0
            projected_monthly_cost = daily_average_cost * 30.44  # Average days per month
            projected_annual_cost = daily_average_cost * 365
            
            # Cost breakdown by device
            device_breakdown = self.get_device_consumption_breakdown(days_back)
            cost_breakdown = {}
            
            if not device_breakdown.empty:
                for _, row in device_breakdown.iterrows():
                    cost_breakdown[row['device_name']] = {
                        'cost': row['total_cost'],
                        'percentage': row['percentage']
                    }
            
            # Identify savings opportunities
            savings_opportunities = []
            
            # High-cost devices
            if not device_breakdown.empty:
                high_cost_devices = device_breakdown[device_breakdown['total_cost'] > projected_monthly_cost * 0.2]
                for _, device in high_cost_devices.iterrows():
                    savings_opportunities.append({
                        'type': 'high_cost_device',
                        'description': f"{device['device_name']} accounts for ${device['total_cost']:.2f} ({device['percentage']:.1f}%) of your energy costs",
                        'potential_savings': device['total_cost'] * 0.1  # Assume 10% savings potential
                    })
            
            # Peak hour usage
            hourly_pattern = self.get_hourly_consumption_pattern(days_back)
            if not hourly_pattern.empty:
                peak_hours = hourly_pattern[(hourly_pattern.index >= 17) & (hourly_pattern.index <= 21)]
                if not peak_hours.empty:
                    peak_consumption = peak_hours['avg_consumption'].sum()
                    peak_cost = peak_consumption * ENERGY_COST_PER_KWH * stats['days_with_data']
                    
                    if peak_cost > total_cost * 0.3:  # If peak hours account for >30% of cost
                        savings_opportunities.append({
                            'type': 'peak_hour_usage',
                            'description': f'Peak hour usage (5-9 PM) costs approximately ${peak_cost:.2f}',
                            'potential_savings': peak_cost * 0.2  # 20% savings by shifting usage
                        })
            
            # Efficiency improvements
            if stats['average_daily'] > 25:  # Above average household usage
                excess_usage = stats['average_daily'] - 25
                excess_cost = excess_usage * ENERGY_COST_PER_KWH * 30.44
                savings_opportunities.append({
                    'type': 'efficiency_improvement',
                    'description': f'Your daily usage is {excess_usage:.1f} kWh above average',
                    'potential_savings': excess_cost
                })
            
            return {
                'total_cost': round(total_cost, 2),
                'daily_average_cost': round(daily_average_cost, 2),
                'projected_monthly_cost': round(projected_monthly_cost, 2),
                'projected_annual_cost': round(projected_annual_cost, 2),
                'cost_breakdown': cost_breakdown,
                'savings_opportunities': savings_opportunities,
                'total_potential_savings': round(sum(opp['potential_savings'] for opp in savings_opportunities), 2),
                'cost_per_kwh': ENERGY_COST_PER_KWH
            }
            
        except Exception as e:
            print(f"Error getting cost analysis: {e}")
            return {}
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache or cache_key not in self._last_cache_update:
            return False
        
        return datetime.now() - self._last_cache_update[cache_key] < self._cache_timeout
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        self._last_cache_update.clear()
