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
bus_tracker_key = os.getenv('BUS_API_KEY')

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
bus_tracker_url = settings["bus-tracker-api"]["api-url"]


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
    """Gotta talk to Metra and get vehicle_id positions!"""
    print("Making Metra API Call...")
    try:
        api_response = requests.get(
            metra_tracker_url, auth=(metra_username, metra_password), timeout=240)
        api_response_json = api_response.json()
    except:  # pylint: disable=bare-except
        print("Error in API Call to Metra Train Tracker")
    return api_response_json


def bus_api_call_to_cta():
    """Gotta talk to Metra and get vehicle_id positions!"""
    print("Making CTA Bus API Call...")
    try:
        api_response = requests.get(
            bus_tracker_url.format(bus_tracker_key), timeout=240)
        api_response_json = api_response.json()
    except:  # pylint: disable=bare-except
        print("Error in API Call to Metra Train Tracker")
    return api_response_json


def find_cta_holiday_train(response, run_number):
    """takes output from the API and looks for the holiday train (usually Run # 1225)"""
    output_line = ""
    for train in response['dataObject']:
        for marker in train["Markers"]:
            if marker["Flags"] == "H":
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
                output_line = f'The CTA Pride Train #{marker["RunNumber"]} is on the {line_name} Line {marker["DirMod"]} {destination}\nNext Stops:'
                prediction_count = 0
                for prediction in marker["Predictions"]:
                    if str(prediction[2]) == "<b>Due</b>":
                        eta = "Due"
                    else:
                        minutes = re.sub('[^0-9]+', '', str(prediction[2]))
                        eta = f"{minutes} minutes"
                    output_line = f'{output_line}\n• {prediction[1]} - {eta}'
                    prediction_count += 1
                # output_line = f'{output_line}\nFollow live at: https://holiday.transitstat.us'
                if prediction_count > 0:
                    print(f"Sending Tweet with contents\n{output_line}")
                    send_tweet(output_line)
    return output_line


def find_metra_holiday_train(response):
    """takes output from the API and looks for the holiday train"""
    for train in response:
        process = False
        unscheduled_text = ""
        run_number = train["trip_update"]["vehicle"]["label"]
        route_id = train["trip_update"]["trip"]["route_id"]
        trip_id = train["trip_update"]["trip"]["trip_id"]
        vehicle_id = train["trip_update"]["vehicle"]["id"]
        if route_id == "ME" and vehicle_id in ["1343"]:
            route_name = "Electric"
            process = True
            # if get_date("dayofweek") == "0":
            #     if run_number in metra_runs["Sunday"] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "scheduled") is False:
            #         process = True
            # elif get_date("dayofweek") == "6" and get_date("today") not in metra_runs["Saturday"]["not-on-these-days"]:
            #     if run_number in metra_runs["Saturday"] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "scheduled") is False:
            #         process = True
            # else:
            #     if run_number in metra_runs["Weekday"] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "scheduled") is False:
            #         process = True
        elif route_id == "RI":
            route_name = "Rock Island"
            # if run_number in metra_runs[get_date("today")] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "scheduled") is False:
            #     process = True
        else:
            route_name = route_id
            # if run_number in metra_runs[get_date("today")] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "scheduled") is False:
            #     if route_id == metra_runs[get_date("today")][run_number]:
            #         process = True
            # elif vehicle_id in metra_runs["unscheduled-trains"] and has_been_tweeted(run_number, vehicle_id, route_id, trip_id, "unscheduled") is False:
            #     if route_id == "ME":
            #         route_name = "Electric"
            #     elif route_id == "RI":
            #         route_name = "Rock Island"
            #     process = True
            #     unscheduled_text = " (Likely Holiday Train)"
        if process is True:
            output_text = f"Metra {route_name} run #{run_number} is the Pride train!\nUp Next:"
            count = 0
            if len(train["trip_update"]["stop_time_update"]) < 3:
                stop_limit = 0
            elif len(train["trip_update"]["stop_time_update"]) < 6:
                stop_limit = len(train["trip_update"]["stop_time_update"])
            else:
                stop_limit = 7
            for stop in train["trip_update"]["stop_time_update"]:
                if count < stop_limit:
                    stop_name = metra_stops[stop["stop_id"]]["stop_name"]
                    minutes_away = minutes_between(
                        stop["arrival"]["time"]["low"])
                    if int(minutes_away) > 2:
                        output_text = f"{output_text}\n• {stop_name} - {minutes_away} min"
                        count += 1
            if count > 3:
                print(f"Sending Tweet with contents\n{output_text}")
                send_tweet(output_text)
        else:
            output_text = ""
    return output_text


