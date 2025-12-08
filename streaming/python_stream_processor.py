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