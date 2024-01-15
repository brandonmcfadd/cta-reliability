"""grabs data from the api and sends it off to the isCTAokay twitter account"""
import os
from datetime import datetime, timedelta
from time import sleep
import tweepy
import requests  # Used for API Calls
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


def get_date(date_type):
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
    return date

def get_ordinal_suffix(day: int) -> str:
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') if day not in (11, 12, 13) else 'th'

def get_run_data_from_api(type):
    """hits the api and returns the current days data"""
    todays_stats_api_url = f"http://api.brandonmcfadden.com/api/v2/cta/get_daily_results/{type}"
    my_api_call_headers = {
        'Authorization': my_api_key
    }

    api_response = requests.request(
        "GET", todays_stats_api_url, headers=my_api_call_headers, timeout=30)

    return api_response.json()


def day_of_performance_stats(data):
    """determines the type of day we having"""
    system_actual = int(data["system"]["ActualRuns"])
    system_scheduled = int(data["system"]["ScheduledRuns"])
    if system_actual/system_scheduled >= 0.98:
        type_of_day = 0
    elif system_actual/system_scheduled >= 0.95 and system_actual/system_scheduled < 0.98:
        type_of_day = 1
    elif system_actual/system_scheduled >= 0.90 and system_actual/system_scheduled < 0.95:
        type_of_day = 2
    elif system_actual/system_scheduled >= 0.80 and system_actual/system_scheduled < 0.90:
        type_of_day = 3
    else:
        type_of_day = 4
    return type_of_day


def prepare_tweet_text_1(data, is_good_day_flag):
    """preps the tweet text for the first tweet"""
    if get_date("hour") in ("0", "00"):
        text_insert = "had"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
    else:
        text_insert = "is having"
        tweet_date = get_date("tweet-date-today")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-today-int")))
        tweet_hour = f" at {get_date('tweet-hour')}"
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    system_perc_reduced = int(
        float(data["system"]["PrePandemicScheduledPercChange"]) * 100) * -1
    on_time_trains = 0

    for line in data["routes"]:
        on_time_trains += int(data["routes"][line]["Trains_On_Time"])
    if on_time_trains > 0:
        on_time_trains_perc = int((on_time_trains/system_actual)*100)
    if is_good_day_flag == 0:
        type_of_day = f"🤩CTA Rail {text_insert} a great day! To do this, the CTA cut {system_perc_reduced}% of scheduled service."
        expression = "!"
    elif is_good_day_flag == 1:
        type_of_day = f"😎CTA Rail {text_insert} a good day! To do this, the CTA cut {system_perc_reduced}% of scheduled service."
        expression = "!"
    elif is_good_day_flag == 2:
        type_of_day = f"🤷CTA Rail {text_insert} a so-so day even with a {system_perc_reduced}% cut of scheduled service."
        expression = "."
    elif is_good_day_flag == 3:
        type_of_day = f"😡CTA Rail {text_insert} a tough day even after cutting {system_perc_reduced}% of scheduled service."
        expression = "."
    else:
        type_of_day = f"🤬CTA Rail {text_insert} a terrible day even after cutting {system_perc_reduced}% of scheduled service."
        expression = "."
    text_output_part_1 = f"{type_of_day}\n{system_perc}% of scheduled trains operated on {tweet_date}{tweet_date_ending}{tweet_hour}{expression}\n{on_time_trains_perc}% arrived at their scheduled intervals.\nTo explore historical data: brandonmcfadden.com/cta-reliability."
    return text_output_part_1


def prepare_tweet_text_2(data):
    "prepares the reply tweet for tweet 1"
    if get_date("hour") in ("0", "00"):
        text_insert = "for"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
    else:
        text_insert = "as of"
        tweet_date = get_date("tweet-date-today")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-today-int")))
        tweet_hour = f" at {get_date('tweet-hour')}"
    system_actual = data["system"]["ActualRuns"]
    system_sched = data["system"]["ScheduledRuns"]
    scheduled_runs_remaining = data["system"]["ScheduledRunsRemaining"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)

    try:
        scheduled_runs_remaining_text = f"{scheduled_runs_remaining:,}"
    except: # pylint: disable=bare-except
        scheduled_runs_remaining_text = "🤷"
    text_output_part_2 = f"System Stats {text_insert} {tweet_date}{tweet_date_ending}{tweet_hour} (actual/scheduled):\nSystem: {system_perc}% • {system_actual:,}/{system_sched:,}"
    for line in data["routes"]:
        actual_runs = data["routes"][line]["ActualRuns"]
        scheduled_runs = data["routes"][line]["ScheduledRuns"]
        percent_run = int(float(data["routes"][line]["PercentRun"]) * 100)
        text_output_part_2 = text_output_part_2 + \
            f"\n{line}: {percent_run}% • {actual_runs:,}/{scheduled_runs:,}"
    text_output_part_2 = text_output_part_2 + \
        f"\nScheduled Runs Remaining: {scheduled_runs_remaining_text}"
    return text_output_part_2


def prepare_tweet_text_3(data):
    "prepares the reply tweet for tweet 1"
    if get_date("hour") in ("0", "00"):
        text_insert = "for"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
    else:
        text_insert = "as of"
        tweet_date = get_date("tweet-date-today")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-today-int")))
        tweet_hour = f" at {get_date('tweet-hour')}"
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    on_time_arrivals = 0
    text_output_part_3 = ""
    for line in data["routes"]:
        on_time_arrivals += int(data["routes"][line]["Trains_On_Time"])
        on_time_runs = data["routes"][line]["Trains_On_Time"]
        try:
            percent_on_time = int(float(data["routes"][line]["Trains_On_Time"]/data["routes"][line]["ActualRuns"]) * 100)
        except: # pylint: disable=bare-except
            percent_on_time = 0
        text_output_part_3 = f"{text_output_part_3}\n{line}: {percent_on_time}% • {on_time_runs:,}/{data['routes'][line]['ActualRuns']:,}"
    system_perc = int(float(on_time_arrivals/system_actual) * 100)
    text_output_part_3 = f"On-Time Performance {text_insert} {tweet_date}{tweet_date_ending}{tweet_hour} (# on-time/actual):\nSystem: {system_perc}% • {on_time_arrivals:,}/{system_actual:,}{text_output_part_3}"
    return text_output_part_3

if get_date("hour") in ("0", "00"):
    current_data = get_run_data_from_api("yesterday")
else:
    current_data = get_run_data_from_api("today")

is_good_day = day_of_performance_stats(current_data)
tweet_text_1 = prepare_tweet_text_1(current_data, is_good_day)
tweet_text_2 = prepare_tweet_text_2(current_data)
tweet_text_3 = prepare_tweet_text_3(current_data)

print(tweet_text_1)
print()
print(tweet_text_2)
print()
print(tweet_text_3)
print()

api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                    twitter_access_token, twitter_access_token_secret)
status1 = api.create_tweet(text=tweet_text_1)
first_tweet = status1.data["id"]
sleep(1)
status2 = api.create_tweet(text=tweet_text_2, in_reply_to_tweet_id=first_tweet)
second_tweet = status2.data["id"]
sleep(1)
status3 = api.create_tweet(text=tweet_text_3, in_reply_to_tweet_id=second_tweet)
third_tweet = status3.data["id"]
print(
    f"sent new tweets https://twitter.com/isCTAokay/status/{first_tweet} and https://twitter.com/isCTAokay/status/{second_tweet} and https://twitter.com/isCTAokay/status/{third_tweet}")
