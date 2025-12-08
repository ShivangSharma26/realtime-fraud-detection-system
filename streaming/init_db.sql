-- Drop tables if they already exist to start fresh
DROP TABLE IF EXISTS anomalies;
DROP TABLE IF EXISTS transactions_scored;

-- Table to store ALL transactions with their anomaly scores
CREATE TABLE transactions_scored (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20),
    merchant_id VARCHAR(20),
    amount DECIMAL(10, 2),
    currency VARCHAR(10),
    country VARCHAR(10),
    channel VARCHAR(10),
    timestamp TIMESTAMP,
    device_score DECIMAL(3, 2),
    ip_risk_score DECIMAL(3, 2),
    anomaly_score DECIMAL(10, 5), -- Raw score from Isolation Forest
    is_anomaly INTEGER            -- 1 for anomaly, 0 for normal
);

-- Table to store ONLY anomalies (for faster querying by dashboards)
CREATE TABLE anomalies (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20),
    merchant_id VARCHAR(20),
    amount DECIMAL(10, 2),
    currency VARCHAR(10),
    country VARCHAR(10),
    channel VARCHAR(10),
    timestamp TIMESTAMP,
    device_score DECIMAL(3, 2),
    ip_risk_score DECIMAL(3, 2),
    anomaly_score DECIMAL(10, 5),
    is_anomaly INTEGER
);

-- Create an index on timestamp for faster time-series queries
CREATE INDEX idx_scored_ts ON transactions_scored(timestamp);
CREATE INDEX idx_anomalies_ts ON anomalies(timestamp);