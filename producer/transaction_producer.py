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
def generate_normal_tx():
    """Generates a typical, low-risk transaction."""
    user_id = f"user_{random.randint(1, 500)}"
    merchant_id = f"merchant_{random.randint(1, 100)}"
    # Expovariate distribution gives more small amounts, fewer large ones (realistic)
    amount = round(random.expovariate(1 / 40) + 1, 2)  # most < $100
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "merchant_id": merchant_id,
        "amount": amount,
        "currency": random.choice(CURRENCIES),
        "country": random.choice(COUNTRIES),
        "channel": random.choice(CHANNELS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Risk scores: lower is better for normal
        "device_score": round(random.uniform(0.2, 0.9), 2),
        "ip_risk_score": round(random.uniform(0.0, 0.8), 2),
    }

def generate_anomalous_tx():
    """Generates a high-risk transaction designed to be flagged."""
    tx = generate_normal_tx()
    # Inject weirdness: very large amount, odd country, high risk scores
    tx["amount"] = round(random.uniform(500, 5000), 2)
    tx["country"] = "NG"  # rare/unusual in our defined list
    tx["ip_risk_score"] = round(random.uniform(0.8, 1.0), 2) # High risk ip
    tx["device_score"] = round(random.uniform(0.0, 0.3), 2) # Low trust device
    return tx

# TODO: Add Kafka connection and main loop