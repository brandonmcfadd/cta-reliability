"""This checks if CTA Holiday Train is active and tweets it!"""
import os
import json
import re
from datetime import datetime, timedelta
from time import sleep
import tweepy
import requests  # Used for API Calls
from dotenv import load_dotenv  # Used to Load Env Var

# Load .env variables
load_dotenv()

# ENV Variables
twitter_api_key = os.getenv('HOLIDAY_TRAIN_API_KEY')
twitter_api_key_secret = os.getenv('HOLIDAY_TRAIN_API_KEY_SECRET')
twitter_access_token = os.getenv('HOLIDAY_TRAIN_ACCESS_TOKEN')
twitter_access_token_secret = os.getenv('HOLIDAY_TRAIN_ACCESS_TOKEN_SECRET')
twitter_bearer_key = os.getenv('HOLIDAY_TRAIN_BEARER_TOKEN')
main_file_path = os.getenv('FILE_PATH')
metra_username = os.getenv('METRA_USERNAME')
metra_password = os.getenv('METRA_PASSWORD')

# Settings
file = open(file=main_file_path + 'settings.json',
            mode='r',
            encoding='utf-8')
settings = json.load(file)

# Metra Runs
file = open(file=main_file_path + 'sorting_information/metra_holiday_trains.json',
            mode='r',
            encoding='utf-8')
metra_runs = json.load(file)

# Metra Stop Info
file = open(file=main_file_path + 'sorting_information/metra_stop_information.json',
            mode='r',
            encoding='utf-8')
metra_stops = json.load(file)

train_tracker_url_map = settings["train-tracker"]["map-url"]
metra_tracker_url = settings["metra-api"]["trips-api-url"]


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "today":
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    elif date_type == "dayofweek":
        date = datetime.strftime(datetime.now(), "%w")
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


def train_api_call_to_metra():
    """Gotta talk to Metra and get vehicle positions!"""
    print("Making Metra API Call...")
    try:
        api_response = requests.get(
            metra_tracker_url, auth=(metra_username, metra_password), timeout=240)
        api_response_json = api_response.json()
    except:  # pylint: disable=bare-except
        print("Error in API Call to Metra Train Tracker")
    return api_response_json


def find_cta_holiday_train(response, run_number):
    """takes output from the API and looks for the holiday train (usually Run # 1225)"""
    output_line = ""
    for train in response['dataObject']:
        for marker in train["Markers"]:
            if marker["RunNumber"] == run_number:
                if marker["LineName"] == "Pur":
                    line_name = "Purple"
                    destination = marker["DestName"]
                elif marker["LineName"] == "Yel":
                    line_name = "Yellow"
                    destination = marker["DestName"]
                elif marker["LineName"] == "Blu":
                    line_name = "Blue"
                    if "icon_ttairport" in marker["DestName"]:
                        destination = "O'Hare"
                    else:
                        destination = marker["DestName"]
                elif marker["LineName"] == "Pnk":
                    line_name = "Pink"
                    destination = marker["DestName"]
                elif marker["LineName"] == "Grn":
                    line_name = "Green"
                    destination = marker["DestName"]
                elif marker["LineName"] == "Brn":
                    line_name = "Brown"
                    destination = marker["DestName"]
                elif marker["LineName"] == "Org":
                    line_name = "Orange"
                    if "icon_ttairport" in marker["DestName"]:
                        destination = "Midway"
                    else:
                        destination = marker["DestName"]
                else:
                    line_name = "Red"
                    destination = marker["DestName"]
                output_line = f'The CTA Holiday Train, run # {marker["RunNumber"]} is on the {line_name} line {marker["DirMod"]} {destination}\nNext Stops:'
                for prediction in marker["Predictions"]:
                    if str(prediction[2]) == "<b>Due</b>":
                        eta = "Due"
                    else:
                        minutes = re.sub('[^0-9]+', '', str(prediction[2]))
                        eta = f"{minutes} minutes"
                    output_line = f'{output_line}\n• {prediction[1]} - {eta}'
                output_line = f'{output_line}\nFollow live at: https://holiday.transitstat.us'
                send_tweet(output_line)
    return output_line


def find_metra_holiday_train(response):
    """takes output from the API and looks for the holiday train"""
    for train in response:
        process = False
        trip_id = train["trip_update"]["vehicle"]["label"]
        route_id = train["trip_update"]["trip"]["route_id"]
        try:
            if route_id == "ME":
                route_name = "Electric"
                if get_date("dayofweek") == "0":
                    if trip_id in metra_runs["Sunday"]:
                        process = True
                elif get_date("dayofweek") == "6":
                    if trip_id in metra_runs["Saturday"]:
                        process = True
                else:
                    if trip_id in metra_runs["Weekday"]:
                        process = True
            elif route_id == "RI":
                route_name = "Rock Island"
                if trip_id in metra_runs[get_date("today")]:
                    process = True
            else:
                route_name = route_id
                if trip_id in metra_runs[get_date("today")]:
                    process = True
            if process is True:
                output_text = f"Holiday Themed Metra {route_name} train # {trip_id} is active!\nNext Stops:"
                count = 0
                while count in range(5):
                    stop_name = metra_stops[train["trip_update"]["stop_time_update"][count]["stop_id"]]["stop_name"]
                    minutes_away = minutes_between(
                        train["trip_update"]["stop_time_update"][count]["arrival"]["time"]["low"])
                    if minutes_away != "0" and minutes_away != 0:
                        output_text = f"{output_text}\n• {stop_name} - {minutes_away} min"
                        count += 1
                send_tweet(output_text)
        except:  # pylint: disable=bare-except
            process = False
            continue
    return output_text


def send_tweet(tweet_text_input):
    """sends the tweet data if the right run is found!"""
    print(f"Sending Tweet with contents\n{tweet_text_input}")
    api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                        twitter_access_token, twitter_access_token_secret)
    status1 = api.create_tweet(text=tweet_text_input)
    first_tweet = status1.data["id"]
    print(
        f"sent new tweets https://twitter.com/ChiHolidayTrain/status/{first_tweet}")
    sleep(5)


cta_tweet_text = find_cta_holiday_train(
    train_api_call_to_cta_map(), "1225")
metra_tweet_text = find_metra_holiday_train(train_api_call_to_metra())