"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import json  # Used for JSON Handling
import time  # Used to Get Current Time
# Used for converting Prediction from Current Time
from datetime import datetime, timedelta
from csv import DictWriter
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls

# Load .env variables
load_dotenv()

# ENV Variables
main_file_path = os.getenv('FILE_PATH')
metra_username = os.getenv('METRA_USERNAME')
metra_password = os.getenv('METRA_PASSWORD')

# Constants
integrity_file_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Status']
metra_vehicles_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Vehicle_Trip_TripID',
                              'Vehicle_Trip_RouteID', 'Vehicle_Trip_StartTime', 'Vehicle_Trip_StartDate', 'Vehicle_Vehicle_ID', 'Vehicle_Vehicle_Label']


def train_api_call_to_metra():
    """Gotta talk to Metra and get vehicle positions!"""
    print("Making Metra API Call...")
    try:
        api_response = requests.get(
            metra_tracker_url_api, auth=(metra_username, metra_password))
        add_train_to_file_api(api_response.json())
    except:  # pylint: disable=bare-except
        print("Error in API Call to Metra Train Tracker")
    return api_response


def minutes_between(date_1, date_2):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S")
    date_2 = datetime.strptime(date_2, "%Y-%m-%dT%H:%M:%S")
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes


def add_train_to_file_api(response):
    """Parses API Result from Train Tracker API and adds results to a list"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_simple_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    file_path = main_file_path + "/cta-reliability/train_arrivals/metra_train_positions-" + \
        str(current_month) + ".csv"
    for vehicle in response:
        with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=metra_vehicles_csv_headers)
            writer_object.writerow({'Full_Date_Time': current_long_time, 'Simple_Date_Time': current_simple_time, 'Vehicle_Trip_TripID': vehicle["vehicle"]["trip"]["trip_id"], 'Vehicle_Trip_RouteID': vehicle["vehicle"]["trip"]["route_id"], 'Vehicle_Trip_StartTime': vehicle[
                                   "vehicle"]["trip"]["start_time"], 'Vehicle_Trip_StartDate': vehicle["vehicle"]["trip"]["start_date"], 'Vehicle_Vehicle_ID': vehicle["vehicle"]["vehicle"]["id"], 'Vehicle_Vehicle_Label': vehicle["vehicle"]["vehicle"]["label"]})


def check_main_train_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/metra_train_positions-" + \
        str(current_month) + ".csv"
    train_csv_file = os.path.exists(file_path)
    if train_csv_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=metra_vehicles_csv_headers)
            writer_object.writeheader()
    else:
        print("File Exists...Continuing...")


def check_integrity_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/metra-integrity-check-" + \
        str(current_month) + ".csv"
    integrity_csv_file = os.path.exists(file_path)
    if integrity_csv_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=integrity_file_csv_headers)
            writer_object.writeheader()
    else:
        print("File Exists...Continuing...")


def add_integrity_file_line(status):
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_simple_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S.%f%z")
    file_path = main_file_path + "/cta-reliability/train_arrivals/metra-integrity-check-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=integrity_file_csv_headers)
        writer_object.writerow({'Full_Date_Time': current_long_time,
                               'Simple_Date_Time': current_simple_time, 'Status': status})


print("Welcome to Metra TrainTracker, Python Edition!")
# Check to make sure output file exists and write headers
while True:  # Where the magic happens
    check_main_train_file_exists()
    check_integrity_file_exists()
    # Settings
    file = open(file=main_file_path + '/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    metra_tracker_url_api = settings["metra-api"]["api-url"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_metra_tracker_api = settings["metra-api"]["api-enabled"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"trains":{},"buses":{}}')

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    print("\n" + current_time_console)

    # If we get to this point, log a successful attempt to reach the API's
    add_integrity_file_line("Success")

    # API Portion runs if enabled and station id's exist
    if enable_metra_tracker_api == "True":
        response1 = train_api_call_to_metra()

    # Wait and do it again
    SLEEP_AMOUNT = 900
    print("Sleeping " + str(SLEEP_AMOUNT) + " Seconds")
    time.sleep(SLEEP_AMOUNT)
