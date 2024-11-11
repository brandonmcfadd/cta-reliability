"""grabs data from the api and sends it off to the isCTAokay twitter account"""
import os
from datetime import datetime, timedelta
from time import sleep
import tweepy
from atproto import Client, models
import json
import requests  # Used for API Calls
import dotenv
from dotenv import load_dotenv  # Used to Load Env Var

# Load .env variables
load_dotenv()

# ENV Variables
twitter_api_key = os.getenv('IS_CTA_OKAY_API_KEY')
twitter_api_key_secret = os.getenv('IS_CTA_OKAY_API_KEY_SECRET')
twitter_access_token = os.getenv('IS_CTA_OKAY_ACCESS_TOKEN')
twitter_access_token_secret = os.getenv('IS_CTA_OKAY_ACCESS_TOKEN_SECRET')
twitter_bearer_key = os.getenv('IS_CTA_OKAY_BEARER_TOKEN')
threads_access_token = os.getenv('THREADS_ACCESS_TOKEN')
bluesky_username = os.getenv('BLUESKY_USERNAME')
bluesky_password = os.getenv('BLUESKY_PASSWORD')
my_api_key = os.getenv('MY_API_KEY')
main_file_path = os.getenv('FILE_PATH')


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "yesterday-short":
        date = datetime.strftime(datetime.now()-timedelta(days=1), "%Y%m%d")
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

def refresh_threads_access_token(token):
    """extends threads token to last 60 more days"""
    threads_access_token_refresh_url = f"https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token={token}"
    api_response = requests.request(
        "GET", threads_access_token_refresh_url, timeout=30)
    response_json = api_response.json()
    os.environ["THREADS_ACCESS_TOKEN"] = response_json["access_token"]
    dotenv.set_key(main_file_path + ".env", "THREADS_ACCESS_TOKEN", os.environ["THREADS_ACCESS_TOKEN"])
    return response_json["expires_in"]


def create_threads_posts(text, access_token, reply_to_id=None):
    """builds the threads blue_sky_post_1 and publishes it"""
    """builds the threads blue_sky_post_1 and publishes it"""
    """builds the threads blue_sky_post_1 and publishes it"""
    """builds the threads blue_sky_post_1 and publishes it"""
    if reply_to_id is None:
        threads_access_create_post = f"https://graph.threads.net/v1.0/25882170881398162/threads?media_type=TEXT&access_token={access_token}"
    else:
        threads_access_create_post = f"https://graph.threads.net/v1.0/25882170881398162/threads?media_type=TEXT&reply_to_id={reply_to_id}&access_token={access_token}"
    payload = json.dumps({
        "text": text
        })
    headers = {
        'Content-Type': 'application/json'
        }
    api_response_1 = requests.request("POST", threads_access_create_post, headers=headers, data=payload, timeout=30)
    response_json_1 = api_response_1.json()
    post_id_1 = response_json_1["id"]
    threads_access_publish_post = f"https://graph.threads.net/v1.0/25882170881398162/threads_publish?creation_id={post_id_1}&access_token={access_token}"
    api_response_2 = requests.request(
        "POST", threads_access_publish_post, timeout=30)
    response_json_2 = api_response_2.json()
    post_id_2 = response_json_2["id"]
    return post_id_2
    

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

def check_stale_state(stale_date):
    """checks to see if CTA Data is stale before tweeting!"""
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r", encoding='utf-8') as file:
        data = json.load(file)
    if data["is_cta_data_stale"] is True:
        response = "\n‼️ Data Is Currently Outdated ‼️"
    elif data["last_cta_stale_date"] == stale_date:
        response = "\n‼Some Data Unavailable Due to Tracker Outage‼️"
    else:
        response = ""
    return response

