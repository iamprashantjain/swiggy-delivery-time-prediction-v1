import os
import sys
import numpy as np
import pandas as pd
import re
import nltk
import string
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from mylogging import logging
from myexception import customexception


nltk.download('stopwords')
nltk.download('wordnet')

# Preprocessing Functions
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

def lemmatization(text):
    return " ".join([lemmatizer.lemmatize(word) for word in text.split()])

def remove_stop_words(text):
    return " ".join([word for word in text.split() if word not in stop_words])

def removing_numbers(text):
    return ''.join([char for char in text if not char.isdigit()])

def lower_case(text):
    return " ".join([word.lower() for word in text.split()])

def removing_punctuations(text):
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    text = text.replace('؛', "")
    return re.sub('\s+', ' ', text).strip()

def removing_urls(text):
    return re.sub(r'https?://\S+|www\.\S+', '', text)

def remove_small_sentences(df):
    df['content'] = df['content'].apply(lambda x: np.nan if len(str(x).split()) < 3 else x)
    return df

def normalize_text(df):
    try:
        logging.info("Starting text normalization.")
        df['content'] = df['content'].astype(str)
        df['content'] = df['content'].apply(lower_case)\
                                     .apply(remove_stop_words)\
                                     .apply(removing_numbers)\
                                     .apply(removing_punctuations)\
                                     .apply(removing_urls)\
                                     .apply(lemmatization)
        df = remove_small_sentences(df)
        df = df.dropna(subset=['content'])
        logging.info("Text normalization completed.")
        return df
    except Exception as e:
        logging.info("Exception occurred during normalize_text in data_preprocessing.")
        raise customexception(e, sys)

def main():
    try:
        input_train = "artifacts/data/raw/train.csv"
        input_test = "artifacts/data/raw/test.csv"
        output_path = "artifacts/data/processed"
        os.makedirs(output_path, exist_ok=True)

        df_train = pd.read_csv(input_train)
        df_test = pd.read_csv(input_test)

        logging.info("Train and test data loaded.")

        df_train_processed = normalize_text(df_train)
        df_test_processed = normalize_text(df_test)

        train_output = os.path.join(output_path, "train_processed.csv")
        test_output = os.path.join(output_path, "test_processed.csv")
        
        df_train_processed.to_csv(train_output, index=False)
        df_test_processed.to_csv(test_output, index=False)

        logging.info("Train and test preprocessed data saved to %s", output_path)

    except Exception as e:
        logging.info("Exception occurred in main data_preprocessing pipeline.")
        raise customexception(e, sys)

if __name__ == "__main__":
    main()