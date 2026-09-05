import numpy as np
import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import logging
import mlflow
import mlflow.sklearn
import dagshub
from mylogging import logging
from myexception import customexception
import os
import sys
from dotenv import load_dotenv;load_dotenv()
import joblib

DAGSHUB_USERNAME = "iamprashantjain"
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")
REPO_NAME = "ml-pipeline-demo-v1"

if not DAGSHUB_TOKEN:
    raise ValueError("DAGSHUB_TOKEN is not set in the environment.")

mlflow.set_tracking_uri(f"https://{DAGSHUB_USERNAME}:{DAGSHUB_TOKEN}"f"@dagshub.com/{DAGSHUB_USERNAME}/{REPO_NAME}.mlflow")


def load_model(file_path: str):
    try:
        model = joblib.load(file_path)
        logging.debug('Model loaded from %s', file_path)
        return model
    except Exception as e:
        logging.error('Error loading model: %s', e)
        raise

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        logging.debug('Data loaded from %s', file_path)
        return df
    except pd.errors.ParserError as e:
        logging.error('Failed to parse the CSV file: %s', e)
        raise
    except Exception as e:
        logging.error('Unexpected error occurred while loading the data: %s', e)
        raise

def evaluate_model(clf, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Evaluate the model and return the evaluation metrics."""
    try:
        y_pred = clf.predict(X_test)
        y_pred_proba = clf.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)

        metrics_dict = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'auc': auc
        }
        logging.debug('Model evaluation metrics calculated')
        return metrics_dict
    except Exception as e:
        logging.error('Error during model evaluation: %s', e)
        raise

def save_metrics(metrics: dict, file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as file:
            json.dump(metrics, file, indent=4)

        logging.debug('Metrics saved to %s', file_path)

    except Exception as e:
        logging.error('Error occurred while saving the metrics: %s', e)
        raise

def save_model_info(run_id: str, model_path: str, file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        model_info = {
            'run_id': run_id,
            'model_path': model_path
        }

        with open(file_path, 'w') as file:
            json.dump(model_info, file, indent=4)

        logging.debug('Model info saved to %s', file_path)

    except Exception as e:
        logging.error('Error occurred while saving the model info: %s', e)
        raise

def main():
    mlflow.set_experiment("dvc-pipeline")

    with mlflow.start_run() as run:
        try:
            clf = load_model(
                './artifacts/model/logistic_regression_model.pkl'
            )

            test_data = load_data(
                './artifacts/data/vectorized/test_vectorized.csv'
            )

            X_test = test_data.iloc[:, :-1].values
            y_test = test_data.iloc[:, -1].values

            metrics = evaluate_model(clf, X_test, y_test)

            save_metrics(
                metrics,
                'reports/metrics.json'
            )

            # Log metrics
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)

            # Log model parameters
            if hasattr(clf, 'get_params'):
                params = clf.get_params()

                for param_name, param_value in params.items():
                    mlflow.log_param(param_name, param_value)

            # Log model
            mlflow.sklearn.log_model(clf, "model")

            # Save experiment information
            save_model_info(
                run.info.run_id,
                "model",
                'reports/experiment_info.json'
            )

            # Log artifacts
            mlflow.log_artifact('reports/metrics.json')
            mlflow.log_artifact('reports/experiment_info.json')

            if os.path.exists('model_evaluation_errors.log'):
                mlflow.log_artifact('model_evaluation_errors.log')

        except Exception as e:
            logging.error('Failed to complete the model evaluation process: %s',e)
            print(f"Error: {e}")
            raise

if __name__ == '__main__':
    main()