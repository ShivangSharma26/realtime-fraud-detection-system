import json
import time
from typing import List
import os
import sys

import pandas as pd
from kafka import KafkaConsumer
from joblib import load
import psycopg2

# --- Path Setup to import from 'ml' folder ---
# Get the root directory of the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add root to sys.path if not already there
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import feature engineering logic from the other module
try:
    from ml.features import build_features, FEATURE_COLUMNS
    print("Successfully imported feature engineering module.")
except ImportError as e:
    print(f"Error importing from ml.features: {e}")
    sys.exit(1)

# --- Configuration Constants ---
KAFKA_BOOTSTRAP = "localhost:29092" # Docker se bahar access ke liye
KAFKA_TOPIC = "transactions_raw"

# PostgreSQL Database Config (Matches docker-compose.yml)
PG_HOST = "localhost"
# Note: Humne bahar ka port 5433 kar diya tha pichle step mein
PG_PORT = 5433 
PG_DB = "anomalies"
PG_USER = "app"
PG_PASSWORD = "app"

MODEL_PATH = os.path.join(ROOT_DIR, "models/isolation_forest.pkl")
THRESHOLD = 0.0 # Model score threshold for anomaly decision

# Streaming Batch Config
BATCH_SIZE = 100      # Process 100 records at a time
BATCH_TIMEOUT = 5     # OR process whatever we have after 5 seconds

print("Streaming processor configured.")
# TODO: Add database connection functions
# TODO: Add main streaming loop
# ... (uppar ka code same rahega)

def make_pg_conn():
    """Creates and returns a new PostgreSQL database connection."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def write_to_postgres(df: pd.DataFrame):
    """
    Writes a scored DataFrame to PostgreSQL tables.
    Inserts all rows into 'transactions_scored' and anomalies into 'anomalies'.
    """
    if df.empty:
        return

    conn = make_pg_conn()
    if not conn:
        return

    cur = conn.cursor()
    try:
        # Prepare data for insertion (convert DataFrame to list of tuples)
        # Ensure columns are in the exact same order as the SQL query below
        columns_to_insert = [
            "transaction_id", "user_id", "merchant_id", "amount",
            "currency", "country", "channel", "timestamp",
            "device_score", "ip_risk_score",
            "anomaly_score", "is_anomaly",
        ]

        # Select columns and convert to list of values
        rows_scored = df[columns_to_insert].values.tolist()

        # SQL query for inserting ALL scored transactions
        insert_tx = """
            INSERT INTO transactions_scored (
                transaction_id, user_id, merchant_id, amount,
                currency, country, channel, timestamp,
                device_score, ip_risk_score,
                anomaly_score, is_anomaly
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (transaction_id) DO NOTHING
        """
        # Bulk insert
        cur.executemany(insert_tx, rows_scored)

        # Filter for anomalies only
        anomalies = df[df["is_anomaly"] == 1]
        if not anomalies.empty:
            rows_anom = anomalies[columns_to_insert].values.tolist()

            # SQL query for inserting ONLY anomalies
            insert_anom = """
                INSERT INTO anomalies (
                    transaction_id, user_id, merchant_id, amount,
                    currency, country, channel, timestamp,
                    device_score, ip_risk_score,
                    anomaly_score, is_anomaly
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (transaction_id) DO NOTHING
            """
            cur.executemany(insert_anom, rows_anom)

        # Commit transaction and close connection
        conn.commit()
        # print(f"Successfully wrote {len(df)} records to database.")

    except Exception as e:
        print(f"Error writing to database: {e}")
        conn.rollback() # Undo changes if error happens
    finally:
        cur.close()
        conn.close()

# TODO: Add main streaming loop
# ... (uppar ka code same rahega)

def main():
    print(f"Loading ML model from: {MODEL_PATH}")
    try:
        model = load(MODEL_PATH)
        print("Model loaded successfully.")
    except FileNotFoundError:
        print(f"Error: Model not found at {MODEL_PATH}. Run ml/train_model.py first.")
        sys.exit(1)

    print(f"Connecting to Kafka topic '{KAFKA_TOPIC}'...")
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            # Automatically deserialize JSON data
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest", # Start reading new messages only
            # group_id="anomaly-detector-group" # Optional: for multiple consumers
        )
        print("Kafka Consumer connected.")
    except Exception as e:
         print(f"Error connecting to Kafka: {e}")
         sys.exit(1)

    buffer: List[dict] = []
    last_flush = time.time()

    print("Python streaming processor started! Waiting for data...")
    try:
        while True:
            # Poll for new messages (wait max 1 second)
            msg_pack = consumer.poll(timeout_ms=1000)

            any_records = False
            for tp, messages in msg_pack.items():
                for message in messages:
                    any_records = True
                    buffer.append(message.value)

            # Check conditions to process the batch
            now = time.time()
            time_up = (now - last_flush) >= BATCH_TIMEOUT
            buffer_full = len(buffer) >= BATCH_SIZE

            if buffer and (buffer_full or time_up):
                print(f"Scoring batch of {len(buffer)} rows (Time up: {time_up}, Full: {buffer_full})...")

                # 1. Convert buffer to DataFrame
                pdf = pd.DataFrame(buffer)

                # 2. Feature Engineering (Reusing logic from training)
                feat_df = build_features(pdf)
                X = feat_df[FEATURE_COLUMNS]

                # 3. Model Inference (Scoring)
                # decision_function gives a score (lower is more anomalous)
                scores = model.decision_function(X)
                pdf["anomaly_score"] = scores
                # If score is below threshold, mark as anomaly (1)
                pdf["is_anomaly"] = (pdf["anomaly_score"] < THRESHOLD).astype(int)

                # 4. Write results to Database
                write_to_postgres(pdf)

                anomaly_count = (pdf['is_anomaly']==1).sum()
                print(f"✔ Processed batch. Anomalies found: {anomaly_count}. (Took {round(time.time()-now, 2)}s)")

                # Reset buffer and timer
                buffer.clear()
                last_flush = now

            # If no new records, sleep briefly to reduce CPU usage
            if not any_records and not buffer:
                time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStreaming processor stopped by user.")
    finally:
        consumer.close()
        print("Kafka Connection closed.")

if __name__ == "__main__":
    main()