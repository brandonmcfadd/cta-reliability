"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import logging
from logging.handlers import RotatingFileHandler
import json  # Used for JSON Handling
import time  # Used to Get Current Time
# Used for converting Prediction from Current Time
from datetime import datetime, timedelta
from csv import DictWriter
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import urllib3
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass


# Load .env variables
load_dotenv()

# ENV Variables
train_api_key = os.getenv('TRAIN_API_KEY')
main_file_path = os.getenv('FILE_PATH')

# Logging Information
LOG_FILENAME = main_file_path + '/logs/cta-reliability.log'
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=1e6, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

# Constants
integrity_file_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Status']
train_arrivals_csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route',
                              'Run_Number', 'Prediction_Time', 'Arrival_Time']


def train_api_call_to_cta_api(map_id):
    """Gotta talk to the CTA and get Train Times"""
    logging.info(
        "Making Main Secure URL CTA Train API Call for stop: %s", map_id)
    try:
        api_response = requests.get(
            train_tracker_url_api.format(train_api_key, map_id), timeout=10)
        train_arrival_times(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error("Main URL - Http Error: %s", errh)
    except requests.exceptions.ConnectionError as errc:
        logging.error("Main URL - Error Connecting: %s", errc)
    except requests.exceptions.Timeout as errt:
        logging.error("Main URL - Timeout Error: %s", errt)
    except requests.exceptions.RequestException as err:
        logging.error("Main URL - Error in API Call to Train Tracker: %s", err)
    return api_response


def train_api_call_to_cta_api_backup(stop_id):
    """Gotta talk to the CTA and get Train Times"""
    logging.warning(
        "Making Backup Insecure URL CTA Train API Call for stop: %s", stop_id)
    try:
        api_response = requests.get(
            train_tracker_url_api_backup.format(train_api_key, stop_id), timeout=10)
        train_arrival_times(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error("Backup URL - Http Error: %s", errh)
    except requests.exceptions.ConnectionError as errc:
        logging.error("Backup URL - Error Connecting: %s", errc)
    except requests.exceptions.Timeout as errt:
        logging.error("Backup URL - Timeout Error: %s", errt)
    except requests.exceptions.RequestException as err:
        logging.error(
            "Backup URL - Error in API Call to Train Tracker: %s", err)
    return api_response


def minutes_between(date_1, date_2):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S")
    date_2 = datetime.strptime(date_2, "%Y-%m-%dT%H:%M:%S")
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes


def add_train_station_to_json(station_name):
    """Function is called if a new station is identified per API Call"""
    station_information = {}
    arrival_information["trains"][station_name] = station_information


def add_train_stop_to_json(eta, stop_id):
    """Function is called if a new train stop is identified per API Call"""
    stop_information = {}
    station_name = eta["staNm"]

    stop_information["full_name"] = eta["rt"] + " Line to " + eta["destNm"]
    stop_information["destination_name"] = eta["destNm"]
    stop_information["route"] = eta["rt"]
    stop_information["stop-id"] = eta["stpId"]
    stop_information["estimated_times"] = []

    arrival_information["trains"][station_name][stop_id] = stop_information


def train_arrival_times(train_api_response):
    """Takes each Train ETA (if exists) and appends to list"""
    for eta in train_api_response["ctatt"]["eta"]:
        train_stop_id = eta["destNm"]
        train_station_name = eta["staNm"]

        if train_station_name not in arrival_information["trains"]:
            add_train_station_to_json(train_station_name)

        if train_stop_id in arrival_information["trains"][train_station_name]:
            add_train_to_file_api(eta, train_station_name, train_stop_id)
        else:
            add_train_stop_to_json(eta, train_stop_id)
            add_train_to_file_api(eta, train_station_name, train_stop_id)


def add_train_to_file_api(eta, station_name, stop_id):
    """Parses API Result from Train Tracker API and adds ETA's to a list"""
    prediction = eta["prdt"]
    arrival = eta["arrT"]
    estimated_time = int(minutes_between(prediction, arrival))
    if eta["isSch"] == "0" and eta["isApp"] == "1" and estimated_time <= 1:
        arrival_information["trains"][station_name][stop_id][
            "estimated_times"].append(str(estimated_time) + "min")
        current_month = datetime.strftime(datetime.now(), "%b%Y")
        file_path = main_file_path + "/cta-reliability/train_arrivals/train_arrivals-" + \
            str(current_month) + ".csv"
        with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=train_arrivals_csv_headers)
            writer_object.writerow({'Station_ID': eta["staId"], 'Stop_ID': eta["stpId"],
                                    'Station_Name': eta["staNm"], 'Destination': eta["destNm"], 
                                    'Route': eta["rt"], 'Run_Number': eta["rn"], 
                                    'Prediction_Time': eta["prdt"],
                                    'Arrival_Time': eta["arrT"]})


def check_main_train_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/train_arrivals-" + \
        str(current_month) + ".csv"
    train_csv_file = os.path.exists(file_path)
    if train_csv_file is False:
        logging.info(
            "Main Train File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=train_arrivals_csv_headers)
            writer_object.writeheader()
    else:
        logging.info("Main Train File Exists...Continuing...")


def check_integrity_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/integrity-check-" + \
        str(current_month) + ".csv"
    integrity_csv_file = os.path.exists(file_path)
    if integrity_csv_file is False:
        logging.info(
            "Integrity File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=integrity_file_csv_headers)
            writer_object.writeheader()
    else:
        logging.info("Integrity File Exists...Continuing...")


def add_integrity_file_line(status):
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_simple_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    file_path = main_file_path + "/cta-reliability/train_arrivals/integrity-check-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=integrity_file_csv_headers)
        writer_object.writerow({'Full_Date_Time': current_long_time,
                               'Simple_Date_Time': current_simple_time, 'Status': status})


logging.info("Welcome to TrainTracker, Python Edition!")
# Check to make sure output file exists and write headers
while True:  # Where the magic happens
    check_main_train_file_exists()
    # check_backup_train_file_exists()
    check_integrity_file_exists()
    # Settings
    file = open(file=main_file_path + '/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    train_tracker_url_api = settings["train-tracker"]["api-url"]
    train_tracker_url_api_backup = settings["train-tracker"]["api-url-backup"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_train_tracker_api = settings["train-tracker"]["api-enabled"]
    train_station_map_ids = settings["train-tracker"]["map-ids"]
    temp_train_station_map_ids = settings["train-tracker"]["temp-map-ids"]
    temp_train_station_map_ids_start_time = settings["train-tracker"]["temp-map-ids-start-time"]
    temp_train_station_map_ids_end_time = settings["train-tracker"]["temp-map-ids-end-time"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"trains":{},"buses":{}}')

    current_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    logging.info(current_time_console)

    # API Portion runs if enabled and station id's exist

    if (current_time >= temp_train_station_map_ids_start_time and
            current_time <= temp_train_station_map_ids_end_time):
        logging.warning("Currently Operating Under Temporary Map IDs")
        if temp_train_station_map_ids != "" and enable_train_tracker_api == "True":
            for train_map_id_to_check in temp_train_station_map_ids:
                try:
                    try:
                        response1 = train_api_call_to_cta_api(
                            train_map_id_to_check)
                    except:  # pylint: disable=bare-except
                        response2 = train_api_call_to_cta_api_backup(
                            train_map_id_to_check)
                except:  # pylint: disable=bare-except
                    logging.critical(
                        "Ultimate Failure :(  - Map ID: %s", train_map_id_to_check)
    else:
        logging.info("Currently Operating Under Standard Map IDs")
        if train_station_map_ids != "" and enable_train_tracker_api == "True":
            for train_map_id_to_check in train_station_map_ids:
                try:
                    try:
                        response1 = train_api_call_to_cta_api(
                            train_map_id_to_check)
                    except:  # pylint: disable=bare-except
                        response2 = train_api_call_to_cta_api_backup(
                            train_map_id_to_check)
                except:  # pylint: disable=bare-except
                    logging.critical(
                        "Ultimate Failure :(  - Map ID: %s", train_map_id_to_check)

    add_integrity_file_line("Success")

    # Wait and do it again
    SLEEP_AMOUNT = 30
    SLEEP_STRING = "Sleeping " + str(SLEEP_AMOUNT) + " Seconds"
    logging.info(SLEEP_STRING)
    time.sleep(SLEEP_AMOUNT)
