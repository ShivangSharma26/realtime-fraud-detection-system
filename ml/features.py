import pandas as pd

# --- Configuration ---
# Yeh woh columns hain jo hum model ko training ke liye denge
FEATURE_COLUMNS = [
    "amount",
    "device_score",
    "ip_risk_score",
    "is_high_risk_country",
    "is_night",
    # "hour" ko hum hata rahe hain kyunki "is_night" uska better version hai
]

# Countries considered higher risk (based on our producer logic)
HIGH_RISK_COUNTRIES = {"NG", "RU", "BR"}

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a raw transactions DataFrame and adds engineered features
    required for the Machine Learning model.
    """
    # Create a copy to avoid settingWithCopy warnings on incoming dataframes
    df = df.copy()

    # Ensure timestamp is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- Feature Engineering ---

    # 1. Extract Hour of day from timestamp
    df["hour"] = df["timestamp"].dt.hour

    # 2. Create 'is_night' flag (e.g., transactions between 10 PM and 6 AM)
    # Raat ke transaction fraud hone ke chance zyada hote hain
    df["is_night"] = ((df["hour"] < 6) | (df["hour"] > 22)).astype(int)

    # 3. Create 'is_high_risk_country' flag
    df["is_high_risk_country"] = df["country"].isin(HIGH_RISK_COUNTRIES).astype(int)

    # 4. Ensure numerical columns are floats (important for scikit-learn)
    df["amount"] = df["amount"].astype(float)
    df["device_score"] = df["device_score"].astype(float)
    df["ip_risk_score"] = df["ip_risk_score"].astype(float)

    return df