"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import logging
from logging.handlers import RotatingFileHandler
import json  # Used for JSON Handling
import time  # Used to Get Current Time
from datetime import datetime, timedelta
from csv import DictWriter
from dotenv import load_dotenv  # Used to Load Env Var
from google.cloud import bigquery
from google.oauth2 import service_account
import requests  # Used for API Calls
import urllib3
urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    pass  # no pyopenssl support used / needed / available

load_dotenv()  # Load .env variables

train_api_key = os.getenv('TRAIN_API_KEY')  # API Key Provided by CTA
main_file_path = os.getenv('FILE_PATH')  # File Path to App Directory
train_arrivals_table = os.getenv('CTA_TRAIN_ARRIVALS_TABLE')
integrity_check_table = os.getenv('CTA_INTEGRITY_CHECK_TABLE')
google_credentials_file = main_file_path + "credentials/cta-utilities-410023-73a50f35625b.json"

LOG_FILENAME = main_file_path + 'logs/cta-reliability.log'  # Logging Information
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10e6, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)


def load_configuration():
    """Loads settings.json information for use throughout the function calls"""
    with open(file=main_file_path + 'settings.json', mode='r', encoding='utf-8') as file:
        return json.load(file)


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "simple-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    elif date_type == "long-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    elif date_type == "current-date-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
    elif date_type == "hour-minute-second":
        date = datetime.strftime(datetime.now(), "%H:%M:%S")
    elif date_type == "current-month":
        date = datetime.strftime(datetime.now(), "%b%Y")
    return date


def call_to_cta_api(station_id, api_call_type, url):
    """Gotta talk to the CTA and get Train Times"""
    logging.info(
        "Making %s CTA Train API Call for stop: %s", api_call_type, station_id)
    try:
        api_response = requests.get(
            url.format(train_api_key, station_id), timeout=10)
        parse_tt_response(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error("%s - Http Error: %s", api_call_type, errh)
    except requests.exceptions.ConnectionError as errc:
        logging.error("%s - Error Connecting: %s", api_call_type, errc)
    except requests.exceptions.Timeout as errt:
        logging.error("%s - Timeout Error: %s", api_call_type, errt)
    except requests.exceptions.RequestException as err:
        logging.error(
            "%s - Error in API Call to Train Tracker: %s", api_call_type, err)
    return api_response


def calc_tt_eta(date_1, date_2):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S")
    date_2 = datetime.strptime(date_2, "%Y-%m-%dT%H:%M:%S")
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes


def parse_tt_response(train_api_response):
    """Takes each Train ETA (if exists) and appends to list"""
    for train in train_api_response["ctatt"]["eta"]:
        prediction = train["prdt"]
        arrival = train["arrT"]
        estimated_time = int(calc_tt_eta(prediction, arrival))
        if train["isSch"] == "0" and train["isApp"] == "1" and estimated_time <= 1:
            add_trains_to_table(train, current_month)
            row_to_insert = [
                {'Station_ID': train["staId"], 'Stop_ID': train["stpId"],
                 'Station_Name': train["staNm"], 'Destination': train["destNm"],
                 'Route': train["rt"], 'Run_Number': train["rn"],
                 'Prediction_Time': train["prdt"],
                 'Arrival_Time': train["arrT"]}
            ]
            add_row_to_bigquery(row_to_insert, train_arrivals_table)


def add_trains_to_table(train, month=""):
    """Parses API Result from Train Tracker API and adds ETA's to a list"""
    file_path = main_file_path + "train_arrivals/train_arrivals-" + \
        str(month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=tt_headers)
        writer_object.writerow({'Station_ID': train["staId"], 'Stop_ID': train["stpId"],
                                'Station_Name': train["staNm"], 'Destination': train["destNm"],
                                'Route': train["rt"], 'Run_Number': train["rn"],
                                'Prediction_Time': train["prdt"],
                                'Arrival_Time': train["arrT"]})


def file_validation(month, file_name, headers):
    """Used to check if file exists"""
    file_path = main_file_path + f"train_arrivals/{file_name}-" + \
        str(month) + ".csv"
    csv_file = os.path.exists(file_path)
    if csv_file is False:
        logging.info(
            "%s File Doesn't Exist...Creating File and Adding Headers...", file_name)
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=headers)
            writer_object.writeheader()
    else:
        logging.info("%s File Exists...Continuing...", file_name)


