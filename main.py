"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os # Used to retrieve secrets in .env file
import json # Used for JSON Handling
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

# Constants
integrity_file_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Status']
train_arrivals_csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route', \
                                'Run_Number', 'Prediction_Time', 'Arrival_Time', 'Is_Approaching', \
                                'Is_Scheduled', 'Is_Delayed', 'Is_Fault']


def train_api_call_to_cta_api(stop_id):
    """Gotta talk to the CTA and get Train Times"""
    print("Making Main Secure URL CTA Train API Call...")
    try:
        api_response = requests.get(
            train_tracker_url_api.format(train_api_key, stop_id), timeout=10)
        train_arrival_times(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Main URL - Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Main URL - Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Main URL - Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("Main URL - Error in API Call to Train Tracker",err)
    return api_response


def train_api_call_to_cta_api_backup(stop_id):
    """Gotta talk to the CTA and get Train Times"""
    print("Making Backup Insecure URL CTA Train API Call...")
    try:
        api_response = requests.get(
            train_tracker_url_api_backup.format(train_api_key, stop_id), timeout=10)
        train_arrival_times(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Backup URL - Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Backup URL - Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Backup URL - Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("Backup URL - Error in API Call to Train Tracker",err)
    return api_response


def train_api_call_to_cta_map():
    """Gotta talk to the CTA and get Train Times part 2!"""
    print("Making CTA Train Map API Call...")
    try:
        api_response = requests.get(train_tracker_url_map, timeout=10)
        train_arrival_times_map(api_response.json())
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Map - Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Map - Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Map - Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("Map - Error in API Call to Train Tracker",err)
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
            writer_object.writerow({'Station_ID': eta["staId"], 'Stop_ID': eta["stpId"], \
                'Station_Name': eta["staNm"], 'Destination': eta["destNm"], 'Route': eta["rt"], \
                'Run_Number': eta["rn"], 'Prediction_Time': eta["prdt"], \
                'Arrival_Time': eta["arrT"], 'Is_Approaching': eta["isApp"], \
                'Is_Scheduled': eta["isSch"], 'Is_Delayed': eta["isDly"], \
                'Is_Fault': eta["isFlt"]})


def add_train_to_file_map(destination, route, run_number, is_scheduled, prediction):
    """Parses API Result from Train Tracker API and adds ETA's to a list"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    current_long_time = datetime.strftime(
        datetime.now(), "%Y-%m-%dT%H:%M:%S")
    file_path = main_file_path + "/cta-reliability/train_arrivals/train_arrivals_backup-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=train_arrivals_csv_headers)
        writer_object.writerow({'Station_ID': int(prediction[0]), 'Stop_ID': "NULL", \
            'Station_Name': prediction[1], 'Destination': destination, 'Route': route, \
            'Run_Number': run_number, 'Prediction_Time': current_long_time, \
            'Arrival_Time': current_long_time, 'Is_Approaching': "NULL", \
            'Is_Scheduled': is_scheduled, 'Is_Delayed': "NULL", 'Is_Fault': "NULL"})


def train_arrival_times_map(response):
    """Used to parse the Train Tracker Map API Response"""
    for train in response['dataObject']:
        for marker in train["Markers"]:
            for prediction in marker["Predictions"]:
                if str(prediction[0]) in train_station_map_ids and marker["DestName"] \
                        in train_station_tracked_destinations \
                        and str(prediction[2]) == "<b>Due</b>":
                    add_train_to_file_map(
                        marker["DestName"], marker["LineName"], \
                        marker["RunNumber"], marker["IsSched"], prediction)


def check_main_train_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/train_arrivals-" + \
        str(current_month) + ".csv"
    train_csv_file = os.path.exists(file_path)
    if train_csv_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=train_arrivals_csv_headers)
            writer_object.writeheader()
    else:
        print("File Exists...Continuing...")


def check_backup_train_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/train_arrivals_backup-" + \
        str(current_month) + ".csv"
    train_csv_file = os.path.exists(file_path)
    if train_csv_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        with open(file_path, 'w+', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=train_arrivals_csv_headers)
            writer_object.writeheader()
    else:
        print("File Exists...Continuing...")


def check_integrity_file_exists():
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/integrity-check-" + \
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
    file_path = main_file_path + "/cta-reliability/train_arrivals/integrity-check-" + \
        str(current_month) + ".csv"
    with open(file_path, 'a', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=integrity_file_csv_headers)
        writer_object.writerow({'Full_Date_Time': current_long_time,
                               'Simple_Date_Time': current_simple_time, 'Status': status})


print("Welcome to TrainTracker, Python Edition!")
# Check to make sure output file exists and write headers
while True:  # Where the magic happens
    check_main_train_file_exists()
    check_backup_train_file_exists()
    check_integrity_file_exists()
    # Settings
    file = open(file=main_file_path + '/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    train_tracker_url_api = settings["train-tracker"]["api-url"]
    train_tracker_url_api_backup = settings["train-tracker"]["api-url-backup"]
    train_tracker_url_map = settings["train-tracker"]["map-url"]
    train_tracker_url_map_backup = settings["train-tracker"]["map-url-backup"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_train_tracker_api = settings["train-tracker"]["api-enabled"]
    enable_train_tracker_map = settings["train-tracker"]["map-enabled"]
    train_station_stop_ids = settings["train-tracker"]["station-ids"]
    train_station_map_ids = settings["train-tracker"]["map-station-ids"]
    train_station_tracked_destinations = settings["train-tracker"]["tracked-destinations"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"trains":{},"buses":{}}')

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    print("\n" + current_time_console)

    # API Portion runs if enabled and station id's exist
    if train_station_stop_ids != "" and enable_train_tracker_api == "True":
        for train_stop_id_to_check in train_station_stop_ids:
            try:
                try:
                    response1 = train_api_call_to_cta_api(train_stop_id_to_check)
                except: # pylint: disable=bare-except
                    response2 = train_api_call_to_cta_api_backup(train_stop_id_to_check)
            except: # pylint: disable=bare-except
                print("Ultimate Failure :()")

    # Map Portion runs if enabled and station id's exist
    if train_station_map_ids != "" \
            and train_station_tracked_destinations != "" \
            and enable_train_tracker_map == "True":
        response2 = train_api_call_to_cta_map()

    add_integrity_file_line("Success")

    # Wait and do it again
    SLEEP_AMOUNT = 30
    print("Sleeping " + str(SLEEP_AMOUNT) + " Seconds")
    time.sleep(SLEEP_AMOUNT)
