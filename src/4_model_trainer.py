from mylogging import logging
from myexception import customexception
import os
import sys
import pandas as pd
import joblib
import yaml
from sklearn.linear_model import LogisticRegression


def load_params(params_path: str) -> dict:
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logging.info("Parameters loaded from %s", params_path)
        return params
    except Exception as e:
        logging.info("Error loading params.yaml")
        raise customexception(e, sys)


def load_data(file_path: str):
    try:
        df = pd.read_csv(file_path)
        X = df.drop(columns=["sentiment"]).values
        y = df["sentiment"].values
        logging.info("Data loaded from %s", file_path)
        return X, y
    except Exception as e:
        logging.info(f"Error loading data from {file_path}")
        raise customexception(e, sys)


def train_model(X_train, y_train, model_params):
    try:
        model = LogisticRegression(**model_params)
        model.fit(X_train, y_train)
        logging.info("Model training completed.")
        return model
    except Exception as e:
        logging.info("Error during model training.")
        raise customexception(e, sys)


def save_model(model, model_path):
    try:
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        logging.info(f"Model saved at {model_path}")
    except Exception as e:
        logging.info("Error saving model.")
        raise customexception(e, sys)


def main():
    try:
        params = load_params("params.yaml")
        trainer_params = params['model_trainer']
        model_params = trainer_params['model_params']

        input_train = trainer_params['input_train']
        output_model_path = trainer_params['output_model_path']

        X_train, y_train = load_data(input_train)

        model = train_model(X_train, y_train, model_params)

        save_model(model, output_model_path)

        logging.info("Model training pipeline completed.")

    except Exception as e:
        logging.info("Exception in model_trainer main function.")
        raise customexception(e, sys)


if __name__ == "__main__":
    main()