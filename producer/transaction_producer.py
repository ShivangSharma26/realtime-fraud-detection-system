import json
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
# from kafka import KafkaProducer # Abhi comment out kiya hai

fake = Faker()

# --- Constants for Realistic Data ---
COUNTRIES = ["US", "GB", "DE", "IN", "CA", "AU"]
CHANNELS = ["web", "mobile", "pos"]
CURRENCIES = ["USD", "EUR", "INR", "GBP"]

# --- Path Setup for Local Logging ---
# Yeh script ke relative path se project root dhundta hai
BASE_DIR = Path(__file__).resolve().parents[1]   # realtime-anomaly-detection root
DATA_DIR = BASE_DIR / "data"
# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "transactions_log.jsonl"

print(f"Data Producer initialized. Local logs will be saved to: {LOG_FILE}")
# TODO: Add data generation functions
# TODO: Add Kafka connection and main loop