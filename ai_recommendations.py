import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
from openai import OpenAI

from config import OPENAI_API_KEY, ENERGY_COST_PER_KWH
from database import DatabaseManager

class AIRecommendations:
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # Initialize OpenAI client if API key is available
        if OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            self.openai_available = True
        else:
            self.openai_client = None
            self.openai_available = False
            print("OpenAI API key not found. AI recommendations will use basic rule-based logic.")
    
    def generate_recommendations(self, energy_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate energy-saving recommendations based on consumption patterns"""
        if self.openai_available:
            return self._generate_ai_recommendations(energy_data)
        else:
            return self._generate_basic_recommendations(energy_data)
    
    def _generate_ai_recommendations(self, energy_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate recommendations using OpenAI API"""
        try:
            # Prepare data summary for AI analysis
            data_summary = self._prepare_data_summary(energy_data)
            
            # Create prompt for AI analysis
            prompt = f"""
            As an energy efficiency expert, analyze the following energy consumption data and provide 3-5 personalized recommendations for reducing energy usage and costs.
            
            Energy Data Summary:
            {data_summary}
            
            Energy cost per kWh: ${ENERGY_COST_PER_KWH}
            
            Please provide recommendations in JSON format with the following structure:
            {{
                "recommendations": [
                    {{
                        "title": "Recommendation title",
                        "description": "Detailed explanation of the recommendation",
                        "category": "heating/cooling/lighting/appliances/general",
                        "estimated_savings": "monthly savings in dollars",
                        "difficulty": "easy/medium/hard",
                        "priority": "high/medium/low"
                    }}
                ]
            }}
            
            Focus on:
            1. Peak usage times and how to shift consumption
            2. Unusual consumption patterns
            3. Device-specific optimizations
            4. Behavioral changes that can reduce energy waste
            5. Seasonal adjustments
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5"
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert energy efficiency consultant with deep knowledge of residential energy consumption patterns and cost-saving strategies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse AI response
            ai_response = json.loads(response.choices[0].message.content)
            recommendations = ai_response.get('recommendations', [])
            
            # Store recommendations in database
            for rec in recommendations:
                self.db_manager.add_recommendation(
                    title=rec['title'],
                    description=rec['description'],
                    estimated_savings=rec.get('estimated_savings', 0),
                    category=rec.get('category', 'general')
                )
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating AI recommendations: {e}")
            return self._generate_basic_recommendations(energy_data)
    
    def _generate_basic_recommendations(self, energy_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate basic recommendations using rule-based logic"""
        recommendations = []
        
        if energy_data.empty:
            return [{
                "title": "Start Monitoring",
                "description": "Begin collecting energy consumption data from your devices to receive personalized recommendations.",
                "category": "general",
                "estimated_savings": 0,
                "difficulty": "easy",
                "priority": "high"
            }]
        
        # Analyze consumption patterns
        hourly_avg = energy_data.groupby(energy_data['timestamp'].dt.hour)['consumption'].mean()
        daily_total = energy_data.groupby(energy_data['timestamp'].dt.date)['consumption'].sum()
        
        # High consumption hours
        peak_hours = hourly_avg.nlargest(3).index.tolist()
        if peak_hours:
            peak_hours_str = ", ".join([f"{h}:00" for h in peak_hours])
            recommendations.append({
                "title": "Shift Peak Hour Usage",
                "description": f"Your highest energy consumption occurs at {peak_hours_str}. Consider shifting non-essential appliance usage to off-peak hours to potentially reduce costs.",
                "category": "general",
                "estimated_savings": daily_total.mean() * 0.1 * ENERGY_COST_PER_KWH * 30,
                "difficulty": "medium",
                "priority": "high"
            })
        
        # High daily consumption
        avg_daily = daily_total.mean()
        if avg_daily > 30:  # Above average household consumption
            recommendations.append({
                "title": "Reduce Overall Consumption",
                "description": f"Your average daily consumption of {avg_daily:.1f} kWh is above typical household usage. Consider upgrading to energy-efficient appliances and improving insulation.",
                "category": "appliances",
                "estimated_savings": (avg_daily - 25) * ENERGY_COST_PER_KWH * 30,
                "difficulty": "hard",
                "priority": "high"
            })
        
        # Weekend vs weekday analysis
        energy_data['is_weekend'] = energy_data['timestamp'].dt.weekday >= 5
        weekday_avg = energy_data[~energy_data['is_weekend']]['consumption'].mean()
        weekend_avg = energy_data[energy_data['is_weekend']]['consumption'].mean()
        
        if weekend_avg > weekday_avg * 1.2:
            recommendations.append({
                "title": "Weekend Energy Awareness",
                "description": "Your weekend energy consumption is significantly higher than weekdays. Consider implementing energy-saving habits during weekends when you're home more often.",
                "category": "general",
                "estimated_savings": (weekend_avg - weekday_avg) * ENERGY_COST_PER_KWH * 8,
                "difficulty": "easy",
                "priority": "medium"
            })
        
        # Add general energy-saving tips
        general_tips = [
            {
                "title": "LED Lighting Upgrade",
                "description": "Replace traditional incandescent bulbs with LED lights to reduce lighting energy consumption by up to 75%.",
                "category": "lighting",
                "estimated_savings": 15.0,
                "difficulty": "easy",
                "priority": "medium"
            },
            {
                "title": "Smart Thermostat",
                "description": "Install a programmable or smart thermostat to optimize heating and cooling schedules based on your daily routine.",
                "category": "heating_cooling",
                "estimated_savings": 35.0,
                "difficulty": "medium",
                "priority": "high"
            },
            {
                "title": "Unplug Standby Devices",
                "description": "Unplug electronics and chargers when not in use to eliminate phantom power draw, which can account for 5-10% of home energy use.",
                "category": "appliances",
                "estimated_savings": 12.0,
                "difficulty": "easy",
                "priority": "medium"
            }
        ]
        
        # Add 1-2 general tips
        recommendations.extend(general_tips[:2])
        
        # Store recommendations in database
        for rec in recommendations:
            self.db_manager.add_recommendation(
                title=rec['title'],
                description=rec['description'],
                estimated_savings=rec.get('estimated_savings', 0),
                category=rec.get('category', 'general')
            )
        
        return recommendations
    
    def _prepare_data_summary(self, energy_data: pd.DataFrame) -> str:
        """Prepare a summary of energy data for AI analysis"""
        if energy_data.empty:
            return "No energy data available for analysis."
        
        # Basic statistics
        total_consumption = energy_data['consumption'].sum()
        avg_daily = energy_data.groupby(energy_data['timestamp'].dt.date)['consumption'].sum().mean()
        peak_hour = energy_data.groupby(energy_data['timestamp'].dt.hour)['consumption'].mean().idxmax()
        
        # Device breakdown
        device_consumption = energy_data.groupby('device_name')['consumption'].sum().sort_values(ascending=False)
        
        # Time patterns
        hourly_avg = energy_data.groupby(energy_data['timestamp'].dt.hour)['consumption'].mean()
        weekend_vs_weekday = energy_data.groupby(energy_data['timestamp'].dt.weekday >= 5)['consumption'].mean()
        
        summary = f"""
        Data Period: {energy_data['timestamp'].min().date()} to {energy_data['timestamp'].max().date()}
        Total Consumption: {total_consumption:.2f} kWh
        Average Daily Consumption: {avg_daily:.2f} kWh
        Peak Consumption Hour: {peak_hour}:00
        
        Device Consumption Breakdown:
        {device_consumption.head().to_string()}
        
        Hourly Average Consumption Pattern:
        {hourly_avg.to_string()}
        
        Weekend vs Weekday Consumption:
        Weekday: {weekend_vs_weekday[False]:.2f} kWh
        Weekend: {weekend_vs_weekday[True]:.2f} kWh
        """
        
        return summary
    
    def get_energy_saving_tips(self, category: str = None) -> List[Dict[str, str]]:
        """Get general energy saving tips by category"""
        all_tips = {
            "lighting": [
                {"tip": "Use LED bulbs", "description": "Replace incandescent bulbs with LED lights for 75% energy savings"},
                {"tip": "Natural light", "description": "Open curtains and blinds during the day to reduce lighting needs"},
                {"tip": "Motion sensors", "description": "Install motion-activated lights in less frequently used areas"}
            ],
            "heating_cooling": [
                {"tip": "Adjust thermostat", "description": "Lower heating by 2°C or raise cooling by 2°C to save 10-15%"},
                {"tip": "Seal air leaks", "description": "Weather-strip doors and windows to prevent energy loss"},
                {"tip": "Use fans", "description": "Ceiling fans can make rooms feel cooler, allowing higher AC settings"}
            ],
            "appliances": [
                {"tip": "Unplug when idle", "description": "Electronics consume power even when off - unplug to stop phantom load"},
                {"tip": "Full loads only", "description": "Run dishwashers and washing machines only with full loads"},
                {"tip": "Cold water washing", "description": "Use cold water for laundry to reduce heating energy by 90%"}
            ],
            "general": [
                {"tip": "Energy audit", "description": "Conduct a home energy audit to identify biggest opportunities"},
                {"tip": "Smart power strips", "description": "Use smart strips to automatically cut power to standby devices"},
                {"tip": "Maintenance", "description": "Keep appliances clean and well-maintained for optimal efficiency"}
            ]
        }
        
        if category and category in all_tips:
            return all_tips[category]
        else:
            # Return a mix of tips from all categories
            tips = []
            for cat_tips in all_tips.values():
                tips.extend(cat_tips[:2])
            return tips
