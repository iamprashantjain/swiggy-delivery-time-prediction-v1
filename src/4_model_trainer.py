from mylogging import logging as logger
from myexception import customexception
import pandas as pd
import yaml
import joblib
from sklearn.compose import TransformedTargetRegressor
from sklearn.preprocessing import PowerTransformer
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from sklearn.linear_model import LinearRegression
from pathlib import Path
from sklearn.ensemble import StackingRegressor

TARGET = "time_taken"


def load_data(data_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        logger.error(f"The file to load does not exist: {data_path}")
        raise FileNotFoundError(f"Data file not found at {data_path}")


def read_params(file_path):
    with open(file_path,"r") as f:
        params_file = yaml.safe_load(f)
    
    return params_file


def save_model(model, save_dir: Path, model_name: str):
    # form the save location
    save_location = save_dir / model_name
    # save the model
    joblib.dump(value=model,filename=save_location)
    
    
def save_transformer(transformer, save_dir: Path, transformer_name: str):
    # form the save location
    save_location = save_dir / transformer_name
    # save the transformer
    joblib.dump(transformer, save_location)
    
    
def train_model(model, X_train: pd.DataFrame, y_train):
    # fit on the data
    model.fit(X_train,y_train)
    return model


def make_X_and_y(data:pd.DataFrame, target_column: str):
    X = data.drop(columns=[target_column])
    y = data[target_column]
    return X, y



if __name__ == "__main__":
    # root path
    root_path = Path.cwd()
    # train data load path
    data_path = root_path / "artifacts" / "data" / "processed" / "train_trans.csv"
    # parameters file
    params_file_path = root_path / "params.yaml"
    
    # load the training data
    training_data = load_data(data_path)
    logger.info("Training Data read successfully")
    
    # split the data into X and y
    X_train, y_train = make_X_and_y(training_data, TARGET)
    logger.info("Dataset splitting completed")
    
    # model parameters
    model_params = read_params(params_file_path)['train']
    
    # rf_params
    rf_params = model_params['Random_Forest']
    logger.info("random forest parameters read")
    
    # build random forest model
    rf = RandomForestRegressor(**rf_params)
    logger.info("built random forest model")
    
    # light gbm params
    lgbm_params = model_params["LightGBM"]
    logger.info("Light GBM parameters read")
    lgbm = LGBMRegressor(**lgbm_params)
    logger.info("built Light GBM model")
    
    # meta model
    lr = LinearRegression()
    logger.info("Meta model built")
    
    # power transformer
    power_transform = PowerTransformer()
    logger.info("Target Transformer built")
    
    # form the stacking regressor
    stacking_reg = StackingRegressor(estimators=[("rf_model",rf),
                                                 ("lgbm_model",lgbm)],
                                     final_estimator=lr,
                                     cv=5,n_jobs=-1)
    logger.info("Stacking regressor built")
    
    # make the model wrapper
    model = TransformedTargetRegressor(regressor=stacking_reg,
                                       transformer=power_transform)
    logger.info("Models wrapped inside wrapper")
    
    # fit the model on training data
    train_model(model,X_train,y_train)
    logger.info("Model training completed")
    
    # model name
    model_filename = "model.joblib"
    # directory to save model
    model_save_dir = root_path / "artifacts" / "models"
    model_save_dir.mkdir(exist_ok=True)
    
    # extract the model from wrapper
    stacking_model = model.regressor_
    transformer = model.transformer_

    # save the model
    save_model(model=model,
            save_dir=model_save_dir,
            model_name=model_filename)
    logger.info("Trained model saved to location")
    
    # save the stacking model
    stacking_filename = "stacking_regressor.joblib"
    save_model(model=stacking_model,
            save_dir=model_save_dir,
            model_name=stacking_filename)
    logger.info("Trained model saved to location")
    
    # save the transformer
    transformer_filename = "power_transformer.joblib"
    transformer_save_dir = model_save_dir
    save_transformer(transformer, transformer_save_dir, transformer_filename)
    logger.info("Transformer saved to location")