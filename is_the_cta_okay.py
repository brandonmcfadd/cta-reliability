import os
import json
import tweepy
import datetime
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

# Settings
file = open(file=main_file_path + '/cta-reliability/settings.json',
            mode='r',
            encoding='utf-8')
settings = json.load(file)


def get_run_data_from_api():
    todays_stats_api_url = "http://rta-api.brandonmcfadden.com/api/v2/cta/get_daily_results/today"

    my_api_call_headers = {
        'Authorization': my_api_key
    }

    api_response = requests.request(
        "GET", todays_stats_api_url, headers=my_api_call_headers, timeout=30)

    return api_response.json()


def day_of_performance_stats(data):
    system_actual = int(data["system"]["ActualRuns"])
    system_scheduled = int(data["system"]["ScheduledRuns"])
    if system_actual/system_scheduled >= 0.9:
        good_day = True
    else:
        good_day = False
    return good_day


def prepare_tweet_text_1(data, is_good_day_flag):
    system_actual = data["system"]["ActualRuns"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    consistent_arrivals = 0
    for line in data["routes"]:
        consistent_arrivals += int(data["routes"][line]["Consistent_Headways"])
    if consistent_arrivals > 0:
        consistent_arrivals_perc = int((consistent_arrivals/system_actual)*100)
    if is_good_day_flag is True:
        type_of_day = "CTA Rail is having a good day! To do this, the CTA cut 21% of scheduled service."
        expression = "!"
    else:
        type_of_day = "CTA Rail is not having a good day even after cutting 21% of scheduled service."
        expression = "."
    text_output_part_1 = f"{type_of_day}\n{system_perc}% of scheduled trains have operated today{expression} {consistent_arrivals_perc}% arrived at consistent intervals.\nFor more on service cuts: ctaction.org/service-cuts.\nTo explore historical data: brandonmcfadden.com/cta-reliability."
    return text_output_part_1


def prepare_tweet_text_2(data):
    system_actual = data["system"]["ActualRuns"]
    system_sched = data["system"]["ScheduledRuns"]
    scheduled_runs_remaining = data["system"]["ScheduledRunsRemaining"]
    last_updated = data["LastUpdated"]
    system_perc = int(float(data["system"]["PercentRun"]) * 100)
    last_updated_datetime = datetime.datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S%z')
    last_updated_string = datetime.datetime.strftime(last_updated_datetime, '%-l%p').lower()

    consistent_arrivals = 0
    text_output_part_2 = f"System Stats as of {last_updated_string} (actual/scheduled):\nSystem: {system_perc}% - {system_actual:,}/{system_sched:,}"
    for line in data["routes"]:
        consistent_arrivals += int(data["routes"][line]["Consistent_Headways"])
        actual_runs = data["routes"][line]["ActualRuns"]
        scheduled_runs = data["routes"][line]["ScheduledRuns"]
        percent_run = int(float(data["routes"][line]["PercentRun"]) * 100)
        text_output_part_2 = text_output_part_2 + \
            f"\n{line}: {percent_run}% - {actual_runs:,}/{scheduled_runs:,}"
    text_output_part_2 = text_output_part_2 + \
        f"\nScheduled Runs Remaining: {scheduled_runs_remaining:,}"
    return text_output_part_2


current_data = get_run_data_from_api()
is_good_day = day_of_performance_stats(current_data)
tweet_text_1 = prepare_tweet_text_1(current_data, is_good_day)
tweet_text_2 = prepare_tweet_text_2(current_data)

print(tweet_text_1)
print()
print(tweet_text_2)

api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                    twitter_access_token, twitter_access_token_secret)
status1 = api.create_tweet(text=tweet_text_1, )
first_tweet = status1.data["id"]
status2 = api.create_tweet(text=tweet_text_2, in_reply_to_tweet_id=first_tweet)
second_tweet = status2.data["id"]
print(
    f"sent new tweets https://twitter.com/isCTAokay/status/{first_tweet} and https://twitter.com/isCTAokay/status/{second_tweet}")