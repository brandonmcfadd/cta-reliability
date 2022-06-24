"""ctapi by Brandon McFadden - Github: https://github.com/brandonmcfadd/ctapi"""
import os
import json
import time  # Used to Get Current Time
# Used for converting Prediction from Current Time
from datetime import datetime, timedelta
from csv import DictWriter
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls

# Load .env variables
load_dotenv()

# ENV Variables
train_api_key = os.getenv('TRAIN_API_KEY')


def train_api_call_to_cta(stop_id):
    """Gotta talk to the CTA and get Train Times"""
    print("Making CTA Train API Call...")
    api_response = requests.get(
        train_tracker_url.format(train_api_key, stop_id))
    train_arrival_times(api_response.json())
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
            add_train_to_file(eta, train_station_name, train_stop_id)
        else:
            add_train_stop_to_json(eta, train_stop_id)
            add_train_to_file(eta, train_station_name, train_stop_id)


def add_train_to_file(eta, station_name, stop_id):
    """Parses API Result from Train Tracker API and adds ETA's to a list"""
    prediction = eta["prdt"]
    arrival = eta["arrT"]
    estimated_time = int(minutes_between(prediction, arrival))
    if eta["isSch"] == "0" and eta["isApp"] == "1" and estimated_time <= 1:
        arrival_information["trains"][station_name][stop_id][
            "estimated_times"].append(str(estimated_time) + "min")
        with open('/home/pi/cta-reliability/train_arrivals.csv', 'a', newline='') as csvfile:
            csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route', 'Run_Number',
                           'Prediction_Time', 'Arrival_Time', 'Is_Approaching', 'Is_Scheduled', 'Is_Delayed', 'Is_Fault']
            writer_object = DictWriter(csvfile, fieldnames=csv_headers)
            writer_object.writerow({'Station_ID': eta["staId"], 'Stop_ID': eta["stpId"], 'Station_Name': eta["staNm"], 'Destination': eta["destNm"], 'Route': eta["rt"], 'Run_Number': eta["rn"],
                                    'Prediction_Time': eta["prdt"], 'Arrival_Time': eta["arrT"], 'Is_Approaching': eta["isApp"], 'Is_Scheduled': eta["isSch"], 'Is_Delayed': eta["isDly"], 'Is_Fault': eta["isFlt"]})


def create_string_of_items(items):
    """Takes each item from list and builds a useable string"""
    string_count = 0
    string = ""
    for item in items:
        if string_count == 0:
            string = item
            string_count += 1
        elif string_count > 0 and string_count < 3:
            string = string + ", " + item
            string_count += 1
    return string


def information_output_to_display(arrival_information_input):
    """Used to create structure for use when outputting data to e-ink epd"""
    display_information_output = []
    for station in arrival_information_input['trains'].copy():
        for train in arrival_information_input['trains'][station].copy():
            if arrival_information['trains'][station][train][
                    "estimated_times"] != []:
                display_information_output.append({
                    'line_1':
                    station,
                    'line_2':
                    (arrival_information['trains'][station][train]['route'] +
                     " Line to " + arrival_information['trains'][station]
                     [train]['destination_name']),
                    'line_3':
                    create_string_of_items(
                        arrival_information['trains'][station][train]
                        ["estimated_times"]),
                    'item_type':
                    "train",
                })
            else:
                display_information_output.append({
                    'line_1':
                    station,
                    'line_2':
                    (arrival_information['trains'][station][train]['route'] +
                     " Line to " + arrival_information['trains'][station]
                     [train]['destination_name']),
                    'line_3':
                    "No arrivals found :(",
                    'item_type':
                    "train",
                })

            arrival_information['trains'][station][train][
                "estimated_times"] = []
    return display_information_output


def information_to_display(status):
    """Used to create structure for use when outputting data to e-ink epd"""
    loop_count = 0
    while loop_count < len(status):
        try:
            print(status[loop_count]['line_1'])
            print(status[loop_count]['line_2'])
            print(status[loop_count]['line_3'])
            print("------------------------")
            loop_count += 1
        except: # pylint: disable=bare-except
            print("Unable to print for some reason")


def check_file_exists():
    """Used to check if file exists"""
    csv_file = os.path.exists("/home/pi/cta-reliability/train_arrivals.csv")
    if csv_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        with open('/home/pi/cta-reliability/train_arrivals.csv', 'w', newline='') as csvfile:
            csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route', 'Run_Number',
                           'Prediction_Time', 'Arrival_Time', 'Is_Approaching', 'Is_Scheduled', 'Is_Delayed', 'Is_Fault']
            writer_object = DictWriter(csvfile, fieldnames=csv_headers)
            writer_object.writeheader()
    else:
        print("File Exists...Continuing...")


print("Welcome to TrainTracker, Python/RasPi Edition!")
# Check to make sure output file exists and write headers
check_file_exists()
while True:  # Where the magic happens
    # Settings
    file = open(file='/home/pi/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    train_tracker_url = settings["train-tracker"]["api-url"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_train_tracker = settings["train-tracker"]["enabled"]
    train_station_stop_ids = settings["train-tracker"]["station-ids"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"trains":{}}')

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    print("\n" + current_time_console)

    if train_station_stop_ids != "" and enable_train_tracker == "True":
        for train_stop_id_to_check in train_station_stop_ids:
            try:
                response = train_api_call_to_cta(train_stop_id_to_check)
            except:  # pylint: disable=bare-except
                print("Error in API Call to Train Tracker")

    information_to_display(
        information_output_to_display(arrival_information))
    SLEEP_AMOUNT = 30
    print("Sleeping " + str(SLEEP_AMOUNT) + " Seconds")
    time.sleep(SLEEP_AMOUNT)