def find_cta_holiday_bus(response):
    """find the bus - tweet the bus!"""
    output_line = ""
    try:
        count = 0
        total_count = 0
        route_id = response["bustime-response"]["prd"][0]["rt"]
        route_dir = response["bustime-response"]["prd"][0]["rtdir"]
        output_line = f'CTA Holiday Bus is {route_dir} on Route #{route_id}\nNext Stops:'
        for prediction in response["bustime-response"]["prd"]:
            if prediction['prdctdn'] != "DUE" and int(prediction['prdctdn']) > 5:
                if (count % 3) == 0 and total_count <= 5:
                    output_line = (
                        f"{output_line}\n{prediction['stpnm']} - {prediction['prdctdn']}")
                    total_count += 1
            count += 1
        if total_count > 3:
            print(f"Sending Tweet with contents\n{output_line}")
            send_tweet(output_line)
    except:  # pylint: disable=bare-except
        print("bus must not be active")
    return output_line


def has_been_tweeted(run_number_in, vehicle_id_in, route_id_in, trip_id_in, type_in):
    """checks if a metra run was tweeted already"""
    with open(main_file_path + "train_arrivals/special/tweeted_metra_trains.json", 'r', encoding="utf-8") as fp:
        json_file_loaded = json.load(fp)
        if get_date("tweeted") in json_file_loaded["hourly"]:
            if run_number_in in json_file_loaded["hourly"][get_date("tweeted")]:
                has_been_tweeted_result = True
            else:
                has_been_tweeted_result = False
        else:
            has_been_tweeted_result = False
    if has_been_tweeted_result is False:
        with open(main_file_path + "train_arrivals/special/tweeted_metra_trains.json", 'w', encoding="utf-8") as fp2:
            if get_date("tweeted") not in json_file_loaded["hourly"]:
                json_file_loaded["hourly"] = {**json_file_loaded["hourly"],
                                              **{get_date("tweeted"): {}}}
            if get_date("today") not in json_file_loaded["daily"]:
                json_file_loaded["daily"] = {**json_file_loaded["daily"],
                                             **{get_date("today"): {}}}
            vehicle_to_add = {"vehicle": vehicle_id_in,
                              "route": route_id_in, "trip": trip_id_in, "type": type_in}
            json_file_loaded["hourly"][get_date(
                "tweeted")][run_number_in] = vehicle_to_add
            json_file_loaded["daily"][get_date(
                "today")][run_number_in] = vehicle_to_add
            json.dump(json_file_loaded, fp2, indent=4,  separators=(',', ': '))
    return has_been_tweeted_result


def send_tweet(tweet_text_input):
    """sends the tweet data if the right run is found!"""
    try:
        api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                            twitter_access_token, twitter_access_token_secret)
        status1 = api.create_tweet(text=tweet_text_input)
        first_tweet = status1.data["id"]
        print(
            f"sent new tweets https://twitter.com/ChiSpecialTrain/status/{first_tweet}")
        sleep(5)
    except:  # pylint: disable=bare-except
        print("Twitter error :(")


cta_tweet_text = find_cta_holiday_train(
    train_api_call_to_cta_map(), "1225")
metra_tweet_text = find_metra_holiday_train(train_api_call_to_metra())
# bus_tweet_text = find_cta_holiday_bus(bus_api_call_to_cta())
