"""This checks for the longest Headway Gap in the CTA System Map"""
import os
import json
from datetime import datetime, timedelta
import requests  # Used for API Calls
from dotenv import load_dotenv  # Used to Load Env Var
import urllib3
urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    pass  # no pyopenssl support used / needed / available

# Load .env variables
load_dotenv()

# ENV Variables
main_file_path = os.getenv('FILE_PATH')
api_key = os.getenv('TRAIN_HEADWAY_API_KEY')

# Settings
file = open(file=main_file_path + 'settings.json',
            mode='r',
            encoding='utf-8')
settings = json.load(file)

tt_api_url = settings["train-tracker"]["api-url"]
train_tracker_url_map = settings["train-tracker"]["special-map-url"]
station_ids = settings["train-tracker"]["all-station-ids"]
metra_tracker_url = settings["metra-api"]["trips-api-url"]
bus_tracker_url = settings["bus-tracker-api"]["api-url"]
line_names = {"Red":"Red","P":"Purple","Y":"Yellow","Blue":"Blue","Pink":"Pink","G":"Green","Brn":"Brown","Org":"Orange"}

def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "today":
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    elif date_type == "tweeted":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H")
    elif date_type == "dayofweek":
        date = datetime.strftime(datetime.now(), "%w")
    elif date_type == "full":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%z")
    return date


def calc_tt_eta(date_1, date_2):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S")
    date_2 = datetime.strptime(date_2, "%Y-%m-%dT%H:%M:%S")
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes


def call_to_cta_api(station_id_input, url):
    """Gotta talk to the CTA and get Train Times"""
    print(f"Making CTA Train API Call for stop: {station_id_input}")
    try:
        api_response = requests.get(
            url.format(api_key, station_id_input), timeout=30)
    except: # pylint: disable=bare-except
        print("Error in API Call to Train Tracker")
    return api_response.json()

def find_headways(response, start_time):
    """takes output from the API and pulls out all the stations and headways"""
    headways = {"LastUpdated":start_time,"Lines":{}}
    for train in response['ctatt']["eta"]:
        prediction = train["prdt"]
        arrival = train["arrT"]
        estimated_time = int(calc_tt_eta(prediction, arrival))
        line_name = line_names[train["rt"]]
        station_name = train["staNm"]
        current_station_id = train["staId"]
        destination = train["destNm"]
        if train["isSch"] == "1":
            scheduled = True
        else:
            scheduled = False
        if line_name not in headways["Lines"]:
            headways["Lines"] = {**headways["Lines"],**{line_name: {}}}
        if station_name not in headways["Lines"][line_name]:
            headways["Lines"][line_name] = {**headways["Lines"][line_name],**{station_name: {}}}
        if destination.startswith(("O'Hare", "Midway")):
            if destination.startswith("O'Hare"):
                destination = "O'Hare"
            else:
                destination = "Midway"
        if destination in ("UIC-Halsted", "Cottage Grove"):
            style = f"cta-{line_name}-line-inverted"
        else:
            style = f"cta-{line_name}-line"
        if destination not in headways["Lines"][line_name][station_name]:
            headways["Lines"][line_name][station_name] = {**headways["Lines"][line_name][station_name],**{destination: {"Arrivals":[],"Headways":[],"Trains":{}}}}
            headways["Lines"][line_name][station_name][destination]["Arrivals"].append(estimated_time)
            headways["Lines"][line_name][station_name][destination]["Arrivals"].sort()
            headways["Lines"][line_name][station_name][destination]["Trains"] = {**headways["Lines"][line_name][station_name][destination]["Trains"],**{str(estimated_time):{"TimeToArrival":int(estimated_time),"Headway":None,"Line":line_name,"RunNumber":train["rn"],"Destination":destination, "StationName":station_name, "StationID":current_station_id, "IsScheduled":scheduled, "Style": style}}}
        else:
            headways["Lines"][line_name][station_name][destination]["Arrivals"].append(estimated_time)
            headways["Lines"][line_name][station_name][destination]["Arrivals"].sort()
            headways["Lines"][line_name][station_name][destination]["Trains"] = {**headways["Lines"][line_name][station_name][destination]["Trains"],**{str(estimated_time):{"TimeToArrival":int(estimated_time),"Headway":None,"Line":line_name,"RunNumber":train["rn"],"Destination":destination, "StationName":station_name, "StationID":current_station_id, "IsScheduled":scheduled, "Style": style}}}
    return headways


def calculate_headways(headways):
    """takes the information from the Map API and determines the gaps"""
    for line in headways["Lines"]:
        for station in headways["Lines"][line]:
            for direction in headways["Lines"][line][station]:
                last_arrival = 0
                for arrival in headways["Lines"][line][station][direction]["Arrivals"]:
                    headway = arrival - last_arrival
                    headways["Lines"][line][station][direction]["Headways"].append(headway)
                    headways["Lines"][line][station][direction]["Trains"][str(arrival)]["Headway"] = headway
                    last_arrival = headway
    return headways


def find_the_big_ones(headways):
    """takes the calculated gaps and finds the largest one"""
    biggest_gap = None
    for line in headways["Lines"]:
        for station in headways["Lines"][line]:
            for direction in headways["Lines"][line][station]:
                for arrival in headways["Lines"][line][station][direction]["Trains"]:
                    train = headways["Lines"][line][station][direction]["Trains"][arrival]
                    if biggest_gap is None:
                        biggest_gap = train
                    if train["Headway"] > biggest_gap["Headway"]:
                        biggest_gap = train
    headways = {**headways,**{"BiggestGap":biggest_gap}}
    return headways

current_time = get_date("full")
for station_id in station_ids:
    api_response_value = call_to_cta_api(station_id, tt_api_url)
    if "eta" in api_response_value["ctatt"]:
        headways_input = find_headways(api_response_value, current_time)
calculated_headways = calculate_headways(headways_input)
headways_output = find_the_big_ones(calculated_headways)

with open(main_file_path + "train_arrivals/special/long_headways.json", 'w', encoding="utf-8") as fp2:
    json.dump(headways_output, fp2, indent=4,  separators=(',', ': '))
