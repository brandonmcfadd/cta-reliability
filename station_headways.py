"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import logging
from logging.handlers import RotatingFileHandler
import json  # Used for JSON Handling
import time  # Used to Get Current Time
# Used for converting Prediction from Current Time
from datetime import datetime, timedelta
import re
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
main_file_path = os.getenv('FILE_PATH')

# Logging Information
LOG_FILENAME = main_file_path + '/cta-reliability/logs/station-headways.log'
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=10e6, backupCount=10)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)

def train_api_call_to_cta_map(line,line_long):
    """Gotta talk to the CTA and get Train Times part 2!"""
    logging.info("Making CTA Train Map API Call for the %s line...", line)
    try:
        api_response = requests.get(train_tracker_url_map.format(line), timeout=10)
        train_arrival_times_map(api_response.json(), line_long)
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error("Map - Http Error: %s", errh)
    except requests.exceptions.ConnectionError as errc:
        logging.error("Map - Error Connecting: %s", errc)
    except requests.exceptions.Timeout as errt:
        logging.error("Map - Timeout Error: %s", errt)
    except requests.exceptions.RequestException as err:
        logging.error("Map - Error in API Call to Train TrackerL %s", err)
    return api_response


def add_train_to_json(line, direction, headway):
    """Function is called to add a train to the json"""
    current_count = arrival_information["trains"][line][direction]["count"]
    arrival_information["trains"][line][direction]["count"] = current_count + 1
    arrival_information["trains"][line][direction]["arrival_headways"].append(
        headway)
    arrival_information["trains"][line][direction]["arrival_headways"].sort()


def train_arrival_times_map(response, line):
    """Used to parse the Train Tracker Map API Response"""
    northbound_destinations = ["Jefferson Park", "Rosemont", "Harlem/Lake", "Howard", "O'Hare&nbsp;<img alt='' height='13' src='/cms/images/icon_ttairport.png' width='13' style='padding-top:2px;' />", "Kimball", "Dempster", "Linden", "Howard"]
    southbound_destinations = ["Forest Park", "UIC-Halsted", "54th/Cermak", "95th/Dan Ryan", "Midway&nbsp;<img alt='' height='13' src='/images/icon_ttairport.png' width='13' style='padding-top:2px;'/>", "Cottage Grove", "Ashland/63rd"]
    for train in response['dataObject']:
        for marker in train["Markers"]:
            for prediction in marker["Predictions"]:
                if str(prediction[0]) in train_station_map_ids:
                    eta = re.sub('[^0-9]+', '', str(prediction[2]))
                    if marker["DestName"] == "Loop":
                        if marker["LineName"] in ["Org", "Pnk"]:
                            if str(prediction[2]) == "<b>Due</b>":
                                add_train_to_json(line, "north", 0)
                            elif int(eta) < 45:
                                add_train_to_json(line, "north", int(eta))
                        elif marker["LineName"] in ["Brn", "Pur"]:
                            if str(prediction[2]) == "<b>Due</b>":
                                add_train_to_json(line, "south", 0)
                            elif int(eta) < 45:
                                add_train_to_json(line, "south", int(eta))
                    else:
                        if eta == "":
                            continue
                        elif str(prediction[2]) == "<b>Due</b>":
                            if marker["DestName"] in northbound_destinations:
                                add_train_to_json(line, "north", 0)
                            elif marker["DestName"] in southbound_destinations and marker["DestName"] == "UIC-Halsted":
                                add_train_to_json(line, "south-express", 0)
                                add_train_to_json(line, "south", 0)
                            elif marker["DestName"] in southbound_destinations:
                                add_train_to_json(line, "south", 0)
                        elif int(eta) < 45:
                            if marker["DestName"] in northbound_destinations:
                                add_train_to_json(line, "north", int(eta))
                            elif marker["DestName"] in southbound_destinations and marker["DestName"] == "UIC-Halsted":
                                add_train_to_json(line, "south-express", int(eta))
                                add_train_to_json(line, "south", int(eta))
                            elif marker["DestName"] in southbound_destinations:
                                add_train_to_json(line, "south", int(eta))
    return True


