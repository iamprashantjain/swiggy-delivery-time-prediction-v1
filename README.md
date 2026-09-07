# Swiggy Delivery Time Prediction - End-to-End MLOps Project

A complete production-grade MLOps pipeline for predicting food delivery times. Built with MLflow, DVC, FastAPI, Docker, and AWS.

## Table of Contents
- [Problem Statement](#problem-statement)
- [ML Workflow](#ml-workflow)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [ML Pipeline](#ml-pipeline)
- [API Usage](#api-usage)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Problem Statement
Predict food delivery times accurately using historical delivery data. Built an end-to-end MLOps system that takes raw data to production deployment with full automation.

## ML Workflow

### 1. Data Gathering
- Web scraping
- API extraction
- Database extraction
- Stakeholder provided data

### 2. Data Assessment
- Explore data using pandas
- Identify data quality issues
- Document cleaning requirements

### 3. Data Cleaning
- Handle missing values
- Fix data types
- Remove duplicates
- Standardize formats

### 4. EDA (Exploratory Data Analysis)
- Univariate analysis
- Bivariate analysis
- Multivariate analysis
- Understand target column relationships
- Identify new feature opportunities

### 5. Data Transformation & Feature Engineering
- Create new features
- Transform existing features
- Encode categorical variables
- Scale numerical features

### 6. EDA & Hypothesis Testing
- Second round of EDA after feature engineering
- Statistical hypothesis testing
- Validate assumptions

### 7. Experiments
- Base model development
- Multi-model comparison
- Hyperparameter tuning
- Best model selection

### 8. DVC Pipeline
- Data cleaning
- Data preprocessing
- Data transformation
- Model training
- Model evaluation

### 9. MLflow Integration
- Log models, preprocessors, and transformers
- Save run information in `run_information.json`
- Track experiments and parameters
- Model registry for versioning

### 10. FastAPI Application
- Pydantic models for validation
- Uvicorn server for fast predictions
- Swagger UI for testing
- RESTful endpoints

## Tech Stack

### ML & Data
- **Python 3.11**
- **Scikit-learn** - ML algorithms
- **Pandas, NumPy** - Data processing
- **Matplotlib, Seaborn** - Visualization

### MLOps
- **MLflow** - Experiment tracking & model registry
- **DagsHub** - ML platform & hosting
- **DVC** - Data version control
- **FastAPI** - API framework
- **Uvicorn** - ASGI server

### DevOps
- **Docker** - Containerization
- **AWS ECR** - Container registry
- **GitHub Actions** - CI/CD
- **AWS** - Deployment (EC2, ECS, EKS)

## Project Structure
```
swiggy-delivery-time-prediction-v1/
├── .dvc/                    # DVC configuration
├── .github/workflows/       # GitHub Actions CI/CD
├── deploy/scripts/          # Deployment scripts
├── experiments/             # ML experiments
├── models/                  # Saved models
├── src/                     # Source code
├── static/                  # Static files
├── templates/               # HTML templates
├── tests/                   # Unit tests
├── app.py                   # FastAPI application
├── appspec.yml              # CodeDeploy configuration
├── dockerfile               # Docker configuration
├── dvc.lock                 # DVC lock file
├── dvc.yaml                 # DVC pipeline
├── params.yaml              # Pipeline parameters
├── requirements.txt         # Python dependencies
├── requirements_docker.txt  # Docker dependencies
└── user_data_script.txt     # EC2 setup script
```

## Setup & Installation

### Local Setup
```bash
# Clone repository
git clone https://github.com/iamprashantjain/swiggy-delivery-time-prediction-v1.git
cd swiggy-delivery-time-prediction-v1

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull data from DVC
dvc pull

# Run DVC pipeline
dvc repro
```

### Docker Setup
```bash
# Build Docker image
docker build -t delivery-time-prediction-api .

# Run container
docker run -d --name delivery-api -p 8000:8000 \
  -e DAGSHUB_TOKEN="your_token" \
  delivery-time-prediction-api
```

## ML Pipeline

### DVC Pipeline Stages
```yaml
stages:
  data_cleaning:
    cmd: python experiments/data_clean.py
    deps:
    - artifacts/data/raw/swiggy.csv
    outs:
    - artifacts/data/processed/cleaned_data.csv

  data_preprocessing:
    cmd: python experiments/preprocess.py
    deps:
    - artifacts/data/processed/cleaned_data.csv
    outs:
    - artifacts/data/processed/preprocessed_data.csv

  model_training:
    cmd: python experiments/train.py
    deps:
    - artifacts/data/processed/preprocessed_data.csv
    outs:
    - models/model.pkl
    metrics:
    - metrics.json
```

### Model Registry (MLflow)
- Models automatically versioned
- Staging → Production promotion
- Performance metrics tracked
- Rollback capabilities

## 🔌 API Usage

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/predict` | POST | Prediction endpoint |

### Sample Request
```json
{
  "ID": "0x1",
  "Delivery_person_ID": "BANGRES11DEL01",
  "Delivery_person_Age": "30",
  "Delivery_person_Ratings": "4.8",
  "Restaurant_latitude": 12.9716,
  "Restaurant_longitude": 77.5946,
  "Delivery_location_latitude": 12.9352,
  "Delivery_location_longitude": 77.6245,
  "Order_Date": "2022-03-15",
  "Time_Orderd": "11:30",
  "Time_Order_picked": "11:45",
  "Weatherconditions": "Sunny",
  "Road_traffic_density": "High",
  "Vehicle_condition": 2,
  "Type_of_order": "Meal",
  "Type_of_vehicle": "motorcycle",
  "multiple_deliveries": "1",
  "Festival": "No",
  "City": "Metropolitian"
}
```

### Sample Response
```json
{
  "prediction": 25.5,
  "model_name": "delivery-time-prediction-model",
  "stage": "Production",
  "success": true
}
```

## CI/CD Pipeline

### GitHub Actions Workflow
1. **Performance Testing**
   - Validate model against thresholds (RMSE, R², MAE)
   - Generate performance reports

2. **Model Promotion**
   - Promote to "Production" stage in MLflow
   - Log metadata and performance metrics

3. **API Testing**
   - Test `/health`, `/predict`, `/docs` endpoints
   - Validate response times (<500ms)
   - Edge case handling

4. **Docker Build & Push**
   - Build production Docker image
   - Push to AWS ECR
   - Tag with commit SHA

```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Pull DVC data
        run: dvc pull
      
      - name: Run performance tests
        run: python tests/performance_test.py
      
      - name: Build and push Docker image
        run: |
          docker build -t delivery-time-prediction-api .
          docker push $ECR_REGISTRY/delivery-time-prediction-api
```

## Deployment Options

### 1. EC2 + CodeDeploy
- Auto Scaling Groups
- Load Balancer
- Blue/Green deployments
- Manual configuration via AWS Console

**Setup:**
```bash
# Create EC2 instance with user data
aws ec2 run-instances \
  --user-data file://user_data_script.txt \
  --iam-instance-profile Name=EC2-ECR-Pull-Role

# Deploy using CodeDeploy
aws deploy create-deployment \
  --application-name delivery-api-app \
  --deployment-group-name delivery-api-group
```

### 2. ECS (Elastic Container Service)
- Serverless with Fargate
- Automatic scaling
- Service discovery
- Load balancing

**Setup:**
```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster delivery-api-cluster \
  --service-name delivery-api-service \
  --task-definition delivery-time-prediction-api \
  --desired-count 2 \
  --launch-type FARGATE
```

### 3. EKS (Elastic Kubernetes Service)
- Full Kubernetes control
- Horizontal Pod Autoscaling
- Ingress controllers
- Helm charts support

**Setup:**
```bash
# Create EKS cluster
eksctl create cluster \
  --name delivery-api-cluster \
  --nodegroup-name standard-workers \
  --nodes 3

# Deploy to EKS
kubectl apply -f k8s/deployment.yaml
```

## Monitoring & Observability
- MLflow for model performance monitoring
- Health checks at `/health` endpoint
- API response time tracking
- CloudWatch metrics (planned)
- Prometheus/Grafana integration (planned)

## Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [MLflow](https://mlflow.org/) - Experiment tracking
- [DVC](https://dvc.org/) - Data version control
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [DagsHub](https://dagshub.com/) - ML platform
- [AWS](https://aws.amazon.com/) - Cloud services

## Connect with Me
- **GitHub**: [iamprashantjain](https://github.com/iamprashantjain)
- **LinkedIn**: [Prashant Jain](https://linkedin.com/in/iamprashantjain)

---

**⭐ Star this repo if you found it helpful!**