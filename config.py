import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = "./energy_tracker.db"

# MQTT Configuration
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "ritesh651"
MQTT_PASSWORD = "ritesh651"
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "energy")

# ThingsBoard Configuration
THINGSBOARD_HOST = "demo.thingsboard.io"
THINGSBOARD_PORT = int(os.getenv("THINGSBOARD_PORT", "443"))
THINGSBOARD_USE_SSL = os.getenv("THINGSBOARD_USE_SSL", "true").lower() == "true"
THINGSBOARD_ACCESS_TOKEN = os.getenv("THINGSBOARD_ACCESS_TOKEN", "k2ktifgmlxnnlc8po2fm")

# OpenAI Configuration
OPENAI_API_KEY = "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"

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = "riteshg123098@gmail.com"
SMTP_PASSWORD = "Ritesh651"
FROM_EMAIL = "riteshg123098@gmail.com"

# Twilio Configuration (optional)
TWILIO_ACCOUNT_SID= 'SKbdcc34069bcfbf95c53a9f0213b68eba'
TWILIO_AUTH_TOKEN= 'RXHWKORZ4e5s2jcEzznJr4D6oDT3tTKs'
TWILIO_PHONE_NUMBER= 9579823812

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
