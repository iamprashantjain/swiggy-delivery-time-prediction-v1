import numpy as np
import pandas as pd
from pathlib import Path
from mylogging import logging as logger
from myexception import customexception
import os
import sys

# Constants
EARTH_RADIUS_KM = 6371
MIN_AGE = 18
MAX_RATING = 5
LOCATION_THRESHOLD = 1.0
TIME_BINS = [0, 6, 12, 17, 20, 24]
TIME_LABELS = ["after_midnight", "morning", "afternoon", "evening", "night"]
DISTANCE_BINS = [0, 5, 10, 15, 25]
DISTANCE_LABELS = ["short", "medium", "long", "very_long"]

columns_to_drop = [
    'rider_id',
    'restaurant_latitude',
    'restaurant_longitude',
    'delivery_latitude',
    'delivery_longitude',
    'order_date',
    "order_time_hour",
    "order_day",
    "city_name",
    "order_day_of_week",
    "order_month"
]


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
        
        if data_path.stat().st_size == 0:
            raise customexception(f"Data file is empty: {data_path}")
        
        df = pd.read_csv(data_path)
        logger.info(f"Data loaded successfully from {data_path}")
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        return df
        
    except pd.errors.EmptyDataError:
        logger.error(f"File is empty: {data_path}")
        raise customexception(f"Empty data file: {data_path}")
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV: {e}")
        raise customexception(f"Failed to parse CSV file: {e}")
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise customexception(f"Failed to load data: {e}")


def change_column_names(data: pd.DataFrame) -> pd.DataFrame:
    """
    Rename columns to standard names.
    
    Args:
        data: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with renamed columns
        
    Raises:
        customexception: If column renaming fails
    """
    try:
        renamed_data = (
            data.rename(str.lower, axis=1)
            .rename({
                "delivery_person_id": "rider_id",
                "delivery_person_age": "age",
                "delivery_person_ratings": "ratings",
                "delivery_location_latitude": "delivery_latitude",
                "delivery_location_longitude": "delivery_longitude",
                "time_orderd": "order_time",
                "time_order_picked": "order_picked_time",
                "weatherconditions": "weather",
                "road_traffic_density": "traffic",
                "city": "city_type",
                "time_taken(min)": "time_taken"
            }, axis=1)
        )
        logger.info("Column names renamed successfully")
        return renamed_data
        
    except Exception as e:
        logger.error(f"Error renaming columns: {e}")
        raise customexception(f"Failed to rename columns: {e}")


def data_cleaning(data: pd.DataFrame) -> pd.DataFrame:
    """
    Perform main data cleaning operations.
    
    Args:
        data: Input DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
        
    Raises:
        customexception: If cleaning fails
    """
    try:
        # Remove minors
        minors_data = data.loc[data['age'].astype('float') < MIN_AGE]
        minor_index = minors_data.index.tolist()
        if minor_index:
            logger.info(f"Removing {len(minor_index)} minor riders (age < {MIN_AGE})")
        
        # Remove six-star ratings (invalid)
        six_star_data = data.loc[data['ratings'] == "6"]
        six_star_index = six_star_data.index.tolist()
        if six_star_index:
            logger.info(f"Removing {len(six_star_index)} invalid rating entries (rating = 6)")
        
        cleaned_data = (
            data
            .drop(columns="id", errors='ignore')
            .drop(index=minor_index, errors='ignore')  # Minor riders in data dropped
            .drop(index=six_star_index, errors='ignore')  # Six star rated drivers dropped
            .replace("NaN ", np.nan)  # Missing values in the data
            .assign(
                # city column out of rider id
                city_name=lambda x: x['rider_id'].str.split("RES").str.get(0),
                # convert age to float
                age=lambda x: x['age'].astype(float),
                # convert ratings to float
                ratings=lambda x: x['ratings'].astype(float),
                # absolute values for location based columns
                restaurant_latitude=lambda x: x['restaurant_latitude'].abs(),
                restaurant_longitude=lambda x: x['restaurant_longitude'].abs(),
                delivery_latitude=lambda x: x['delivery_latitude'].abs(),
                delivery_longitude=lambda x: x['delivery_longitude'].abs(),
                # order date to datetime and feature extraction
                order_date=lambda x: pd.to_datetime(x['order_date'], dayfirst=True),
                order_day=lambda x: x['order_date'].dt.day,
                order_month=lambda x: x['order_date'].dt.month,
                order_day_of_week=lambda x: x['order_date'].dt.day_name().str.lower(),
                is_weekend=lambda x: (x['order_date']
                                      .dt.day_name()
                                      .isin(["Saturday", "Sunday"])
                                      .astype(int)),
                # time based columns
                order_time=lambda x: pd.to_datetime(x['order_time'], format='mixed'),
                order_picked_time=lambda x: pd.to_datetime(x['order_picked_time'], format='mixed'),
                # time taken to pick order
                pickup_time_minutes=lambda x: (
                    (x['order_picked_time'] - x['order_time'])
                    .dt.seconds / 60
                ),
                # hour in which order was placed
                order_time_hour=lambda x: x['order_time'].dt.hour,
                # time of the day when order was placed
                order_time_of_day=lambda x: (x['order_time_hour'].pipe(time_of_day)),
                # categorical columns
                weather=lambda x: (
                    x['weather']
                    .str.replace("conditions ", "")
                    .str.lower()
                    .replace("nan", np.nan)
                ),
                traffic=lambda x: x["traffic"].str.rstrip().str.lower(),
                type_of_order=lambda x: x['type_of_order'].str.rstrip().str.lower(),
                type_of_vehicle=lambda x: x['type_of_vehicle'].str.rstrip().str.lower(),
                festival=lambda x: x['festival'].str.rstrip().str.lower(),
                city_type=lambda x: x['city_type'].str.rstrip().str.lower(),
                # multiple deliveries column
                multiple_deliveries=lambda x: x['multiple_deliveries'].astype(float),
                # target column modifications
                time_taken=lambda x: (x['time_taken']
                                      .str.replace("(min) ", "")
                                      .astype(int))
            )
            .drop(columns=["order_time", "order_picked_time"], errors='ignore')
        )
        
        logger.info(f"Data cleaning completed. {len(cleaned_data)} rows remaining")
        return cleaned_data
        
    except KeyError as e:
        logger.error(f"Required column not found: {e}")
        raise customexception(f"Required column missing in data: {e}")
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        raise customexception(f"Failed to clean data: {e}")


