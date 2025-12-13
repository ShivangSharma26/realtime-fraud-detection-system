# 🚨 Real-Time Fraud Detection System (MLOps Pipeline)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.0+-red.svg)](https://airflow.apache.org/)

## 🌟 Project Overview

This project implements a comprehensive **end-to-end MLOps pipeline** for detecting fraudulent transactions in real-time. The system is designed to:

- **Process streaming/near-real-time transaction data**
- **Run ML inference with low latency** using a trained classification model
- **Flag suspicious transactions** for immediate action
- **Automatically retrain models** on fresh data using orchestrated workflows
- **Scale horizontally** with containerized microservices

The entire workflow is automated using modern orchestration and containerization tools, creating a **reliable, scalable, and continuously deployed production system**.

---

## 🛠️ Technology Stack

| **Category** | **Technology** | **Purpose** |
|--------------|----------------|-------------|
| **Orchestration** | Apache Airflow | Schedules, manages, and monitors the entire data and ML pipeline (ETL, training, retraining) |
| **Data Transformation** | dbt (data build tool) | Defines and executes data cleaning and feature engineering logic in the warehouse |
| **Data Warehouse** | Snowflake / PostgreSQL | Scalable storage for feature stores and historical transaction data |
| **Data Streaming** | Pandas / Data Generator | Simulates real-time transaction data flow |
| **Machine Learning** | Scikit-learn (Random Forest) | Binary classification model to predict fraudulent transactions |
| **Model Serving** | FastAPI & Uvicorn | High-performance REST API for low-latency model inference |
| **Containerization** | Docker & Docker Compose | Packages the entire ecosystem for consistent deployment |
| **Database** | PostgreSQL | Metadata database for Airflow and transaction storage |

---

## 🏗️ System Architecture

The system follows a **layered MLOps architecture** optimized for production fraud detection:

### 1️⃣ **Data Simulation & Ingestion**
Simulated transaction data is generated and stored periodically to mimic real-world streaming behavior.

### 2️⃣ **Data Transformation (dbt)**
- Airflow triggers dbt models to create clean, feature-rich tables
- Calculates advanced features like transaction velocity, time deltas, location patterns
- Outputs structured data ready for model consumption

### 3️⃣ **ML Training Pipeline**
- Scheduled via Airflow DAGs
- Runs in a dedicated **Dockerized ML Trainer** service
- Fetches latest features from the transformed data layer
- Trains a fraud detection classifier (Random Forest/XGBoost)
- Saves the trained model (`fraud_model.pkl`) to a persistent shared volume

### 4️⃣ **Real-Time Model Serving (FastAPI)**
- Continuously running API service
- Loads the latest trained model automatically
- Accepts incoming transaction requests
- Extracts features and returns fraud predictions with **millisecond latency**

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Data Ingestion │────▶│ dbt Transform│────▶│  ML Training    │
│   (Simulated)   │     │   (Airflow)  │     │   (Airflow)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │ Model Storage   │
                                              │ (fraud_model)   │
                                              └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │   FastAPI       │
                                              │ Prediction API  │
                                              └─────────────────┘
```

---

## ⚙️ Setup and Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- ✅ **Docker Desktop** (running)
- ✅ **Git**
- ✅ **Snowflake/PostgreSQL credentials** (for data warehouse connection)

### Step 1: Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd realtime-fraud-detection-system
```

### Step 2: Configure Environment Variables

Create a `.env` file in the root directory with your configuration:

```bash
# --- Database Credentials (Snowflake/Postgres) ---
DB_ACCOUNT=<YOUR_DB_ACCOUNT>
DB_USER=<YOUR_DB_USER>
DB_PASSWORD=<YOUR_DB_PASSWORD>
DB_WAREHOUSE=<YOUR_DB_WAREHOUSE>
DB_DATABASE=<YOUR_DB_DATABASE>
DB_SCHEMA=FRAUD_SCHEMA

# --- Docker Volume Configuration (REQUIRED) ---
# Absolute path to this project folder on your host machine
PROJECT_PATH_ON_HOST=/absolute/path/to/realtime-fraud-detection-system
```

### Step 3: Build and Start Services

Build custom Docker images and launch the entire stack:

```bash
# Start all core services (Airflow, Postgres, etc.)
docker-compose up -d

# Build the ML Trainer service
docker-compose build ml-trainer

# Build the Fraud Detection API service
docker-compose build fraud-api
```

---

## 🚀 Running the Pipeline (Model Training)

### Access Airflow UI

1. Navigate to: **http://localhost:8080**
2. Login with default credentials:
   - **Username:** `admin`
   - **Password:** `admin`

### Trigger the Training Pipeline

