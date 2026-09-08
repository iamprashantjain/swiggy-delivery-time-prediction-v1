import pytest
import mlflow
import dagshub
import json
from pathlib import Path
from sklearn.pipeline import Pipeline
import joblib
import pandas as pd
from sklearn.metrics import mean_absolute_error
from src.mylogging import logging as logger
from src.myexception import customexception
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


def load_transformer(transformer_path):
    transformer = joblib.load(transformer_path)
    return transformer

# set model name
model_name = load_model_information("run_information.json")["model_name"]
stage = "Staging"

# load the model
model_path = f"models:/{model_name}/{stage}"

# load the latest model from model registry
model = mlflow.sklearn.load_model(model_path)

# set the root path
root_path = Path(__file__).parent.parent

# load the preprocessor
preprocessor_path = root_path / "models" / "preprocessor.joblib"
preprocessor = load_transformer(preprocessor_path)


# build the model pipeline
model_pipe = Pipeline(steps=[
    ('preprocess',preprocessor),
    ("regressor",model)
])

test_data_path = root_path / "artifacts" / "data" / "interim" / "test.csv"

@pytest.mark.parametrize(argnames="model_pipe, test_data_path, threshold_error",
                        argvalues=[(model_pipe, test_data_path, 5)])
def test_model_performance(model_pipe,test_data_path,threshold_error):
    # load test data
    df = pd.read_csv(test_data_path)
    
    # drop the missing values
    df.dropna(inplace=True)
    
    # make X and y
    X = df.drop(columns=["time_taken"])
    y = df['time_taken']
    
    # get the predictions
    y_pred = model_pipe.predict(X)
    
    # calculate the mean error
    mean_error = mean_absolute_error(y,y_pred)
    
    # check for performance
    assert mean_error <= threshold_error, f"The model does not pass the performance threshold of {threshold_error} minutes"
    print("The avg error is", mean_error)
    
    print(f"The {model_name} model passed the performance test")
    