def clean_lat_long(data: pd.DataFrame, threshold: float = LOCATION_THRESHOLD) -> pd.DataFrame:
    """
    Clean latitude and longitude columns.
    
    Args:
        data: Input DataFrame
        threshold: Minimum valid value threshold
        
    Returns:
        pd.DataFrame: DataFrame with cleaned location columns
        
    Raises:
        customexception: If cleaning fails
    """
    try:
        location_columns = [
            'restaurant_latitude',
            'restaurant_longitude',
            'delivery_latitude',
            'delivery_longitude'
        ]
        
        # Check if columns exist
        missing_cols = [col for col in location_columns if col not in data.columns]
        if missing_cols:
            raise customexception(f"Missing location columns: {missing_cols}")
        
        cleaned_data = data.assign(**{
            col: (np.where(data[col] < threshold, np.nan, data[col].values))
            for col in location_columns
        })
        
        null_count = sum(cleaned_data[col].isnull().sum() for col in location_columns)
        if null_count > 0:
            logger.info(f"Set {null_count} invalid location values to NaN")
        
        return cleaned_data
        
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error cleaning latitude/longitude: {e}")
        raise customexception(f"Failed to clean location columns: {e}")


def time_of_day(ser: pd.Series):
    """
    Categorize time of day.
    
    Args:
        ser: Series with hour values
        
    Returns:
        pd.Series: Categorized time of day
    """
    try:
        return pd.cut(
            ser,
            bins=TIME_BINS,
            right=True,
            labels=TIME_LABELS
        )
    except Exception as e:
        logger.error(f"Error categorizing time of day: {e}")
        raise customexception(f"Failed to categorize time of day: {e}")


def calculate_haversine_distance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate haversine distance between restaurant and delivery location.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with distance column
        
    Raises:
        customexception: If calculation fails
    """
    try:
        location_columns = [
            'restaurant_latitude',
            'restaurant_longitude',
            'delivery_latitude',
            'delivery_longitude'
        ]
        
        # Check if columns exist
        missing_cols = [col for col in location_columns if col not in df.columns]
        if missing_cols:
            raise customexception(f"Missing location columns: {missing_cols}")
        
        lat1 = df[location_columns[0]]
        lon1 = df[location_columns[1]]
        lat2 = df[location_columns[2]]
        lon2 = df[location_columns[3]]
        
        # Convert to radians
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance = EARTH_RADIUS_KM * c
        
        df_with_distance = df.assign(distance=distance)
        logger.info(f"Haversine distance calculated (mean: {distance.mean():.2f} km)")
        
        return df_with_distance
        
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error calculating haversine distance: {e}")
        raise customexception(f"Failed to calculate distance: {e}")


def create_distance_type(data: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize distance into types.
    
    Args:
        data: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with distance_type column
        
    Raises:
        customexception: If categorization fails
    """
    try:
        if 'distance' not in data.columns:
            raise customexception("'distance' column not found in data")
        
        data_with_type = data.assign(
            distance_type=pd.cut(
                data["distance"],
                bins=DISTANCE_BINS,
                right=False,
                labels=DISTANCE_LABELS
            )
        )
        
        logger.info(f"Distance types created: {data_with_type['distance_type'].value_counts().to_dict()}")
        return data_with_type
        
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error creating distance type: {e}")
        raise customexception(f"Failed to create distance types: {e}")