1. Locate the DAG named: `fraud_model_retrain_pipeline`
2. Click the **▶️ trigger** button to start training
3. Monitor the progress in the DAG graph view
4. Once complete, the trained model will be saved and ready for serving

---

## 🖥️ Using the Fraud Prediction API

After successful training, the FastAPI service automatically loads the latest model.

### Health Check

```bash
curl http://localhost:8001/
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Fraud Detection API is running!"
}
```

### Interactive API Documentation

Visit: **http://localhost:8001/docs** for Swagger UI

### Making Predictions

**Endpoint:** `POST /predict`

**Example Request Body:**

```json
{
  "transaction_amount": 450.75,
  "time_since_last_txn": 1.5,
  "num_txns_last_hour": 12,
  "user_location_match": true
}
```

**Sample cURL Request:**

```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 450.75,
    "time_since_last_txn": 1.5,
    "num_txns_last_hour": 12,
    "user_location_match": true
  }'
```

**Expected Response:**

```json
{
  "prediction": 0,
  "probability": 0.982,
  "flag": "LEGITIMATE",
  "message": "Prediction served successfully in 5ms."
}
```

**Response Fields:**
- `prediction`: `0` (Legitimate) or `1` (Fraud)
- `probability`: Model confidence score (0-1)
- `flag`: Human-readable status
- `message`: Processing metadata

---

## 📊 Feature Engineering

The system automatically engineers the following features from raw transaction data:

| **Feature** | **Type** | **Description** |
|-------------|----------|-----------------|
| `transaction_amount` | Float | Dollar amount of the transaction |
| `time_since_last_txn` | Float | Minutes elapsed since user's last transaction |
| `num_txns_last_hour` | Integer | Count of transactions in the past 60 minutes |
| `user_location_match` | Boolean | Whether transaction location matches user profile |

Additional features can be added by modifying the dbt transformation models.

---

## 🔄 Model Retraining Workflow

The system supports **automated model retraining** via scheduled Airflow DAGs:

1. **Data Refresh:** New transaction data is ingested daily/hourly
2. **Feature Engineering:** dbt runs incremental transformations
3. **Model Training:** ML trainer fetches latest features and retrains
4. **Model Deployment:** New model is automatically picked up by the API (hot reload)
5. **Monitoring:** Performance metrics are logged to Airflow

You can customize the retraining schedule in the Airflow DAG definition.

---

## 🛑 Cleanup

### Stop All Services (Keep Data)

```bash
docker-compose down
```

### Stop and Remove Everything (Including Database)

```bash
docker-compose down -v
```

---

## 📁 Project Structure

```
realtime-fraud-detection-system/
├── airflow/
│   ├── dags/              # Airflow DAG definitions
│   ├── plugins/           # Custom Airflow operators
│   └── logs/              # Airflow execution logs
├── dbt/
│   ├── models/            # dbt transformation models
│   └── profiles.yml       # Database connection profiles
├── ml_trainer/
│   ├── train.py           # Model training script
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # ML trainer container
├── fraud_api/
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # API dependencies
│   └── Dockerfile         # API container
├── models/                # Saved ML models (mounted volume)
├── docker-compose.yml     # Multi-container orchestration
├── .env                   # Environment variables
└── README.md              # This file
```

---

## 🧪 Testing

### Unit Tests

```bash
# Test dbt transformations
cd dbt && dbt test

# Test ML trainer
cd ml_trainer && pytest tests/

# Test API endpoints
cd fraud_api && pytest tests/
```

### Load Testing the API

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run 1000 requests with 10 concurrent connections
ab -n 1000 -c 10 -T 'application/json' \
   -p transaction.json \
   http://localhost:8001/predict
```

---

## 🔐 Security Considerations

- 🔒 Store credentials in `.env` (never commit to Git)
- 🔒 Use secrets management (e.g., AWS Secrets Manager) in production
- 🔒 Enable HTTPS/TLS for API endpoints
- 🔒 Implement API authentication (OAuth2/JWT tokens)
- 🔒 Apply rate limiting on the prediction endpoint

---

## 📈 Future Enhancements

- [ ] Implement real Kafka/Kinesis streaming ingestion
- [ ] Add model monitoring dashboard (MLflow)
- [ ] Deploy to Kubernetes for horizontal scaling
- [ ] Integrate A/B testing for model versions
- [ ] Add explainability (SHAP/LIME) to predictions
- [ ] Implement feedback loop for continuous learning

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **SHIVANG SHARMA** - *Initial work* - [YourGitHub](https://github.com/ShivangSharma26)

---

## 🙏 Acknowledgments

- Apache Airflow community
- dbt Labs for the amazing transformation framework
- FastAPI for blazing-fast API performance
- Scikit-learn for robust ML algorithms



---

**⭐ If you find this project helpful, please give it a star!**