def prepare_tweet_text_1(data, is_good_day_flag):
    """preps the tweet text for the first tweet"""
    if get_date("hour") in ("0", "00"):
        text_insert = "had"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
        additional_text = check_stale_state(get_date("yesterday-short"))
    else:
        text_insert = "is having"
        tweet_date = get_date("tweet-date-today")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-today-int")))
        tweet_hour = f" as of {get_date('tweet-hour')}"
        additional_text = check_stale_state(get_date("short"))
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    system_perc_reduced = int(
            float(data["system"]["PrePandemicScheduledPercChange"]) * 100)
    if system_perc_reduced >= 0:
        system_perc_reduced_text = "increased"
    else:
        system_perc_reduced = system_perc_reduced * -1
        system_perc_reduced_text = "reduced"
    on_time_trains = 0

    for line in data["routes"]:
        on_time_trains += int(data["routes"][line]["Trains_On_Time"])
    if on_time_trains > 0:
        on_time_trains_perc = int((on_time_trains/system_actual)*100)
    if is_good_day_flag == 0:
        type_of_day = f"🤩CTA Rail {text_insert} a great day!"
        expression = "!"
    elif is_good_day_flag == 1:
        type_of_day = f"😎CTA Rail {text_insert} a good day!"
        expression = "!"
    elif is_good_day_flag == 2:
        type_of_day = f"🤷CTA Rail {text_insert} a so-so day."
        expression = "."
    elif is_good_day_flag == 3:
        type_of_day = f"😡CTA Rail {text_insert} a tough day."
        expression = "."
    else:
        type_of_day = f"🤬CTA Rail {text_insert} a terrible day."
        expression = "."
    text_output_part_1 = f"{type_of_day}\n{system_perc}% of scheduled trains operated on {tweet_date}{tweet_date_ending}{tweet_hour}{expression}\n{on_time_trains_perc}% arrived at their scheduled intervals.\nSchedules are {system_perc_reduced_text} {system_perc_reduced}% from pre-pandemic schedules.{additional_text}"
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
        f"\nRuns Remaining: {scheduled_runs_remaining_text}"
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


def prepare_threads_text_1(data, is_good_day_flag):
    """preps the tweet text for the first tweet"""
    if get_date("hour") in ("0", "00"):
        text_insert = "had"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
        additional_text = check_stale_state(get_date("yesterday-short"))
    else:
        text_insert = "is having"
        tweet_date = get_date("tweet-date-today")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-today-int")))
        tweet_hour = f" as of {get_date('tweet-hour')}"
        additional_text = check_stale_state(get_date("short"))
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    system_perc_reduced = int(
            float(data["system"]["PrePandemicScheduledPercChange"]) * 100)
    if system_perc_reduced >= 0:
        system_perc_reduced_text = "increased"
    else:
        system_perc_reduced = system_perc_reduced * -1
        system_perc_reduced_text = "reduced"
    on_time_trains = 0

    for line in data["routes"]:
        on_time_trains += int(data["routes"][line]["Trains_On_Time"])
    if on_time_trains > 0:
        on_time_trains_perc = int((on_time_trains/system_actual)*100)
    if is_good_day_flag == 0:
        type_of_day = f"🤩CTA Rail {text_insert} a great day!"
        expression = "!"
    elif is_good_day_flag == 1:
        type_of_day = f"😎CTA Rail {text_insert} a good day!"
        expression = "!"
    elif is_good_day_flag == 2:
        type_of_day = f"🤷CTA Rail {text_insert} a so-so day."
        expression = "."
    elif is_good_day_flag == 3:
        type_of_day = f"😡CTA Rail {text_insert} a tough day."
        expression = "."
    else:
        type_of_day = f"🤬CTA Rail {text_insert} a terrible day."
        expression = "."
    text_output_part_1 = f"{type_of_day}\n{system_perc}% of scheduled trains operated on {tweet_date}{tweet_date_ending}{tweet_hour}{expression}\n{on_time_trains_perc}% arrived at their scheduled intervals.\nSchedules are {system_perc_reduced_text} {system_perc_reduced}% from pre-pandemic schedules.{additional_text}"
    return text_output_part_1


