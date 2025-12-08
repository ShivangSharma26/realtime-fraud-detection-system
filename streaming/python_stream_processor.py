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