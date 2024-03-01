"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import json  # Used for JSON Handling
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls

# Load .env variables
load_dotenv()

# ENV Variables
github_pat = os.getenv('GITHUB_PAT')
github_username = os.getenv('GITHUB_USERNAME')
github_repo = os.getenv('GITHUB_REPO')
main_file_path = os.getenv('FILE_PATH')

def get_alerts():
    """reach CTA API and get current alerts"""
    url = "http://lapi.transitchicago.com/api/1.0/alerts.aspx?routeid=P,Y,Blue,Pink,G,Org,Brn,Red&outputType=JSON&accessibility=true"
    response = requests.request("GET", url, timeout=60)
    return response.json()

def process_alerts(alerts_response):
    """work through each alert and determine if it is existing or old"""
    json_file_path = main_file_path + "train_arrivals/special/cta_alerts.json"
    with open(json_file_path, "r", encoding="utf-8") as file:
        cta_alerts = json.load(file)
        cta_alerts_original = cta_alerts

    for alert in alerts_response["CTAAlerts"]["Alert"]:
        alert_id = int(alert["AlertId"])
        if alert["AlertId"] in cta_alerts:
            if cta_alerts[alert["AlertId"]][-1] == alert:
                print(f"Alert {alert['AlertId']} already in file and current.")
            else:
                print(f"Alert {alert['AlertId']} has been updated.")
                cta_alerts[alert["AlertId"]].append(alert)
        else:
            cta_alerts[alert["AlertId"]] = []
            cta_alerts[alert["AlertId"]].append(alert)
    if cta_alerts != cta_alerts_original:
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(cta_alerts, file, indent=4)

alerts_to_process = get_alerts()
process_alerts(alerts_to_process)
