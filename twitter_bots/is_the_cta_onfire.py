"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import json  # Used for JSON Handling
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import tweepy

# Load .env variables
load_dotenv()

# ENV Variables
twitter_api_key = os.getenv('IS_CTA_ON_FIRE_API_KEY')
twitter_api_key_secret = os.getenv('IS_CTA_ON_FIRE_API_KEY_SECRET')
twitter_access_token = os.getenv('IS_CTA_ON_FIRE_ACCESS_TOKEN')
twitter_access_token_secret = os.getenv('IS_CTA_ON_FIRE_ACCESS_TOKEN_SECRET')
twitter_bearer_key = os.getenv('IS_CTA_ON_FIRE_BEARER_TOKEN')
threads_access_token = os.getenv('THREADS_ACCESS_TOKEN')
my_api_key = os.getenv('MY_API_KEY')
main_file_path = os.getenv('FILE_PATH')

def send_tweet(tweet_text_input):
    """sends the tweet data if the right run is found!"""
    try:
        api = tweepy.Client(twitter_bearer_key, twitter_api_key, twitter_api_key_secret,
                            twitter_access_token, twitter_access_token_secret)
        status1 = api.create_tweet(text=tweet_text_input)
        first_tweet = status1.data["id"]
        print(
            f"sent new tweets https://twitter.com/isCTAonFire/status/{first_tweet}")
    except:  # pylint: disable=bare-except
        print("Twitter error :(")

def get_alerts():
    """reach CTA API and get current alerts"""
    url = "http://lapi.transitchicago.com/api/1.0/alerts.aspx?routeid=P,Y,Blue,Pink,G,Org,Brn,Red&outputType=JSON&accessibility=true"
    response = requests.request("GET", url, timeout=60)
    return response.json()

def process_alerts(alerts_response):
    """work through each alert and determine if it is existing or old"""
    json_file_path = main_file_path + "train_arrivals/special/cta_onfire_alerts.json"
    with open(json_file_path, "r", encoding="utf-8") as file:
        cta_alerts = json.load(file)
        cta_alerts_original = cta_alerts
    
    for alert in alerts_response["CTAAlerts"]["Alert"]:
        process = False
        count = 1
        affected_services = ""
        if "fire at track level" in alert["ShortDescription"] or "fire on the tracks" in alert["ShortDescription"] or "track fire" in alert["ShortDescription"]:
            process = True
            alert_text = "🚨🔥 The CTA is on fire! 🔥🚨"
        elif "track conditions" in alert["ShortDescription"]:
            process = True
            alert_text = "🚨🔥 The CTA might be on fire! 👀"
        if process is True:
            if alert["AlertId"] in cta_alerts:
                if cta_alerts[alert["AlertId"]][-1] == alert:
                    print(f"Alert {alert['AlertId']} already in file and current.")
                else:
                    print(f"Alert {alert['AlertId']} has been updated.")
                    alert_url = alert["AlertURL"]["#cdata-section"]
                    headline = str(alert["ShortDescription"]).replace("Crews working to restore service.","")
                    for service in alert["ImpactedService"]["Service"]:
                        if service["ServiceTypeDescription"] == "Train Route" and count == 1:
                            affected_services = service["ServiceName"]
                            count += 1
                        elif service["ServiceTypeDescription"] == "Train Route" and count == 2:
                            service_name = str(service['ServiceName']).replace(" Line", "")
                            affected_services = f"{service_name} & {affected_services}"
                            count += 1
                        elif service["ServiceTypeDescription"] == "Train Route" and count > 2:
                            service_name = str(service['ServiceName']).replace(" Line", "")
                            affected_services = f"{service_name}, {affected_services}"
                            count += 1
                    final_tweet_text = f"{alert_text}\n{headline}\nAffected Services: {affected_services}\n{alert_url}"
                    print(final_tweet_text)
                    send_tweet(final_tweet_text)
                    cta_alerts[alert["AlertId"]].append(alert)
            else:
                cta_alerts[alert["AlertId"]] = []
                cta_alerts[alert["AlertId"]].append(alert)
            with open(json_file_path, "w", encoding="utf-8") as file:
                json.dump(cta_alerts, file, indent=4)

alerts_to_process = get_alerts()
process_alerts(alerts_to_process)
