import logging
import os
import shutil
import zipfile
from logging import config

import pandas as pd
import requests

from source.main.ingestion.preprocessing import process_dataframes


SOURCE_URL = "https://github.com/aavail/ai-workflow-capstone/archive/refs/heads/master.zip"


def get_dataset_from_source(source_url, target_file="target.zip"):
    """
    Downloads the AAVAIL dataset from the GitHub repository
    :param source_url:
    :param target_file:
    :return:
    """
    filename = os.path.join(os.getcwd(), target_file)
    logging.info("Downloading source files from %s ...", SOURCE_URL)
    request = requests.get(source_url)
    logging.info("Download complete")
    with open(filename, 'wb') as file:
        file.write(request.content)
    logging.info("Saved contents to %s", filename)


def extract_zipfiles(zip_path, target_directory):
    """
    Extracts the json files from the zipped repo
    :param zip_path:
    :param target_directory:
    :return:
    """
    if not os.path.exists(target_directory):
        os.mkdir(target_directory)
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.extractall(target_directory)
    os.remove(zip_path)

    base_dir = "{}/ai-workflow-capstone-master".format(target_directory)
    for file in os.listdir(base_dir):
        json_path = "{}/ai-workflow-capstone-master/{}".format(target_directory, file)
        os.chmod(json_path, 0o666)
        shutil.move(json_path, target_directory)
        logging.info("Extracted contents of the zip file to %s", DATA_DIR)


def load_dataset(target_directory):
    """
    Transforms json files to pandas dataframes
    :param target_directory:
    :return:
    """
    base_dir = "{}/{}/".format(DATA_DIR, target_directory)
    raw_files = os.listdir(base_dir)
    logging.info("Creating pandas dataframes from source files ...")
    dataframes = []
    for json_file in raw_files:
        dataframes.append(pd.read_json("{}/{}".format(base_dir, json_file)))
        logging.debug("Successfully transformed %s to a pandas dataframe.", json_file)
    logging.info("Finished processing input data (%d files). ", len(dataframes))
    return dataframes


if __name__ == '__main__':
    config.fileConfig(os.environ["BASE_DIR"] + "/log_config.conf")

    DATA_DIR = os.environ["BASE_DIR"] + "/data"
    LOAD_DIR = DATA_DIR + "/input"
    ZIP_FILENAME = "data_source_raw.zip"

    get_dataset_from_source(source_url=SOURCE_URL, target_file=ZIP_FILENAME)
    extract_zipfiles(ZIP_FILENAME, DATA_DIR)
    raw_dataframes = load_dataset("cs-train")
    target_df = process_dataframes(raw_dataframes)
    if not os.path.exists(LOAD_DIR):
        os.mkdir(LOAD_DIR)
    target_df.to_hdf(LOAD_DIR + "/cs-input.h5", key="target_df", mode="w")
    logging.info("Saved processed dataframe to %s as cs-input.h5", LOAD_DIR)
