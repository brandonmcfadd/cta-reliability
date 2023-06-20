from datetime import datetime, timedelta
from dateutil import tz
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
    elif date_type == "long":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%k:%M:%SZ")
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


def get_last_refresh_time(dataset):
    url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset}/refreshes?$top=1"

    payload = json.dumps({
        "impersonatedUserName": "brandonmcfadden@brandonmcfadden.onmicrosoft.com"
    })
    headers = {
        'Authorization': 'Bearer {}'.format(bearer_token),
    }
    
    response = requests.request("GET", url, headers=headers, data=payload)
    response_json = json.loads(response.text)
    try:
        end_time = response_json['value'][0].get('endTime')
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Chicago')
        utc = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc = utc.replace(tzinfo=from_zone)
        cst = utc.astimezone(to_zone)
        cst_string = datetime.strftime(cst, "%Y-%m-%dT%H:%M:%S%z")
        return(cst_string)
    except:
        print("error in:", response_json)


def parse_response_cta(data,last_refresh):
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        json_file = main_file_path_json + "cta/" + shortened_date + ".json"
        file_data = {
            "Data Provided By": "Brandon McFadden - http://rta-api.brandonmcfadden.com",
            "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
            "V2 API Information At": "http://rta-api.brandonmcfadden.com",
            "Entity": "cta",
            "Date": shortened_date,
            "LastUpdated": last_refresh,
            "IntegrityChecksPerformed": item["date_range[Integrity - Actual]"],
            "IntegrityPercentage": item["date_range[Integrity - Percentage]"],
            "system": {
                "ActualRuns": item["date_range[System - Actual]"],
                "ScheduledRuns": item["date_range[System - Scheduled]"],
                "PercentRun": item["date_range[System - Percentage]"]
            },
            "routes": {
                "Blue": {
                    "ActualRuns": item["date_range[Blue Line - Actual]"],
                    "ActualRunsOHareBranch": item["date_range[Branch - Blue Line - O'Hare Branch]"],
                    "ActualRunsFPBranch": item["date_range[Branch - Blue Line - Forest Park Branch]"],
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
                }
            }
        }

        with open(json_file, 'w') as f:
            json.dump(file_data, f, indent=2)


def parse_response_metra(data):
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        json_file = main_file_path_json + "metra/" + shortened_date + ".json"
        file_data = {
            "Data Provided By": "Brandon McFadden - http://rta-api.brandonmcfadden.com",
            "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
            "V2 API Information At": "http://rta-api.brandonmcfadden.com",
            "Entity": "metra",
            "Date": shortened_date,
            "IntegrityChecksPerformed": item["date_range[Integrity - Actual]"],
            "IntegrityPercentage": item["date_range[Integrity - Percentage]"],
            "system": {
                "ActualRuns": item["date_range[System - Actual]"],
                "ScheduledRuns": item["date_range[System - Scheduled]"],
                "PercentRun": item["date_range[System - Percentage]"]
            },
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
                }
            }
        }

        with open(json_file, 'w') as f:
            json.dump(file_data, f, indent=2)


bearer_token = get_token()

remaining = 7

last_refresh_time = get_last_refresh_time(cta_dataset_id)

while remaining >= 0:
    try: 
        parse_response_cta(get_report_data(cta_dataset_id, remaining),last_refresh_time)
    except: # pylint: disable=bare-except
        print("Failed to grab CTA #", remaining)
    print("total cta remaining:", remaining)
    try:
        parse_response_metra(get_report_data(metra_dataset_id, remaining))
    except: # pylint: disable=bare-except
        print("Failed to grab Metra #", remaining)
    print("total metra remaining:", remaining)
    remaining -= 1
    sleep(1)
