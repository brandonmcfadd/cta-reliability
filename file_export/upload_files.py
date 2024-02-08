"""Used to Upload the aggregate files from the local server to Azure Blob for the PowerBi Reports"""
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv  # Used to Load Env Var
from azure.storage.blob import BlobServiceClient

# Load .env variables
load_dotenv()

# ENV Variables
storage_account_key = os.getenv('STORAGE_ACCOUNT_KEY')
storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME')
connection_string = os.getenv('CONNECTION_STRING')
container_name = os.getenv('CONTAINER_NAME')
main_file_path = os.getenv('FILE_PATH')

# Logging Information
LOG_FILENAME = main_file_path + 'logs/file-uploads.log'
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10e6, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)


# Constants
MAIN_FILE_PATH_1 = "train_arrivals/train_arrivals-"
MAIN_FILE_PATH_2 = "train_arrivals/integrity-check-"
MAIN_FILE_PATH_3 = "train_arrivals/metra_train_updates-"
MAIN_FILE_PATH_4 = "train_arrivals/metra-integrity-check-"

# Dates
current_day = datetime.strftime(datetime.now(), "%d")
current_month = datetime.strftime(datetime.now(), "%b%Y")


def upload_to_blob_storage(file_path, file_name):
    """used to upload the files from the local server to the blob for use in PowerBi"""
    blob_service_client = BlobServiceClient.from_connection_string(
        connection_string)
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
        logging.info("Uploaded %s.", file_name)


if current_day == "01" or current_day == "1":
    last_month_dt = datetime.strptime(
        current_month, "%b%Y") - relativedelta(months=1)
    last_month = datetime.strftime(last_month_dt, "%b%Y")
    file_path_1 = main_file_path + MAIN_FILE_PATH_1 + \
        str(current_month) + ".csv"
    file_path_1_last_month = main_file_path + MAIN_FILE_PATH_1 + \
        str(last_month) + ".csv"
    file_path_2 = main_file_path + MAIN_FILE_PATH_2 + \
        str(current_month) + ".csv"
    file_path_2_last_month = main_file_path + MAIN_FILE_PATH_2 + \
        str(last_month) + ".csv"
    file_path_3 = main_file_path + MAIN_FILE_PATH_3 + \
        str(current_month) + ".csv"
    file_path_3_last_month = main_file_path + MAIN_FILE_PATH_3 + \
        str(last_month) + ".csv"
    file_path_4 = main_file_path + MAIN_FILE_PATH_4 + \
        str(current_month) + ".csv"
    file_path_4_last_month = main_file_path + MAIN_FILE_PATH_4 + \
        str(last_month) + ".csv"

    logging.info("Uploading file from path: %s", file_path_1_last_month)
    upload_to_blob_storage(file_path_1_last_month,
                           f'train_arrivals/train_arrivals-{last_month}.csv')

    logging.info("Uploading file from path: %s", file_path_2_last_month)
    upload_to_blob_storage(file_path_2_last_month,
                           f'train_arrivals/integrity-check-{last_month}.csv')

    logging.info("Uploading file from path: %s", file_path_3_last_month)
    upload_to_blob_storage(
        file_path_3_last_month, f'train_arrivals/metra_train_updates-{last_month}.csv')

    logging.info("Uploading file from path: %s", file_path_4_last_month)
    upload_to_blob_storage(
        file_path_4_last_month, f'train_arrivals/metra-integrity-check-{last_month}.csv')

    logging.info("Uploading file from path: %s",file_path_1)
    upload_to_blob_storage(
        file_path_1, f'train_arrivals/train_arrivals-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_2)
    upload_to_blob_storage(
        file_path_2, f'train_arrivals/integrity-check-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_3)
    upload_to_blob_storage(
        file_path_3, f'train_arrivals/metra_train_updates-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_4)
    upload_to_blob_storage(
        file_path_4, f'train_arrivals/metra-integrity-check-{current_month}.csv')
else:
    file_path_1 = main_file_path + MAIN_FILE_PATH_1 + \
        str(current_month) + ".csv"
    file_path_2 = main_file_path + MAIN_FILE_PATH_2 + \
        str(current_month) + ".csv"
    file_path_3 = main_file_path + MAIN_FILE_PATH_3 + \
        str(current_month) + ".csv"
    file_path_4 = main_file_path + MAIN_FILE_PATH_4 + \
        str(current_month) + ".csv"
    logging.info("Uploading file from path: %s",file_path_1)
    upload_to_blob_storage(
        file_path_1, f'train_arrivals/train_arrivals-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_2)
    upload_to_blob_storage(
        file_path_2, f'train_arrivals/integrity-check-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_3)
    upload_to_blob_storage(
        file_path_3, f'train_arrivals/metra_train_updates-{current_month}.csv')

    logging.info("Uploading file from path: %s",file_path_4)
    upload_to_blob_storage(
        file_path_4, f'train_arrivals/metra-integrity-check-{current_month}.csv')
