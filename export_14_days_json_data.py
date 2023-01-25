from datetime import datetime, timedelta
import os
from time import sleep  # Used to retrieve secrets in .env file
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import json

# Load .env variables
load_dotenv()

microsoft_username = os.getenv('MICROSOFT_USERNAME')
microsoft_password = os.getenv('MICROSOFT_PASSWORD')
microsoft_client_id = os.getenv('MICROSOFT_CLIENT_ID')
microsoft_client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
main_file_path_json = os.getenv('FILE_PATH_JSON')
cta_dataset_id = os.getenv('CTA_DATASET_ID')
metra_dataset_id = os.getenv('METRA_DATASET_ID')


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    return date


def get_token():
    url = "https://login.microsoftonline.com/common/oauth2/token"

    payload = "grant_type=password\n&username={}\n&password={}\n&client_id={}\n&client_secret={}\n&resource=https://analysis.windows.net/powerbi/api".format(
        microsoft_username, microsoft_password, microsoft_client_id, microsoft_client_secret)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=Ar43AgyVlG9Iq2cDNhyCm7TZQxmvAQAAAC18YtsOAAAAM7ttQwEAAADze2LbDgAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload).json()

    return(response.get('access_token'))


def get_report_data(dataset, days_old):
    url = "https://api.powerbi.com/v1.0/myorg/datasets/{}/executeQueries".format(
        dataset)

    payload = json.dumps({
        "queries": [
            {
                "query": "EVALUATE FILTER(date_range,date_range[Days Old]={})".format(days_old)
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        },
        "impersonatedUserName": "brandonmcfadden@brandonmcfadden.onmicrosoft.com"
    })
    headers = {
        'Authorization': 'Bearer {}'.format(bearer_token),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = json.loads(response.text)
    try:
        return(response_json['results'][0].get('tables')[0].get('rows'))
    except:
        print("error in:", response_json)


def parse_response_cta(data):
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        json_file = main_file_path_json + "cta/" + shortened_date + ".json"
        file_data = {
            "Data Provided By": "Brandon McFadden - rtareliability.brandonmcfadden.com",
            "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
            "Entity": "cta",
            "Date": shortened_date,
            "IntegrityChecksPerformed": item["date_range[Integrity - Actual]"],
            "IntegrityPercentage": item["date_range[Integrity - Percentage]"],
            "routes": {
                "Blue": {
                    "ActualRuns": item["date_range[Blue Line - Actual]"],
                    "ScheduledRuns": item["date_range[Blue Line - Scheduled]"],
                    "PercentRun": item["date_range[Blue Line - Percentage]"]
                },
                "Brown": {
                    "ActualRuns": item["date_range[Brown Line - Actual]"],
                    "ScheduledRuns": item["date_range[Brown Line - Scheduled]"],
                    "PercentRun": item["date_range[Brown Line - Percentage]"]
                },
                "Green": {
                    "ActualRuns": item["date_range[Green Line - Actual]"],
                    "ScheduledRuns": item["date_range[Green Line - Scheduled]"],
                    "PercentRun": item["date_range[Green Line - Percentage]"]
                },
                "Orange": {
                    "ActualRuns": item["date_range[Orange Line - Actual]"],
                    "ScheduledRuns": item["date_range[Orange Line - Scheduled]"],
                    "PercentRun": item["date_range[Orange Line - Percentage]"]
                },
                "Pink": {
                    "ActualRuns": item["date_range[Pink Line - Actual]"],
                    "ScheduledRuns": item["date_range[Pink Line - Scheduled]"],
                    "PercentRun": item["date_range[Pink Line - Percentage]"]
                },
                "Purple": {
                    "ActualRuns": item["date_range[Purple Line - Actual]"],
                    "ScheduledRuns": item["date_range[Purple Line - Scheduled]"],
                    "PercentRun": item["date_range[Purple Line - Percentage]"]
                },
                "Red": {
                    "ActualRuns": item["date_range[Red Line - Actual]"],
                    "ScheduledRuns": item["date_range[Red Line - Scheduled]"],
                    "PercentRun": item["date_range[Red Line - Percentage]"]
                },
                "Yellow": {
                    "ActualRuns": item["date_range[Yellow Line - Actual]"],
                    "ScheduledRuns": item["date_range[Yellow Line - Scheduled]"],
                    "PercentRun": item["date_range[Yellow Line - Percentage]"]
                },
            }
        }

        with open(json_file, 'w') as f:
            json.dump(file_data, f, indent=2)


def parse_response_metra(data):
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        json_file = main_file_path_json + "metra/" + shortened_date + ".json"
        file_data = {
            "Data Provided By": "Brandon McFadden - rtareliability.brandonmcfadden.com",
            "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
            "Entity": "metra",
            "Date": shortened_date,
            "IntegrityChecksPerformed": item["date_range[Integrity - Actual]"],
            "IntegrityPercentage": item["date_range[Integrity - Percentage]"],
            "routes": {
                "BNSF": {
                    "ActualRuns": item["date_range[BNSF Line - Actual]"],
                    "ScheduledRuns": item["date_range[BNSF Line - Scheduled]"],
                    "PercentRun": item["date_range[BNSF Line - Percentage]"]
                },
                "HC": {
                    "ActualRuns": item["date_range[HC Line - Actual]"],
                    "ScheduledRuns": item["date_range[HC Line - Scheduled]"],
                    "PercentRun": item["date_range[HC Line - Percentage]"]
                },
                "MN-N": {
                    "ActualRuns": item["date_range[MD-N Line - Actual]"],
                    "ScheduledRuns": item["date_range[MD-N Line - Scheduled]"],
                    "PercentRun": item["date_range[MD-N Line - Percentage]"]
                },
                "MN-W": {
                    "ActualRuns": item["date_range[MD-W Line - Actual]"],
                    "ScheduledRuns": item["date_range[MD-W Line - Scheduled]"],
                    "PercentRun": item["date_range[MD-W Line - Percentage]"]
                },
                "ME": {
                    "ActualRuns": item["date_range[ME Line - Actual]"],
                    "ScheduledRuns": item["date_range[ME Line - Scheduled]"],
                    "PercentRun": item["date_range[ME Line - Percentage]"]
                },
                "NCS": {
                    "ActualRuns": item["date_range[NCS Line - Actual]"],
                    "ScheduledRuns": item["date_range[NCS Line - Scheduled]"],
                    "PercentRun": item["date_range[NCS Line - Percentage]"]
                },
                "RI": {
                    "ActualRuns": item["date_range[RI Line - Actual]"],
                    "ScheduledRuns": item["date_range[RI Line - Scheduled]"],
                    "PercentRun": item["date_range[RI Line - Percentage]"]
                },
                "UP-N": {
                    "ActualRuns": item["date_range[UP-N Line - Actual]"],
                    "ScheduledRuns": item["date_range[UP-N Line - Scheduled]"],
                    "PercentRun": item["date_range[UP-N Line - Percentage]"]
                },
                "UP-NW": {
                    "ActualRuns": item["date_range[UP-NW Line - Actual]"],
                    "ScheduledRuns": item["date_range[UP-NW Line - Scheduled]"],
                    "PercentRun": item["date_range[UP-NW Line - Percentage]"]
                },
                "UP-W": {
                    "ActualRuns": item["date_range[UP-W Line - Actual]"],
                    "ScheduledRuns": item["date_range[UP-W Line - Scheduled]"],
                    "PercentRun": item["date_range[UP-W Line - Percentage]"]
                },
            }
        }

        with open(json_file, 'w') as f:
            json.dump(file_data, f, indent=2)


bearer_token = get_token()

remaining = 14

while remaining >= 0:
    parse_response_cta(get_report_data(cta_dataset_id, remaining))
    print("sleeping 1 seconds - total cta remaining:", remaining)
    sleep(1)
    parse_response_metra(get_report_data(metra_dataset_id, remaining))
    print("sleeping 1 seconds - total metra remaining:", remaining)
    sleep(1)
    remaining -= 1
