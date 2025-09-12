import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import threading
import schedule
import time

from config import *
from database import DatabaseManager

class NotificationManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.email_enabled = bool(SMTP_USERNAME and SMTP_PASSWORD)
        
        if not self.email_enabled:
            print("Email notifications disabled - SMTP credentials not configured")
        
        # Start background scheduler for periodic notifications
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_running = True
        self.scheduler_thread.start()
        
        # Schedule daily and weekly reports
        schedule.every().day.at("08:00").do(self._send_daily_report)
        schedule.every().sunday.at("09:00").do(self._send_weekly_report)
    
    def _run_scheduler(self):
        """Run the notification scheduler in background"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> bool:
        """Send email notification"""
        if not self.email_enabled:
            print(f"Email notification (would send): {subject} to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach text version
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Attach HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_high_usage_alert(self, device_name: str, consumption: float, threshold: float, to_email: str = None):
        """Send alert for high energy usage"""
        subject = f"⚠️ High Energy Usage Alert - {device_name}"
        
        cost_estimate = consumption * ENERGY_COST_PER_KWH
        excess_cost = (consumption - threshold) * ENERGY_COST_PER_KWH
        
        body = f"""
High Energy Usage Alert

Device: {device_name}
Consumption: {consumption:.2f} kWh
Threshold: {threshold:.2f} kWh
Excess Usage: {(consumption - threshold):.2f} kWh

Estimated Cost: ${cost_estimate:.2f}
Excess Cost: ${excess_cost:.2f}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This alert was generated because your energy consumption exceeded the configured threshold.
Consider checking your devices and reducing usage if possible.

Best regards,
Your Energy Tracker
        """
        
        html_body = f"""
<html>
<body>
<h2 style="color: #ff6b6b;">⚠️ High Energy Usage Alert</h2>
<p>Your energy consumption has exceeded the configured threshold.</p>

<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f8f9fa;">
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Device</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6;">{device_name}</td>
</tr>
<tr>
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Consumption</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6;">{consumption:.2f} kWh</td>
</tr>
<tr style="background-color: #f8f9fa;">
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Threshold</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6;">{threshold:.2f} kWh</td>
</tr>
<tr>
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Excess Usage</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6; color: #ff6b6b;"><strong>{(consumption - threshold):.2f} kWh</strong></td>
</tr>
<tr style="background-color: #f8f9fa;">
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Estimated Cost</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6;">${cost_estimate:.2f}</td>
</tr>
<tr>
    <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Excess Cost</strong></td>
    <td style="padding: 10px; border: 1px solid #dee2e6; color: #ff6b6b;"><strong>${excess_cost:.2f}</strong></td>
</tr>
</table>

<p style="margin-top: 20px;">
<strong>Recommendations:</strong>
<ul>
<li>Check if any devices are running unnecessarily</li>
<li>Consider shifting some usage to off-peak hours</li>
<li>Review your energy-saving settings</li>
</ul>
</p>

<p style="color: #666; font-size: 12px; margin-top: 30px;">
Alert generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
This is an automated message from your Energy Tracker system.
</p>
</body>
</html>
        """
        
        # Use default email if not provided
        if not to_email:
            user_profile = self.db_manager.get_user_profile()
            to_email = user_profile.get('email', 'user@example.com')
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_anomaly_alert(self, anomalies: List[Dict[str, Any]], to_email: str = None):
        """Send alert for detected anomalies"""
        if not anomalies:
            return
        
        subject = f"🔍 Energy Anomaly Detection - {len(anomalies)} issues detected"
        
        # Group anomalies by severity
        high_severity = [a for a in anomalies if a.get('severity') == 'high']
        medium_severity = [a for a in anomalies if a.get('severity') == 'medium']
        
        body = f"""
Energy Anomaly Detection Report

{len(anomalies)} anomalies detected in your energy consumption:

High Severity Issues: {len(high_severity)}
Medium Severity Issues: {len(medium_severity)}

Details:
"""
        
        html_body = f"""
<html>
<body>
<h2 style="color: #ff9f43;">🔍 Energy Anomaly Detection Report</h2>
<p>{len(anomalies)} anomalies detected in your energy consumption patterns.</p>

<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
<strong>Summary:</strong><br>
High Severity Issues: <span style="color: #dc3545; font-weight: bold;">{len(high_severity)}</span><br>
Medium Severity Issues: <span style="color: #fd7e14; font-weight: bold;">{len(medium_severity)}</span>
</div>

<h3>Anomaly Details:</h3>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #343a40; color: white;">
    <th style="padding: 10px; border: 1px solid #dee2e6;">Device</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Type</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Severity</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Message</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Time</th>
</tr>
"""
        
        for i, anomaly in enumerate(anomalies):
            severity_color = '#dc3545' if anomaly.get('severity') == 'high' else '#fd7e14'
            row_color = '#f8f9fa' if i % 2 == 0 else 'white'
            
            body += f"- {anomaly['device_name']}: {anomaly['message']} [{anomaly.get('severity', 'unknown')}]\n"
            
            html_body += f"""
<tr style="background-color: {row_color};">
    <td style="padding: 8px; border: 1px solid #dee2e6;">{anomaly['device_name']}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">{anomaly['type']}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6; color: {severity_color}; font-weight: bold;">
        {anomaly.get('severity', 'unknown').upper()}
    </td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">{anomaly['message']}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">
        {anomaly['timestamp'].strftime('%H:%M:%S') if isinstance(anomaly['timestamp'], datetime) else str(anomaly['timestamp'])}
    </td>
</tr>
"""
        
        html_body += """
</table>

