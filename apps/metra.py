"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import pytz
import logging
from logging.handlers import RotatingFileHandler
import json  # Used for JSON Handling
import time  # Used to Get Current Time
# Used for converting Prediction from Current Time
from datetime import datetime, timedelta
from dateutil import tz
from csv import DictWriter
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls

# Load .env variables
load_dotenv()

# ENV Variables
main_file_path = os.getenv('FILE_PATH')
metra_username = os.getenv('METRA_USERNAME')
metra_password = os.getenv('METRA_PASSWORD')

# Logging Information
LOG_FILENAME = main_file_path + 'logs/metra-reliability.log'
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10e6, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

# Constants
integrity_file_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Status']
metra_vehicles_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Vehicle_Trip_TripID',
                              'Vehicle_Trip_RouteID', 'Vehicle_Trip_StartTime', 'Vehicle_Trip_StartDate', 'Vehicle_Vehicle_ID', 'Stop_Name', 'Stop_Arrival_Time', 'Stop_Sequence']

def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "simple-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    elif date_type == "long-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    elif date_type == "zulu-time":
        date = datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%S.%fZ")
    elif date_type == "current-date-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S")
    elif date_type == "hour-minute-second":
        date = datetime.strftime(datetime.now(), "%H:%M:%S")
    elif date_type == "current-month":
        date = datetime.strftime(datetime.now(), "%b%Y")
    return date


def train_api_call_to_metra():
    """Gotta talk to Metra and get vehicle positions!"""
    logging.info("Making Metra API Call...")
    try:
        api_response = requests.get(
            metra_tracker_url_api, auth=(metra_username, metra_password), timeout=300)
        add_train_to_file_api(api_response.json())
    except:  # pylint: disable=bare-except
        logging.error("Error in API Call to Metra Train Tracker")
    return api_response


def minutes_between(date_1, date_2):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S.%f%z")
    date_2 = datetime.strptime(date_2, "%Y-%m-%dT%H:%M:%S.%f%z")
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes

def convert_from_utc(date):
    """Converts UTC to Chicago Time"""
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Chicago')
    utc_time = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")
    utc = utc_time.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    return central

def add_train_to_file_api(response):
    """Parses API Result from Train Tracker API and adds results to a list"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_simple_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    file_path = main_file_path + "/train_arrivals/metra_train_updates-" + \
        str(current_month) + ".csv"
    for vehicle in response:
        stops_remaining = len(vehicle['trip_update']['stop_time_update'])
        try:
            stop_time = vehicle['trip_update']['stop_time_update'][-1]['arrival']['time']['low']
            stop_time_converted = datetime.strftime(convert_from_utc(stop_time),"%Y-%m-%dT%H:%M:%S")
            diff_in_minutes = minutes_between(get_date('zulu-time'),stop_time)
            stop_sequence = vehicle['trip_update']['stop_time_update'][-1]['stop_sequence']
            log_vehicle = True
        except: # pylint: disable=bare-except
            diff_in_minutes = 99
            log_vehicle = False
        if stops_remaining <= 1 and (diff_in_minutes >= 0 and diff_in_minutes <= 2) and log_vehicle is True and stop_sequence > 1:
            with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
                writer_object = DictWriter(
                    csvfile, fieldnames=metra_vehicles_csv_headers)
                writer_object.writerow({'Full_Date_Time': current_long_time, 'Simple_Date_Time': current_simple_time, 'Vehicle_Trip_TripID': vehicle['trip_update']["trip"]["trip_id"], 'Vehicle_Trip_RouteID': vehicle['trip_update']["trip"]["route_id"], 'Vehicle_Trip_StartTime': vehicle['trip_update']["trip"]["start_time"], 'Vehicle_Trip_StartDate': vehicle['trip_update']["trip"]["start_date"], 'Vehicle_Vehicle_ID': vehicle['trip_update']["vehicle"]["id"], 'Stop_Name': vehicle['trip_update']['stop_time_update'][-1]['stop_id'], 'Stop_Arrival_Time': stop_time_converted, 'Stop_Sequence': stop_sequence})


def check_main_train_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/train_arrivals/metra_train_updates-" + \
        str(current_month) + ".csv"
    train_csv_file = os.path.exists(file_path)
    if train_csv_file is False:
        logging.warning("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=metra_vehicles_csv_headers)
            writer_object.writeheader()
    else:
        logging.info("File Exists...Continuing...")


def check_integrity_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/train_arrivals/metra-integrity-check-" + \
        str(current_month) + ".csv"
    integrity_csv_file = os.path.exists(file_path)
    if integrity_csv_file is False:
        logging.warning("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=integrity_file_csv_headers)
            writer_object.writeheader()
    else:
        logging.info("File Exists...Continuing...")


def add_integrity_file_line(status):
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_simple_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    file_path = main_file_path + "/train_arrivals/metra-integrity-check-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=integrity_file_csv_headers)
        writer_object.writerow({'Full_Date_Time': current_long_time,
                               'Simple_Date_Time': current_simple_time, 'Status': status})


logging.info("Welcome to Metra TrainTracker, Python Edition!")
# Check to make sure output file exists and write headers
while True:  # Where the magic happens
    check_main_train_file_exists()
    check_integrity_file_exists()
    # Settings
    file = open(file=main_file_path + 'settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    metra_tracker_url_api = settings["metra-api"]["trips-api-url"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_metra_tracker_api = settings["metra-api"]["api-enabled"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"trains":{},"buses":{}}')

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    logging.info(current_time_console)

    # If we get to this point, log a successful attempt to reach the API's
    add_integrity_file_line("Success")

    # API Portion runs if enabled and station id's exist
    if enable_metra_tracker_api == "True":
        response1 = train_api_call_to_metra()

    # Wait and do it again
    SLEEP_AMOUNT = 60
    SLEEP_STRING = "Sleeping " + str(SLEEP_AMOUNT) + " Seconds"
    logging.info(SLEEP_STRING)
    time.sleep(SLEEP_AMOUNT)
