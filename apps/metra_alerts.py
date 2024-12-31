"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
from datetime import datetime
import os  # Used to retrieve secrets in .env file
import json
import time  # Used for JSON Handling
from atproto import Client, models
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls

# Load .env variables
load_dotenv()

# ENV Variables
main_file_path = os.getenv('FILE_PATH')
metra_username = os.getenv('METRA_USERNAME')
metra_password = os.getenv('METRA_PASSWORD')
bluesky_username = os.getenv('BLUESKY_USERNAME_METRA_ALERT')
bluesky_password = os.getenv('BLUESKY_PASSWORD')

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
    else:
        date = None
    return date

def get_alerts():
    """reach Metra API and get current alerts"""
    api_response = requests.get(
            metra_tracker_url_api, auth=(metra_username, metra_password), timeout=300)
    return api_response.json()

def send_bluesky_post(text):
    """reach Bluesky API and send the posts"""
    try:
        client = Client()
        client.login(bluesky_username, bluesky_password)
        metra_track_link = "MetraTracker.com"
        if metra_track_link in text or metra_track_link.lower() in text:
            text = str(text).replace(metra_track_link, "Metra Train Tracker").replace(metra_track_link.lower(), "Metra Train Tracker").strip()
            embed = models.AppBskyEmbedExternal.Main(
                external=models.AppBskyEmbedExternal.External(
                    title='Metra Train Tracker',
                    description="Metra Train Tracker provides real time information about your train's location and predicted time of departure at your stop.",
                    uri='https://metratracker.com/home',
                )
            )
            blue_sky_post_1 = client.send_post(text, embed=embed)
            print(f"Sent new posts on Bluesky: {blue_sky_post_1.uri}.")
        else:
            blue_sky_post_2 = client.send_post(text)
            print(f"Sent new posts on Bluesky: {blue_sky_post_2.uri}.")
    except: # pylint: disable=bare-except
        print('Not All Bluesky Posts Sent :(')

def process_alerts(alerts_response):
    """work through each alert and determine if it is existing or old"""
    json_file_path = main_file_path + "train_arrivals/special/metra_alerts.json"
    new_alerts = []
    with open(json_file_path, "r", encoding="utf-8") as file_1:
        metra_alerts = json.load(file_1)
    for alert in alerts_response:
        alert_url = str(alert["alert"]["url"]["translation"][0]["text"])
        alert_headline = str(alert["alert"]["header_text"]["translation"][0]["text"])
        alert_text = str(alert["alert"]["description_text"]["translation"][0]["text"])
        alert_store = f"{alert_headline} - {alert_text}"
        if "Twitter=1" in alert_url and "train-lines" in alert_url:
            route_id = str(alert["alert"]["informed_entity"][0]["route_id"])
            if alert_store in metra_alerts:
                print(f"Alert {alert_headline} already in file.")
                new_alerts.append(alert_store)
            else:
                print(f"Alert {alert_headline} is new.")
                new_alerts.append(alert_store)
                if route_id == "ME":
                    route_name = "Electric"
                    emoji = "🚊"
                elif route_id == "RI":
                    route_name = "Rock Island"
                    emoji = "🚆"
                else:
                    route_name = route_id
                    emoji = "🚆"
                post_text = f"{emoji}Metra {route_name}:\n{alert_text}"
                send_bluesky_post(post_text)
    with open(json_file_path, "w", encoding="utf-8") as file_1:
        json.dump(new_alerts, file_1, indent=4)

while True:  # Always open while loop to continue checking for trains

    file = open(file=main_file_path + 'settings.json',
                    mode='r',
                    encoding='utf-8')
    settings = json.load(file)

    # API URL's
    metra_tracker_url_api = settings["metra-api"]["alerts-api-url"]

    alerts_to_process = get_alerts()
    process_alerts(alerts_to_process)
    print("Sleeping 60 Seconds")
    time.sleep(60)
