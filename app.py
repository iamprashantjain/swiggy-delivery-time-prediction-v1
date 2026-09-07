from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.pipeline import Pipeline
import uvicorn
import pandas as pd
import mlflow
import json
import joblib
import os
from mlflow import MlflowClient
from sklearn import set_config
from experiments.data_clean_utils import perform_data_cleaning
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set output as pandas
set_config(transform_output='pandas')

# DagsHub & MLflow configuration
DAGSHUB_USERNAME = "iamprashantjain"
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")
REPO_NAME = "swiggy-delivery-time-prediction-v1"

if not DAGSHUB_TOKEN:
    raise RuntimeError("DAGSHUB_TOKEN is not set in the environment.")

MLFLOW_TRACKING_URI = (
    f"https://dagshub.com/"
    f"{DAGSHUB_USERNAME}/{REPO_NAME}.mlflow"
)

os.environ["MLFLOW_TRACKING_URI"] = MLFLOW_TRACKING_URI
os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


# Data validation
class Data(BaseModel):
    ID: str
    Delivery_person_ID: str
    Delivery_person_Age: str
    Delivery_person_Ratings: str
    Restaurant_latitude: float
    Restaurant_longitude: float
    Delivery_location_latitude: float
    Delivery_location_longitude: float
    Order_Date: str
    Time_Orderd: str
    Time_Order_picked: str
    Weatherconditions: str
    Road_traffic_density: str
    Vehicle_condition: int
    Type_of_order: str
    Type_of_vehicle: str
    multiple_deliveries: str
    Festival: str
    City: str

def load_model_information(file_path):
    try:
        with open(file_path) as f:
            run_info = json.load(f)
        return run_info
    except FileNotFoundError:
        logger.error(f"Model information file {file_path} not found")
        raise

def load_transformer(transformer_path):
    try:
        transformer = joblib.load(transformer_path)
        return transformer
    except FileNotFoundError:
        logger.error(f"Transformer file {transformer_path} not found")
        raise

# MLflow client
client = MlflowClient()

# Global variables for model and preprocessor
_model_pipe = None
_model_name = None
_stage = None

def initialize_model():
    global _model_pipe, _model_name, _stage
    
    if _model_pipe is not None:
        return _model_pipe
    
    try:
        # Load model info
        model_info = load_model_information("run_information.json")
        _model_name = model_info['model_name']
        _stage = "Production"
        
        # Get latest model version
        latest_model_ver = client.get_latest_versions(name=_model_name, stages=[_stage])
        if not latest_model_ver:
            raise ValueError(f"No model found in {_stage} stage")
        
        logger.info(f"Latest model in production is version {latest_model_ver[0].version}")
        
        # Load model
        model_path = f"models:/{_model_name}/{_stage}"
        model = mlflow.sklearn.load_model(model_path)
        logger.info("Model loaded successfully")
        
        # Load preprocessor
        preprocessor_path = "models/preprocessor.joblib"
        preprocessor = load_transformer(preprocessor_path)
        
        # Build pipeline
        _model_pipe = Pipeline(steps=[
            ('preprocess', preprocessor),
            ("regressor", model)
        ])
        
        logger.info("Model pipeline built successfully")
        return _model_pipe
        
    except Exception as e:
        logger.error(f"Failed to initialize model: {str(e)}")
        raise

# Create the app
app = FastAPI(title="Delivery Time Prediction API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (create directory if it doesn't exist)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Initialize model on startup
@app.on_event("startup")
async def startup_event():
    initialize_model()

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        model_pipe = initialize_model()

        if model_pipe is None:
            raise HTTPException(
                status_code=503,
                detail="Model not initialized"
            )

        return {
            "status": "healthy",
            "model_name": _model_name,
            "stage": _stage
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )


# Home endpoint
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "model_name": _model_name or "Unknown",
            "stage": _stage or "Production"
        }
    )

# Prediction endpoint
@app.post(path="/predict")
async def do_predictions(data: Data):
    try:
        # Get the model pipeline
        model_pipe = initialize_model()
        if model_pipe is None:
            raise HTTPException(status_code=503, detail="Model not available")
        
        # Convert input to DataFrame
        pred_data = pd.DataFrame([data.model_dump()])
        
        # Clean the raw input data (prediction mode - no target column)
        cleaned_data = perform_data_cleaning(pred_data, is_training=False)
        
        # Get predictions
        predictions = model_pipe.predict(cleaned_data)[0]
        
        return {
            "prediction": float(predictions),
            "model_name": _model_name,
            "stage": _stage,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }, 500


if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=8000, reload=False)