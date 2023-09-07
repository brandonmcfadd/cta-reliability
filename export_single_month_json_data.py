from datetime import datetime, timedelta
from dateutil import tz
import os
from time import sleep  # Used to retrieve secrets in .env file
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import json
from dateutil.relativedelta import relativedelta

# Load .env variables
load_dotenv()

microsoft_username = os.getenv('MICROSOFT_USERNAME')
microsoft_password = os.getenv('MICROSOFT_PASSWORD')
microsoft_client_id = os.getenv('MICROSOFT_CLIENT_ID')
microsoft_client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
main_file_path_json = os.getenv('FILE_PATH_JSON')
cta_dataset_id = os.getenv('CTA_DATASET_ID')
metra_dataset_id = os.getenv('METRA_DATASET_ID')


def get_date(date_type, delay):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "file":
        date = datetime.strftime(datetime.now()-relativedelta(months=delay), "%Y-%m")
    elif date_type == "year":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%Y")
    elif date_type == "month":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%m")
    elif date_type == "day":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%d")
    elif date_type == "longmonth":
        date = datetime.strftime(datetime.now()-relativedelta(months=delay), "%B %Y")
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


def get_report_data(dataset, delay):
    """makes call to PBI API to actually get the data we need"""
    url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset}/executeQueries"
    last_month = get_date("longmonth", delay)
    payload = json.dumps({
        "queries": [
            {
                "query": f"EVALUATE FILTER(train_arrivals,train_arrivals[Month and Year]=\"{last_month}\")"
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        },
        "impersonatedUserName": "brandonmcfadden@brandonmcfadden.onmicrosoft.com"
    })
    headers = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_json = json.loads(response.text)
    try:
        return response_json['results'][0].get('tables')[0].get('rows')
    except:  # pylint: disable=bare-except
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
    count = 0
    integrity_checks_performed = 0
    actual_runs = 0
    scheduled_runs = 0
    actual_runs_blue_line = 0
    actual_runs_blue_line_ohare = 0
    actual_runs_blue_line_forest_park = 0
    scheduled_runs_blue_line = 0
    scheduled_runs_blue_line_ohare = 0
    scheduled_runs_blue_line_forest_park = 0
    consistent_headways_blue_line = 0
    actual_runs_brown_line = 0
    scheduled_runs_brown_line = 0
    consistent_headways_brown_line = 0
    actual_runs_green_line = 0 
    scheduled_runs_green_line = 0
    consistent_headways_green_line = 0
    actual_runs_orange_line = 0 
    scheduled_runs_orange_line = 0
    consistent_headways_orange_line = 0
    actual_runs_pink_line = 0 
    scheduled_runs_pink_line = 0
    consistent_headways_pink_line = 0
    actual_runs_purple_line = 0 
    scheduled_runs_purple_line = 0
    consistent_headways_purple_line = 0
    actual_runs_red_line = 0 
    scheduled_runs_red_line = 0
    consistent_headways_red_line = 0
    actual_runs_yellow_line = 0
    scheduled_runs_yellow_line = 0
    consistent_headways_yellow_line = 0 
    for item in data:
        print(item)
        count += 1
        integrity_checks_performed += item["date_range[Integrity - Actual]"]
        actual_runs += item["date_range[System - Actual]"]
        scheduled_runs += item["date_range[System - Scheduled]"]
        actual_runs_blue_line += item["date_range[Blue Line - Actual]"]
        actual_runs_blue_line_ohare += item["date_range[Branch - Blue Line - O'Hare Branch - Actual]"]
        actual_runs_blue_line_forest_park += item["date_range[Branch - Blue Line - Forest Park Branch - Actual]"]
        scheduled_runs_blue_line += item["date_range[Blue Line - Scheduled]"]
        scheduled_runs_blue_line_ohare += item["date_range[Blue Line - Scheduled]"]
        scheduled_runs_blue_line_forest_park += item["date_range[Branch - Blue Line - Forest Park - Scheduled]"]
        consistent_headways_blue_line += item["date_range[Blue Line - Consistent Headways]"]
        actual_runs_brown_line += item["date_range[Brown Line - Actual]"]
        scheduled_runs_brown_line += item["date_range[Brown Line - Scheduled]"]
        consistent_headways_brown_line += item["date_range[Brown Line - Consistent Headways]"]
        actual_runs_green_line += item["date_range[Green Line - Actual]"]
        scheduled_runs_green_line += item["date_range[Green Line - Scheduled]"]
        consistent_headways_green_line += item["date_range[Green Line - Consistent Headways]"]
        actual_runs_orange_line += item["date_range[Orange Line - Actual]"]
        scheduled_runs_orange_line += item["date_range[Orange Line - Scheduled]"]
        consistent_headways_orange_line += item["date_range[Orange Line - Consistent Headways]"]
        actual_runs_pink_line += item["date_range[Pink Line - Actual]"]
        scheduled_runs_pink_line += item["date_range[Pink Line - Scheduled]"]
        consistent_headways_pink_line += item["date_range[Pink Line - Consistent Headways]"]
        actual_runs_purple_line += item["date_range[Purple Line - Actual]"]
        scheduled_runs_purple_line += item["date_range[Purple Line - Scheduled]"]
        consistent_headways_purple_line += item["date_range[Purple Line - Consistent Headways]"]
        actual_runs_red_line += item["date_range[Red Line - Actual]"]
        scheduled_runs_red_line += item["date_range[Red Line - Scheduled]"]
        consistent_headways_red_line += item["date_range[Red Line - Consistent Headways]"]
        actual_runs_yellow_line += item["date_range[Yellow Line - Actual]"]
        scheduled_runs_yellow_line += item["date_range[Yellow Line - Scheduled]"]
        consistent_headways_yellow_line += item["date_range[Yellow Line - Consistent Headways]"]


    shortened_date = get_date("longmonth", 1)
    json_file = main_file_path_json + "cta/" + shortened_date + ".json"
    file_data = {
        "Data Provided By": "Brandon McFadden - http://rta-api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "V2 API Information At": "http://rta-api.brandonmcfadden.com",
        "Entity": "cta",
        "Date": shortened_date,
        "LastUpdated": last_refresh,
        "IntegrityChecksPerformed": integrity_checks_performed,
        "IntegrityPercentage": integrity_checks_performed / (1440 * count),
        "system": {
            "ActualRuns": actual_runs,
            "ScheduledRuns": scheduled_runs,
            "PercentRun": actual_runs / scheduled_runs
        },
        "routes": {
            "Blue": {
                "ActualRuns": actual_runs_blue_line,
                "ActualRunsOHareBranch": actual_runs_blue_line_ohare,
                "ActualRunsFPBranch": actual_runs_blue_line_forest_park,
                "ScheduledRuns": scheduled_runs,
                "ScheduledRunsOHareBranch": scheduled_runs_blue_line_ohare,
                "ScheduledRunsFPBranch": scheduled_runs_blue_line_forest_park,
                "PercentRun": actual_runs_blue_line / scheduled_runs_blue_line,
                "PercentRunOHareBranch": actual_runs_blue_line / scheduled_runs_blue_line,
                "PercentRunFPBranch": actual_runs_blue_line_forest_park / scheduled_runs_blue_line_forest_park,
                "Consistent_Headways": consistent_headways_blue_line
            },
            "Brown": {
                "ActualRuns": actual_runs_brown_line,
                "ScheduledRuns": scheduled_runs_brown_line,
                "PercentRun": actual_runs_brown_line / scheduled_runs_brown_line,
                "Consistent_Headways": consistent_headways_brown_line
            },
            "Green": {
                "ActualRuns": actual_runs_green_line,
                "ScheduledRuns": scheduled_runs_green_line,
                "PercentRun": actual_runs_green_line / scheduled_runs_green_line,
                "Consistent_Headways": consistent_headways_green_line
            },
            "Orange": {
                "ActualRuns": actual_runs_orange_line,
                "ScheduledRuns": scheduled_runs_orange_line,
                "PercentRun": actual_runs_orange_line / scheduled_runs_orange_line,
                "Consistent_Headways": consistent_headways_orange_line
            },
            "Pink": {
                "ActualRuns": actual_runs_pink_line,
                "ScheduledRuns": scheduled_runs_pink_line,
                "PercentRun": actual_runs_pink_line / scheduled_runs_pink_line,
                "Consistent_Headways": consistent_headways_pink_line
            },
            "Purple": {
                "ActualRuns": actual_runs_purple_line,
                "ScheduledRuns": scheduled_runs_purple_line,
                "PercentRun": actual_runs_purple_line / scheduled_runs_purple_line,
                "Consistent_Headways": consistent_headways_purple_line
            },
            "Red": {
                "ActualRuns": actual_runs_red_line,
                "ScheduledRuns": scheduled_runs_red_line,
                "PercentRun": actual_runs_red_line / scheduled_runs_red_line,
                "Consistent_Headways": consistent_headways_red_line
            },
            "Yellow": {
                "ActualRuns": actual_runs_yellow_line,
                "ScheduledRuns": scheduled_runs_yellow_line,
                "PercentRun": actual_runs_yellow_line / scheduled_runs_yellow_line,
                "Consistent_Headways": consistent_headways_yellow_line
            }
        }
    }

    with open(json_file, 'w') as f:
        json.dump(file_data, f, indent=2)


# def parse_response_metra(data):
#     for item in data:
#         shortened_date = item["date_range[Dates]"][:10]
#         json_file = main_file_path_json + "metra/" + shortened_date + ".json"
#         file_data = {
#             "Data Provided By": "Brandon McFadden - http://rta-api.brandonmcfadden.com",
#             "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
#             "V2 API Information At": "http://rta-api.brandonmcfadden.com",
#             "Entity": "metra",
#             "Date": shortened_date,
#             "IntegrityChecksPerformed": item["date_range[Integrity - Actual]"],
#             "IntegrityPercentage": item["date_range[Integrity - Percentage]"],
#             "system": {
#                 "ActualRuns": item["date_range[System - Actual]"],
#                 "ScheduledRuns": item["date_range[System - Scheduled]"],
#                 "PercentRun": item["date_range[System - Percentage]"]
#             },
#             "routes": {
#                 "BNSF": {
#                     "ActualRuns": item["date_range[BNSF Line - Actual]"],
#                     "ScheduledRuns": item["date_range[BNSF Line - Scheduled]"],
#                     "PercentRun": item["date_range[BNSF Line - Percentage]"]
#                 },
#                 "HC": {
#                     "ActualRuns": item["date_range[HC Line - Actual]"],
#                     "ScheduledRuns": item["date_range[HC Line - Scheduled]"],
#                     "PercentRun": item["date_range[HC Line - Percentage]"]
#                 },
#                 "MN-N": {
#                     "ActualRuns": item["date_range[MD-N Line - Actual]"],
#                     "ScheduledRuns": item["date_range[MD-N Line - Scheduled]"],
#                     "PercentRun": item["date_range[MD-N Line - Percentage]"]
#                 },
#                 "MN-W": {
#                     "ActualRuns": item["date_range[MD-W Line - Actual]"],
#                     "ScheduledRuns": item["date_range[MD-W Line - Scheduled]"],
#                     "PercentRun": item["date_range[MD-W Line - Percentage]"]
#                 },
#                 "ME": {
#                     "ActualRuns": item["date_range[ME Line - Actual]"],
#                     "ScheduledRuns": item["date_range[ME Line - Scheduled]"],
#                     "PercentRun": item["date_range[ME Line - Percentage]"]
#                 },
#                 "NCS": {
#                     "ActualRuns": item["date_range[NCS Line - Actual]"],
#                     "ScheduledRuns": item["date_range[NCS Line - Scheduled]"],
#                     "PercentRun": item["date_range[NCS Line - Percentage]"]
#                 },
#                 "RI": {
#                     "ActualRuns": item["date_range[RI Line - Actual]"],
#                     "ScheduledRuns": item["date_range[RI Line - Scheduled]"],
#                     "PercentRun": item["date_range[RI Line - Percentage]"]
#                 },
#                 "UP-N": {
#                     "ActualRuns": item["date_range[UP-N Line - Actual]"],
#                     "ScheduledRuns": item["date_range[UP-N Line - Scheduled]"],
#                     "PercentRun": item["date_range[UP-N Line - Percentage]"]
#                 },
#                 "UP-NW": {
#                     "ActualRuns": item["date_range[UP-NW Line - Actual]"],
#                     "ScheduledRuns": item["date_range[UP-NW Line - Scheduled]"],
#                     "PercentRun": item["date_range[UP-NW Line - Percentage]"]
#                 },
#                 "UP-W": {
#                     "ActualRuns": item["date_range[UP-W Line - Actual]"],
#                     "ScheduledRuns": item["date_range[UP-W Line - Scheduled]"],
#                     "PercentRun": item["date_range[UP-W Line - Percentage]"]
#                 }
#             }
#         }

#         with open(json_file, 'w') as f:
#             json.dump(file_data, f, indent=2)


bearer_token = get_token()

remaining = 1

last_refresh_time = get_last_refresh_time(cta_dataset_id)

while remaining >= 0:
    # try: 
    parse_response_cta(get_report_data(cta_dataset_id, remaining),last_refresh_time)
    # except: # pylint: disable=bare-except
        # print("Failed to grab CTA #", remaining)
    # print("total cta remaining:", remaining)
    # try:
    #     parse_response_metra(get_report_data(metra_dataset_id, remaining))
    # except: # pylint: disable=bare-except
    #     print("Failed to grab Metra #", remaining)
    # print("total metra remaining:", remaining)
    remaining -= 1
    sleep(1)