<p style="margin-top: 20px;">
<strong>Recommended Actions:</strong>
<ul>
<li>Review the affected devices for any unusual behavior</li>
<li>Check if devices are functioning properly</li>
<li>Consider adjusting usage patterns if needed</li>
<li>Contact support if issues persist</li>
</ul>
</p>

<p style="color: #666; font-size: 12px; margin-top: 30px;">
Report generated at: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """<br>
This is an automated message from your Energy Tracker system.
</p>
</body>
</html>
        """
        
        body += f"""

Recommendations:
- Review the affected devices for any unusual behavior
- Check if devices are functioning properly
- Consider adjusting usage patterns if needed

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Use default email if not provided
        if not to_email:
            user_profile = self.db_manager.get_user_profile()
            to_email = user_profile.get('email', 'user@example.com')
        
        return self.send_email(to_email, subject, body, html_body)
    
    def _send_daily_report(self):
        """Send daily energy consumption report"""
        try:
            # Get yesterday's data
            yesterday = datetime.now().date() - timedelta(days=1)
            data = self.db_manager.get_energy_data_range(yesterday, yesterday)
            
            if data.empty:
                return
            
            total_consumption = data['consumption'].sum()
            total_cost = total_consumption * ENERGY_COST_PER_KWH
            device_breakdown = data.groupby('device_name')['consumption'].sum().sort_values(ascending=False)
            
            subject = f"📊 Daily Energy Report - {yesterday.strftime('%B %d, %Y')}"
            
            body = f"""
Daily Energy Consumption Report
Date: {yesterday.strftime('%B %d, %Y')}

Summary:
- Total Consumption: {total_consumption:.2f} kWh
- Estimated Cost: ${total_cost:.2f}

Device Breakdown:
"""
            
            html_body = f"""
<html>
<body>
<h2 style="color: #28a745;">📊 Daily Energy Report</h2>
<h3>{yesterday.strftime('%B %d, %Y')}</h3>

<div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
<h4>Summary</h4>
<p><strong>Total Consumption:</strong> {total_consumption:.2f} kWh</p>
<p><strong>Estimated Cost:</strong> ${total_cost:.2f}</p>
</div>

<h4>Device Breakdown</h4>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #28a745; color: white;">
    <th style="padding: 10px; border: 1px solid #dee2e6;">Device</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Consumption (kWh)</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Cost ($)</th>
    <th style="padding: 10px; border: 1px solid #dee2e6;">Percentage</th>
</tr>
"""
            
            for i, (device, consumption) in enumerate(device_breakdown.items()):
                percentage = (consumption / total_consumption) * 100
                cost = consumption * ENERGY_COST_PER_KWH
                row_color = '#f8f9fa' if i % 2 == 0 else 'white'
                
                body += f"- {device}: {consumption:.2f} kWh (${cost:.2f}) - {percentage:.1f}%\n"
                
                html_body += f"""
<tr style="background-color: {row_color};">
    <td style="padding: 8px; border: 1px solid #dee2e6;">{device}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">{consumption:.2f}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">${cost:.2f}</td>
    <td style="padding: 8px; border: 1px solid #dee2e6;">{percentage:.1f}%</td>
</tr>
"""
            
            html_body += """
</table>
</body>
</html>
"""
            
            # Get user email
            user_profile = self.db_manager.get_user_profile()
            to_email = user_profile.get('email', 'user@example.com')
            
            self.send_email(to_email, subject, body, html_body)
            
        except Exception as e:
            print(f"Error sending daily report: {e}")
    
    def _send_weekly_report(self):
        """Send weekly energy consumption report"""
        try:
            # Get last week's data
            end_date = datetime.now().date() - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            data = self.db_manager.get_energy_data_range(start_date, end_date)
            
            if data.empty:
                return
            
            total_consumption = data['consumption'].sum()
            total_cost = total_consumption * ENERGY_COST_PER_KWH
            avg_daily = total_consumption / 7
            
            # Daily breakdown
            daily_totals = data.groupby(data['timestamp'].dt.date)['consumption'].sum()
            
            subject = f"📈 Weekly Energy Report - {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}"
            
            body = f"""
Weekly Energy Consumption Report
Period: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}

Summary:
- Total Consumption: {total_consumption:.2f} kWh
- Average Daily: {avg_daily:.2f} kWh
- Total Estimated Cost: ${total_cost:.2f}

Daily Breakdown:
"""
            
            for date, consumption in daily_totals.items():
                body += f"- {date.strftime('%A, %b %d')}: {consumption:.2f} kWh\n"
            
            # Get user email
            user_profile = self.db_manager.get_user_profile()
            to_email = user_profile.get('email', 'user@example.com')
            
            self.send_email(to_email, subject, body)
            
        except Exception as e:
            print(f"Error sending weekly report: {e}")
    
    def send_recommendation_notification(self, recommendations: List[Dict[str, Any]], to_email: str = None):
        """Send notification with new AI recommendations"""
        if not recommendations:
            return
        
        subject = f"💡 New Energy Saving Recommendations - {len(recommendations)} tips"
        
        total_savings = sum(rec.get('estimated_savings', 0) for rec in recommendations)
        
        body = f"""
New Energy Saving Recommendations

We've analyzed your energy consumption patterns and generated {len(recommendations)} personalized recommendations:

Potential Monthly Savings: ${total_savings:.2f}

Recommendations:
"""
        
        for i, rec in enumerate(recommendations, 1):
            body += f"\n{i}. {rec['title']}\n"
            body += f"   {rec['description']}\n"
            if rec.get('estimated_savings'):
                body += f"   Potential savings: ${rec['estimated_savings']:.2f}/month\n"
        
        # Use default email if not provided
        if not to_email:
            user_profile = self.db_manager.get_user_profile()
            to_email = user_profile.get('email', 'user@example.com')
        
        return self.send_email(to_email, subject, body)
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.scheduler_running = False
