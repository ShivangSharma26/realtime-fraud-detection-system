import pandas as pd
from pathlib import Path
from joblib import dump
from sklearn.ensemble import IsolationForest

# Hum apni banayi hui features file ko import kar rahe hain
from features import build_features, FEATURE_COLUMNS

# --- Path Setup ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
INPUT_PARQUET = DATA_DIR / "transactions.parquet"
MODEL_PATH = MODELS_DIR / "isolation_forest.pkl"

# Ensure models directory exists
MODELS_DIR.mkdir(exist_ok=True)

def main():
    print(f"Loading training data from: {INPUT_PARQUET}")
    try:
        df = pd.read_parquet(INPUT_PARQUET)
    except FileNotFoundError:
         print(f"Error: {INPUT_PARQUET} not found. Run ml/prepare_data.py first.")
         return

    print("Building features for training...")
    df_feat = build_features(df)

    # Sirf feature columns ko select karo training ke liye
    X = df_feat[FEATURE_COLUMNS]

    print(f"Training model on {len(X)} records with features: {FEATURE_COLUMNS}")
    print("Initializing Isolation Forest...")

    # --- Model Configuration ---
    model = IsolationForest(
        n_estimators=200,   # Number of trees in the forest
        contamination=0.05, # Hum assume kar rahe hain ki data mein ~5% fraud hai (humare producer ke logic ke hisab se)
        random_state=42,    # For reproducible results
        n_jobs=-1,          # Use all available CPU cores
        verbose=0
    )

    print("Fitting model to data...")
    model.fit(X)

    print(f"Saving trained model to: {MODEL_PATH}")
    dump(model, MODEL_PATH)
    print("Model training complete successfully!")

if __name__ == "__main__":
    main()