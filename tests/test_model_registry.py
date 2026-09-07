import pytest
import mlflow
from mlflow import MlflowClient
import dagshub
import json
import os
from dotenv import load_dotenv;load_dotenv()


# DAGS HUB CONFIGURATION
DAGSHUB_USERNAME = "iamprashantjain"
REPO_NAME = "swiggy-delivery-time-prediction-v1"

DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")

if not DAGSHUB_TOKEN:
    raise ValueError(
        "DAGSHUB_TOKEN is not set in the environment.\n"
        "Please add DAGSHUB_TOKEN to your .env file."
    )


os.environ["MLFLOW_TRACKING_USERNAME"] = DAGSHUB_USERNAME
os.environ["MLFLOW_TRACKING_PASSWORD"] = DAGSHUB_TOKEN

tracking_uri = (
    f"https://dagshub.com/"
    f"{DAGSHUB_USERNAME}/"
    f"{REPO_NAME}.mlflow"
)

mlflow.set_tracking_uri(tracking_uri)
logger.info(f"MLflow tracking URI: {tracking_uri}")



def load_model_information(file_path):
    with open(file_path) as f:
        run_info = json.load(f)
        
    return run_info

# set model name
model_name = load_model_information("run_information.json")["model_name"]



@pytest.mark.parametrize(argnames="model_name, stage",
                         argvalues=[(model_name, "Staging")])
def test_load_model_from_registry(model_name,stage):
    client = MlflowClient()
    latest_versions = client.get_latest_versions(name=model_name,stages=[stage])
    latest_version = latest_versions[0].version if latest_versions else None
    
    assert latest_version is not None, f"No model at {stage} stage"
    
    # load the model
    model_path = f"models:/{model_name}/{stage}"

    # load the latest model from model registry
    model = mlflow.sklearn.load_model(model_path)
    
    assert model is not None, "Failed to load model from registry"
    print(f"The {model_name} model with version {latest_version} was loaded successfully")
    
