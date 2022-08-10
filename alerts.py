"""ctapi by Brandon McFadden - Github: https://github.com/brandonmcfadd/ctapi"""
from datetime import datetime
import os
import time  # Used to Get Current Time
import json
import requests  # Used for API Calls
from dotenv import load_dotenv  # Used to Load Env Var

# Load .env variables
load_dotenv()

main_file_path = os.getenv('FILE_PATH')
print(main_file_path)

def api_call_to_alerts_api():
    """Gotta talk to the CTA and get Train Times"""
    print("Making CTA Train API Call...")
    api_response = requests.get(alerts_api_url).json()
    alerts_api(api_response)
    return api_response


def alerts_api(alerts):
    """Function is called if a new train stop is identified per API Call"""
    for alert in alerts["CTAAlerts"]["Alert"]:
        add_alert_to_file(alert)


def add_alert_to_file(alert):
    """Turns JSON Response into a useable format"""
    alert_output = {}
    alert_id = alert["AlertId"]
    alert_output["AlertID"] = alert["AlertId"]
    alert_output["Headline"] = alert["Headline"]
    alert_output["ShortDescription"] = alert["ShortDescription"]
    alert_output["AlertType"] = alert["SeverityCSS"]
    alert_output["Impact"] = alert["Impact"]
    alert_output["EventStart"] = alert["EventStart"]
    alert_output["EventEnd"] = alert["EventEnd"]
    alert_output["ImpactedService"] = alert["ImpactedService"]["Service"]
    alert_output["GUID"] = alert["GUID"]
    alerts_json[alert_id] = alert_output


def check_alerts_file_exists(file_action):
    """Used to check if file exists"""
    current_month = datetime.strftime(datetime.now(), "%b%Y")
    file_path = main_file_path + "/cta-reliability/train_arrivals/alerts-api-" + \
        str(current_month) + ".json"
    alerts_api_file = os.path.exists(file_path)
    if alerts_api_file is False:
        print("File Doesn't Exist...Creating File and Adding Headers...")
        dictionary = json.loads('{}')
        json_object = json.dumps(dictionary)
        with open(file_path, "w") as outfile:
            outfile.write(json_object)
    else:
        if file_action == "Read":
            with open(file_path, "r") as infile:
                dictionary = json.load(infile)
        elif file_action == "Write":
            with open(file_path, "w") as outfile:
                dictionary = None
                outfile.write(json.dumps(alerts_json))

    return dictionary


print("Welcome to TrainTracker, Python/RasPi Edition!")
while True:  # Where the magic happens
    # Settings
    settings_file = open(file=main_file_path + '/cta-reliability/settings.json',
                mode='r',
                encoding='utf-8')
    settings = json.load(settings_file)

    # API URL's
    alerts_api_url = settings["alerts-api"]["api-url"]

    # Variables for Settings information - Only make settings changes in the settings.json file
    enable_alerts_tracker = settings["alerts-api"]["api-enabled"]

    alerts_json = check_alerts_file_exists("Read")

    current_time_console = "The Current Time is: " + \
        datetime.strftime(datetime.now(), "%H:%M")
    print("\n" + current_time_console)

    if enable_alerts_tracker == "True":
        # try:
        response = api_call_to_alerts_api()
        check_alerts_file_exists("Write")
        # except:  # pylint: disable=bare-except
            # print("Error in API Call to Alerts Tracker")

    # Wait and do it again
    SLEEP_AMOUNT = 60
    print("Sleeping " + str(SLEEP_AMOUNT) + " Seconds")
    time.sleep(SLEEP_AMOUNT)