def drop_columns(data: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Drop specified columns from DataFrame.
    
    Args:
        data: Input DataFrame
        columns: List of columns to drop
        
    Returns:
        pd.DataFrame: DataFrame with columns dropped
        
    Raises:
        customexception: If dropping fails
    """
    try:
        # Only drop columns that exist
        existing_cols = [col for col in columns if col in data.columns]
        dropped_cols = [col for col in columns if col not in data.columns]
        
        if dropped_cols:
            logger.warning(f"Columns not found (skipping): {dropped_cols}")
        
        if existing_cols:
            df = data.drop(columns=existing_cols)
            logger.info(f"Dropped columns: {existing_cols}")
        else:
            df = data
            logger.warning("No columns to drop")
        
        return df
        
    except Exception as e:
        logger.error(f"Error dropping columns: {e}")
        raise customexception(f"Failed to drop columns: {e}")


def validate_cleaned_data(data: pd.DataFrame) -> None:
    """
    Validate the cleaned data.
    
    Args:
        data: Cleaned DataFrame to validate
        
    Raises:
        customexception: If validation fails
    """
    try:
        if data.empty:
            raise customexception("Cleaned data is empty")
        
        # Check required columns
        required_cols = ['distance', 'distance_type', 'time_taken']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise customexception(f"Missing required columns in cleaned data: {missing_cols}")
        
        # Check if time_taken has valid values
        if data['time_taken'].isnull().any():
            logger.warning(f"{data['time_taken'].isnull().sum()} rows have null time_taken")
        
        # Check distance values
        if data['distance'].isnull().any():
            logger.warning(f"{data['distance'].isnull().sum()} rows have null distance")
        
        logger.info("Cleaned data validation successful")
        
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error validating cleaned data: {e}")
        raise customexception(f"Data validation failed: {e}")


def perform_data_cleaning(data: pd.DataFrame, saved_data_path: Path) -> None:
    """
    Perform full data cleaning pipeline.
    
    Args:
        data: Raw DataFrame
        saved_data_path: Path to save cleaned data
        
    Raises:
        customexception: If cleaning pipeline fails
    """
    try:
        logger.info("Starting data cleaning pipeline...")
        
        cleaned_data = (
            data
            .pipe(change_column_names)
            .pipe(data_cleaning)
            .pipe(clean_lat_long)
            .pipe(calculate_haversine_distance)
            .pipe(create_distance_type)
            .pipe(drop_columns, columns=columns_to_drop)
        )
        
        # Validate cleaned data
        validate_cleaned_data(cleaned_data)
        
        # Save the data
        saved_data_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned_data.to_csv(saved_data_path, index=False)
        
        logger.info(f"Data cleaned and saved to: {saved_data_path}")
        logger.info(f"Final dataset: {len(cleaned_data)} rows, {len(cleaned_data.columns)} columns")
        
    except customexception:
        raise
    except Exception as e:
        logger.error(f"Error in data cleaning pipeline: {e}")
        raise customexception(f"Data cleaning pipeline failed: {e}")


if __name__ == "__main__":
    try:
        logger.info("="*60)
        logger.info("STARTING DATA CLEANING PIPELINE")
        logger.info("="*60)
        
        # Root path
        root_path = Path.cwd()
        logger.info(f"Project root: {root_path}")
        
        # Data save directory
        cleaned_data_save_dir = root_path / "artifacts" / "data" / "cleaned"
        cleaned_data_save_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Output directory: {cleaned_data_save_dir}")
        
        # Cleaned data file name
        cleaned_data_filename = "swiggy_cleaned.csv"
        cleaned_data_save_path = cleaned_data_save_dir / cleaned_data_filename
        
        # Data load path
        data_load_path = root_path / "artifacts" / "data" / "raw" / "swiggy.csv"
        logger.info(f"Input file: {data_load_path}")
        
        # Load the data
        logger.info("\nStep 1: Loading data...")
        df = load_data(data_load_path)
        
        # Clean the data and save
        logger.info("\nStep 2: Cleaning data...")
        perform_data_cleaning(data=df, saved_data_path=cleaned_data_save_path)
        
        logger.info("\n" + "="*60)
        logger.info("✅ DATA CLEANING COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
    except customexception as e:
        logger.error(f"\n❌ Custom Exception: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Unexpected Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)