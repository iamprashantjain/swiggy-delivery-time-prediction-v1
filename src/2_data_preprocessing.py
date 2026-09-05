import pandas as pd
from sklearn.model_selection import train_test_split
import yaml
import logging
from pathlib import Path
from mylogging import logging as logger
from myexception import customexception
import os
import sys

TARGET = "time_taken"

def load_data(data_path: Path) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        data_path: Path to CSV file
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        customexception: If file not found or other errors
    """
    try:
        if not data_path.exists():
            raise customexception(f"Data file not found at: {data_path}")
            
        df = pd.read_csv(data_path)
        logger.info(f"Successfully loaded {len(df)} rows from {data_path}")
        return df
        
    except pd.errors.EmptyDataError:
        logger.error(f"File is empty: {data_path}")
        raise customexception(f"Empty data file: {data_path}")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise customexception(f"Failed to load data: {e}")


def split_data(data: pd.DataFrame, test_size: float, random_state: int):
    """
    Split data into train and test sets.
    
    Args:
        data: Input DataFrame
        test_size: Proportion of test data
        random_state: Random seed for reproducibility
        
    Returns:
        tuple: (train_data, test_data)
        
    Raises:
        customexception: If data is empty or invalid
    """
    try:
        if data.empty:
            raise customexception("Cannot split empty DataFrame")
        
        if not (0 < test_size < 1):
            raise customexception(f"Invalid test_size: {test_size}. Must be between 0 and 1")
        
        train_data, test_data = train_test_split(
            data, 
            test_size=test_size, 
            random_state=random_state
        )
        
        logger.info(f"Data split: Train={len(train_data)}, Test={len(test_data)}")
        return train_data, test_data
        
    except Exception as e:
        logger.error(f"Error splitting data: {e}")
        raise customexception(f"Failed to split data: {e}")


def read_params(file_path: Path):
    """
    Read parameters from YAML file.
    
    Args:
        file_path: Path to parameters YAML file
        
    Returns:
        dict: Parameters dictionary
        
    Raises:
        customexception: If file not found or invalid YAML
    """
    try:
        if not file_path.exists():
            raise customexception(f"Parameters file not found: {file_path}")
            
        with open(file_path, "r") as f:
            params_file = yaml.safe_load(f)
            
        if params_file is None:
            raise customexception(f"Empty or invalid YAML file: {file_path}")
            
        logger.info(f"Parameters loaded from: {file_path}")
        return params_file
        
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML format: {e}")
        raise customexception(f"Failed to parse YAML file: {e}")
    except Exception as e:
        logger.error(f"Error reading parameters: {e}")
        raise customexception(f"Failed to read parameters: {e}")


def save_data(data: pd.DataFrame, save_path: Path) -> None:
    """
    Save DataFrame to CSV.
    
    Args:
        data: DataFrame to save
        save_path: Path where to save
        
    Raises:
        customexception: If save fails
    """
    try:
        # Create parent directories if they don't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data.to_csv(save_path, index=False)
        logger.info(f"Data saved to: {save_path}")
        
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        raise customexception(f"Failed to save data to {save_path}: {e}")


def validate_data(data: pd.DataFrame) -> None:
    """
    Validate data before splitting.
    
    Args:
        data: DataFrame to validate
        
    Raises:
        customexception: If validation fails
    """
    try:
        if data.empty:
            raise customexception("Data is empty")
            
        if TARGET not in data.columns:
            raise customexception(f"Target column '{TARGET}' not found in data")
            
        logger.info("Data validation successful")
        
    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        raise customexception(f"Validation failed: {e}")


if __name__ == "__main__":
    try:
        # Set file paths
        root_path = Path.cwd()
        data_path = root_path / "artifacts" / "data" / "cleaned" / "swiggy_cleaned.csv"
        
        # Save data directory
        save_data_dir = root_path / "artifacts" / "data" / "interim"
        save_data_dir.mkdir(exist_ok=True, parents=True)
        
        # Train and test data save paths
        train_filename = "train.csv"
        test_filename = "test.csv"
        save_train_path = save_data_dir / train_filename
        save_test_path = save_data_dir / test_filename
        
        # Parameters file
        params_file_path = root_path / "params.yaml"
        
        # Load the cleaned data
        logger.info("Loading cleaned data...")
        df = load_data(data_path)
        
        # Validate data
        validate_data(df)
        
        # Read the parameters
        logger.info("Reading parameters...")
        parameters = read_params(params_file_path)['data_preprocessing']
        test_size = parameters['test_size']
        random_state = parameters['random_state']
        logger.info(f"Parameters: test_size={test_size}, random_state={random_state}")
        
        # Split into train and test data
        logger.info("Splitting data...")
        train_data, test_data = split_data(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
        
        # Save the train and test data
        data_subsets = [train_data, test_data]
        data_paths = [save_train_path, save_test_path]
        filename_list = [train_filename, test_filename]
        
        for filename, path, data in zip(filename_list, data_paths, data_subsets):
            save_data(data=data, save_path=path)
            logger.info(f"{filename.replace('.csv', '')} data saved")
            
        logger.info("Data preparation completed successfully!")
        
    except customexception as e:
        logger.error(f"Custom exception: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)