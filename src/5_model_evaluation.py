import pandas as pd
import joblib
import logging
import mlflow
import mlflow.data
import mlflow.sklearn
from mylogging import logging as logger
from myexception import customexception
import dagshub
from pathlib import Path
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import json
import os
from dotenv import load_dotenv; load_dotenv()


DAGSHUB_USERNAME = "iamprashantjain"
DAGSHUB_TOKEN = os.getenv("DAGSHUB_TOKEN")
REPO_NAME = 'swiggy-delivery-time-prediction-v1'

if not DAGSHUB_TOKEN:
    raise ValueError("DAGSHUB_TOKEN is not set in the environment.")

mlflow.set_tracking_uri(f"https://{DAGSHUB_USERNAME}:{DAGSHUB_TOKEN}"f"@dagshub.com/{DAGSHUB_USERNAME}/{REPO_NAME}.mlflow")

# set mlflow experiment name
mlflow.set_experiment("DVC Pipeline")

TARGET = "time_taken"


def load_data(data_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        logger.error(f"The file to load does not exist: {data_path}")
        raise FileNotFoundError(f"Data file not found at {data_path}")


def make_X_and_y(data: pd.DataFrame, target_column: str):
    X = data.drop(columns=[target_column])
    y = data[target_column]
    return X, y


def load_model(model_path: Path):
    model = joblib.load(model_path)
    return model


def save_model_info(save_json_path, run_id, artifact_path, model_name):
    info_dict = {
        "run_id": run_id,
        "artifact_path": artifact_path,
        "model_name": model_name
    }
    with open(save_json_path, "w") as f:
        json.dump(info_dict, f, indent=4)


if __name__ == "__main__":
    # root path
    root_path = Path.cwd()
    # train data load path
    train_data_path = root_path / "artifacts" / "data" / "processed" / "train_trans.csv"
    test_data_path = root_path / "artifacts" / "data" / "processed" / "test_trans.csv"
    # model path
    model_path = root_path / "artifacts" / "models" / "model.joblib"

    # load the training data
    train_data = load_data(train_data_path)
    logger.info("Train data loaded successfully")
    # load the test data
    test_data = load_data(test_data_path)
    logger.info("Test data loaded successfully")

    # split the train and test data
    X_train, y_train = make_X_and_y(train_data, TARGET)
    X_test, y_test = make_X_and_y(test_data, TARGET)
    logger.info("Data split completed")

    # load the model
    model = load_model(model_path)
    logger.info("Model Loaded successfully")

    # get the predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    logger.info("prediction on data complete")

    # calculate the train and test mae
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    logger.info("error calculated")

    # calculate the r2 scores
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    logger.info("r2 score calculated")

    # calculate cross val scores
    cv_scores = cross_val_score(model,
                                X_train,
                                y_train,
                                cv=5,
                                scoring="neg_mean_absolute_error",
                                n_jobs=-1)
    logger.info("cross validation complete")

    # mean cross val score
    mean_cv_score = -(cv_scores.mean())

    # log with mlflow
    with mlflow.start_run() as run:
        # set tags
        mlflow.set_tag("model", "Food Delivery Time Regressor")

        # log parameters
        mlflow.log_params(model.get_params())

        # log metrics
        mlflow.log_metric("train_mae", train_mae)
        mlflow.log_metric("test_mae", test_mae)
        mlflow.log_metric("train_r2", train_r2)
        mlflow.log_metric("test_r2", test_r2)
        mlflow.log_metric("mean_cv_score", -(cv_scores.mean()))

        # log individual cv scores
        mlflow.log_metrics({f"CV {num}": score for num, score in enumerate(-cv_scores)})

        # mlflow dataset input datatype
        train_data_input = mlflow.data.from_pandas(train_data, targets=TARGET)
        test_data_input = mlflow.data.from_pandas(test_data, targets=TARGET)

        # log input
        mlflow.log_input(dataset=train_data_input, context="training")
        mlflow.log_input(dataset=test_data_input, context="validation")

        # model signature
        model_signature = mlflow.models.infer_signature(
            model_input=X_train.sample(20, random_state=42),
            model_output=model.predict(X_train.sample(20, random_state=42))
        )

        # log the final model
        logger.info("Starting model logging to MLflow...")
        try:
            import shutil
            import os
            
            model_save_path = root_path / "artifacts" / "models" / "mlflow_model"
            if os.path.exists(model_save_path):
                shutil.rmtree(model_save_path)
            
            # 🔥 FIX: Define trusted types for LightGBM model
            TRUSTED_TYPES = [
                'collections.OrderedDict',
                'lightgbm.basic.Booster',
                'lightgbm.sklearn.LGBMRegressor',
                'sklearn.utils._bunch.Bunch'
            ]
            
            # Save model locally in MLflow format with trusted types
            mlflow.sklearn.save_model(
                sk_model=model, 
                path=model_save_path, 
                signature=model_signature,
                skops_trusted_types=TRUSTED_TYPES  # 🔥 THIS IS THE FIX!
            )
            
            # Log the directory as an artifact
            mlflow.log_artifacts(model_save_path, artifact_path="model")
            logger.info("Model logged successfully to MLflow as 'model' artifact folder")
            
            # Clean up local temp folder
            shutil.rmtree(model_save_path)
        except Exception as e:
            logger.error(f"Failed to log model to MLflow: {str(e)}")
            raise e

        # log other artifacts
        mlflow.log_artifact(root_path / "artifacts" / "models" / "stacking_regressor.joblib")
        mlflow.log_artifact(root_path / "artifacts" / "models" / "power_transformer.joblib")
        mlflow.log_artifact(root_path / "artifacts" / "models" / "preprocessor.joblib")

        # Verify internally
        client = mlflow.tracking.MlflowClient()
        artifacts = client.list_artifacts(run.info.run_id)
        logger.info(f"Verified artifacts in run: {[a.path for a in artifacts]}")

        # get the current run artifact uri
        artifact_uri = mlflow.get_artifact_uri()

        logger.info("Mlflow logging complete and model logged")

    # get the run id 
    run_id = run.info.run_id
    model_name = "delivery_time_pred_model"

    # save the model info
    save_json_path = root_path / "run_information.json"
    save_model_info(save_json_path=save_json_path,
                    run_id=run_id,
                    artifact_path=artifact_uri,
                    model_name="model")
    logger.info("Model Information saved")