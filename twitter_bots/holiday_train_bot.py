"""This checks if CTA Holiday Train is active and tweets it!"""
import os
import json
import re
import tweepy
import requests  # Used for API Calls
from datetime import datetime
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

train_tracker_url_map = settings["train-tracker"]["map-url"]
metra_tracker_url = settings["metra-api"]["trips-api-url"]
RUN_NUMBER_TO_FIND = "1225"


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "today":
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    return date


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
            metra_tracker_url, auth=(metra_username, metra_password))
        api_response_json = api_response.json()
    except:  # pylint: disable=bare-except
        print("Error in API Call to Metra Train Tracker")
    return api_response_json


def find_CTA_holiday_train(response, run_number):
    """takes output from the API and looks for the holiday train (usually Run # 1225)"""
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
                    if marker["DestName"] == "O'Hare&nbsp;<img alt='' height='13' src='/cms/images/icon_ttairport.png' width='13' style='padding-top:2px;' />":
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
                    if marker["DestName"] == "Midway&nbsp;<img alt='' height='13' src='/cms/images/icon_ttairport.png' width='13' style='padding-top:2px;' />":
                        destination = "Midway"
                    else: 
                        destination = marker["DestName"]
                else:
                    line_name = "Red"
                    destination = marker["DestName"]
                output_line = f'Run # {marker["RunNumber"]}, the CTA Holiday Train is on the {line_name} line {marker["DirMod"]} {destination}\nNext Stops:'
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

def find_Metra_holiday_train(response, date):
    """takes output from the API and looks for the holiday train (usually Run # 1225)"""
    output_line = "The CTA Holiday Train is Active!"
    for train in response:
        print(train)
        # for marker in train["Markers"]:
        #     if marker["RunNumber"] == run_number:
        #         if marker["LineName"] == "Pur":
        #             line_name = "Purple"
        #         elif marker["LineName"] == "Yel":
        #             line_name = "Yellow"
        #         elif marker["LineName"] == "Blu":
        #             line_name = "Blue"
        #         elif marker["LineName"] == "Pnk":
        #             line_name = "Pink"
        #         elif marker["LineName"] == "Grn":
        #             line_name = "Green"
        #         elif marker["LineName"] == "Brn":
        #             line_name = "Brown"
        #         elif marker["LineName"] == "Org":
        #             line_name = "Orange"
        #         else:
        #             line_name = "Red"
        #         output_line = f'{output_line}\nRun # {marker["RunNumber"]} ({line_name} line {marker["DirMod"]} {marker["DestName"]})\nNext Stops:'
        #         for prediction in marker["Predictions"]:
        #             if str(prediction[2]) == "<b>Due</b>":
        #                 eta = "Due"
        #             else:
        #                 minutes = re.sub('[^0-9]+', '', str(prediction[2]))
        #                 eta = f"{minutes} minutes"
        #             output_line = f'{output_line}\n• {prediction[1]} - {eta}'
        #         output_line = f'{output_line}\nFollow live at: https://holiday.transitstat.us'
                # print(output_line)
                # send_tweet(output_line)
    return output_line

def send_tweet(tweet_text_input):
    """sends the tweet data if the right run is found!"""
    api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                    twitter_access_token, twitter_access_token_secret)
    status1 = api.create_tweet(text=tweet_text_input)
    first_tweet = status1.data["id"]
    print(
        f"sent new tweets https://twitter.com/ChiHolidayTrain/status/{first_tweet} with contents\n{tweet_text_input}")

cta_tweet_text = find_CTA_holiday_train(train_api_call_to_cta_map(), RUN_NUMBER_TO_FIND)
# metra_tweet_text = find_Metra_holiday_train(train_api_call_to_metra(), metra_runs)
