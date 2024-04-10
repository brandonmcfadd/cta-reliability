"""grabs data from the api and sends it off to the isCTAokay twitter account"""
import os
from datetime import datetime, timedelta
from time import sleep
import tweepy
import requests  # Used for API Calls
import json
from dotenv import load_dotenv  # Used to Load Env Var

# Load .env variables
load_dotenv()

# ENV Variables
twitter_api_key = os.getenv('IS_CTA_OKAY_API_KEY')
twitter_api_key_secret = os.getenv('IS_CTA_OKAY_API_KEY_SECRET')
twitter_access_token = os.getenv('IS_CTA_OKAY_ACCESS_TOKEN')
twitter_access_token_secret = os.getenv('IS_CTA_OKAY_ACCESS_TOKEN_SECRET')
twitter_bearer_key = os.getenv('IS_CTA_OKAY_BEARER_TOKEN')
my_api_key = os.getenv('MY_API_KEY')
main_file_path = os.getenv('FILE_PATH')


def get_date(date_type, date_input=""):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "long":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%k:%M:%SZ")
    elif date_type == "tweet-date-today":
        date = datetime.strftime(datetime.now(), '%b %-e')
    elif date_type == "tweet-date-yesterday":
        date = datetime.strftime(datetime.now()-timedelta(days=1), '%b %-e')
    elif date_type == "tweet-date-today-int":
        date = datetime.strftime(datetime.now(), '%e')
    elif date_type == "tweet-date-yesterday-int":
        date = datetime.strftime(datetime.now()-timedelta(days=1), '%e')
    elif date_type == "tweet-hour":
        date = datetime.strftime(datetime.now()-timedelta(days=1), '%-l%p').lower()
    elif date_type == "current-month":
        date = datetime.strftime(datetime.now(), "%b%Y")
    elif date_type == "convert":
        date = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S").strftime("%B %d %Y at %I:%M%P")
    return date


def calc_tt_eta(date_1):
    """Takes the difference between two times and returns the minutes"""
    date_1 = datetime.strptime(date_1, "%Y-%m-%dT%H:%M:%S")
    date_2 = datetime.now()
    difference = date_2 - date_1
    difference_in_minutes = int(difference / timedelta(minutes=1))
    return difference_in_minutes

def send_tweet(txt, thread_id=None):
    """takes in text input and sends it off to twitter!"""
    api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                    twitter_access_token, twitter_access_token_secret)
    if thread_id is not None:
        status1 = api.create_tweet(text=txt)
    else:
        status1 = api.create_tweet(text=txt, in_reply_to_tweet_id=thread_id)
    tweet_id = status1.data["id"]
    print(f"sent new tweets!\n{txt}\nhttps://twitter.com/isCTAokay/status/{tweet_id}")
    sleep(1)
    return tweet_id


def save_stale_state(state):
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    old_state = data["is_cta_data_stale"]    
    data["is_cta_data_stale"] = state
    if state is True:
        data["last_cta_stale_date"] = get_date("short")
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("Stale State updated successfully.")

file_path = main_file_path + "train_arrivals/train_arrivals-" + \
    str(get_date('current-month')) + ".csv"
with open(file_path, 'r', encoding="utf-8") as f:
    last_line = f.readlines()[-1]
last_line_split = last_line.split(',')
diff_in_minutes = calc_tt_eta(last_line_split[6])
if diff_in_minutes >= 15:
    last_train_time = get_date("convert", last_line_split[6])
    output_text = f"‼️ CTA Reliability Tracker Data May Be Outdated ‼️\nThe last CTA train was logged on {last_train_time}."
    save_stale_state(True)
    send_tweet(output_text)
    print(output_text)
else:
    save_stale_state(False)