def prepare_output():
    """gets it twitter ready"""
    lines_to_check = {"R":"Red","P":"Pur","Y":"Yel","B":"Blu","V":"Pnk","G":"Grn","T":"Brn","O":"Org"}
    for line_short, line_long in lines_to_check.items():
        last_headway = 0
        for headway in arrival_information["trains"][line_long]["north"]["arrival_headways"]:
            moving_headway = headway - last_headway
            last_headway = headway
            arrival_information["trains"][line_long]["north"]["actual_headways"].append(
                moving_headway)
        if arrival_information["trains"][line_long]["north"]["count"] > 0:
            arrival_information["trains"][line_long]["north"]["average_headway"] = int(sum(arrival_information["trains"][line_long]["north"]["actual_headways"])/arrival_information["trains"][line_long]["north"]["count"])
        last_headway = 0
        for headway in arrival_information["trains"][line_long]["south"]["arrival_headways"]:
            moving_headway = headway - last_headway
            last_headway = headway
            arrival_information["trains"][line_long]["south"]["actual_headways"].append(
                moving_headway)
        last_headway = 0
        if arrival_information["trains"][line_long]["south"]["count"] > 0:
            arrival_information["trains"][line_long]["south"]["average_headway"] = int(sum(arrival_information["trains"][line_long]["south"]["actual_headways"])/arrival_information["trains"][line_long]["south"]["count"])
        try:
            for headway in arrival_information["trains"][line_long]["south-express"]["arrival_headways"]:
                moving_headway = headway - last_headway
                last_headway = headway
                arrival_information["trains"][line_long]["south-express"]["actual_headways"].append(
                    moving_headway)
            if arrival_information["trains"][line_long]["south-express"]["count"] > 0:
                arrival_information["trains"][line_long]["south-express"]["average_headway"] = int(sum(arrival_information["trains"][line_long]["south-express"]["actual_headways"])/arrival_information["trains"][line_long]["south-express"]["count"])
        except:
            pass


def output_data_to_file():
    """puts the data in a json file for the api"""
    date = datetime.strftime(datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
    arrival_information["last_update"] = date
    file_path = main_file_path + "cta-reliability/train_arrivals/json/"
    with open(file_path + "special-station.json", 'w', encoding='utf-8') as file1:
        json.dump(arrival_information, file1, indent=2)
    logging.info("File Outputs Complete")


logging.info("Welcome to TrainTracker, Python Edition!")
# Check to make sure output file exists and write headers
while True:  # Where the magic happens
# Settings
    file = open(file=main_file_path + '/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(file)

    # API URL's
    train_tracker_url_map = settings["train-tracker"]["headway-map-url"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    train_station_map_ids = settings["train-tracker"]["headway-map-station-ids"]

    # Setting Up Variable for Storing Station Information
    arrival_information = json.loads('{"Data Provided By":"Brandon McFadden - http://rta-api.brandonmcfadden.com","Reports Acccessible At":"https://brandonmcfadden.com/cta-reliability","V2 API Information At":"http://rta-api.brandonmcfadden.com","Entity":"cta","last_update":"1970-01-01T00:00:00-0500","trains":{"Blu":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south-express":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Brn":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Grn":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Org":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Pnk":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Pur":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Red":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}},"Yel":{"north":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0},"south":{"count":0,"arrival_headways":[],"actual_headways":[],"average_headway":0}}}}')

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M:%S")
    logging.info(current_time_console)

    lines_to_process = {"R":"Red","P":"Pur","Y":"Yel","B":"Blu","V":"Pnk","G":"Grn","T":"Brn","O":"Org"}
    # lines_to_process = {"B":"Blu"}
    # Map Portion runs if enabled and station id's exist
    for key, value in lines_to_process.items():
        train_api_call_to_cta_map(key,value)
    prepare_output()
    output_data_to_file()


    # Wait and do it again
    SLEEP_AMOUNT = 30
    SLEEP_STRING = "Sleeping " + str(SLEEP_AMOUNT) + " Seconds"
    logging.info(SLEEP_STRING)
    time.sleep(SLEEP_AMOUNT)
