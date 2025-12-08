import json
import pandas as pd
from pathlib import Path

# --- Path Setup ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
INPUT_JSONL = DATA_DIR / "transactions_log.jsonl"
OUTPUT_PARQUET = DATA_DIR / "transactions.parquet"

def main():
    print(f"Reading raw data from: {INPUT_JSONL}")
    records = []
    try:
        with open(INPUT_JSONL, "r") as f:
            for line in f:
                # Kabhi kabhi aakhri line adhuri ho sakti hai, isliye try-except
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Error: File not found at {INPUT_JSONL}. Please run the producer first.")
        return

    if not records:
        print("No records found in the log file.")
        return

    print(f"Found {len(records)} records. Converting to DataFrame...")
    df = pd.DataFrame(records)

    # Convert timestamp string to datetime object for easier processing later
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    print(f"Saving processed data to: {OUTPUT_PARQUET}")
    # index=False ka matlab hai row numbers save nahi karne
    df.to_parquet(OUTPUT_PARQUET, index=False)
    print("Data preparation complete.")

if __name__ == "__main__":
    main()