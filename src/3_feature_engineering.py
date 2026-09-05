import os
import sys
import pandas as pd
import joblib
import yaml
from sklearn.feature_extraction.text import CountVectorizer
from mylogging import logging
from myexception import customexception

def load_params(params_path: str):
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logging.info("Parameters loaded from %s", params_path)
        return params
    except Exception as e:
        logging.info("Exception occurred while loading params.yaml")
        raise customexception(e, sys)


def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        logging.info("Data loaded from %s", file_path)
        return df
    except Exception as e:
        logging.info(f"Error loading file {file_path}")
        raise customexception(e, sys)


def vectorize_text(train_df, test_df, max_features):
    try:
        vectorizer = CountVectorizer(max_features=max_features)

        X_train = vectorizer.fit_transform(train_df['content'])
        X_test = vectorizer.transform(test_df['content'])

        logging.info("Vectorization done with max_features=%s", max_features)
        return X_train, X_test, vectorizer
    except Exception as e:
        logging.info("Exception occurred during vectorization.")
        raise customexception(e, sys)


def save_vectorized_data(X_train, X_test, train_df, test_df, vectorizer, output_path):
    try:
        os.makedirs(output_path, exist_ok=True)

        train_features = pd.DataFrame(X_train.toarray(), columns=vectorizer.get_feature_names_out())
        train_features['sentiment'] = train_df['sentiment'].values

        test_features = pd.DataFrame(X_test.toarray(), columns=vectorizer.get_feature_names_out())
        test_features['sentiment'] = test_df['sentiment'].values

        train_path = os.path.join(output_path, "train_vectorized.csv")
        test_path = os.path.join(output_path, "test_vectorized.csv")
        vectorizer_path = os.path.join(output_path, "vectorizer.pkl")

        train_features.to_csv(train_path, index=False)
        test_features.to_csv(test_path, index=False)
        joblib.dump(vectorizer, vectorizer_path)

        logging.info("Vectorized datasets and vectorizer saved to %s", output_path)
    except Exception as e:
        logging.info("Exception occurred during saving vectorized data.")
        raise customexception(e, sys)


def main():
    try:
        params = load_params("params.yaml")
        vectorizer_params = params['text_vectorization']

        input_train = vectorizer_params['input_train']
        input_test = vectorizer_params['input_test']
        output_path = vectorizer_params['output_path']
        max_features = vectorizer_params['max_features']

        train_df = load_data(input_train)
        test_df = load_data(input_test)

        X_train, X_test, vectorizer = vectorize_text(train_df, test_df, max_features)

        save_vectorized_data(X_train, X_test, train_df, test_df, vectorizer, output_path)

    except Exception as e:
        logging.info("Exception occurred in main text_vectorization pipeline.")
        raise customexception(e, sys)


if __name__ == "__main__":
    main()