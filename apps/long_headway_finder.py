"""This checks for the longest Headway Gap in the CTA System Map"""
import os
import json
import re
from datetime import datetime, timedelta
import requests  # Used for API Calls
from dotenv import load_dotenv  # Used to Load Env Var

# Load .env variables
load_dotenv()

# ENV Variables
main_file_path = os.getenv('FILE_PATH')

# Settings
file = open(file=main_file_path + 'settings.json',
            mode='r',
            encoding='utf-8')
settings = json.load(file)

train_tracker_url_map = settings["train-tracker"]["map-url"]
metra_tracker_url = settings["metra-api"]["trips-api-url"]
bus_tracker_url = settings["bus-tracker-api"]["api-url"]
line_names = {"Red":"Red","Pur":"Purple","Yel":"Yellow","Blu":"Blue","Pnk":"Pink","Grn":"Green","Brn":"Brown","Org":"Orange"}

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


def minutes_between(date_1):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S.%fZ")
    difference = date_1 - datetime.utcnow()
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes


def train_api_call_to_cta_map():
    """Gotta talk to the CTA and get Train Times!"""
    print("Making CTA Train Map API Call...")
    try:
        api_response = requests.get(train_tracker_url_map, timeout=10)
        api_output = api_response.json()
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Map - Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Map - Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Map - Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Map - Error in API Call to Train Tracker", err)
    return api_output

def find_headways(response):
    """takes output from the API and pulls out all the stations and headways"""
    headways = {"LastUpdated":get_date("full"),"Lines":{}}
    for train in response['dataObject']:
        for marker in train["Markers"]:
            for prediction in marker["Predictions"]:
                if str(prediction[2]) == "<b>Due</b>":
                    eta = 0
                elif str(prediction[2]) == "Delayed":
                    eta = None
                else:
                    minutes = re.sub('[^0-9]+', '', str(prediction[2]))
                    eta = int(minutes)
                if eta is not None:
                    line_name = line_names[marker["LineName"]]
                    station_name = str(prediction[1])
                    station_id = int(prediction[0])
                    if line_name not in headways["Lines"]:
                        headways["Lines"] = {**headways["Lines"],**{line_name: {}}}
                    if station_name not in headways["Lines"][line_name]:
                        headways["Lines"][line_name] = {**headways["Lines"][line_name],**{station_name: {}}}
                    if str(marker["DestName"]).startswith(("O'Hare", "Midway")):
                        if str(marker["DestName"]).startswith("O'Hare"):
                            destination = "O'Hare"
                        else:
                            destination = "Midway"
                    else:
                        destination = marker["DestName"]
                    if destination in ("UIC-Halsted", "Cottage Grove"):
                        style = f"cta-{line_name}-line-inverted"
                    else:
                        style = f"cta-{line_name}-line"
                    if destination not in headways["Lines"][line_name][station_name]:
                        headways["Lines"][line_name][station_name] = {**headways["Lines"][line_name][station_name],**{destination: {"Arrivals":[],"Headways":[],"Trains":{}}}}
                    else:
                        headways["Lines"][line_name][station_name][destination]["Arrivals"].append(eta)
                        headways["Lines"][line_name][station_name][destination]["Arrivals"].sort()
                        headways["Lines"][line_name][station_name][destination]["Trains"] = {**headways["Lines"][line_name][station_name][destination]["Trains"],**{str(eta):{"TimeToArrival":eta,"Headway":None,"Line":line_name,"RunNumber":marker["RunNumber"],"Destination":destination, "StationName":station_name, "StationID":station_id, "Style": style}}}
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
    return(headways)


with open(main_file_path + "train_arrivals/special/long_headways.json", 'w', encoding="utf-8") as fp2:
    headways_input = find_headways(train_api_call_to_cta_map())
    calculated_headways = calculate_headways(headways_input)
    headways_output = find_the_big_ones(calculated_headways)
    json.dump(headways_output, fp2, indent=4,  separators=(',', ': '))