def add_time_integrity_file(status):
    """Used to check if file exists"""
    simple_time = get_date("simple-time")
    long_time = get_date("long-time")
    file_path = main_file_path + "train_arrivals/integrity-check-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=integrity_headers)
        row_data = {'Full_Date_Time': long_time,
                    'Simple_Date_Time': simple_time, 'Status': status}
        writer_object.writerow(row_data)
    row_to_insert = [{'Full_Date_Time': long_time,
                      'Simple_Date_Time': simple_time, 'Status': status}]
    add_row_to_bigquery(row_to_insert, integrity_check_table)


def add_row_to_bigquery(row, table_id):
    """Takes a Row as Input and inserts it to the specified Google Big Query Table"""
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_file, scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials, project=credentials.project_id,)

    errors = client.insert_rows_json(table_id, row)  # Make an API request.
    if errors:
        logging.error("Encountered errors while inserting rows: %s", errors)
    else:
        logging.info(
            "Successfully Inserted Row Into Table %s: %s", table_id, row)


while True:  # Always open while loop to continue checking for trains
    current_month = get_date("current-month")

    # Loads the settings.json file to grab things like map-ids
    settings = load_configuration()

    # API URL's
    tt_api_url = settings["train-tracker"]["api-url"]
    tt_backup_api_url = settings["train-tracker"]["api-url-backup"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    tt_map_ids = settings["train-tracker"]["map-ids"]
    temp_map_ids = settings["train-tracker"]["temp-map-ids"]
    temp_tt_start_time = settings["train-tracker"]["temp-map-ids-start-time"]
    temp_tt_end_time = settings["train-tracker"]["temp-map-ids-end-time"]
    tt_headers = settings["train-tracker"]["train-tracker-headers"]
    integrity_headers = settings["train-tracker"]["integrity-file-headers"]

    current_time = get_date("current-date-time")
    current_time_console = f"The Current Time is: {get_date('hour-minute-second')}"
    logging.info(current_time_console)

    file_validation(current_month, "train_arrivals", tt_headers)
    file_validation(current_month, "integrity-check", integrity_headers)

    if (current_time >= temp_tt_start_time and
            current_time <= temp_tt_end_time):  # Checks if app should run in IROPs mode
        logging.warning("Currently Operating Under Temporary Map IDs")
        for map_id in temp_map_ids:
            try:
                try:
                    response1 = call_to_cta_api(
                        map_id, "Main Secure URL", tt_api_url)
                except:  # pylint: disable=bare-except
                    response2 = call_to_cta_api(
                        map_id, "Backup Insecure URL", tt_backup_api_url)
            except:  # pylint: disable=bare-except
                logging.critical("Ultimate Failure :(  - Map ID: %s", map_id)
    else:
        logging.info("Currently Operating Under Standard Map IDs")
        for map_id in tt_map_ids:
            try:
                try:
                    response1 = call_to_cta_api(
                        map_id, "Main Secure URL", tt_api_url)
                except:  # pylint: disable=bare-except
                    response2 = call_to_cta_api(
                        map_id, "Backup Insecure URL", tt_backup_api_url)
            except:  # pylint: disable=bare-except
                logging.critical("Ultimate Failure :(  - Map ID: %s", map_id)

    add_time_integrity_file("Success")

    logging.info("Sleeping 30 Seconds")  # Wait and do it again
    time.sleep(30)
