import json
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from faker import Faker
from kafka import KafkaProducer # Uncommented

fake = Faker()

# Initialize Kafka Producer
# NOTE: 'localhost:29092' is exposed by Docker for external clients (like this script)
producer = KafkaProducer(
    bootstrap_servers="localhost:29092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

COUNTRIES = ["US", "GB", "DE", "IN", "CA", "AU"]
CHANNELS = ["web", "mobile", "pos"]
CURRENCIES = ["USD", "EUR", "INR", "GBP"]

# --- set up data folder & log file relative to project root ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / "transactions_log.jsonl"
# ------------------------------------------------------------------

def generate_normal_tx():
    user_id = f"user_{random.randint(1, 500)}"
    merchant_id = f"merchant_{random.randint(1, 100)}"
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
        "device_score": round(random.uniform(0.2, 0.9), 2),
        "ip_risk_score": round(random.uniform(0.0, 0.8), 2),
    }

def generate_anomalous_tx():
    tx = generate_normal_tx()
    # Inject weirdness: very large amount, odd country, high risk
    tx["amount"] = round(random.uniform(500, 5000), 2)
    tx["country"] = "NG"  # rare/unusual
    tx["ip_risk_score"] = round(random.uniform(0.8, 1.0), 2)
    tx["device_score"] = round(random.uniform(0.0, 0.3), 2)
    return tx

def main():
    print(f"Starting transaction producer. Logging to {LOG_FILE}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            # 95% normal, 5% anomalous randomly setup
            if random.random() < 0.95:
                tx = generate_normal_tx()
            else:
                tx = generate_anomalous_tx()
                print(f"[ALERT] Generated anomaly: {tx['transaction_id']}")

            # 1. send to Kafka
            producer.send("transactions_raw", tx)

            # 2. mirror to local file for training later
            with LOG_FILE.open("a") as f:
                f.write(json.dumps(tx) + "\n")

            # print("Produced:", tx["transaction_id"], tx["amount"]) # Thoda kam shor karte hain
            time.sleep(0.05)  # ~20 tx/sec

    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
        producer.close()

if __name__ == "__main__":
    main()