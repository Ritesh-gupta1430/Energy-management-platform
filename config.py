import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///energy_tracker.db")

# MQTT Configuration
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "test.mosquitto.org")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "energy")

# ThingsBoard Configuration
THINGSBOARD_HOST = os.getenv("THINGSBOARD_HOST", "demo.thingsboard.io")
THINGSBOARD_PORT = int(os.getenv("THINGSBOARD_PORT", "443"))
THINGSBOARD_USE_SSL = os.getenv("THINGSBOARD_USE_SSL", "true").lower() == "true"
THINGSBOARD_ACCESS_TOKEN = os.getenv("THINGSBOARD_ACCESS_TOKEN", "")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Application Configuration
ENERGY_COST_PER_KWH = float(os.getenv("ENERGY_COST_PER_KWH", "0.12"))
HIGH_USAGE_THRESHOLD = float(os.getenv("HIGH_USAGE_THRESHOLD", "5.0"))
ANOMALY_DETECTION_THRESHOLD = float(os.getenv("ANOMALY_DETECTION_THRESHOLD", "2.0"))

# Gamification Settings
POINTS_PER_KWH_SAVED = int(os.getenv("POINTS_PER_KWH_SAVED", "10"))
POINTS_MANUAL_INPUT = int(os.getenv("POINTS_MANUAL_INPUT", "5"))
POINTS_DAILY_LOGIN = int(os.getenv("POINTS_DAILY_LOGIN", "2"))

# Session Configuration
SESSION_SECRET = os.getenv("SESSION_SECRET", "default_secret_key")