def prepare_threads_text_2(data):
    "prepares the reply text for thread reply"
    if get_date("hour") in ("0", "00"):
        text_insert = "for"
        tweet_date = get_date("tweet-date-yesterday")
        tweet_date_ending = get_ordinal_suffix(int(get_date("tweet-date-yesterday-int")))
        tweet_hour = ""
    else:
        text_insert = "As of"
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
    text_output_part_1 = f"{text_insert} {tweet_date}{tweet_date_ending}{tweet_hour}\n\nService Delivery (actual/scheduled):\nSystem: {system_perc}% • {system_actual:,}/{system_sched:,}"
    for line in data["routes"]:
        actual_runs = data["routes"][line]["ActualRuns"]
        scheduled_runs = data["routes"][line]["ScheduledRuns"]
        percent_run = int(float(data["routes"][line]["PercentRun"]) * 100)
        text_output_part_1 = text_output_part_1 + \
            f"\n{line}: {percent_run}% • {actual_runs:,}/{scheduled_runs:,}"
    text_output_part_1 = text_output_part_1 + \
        f"\nRuns Remaining: {scheduled_runs_remaining_text}"
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    on_time_arrivals = 0
    text_output_part_2 = ""
    for line in data["routes"]:
        on_time_arrivals += int(data["routes"][line]["Trains_On_Time"])
        on_time_runs = data["routes"][line]["Trains_On_Time"]
        try:
            percent_on_time = int(float(data["routes"][line]["Trains_On_Time"]/data["routes"][line]["ActualRuns"]) * 100)
        except: # pylint: disable=bare-except
            percent_on_time = 0
        text_output_part_2 = f"{text_output_part_2}\n{line}: {percent_on_time}% • {on_time_runs:,}/{data['routes'][line]['ActualRuns']:,}"
    system_perc = int(float(on_time_arrivals/system_actual) * 100)
    text_output_part_3 = f"{text_output_part_1}\n\nOn-Time Performance (# on-time/actual):\nSystem: {system_perc}% • {on_time_arrivals:,}/{system_actual:,}{text_output_part_2}\nTo explore historical data: brandonmcfadden.com/cta-reliability"
    return text_output_part_3

if get_date("hour") in ("0", "00"):
    current_data = get_run_data_from_api("yesterday")
else:
    current_data = get_run_data_from_api("today")

is_good_day = day_of_performance_stats(current_data)
tweet_text_1 = prepare_tweet_text_1(current_data, is_good_day)
tweet_text_2 = prepare_tweet_text_2(current_data)
tweet_text_3 = prepare_tweet_text_3(current_data)
tweet_text_4 = "To explore historical data: brandonmcfadden.com/cta-reliability"
threads_text_1 = prepare_threads_text_1(current_data, is_good_day)
threads_text_2 = prepare_threads_text_2(current_data)
print("Threads Token Refresh Successful. Expires in", refresh_threads_access_token(threads_access_token), "sec")

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
sleep(1)
status4 = api.create_tweet(text=tweet_text_4, in_reply_to_tweet_id=third_tweet)
fourth_tweet = status4.data["id"]
print(
    f"sent new tweets https://twitter.com/isCTAokay/status/{first_tweet} and https://twitter.com/isCTAokay/status/{second_tweet} and https://twitter.com/isCTAokay/status/{third_tweet} and https://twitter.com/isCTAokay/status/{fourth_tweet}")

threads_post_1 = create_threads_posts(threads_text_1, threads_access_token)
threads_post_2 = create_threads_posts(tweet_text_2, threads_access_token, threads_post_1)
threads_post_3 = create_threads_posts(tweet_text_3, threads_access_token, threads_post_2)
threads_post_4 = create_threads_posts(tweet_text_4, threads_access_token, threads_post_3)
print(f"Sent new threads posts with IDs: {threads_post_1} and {threads_post_2} and {threads_post_3} and {threads_post_4}")

client = Client()
client.login(bluesky_username, bluesky_password)
blue_sky_post_1 = client.send_post(threads_text_1)
root = models.create_strong_ref(blue_sky_post_1)

parent_1 = models.create_strong_ref(blue_sky_post_1)
blue_sky_post_2 = client.send_post(text=tweet_text_2,reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_1, root=root))
parent_2 = models.create_strong_ref(blue_sky_post_2)
blue_sky_post_3 = client.send_post(text=tweet_text_3,reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_2, root=root))
parent_3 = models.create_strong_ref(blue_sky_post_3)

with open(main_file_path + "twitter_bots/isCTAok.png", 'rb') as f:
  img_data = f.read()

thumb = client.upload_blob(img_data)
embed = models.AppBskyEmbedExternal.Main(
    external=models.AppBskyEmbedExternal.External(
        title='CTA Reliability Tracker',
        description='Providing insight and transparency into the service levels of the Chicago Transit Authority',
        uri='https://brandonmcfadden.com/cta-reliability',
        thumb=thumb.blob,
    )
)
blue_sky_post_4 = client.send_post(tweet_text_4, embed=embed,reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_3, root=root))
print(f"Sent new posts on Bluesky: {blue_sky_post_1.uri}, {blue_sky_post_2.uri}, {blue_sky_post_3.uri}, {blue_sky_post_4.uri}.")