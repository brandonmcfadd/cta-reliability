"""interacts with PowerBi API to query for a specific days arrival data"""
import os
import json
from time import sleep  # Used to retrieve secrets in .env file
from datetime import datetime
from dateutil import tz
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
from azure.identity import ClientSecretCredential

# Load .env variables
load_dotenv()

microsoft_client_id = os.getenv('MICROSOFT_CLIENT_ID')
microsoft_tenant_id = os.getenv('MICROSOFT_TENANT_ID')
microsoft_client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
microsoft_workspace_id = os.getenv('MICROSOFT_WORKSPACE_ID')
main_file_path = os.getenv('FILE_PATH')
cta_dataset_id = os.getenv('CTA_DATASET_ID')
metra_dataset_id = os.getenv('METRA_DATASET_ID')

main_file_path_json = main_file_path + "train_arrivals/json/"


def get_date(date_type, current_date=""):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "long":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%k:%M:%SZ")
    elif date_type == "day-of-week":
        date = datetime.strftime(datetime.strptime(current_date, "%Y-%m-%d"), "%w")
    return date


def get_token():
    """gets token for PBI service to make API calls under service principal"""
    scope = 'https://analysis.windows.net/powerbi/api/.default'
    client_secret_credential_class = ClientSecretCredential(
        tenant_id=microsoft_tenant_id, client_id=microsoft_client_id, client_secret=microsoft_client_secret)
    access_token_class = client_secret_credential_class.get_token(scope)
    token_string = access_token_class.token
    return token_string


def get_report_data(dataset, days_old):
    """makes api call to PBI service to extract data from dataset"""
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{microsoft_workspace_id}/datasets/{dataset}/executeQueries"

    payload = json.dumps({
        "queries": [
            {
                "query": f"EVALUATE FILTER(date_range,date_range[Days Old]={days_old})"
            }
        ],
        "serializerSettings": {
            "includeNulls": True
        }
    })
    headers = {
        'Authorization': f"Bearer {bearer_token}",
        'Content-Type': 'application/json'
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, timeout=360)
    response_json = json.loads(response.text)

    try:
        return (response_json['results'][0].get('tables')[0].get('rows'))
    except:  # pylint: disable=bare-except
        print("error in:", response_json)


def get_last_refresh_time(dataset):
    """grabs the last dataset refresh time to add to the files"""
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{microsoft_workspace_id}/datasets/{dataset}/refreshes?$top=1"

    headers = {
        'Authorization': f"Bearer {bearer_token}",
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, timeout=360)
    response_json = json.loads(response.text)
    try:
        end_time = response_json['value'][0].get('endTime')
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Chicago')
        utc = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc = utc.replace(tzinfo=from_zone)
        cst = utc.astimezone(to_zone)
        cst_string = datetime.strftime(cst, "%Y-%m-%dT%H:%M:%S%z")
        return cst_string
    except:  # pylint: disable=bare-except
        print("error in:", response_json)


def parse_response_cta(data, last_refresh, days_old):
    """takes the data from the API and prepares it to add to JSON output"""
    system_total, system_scheduled, system_scheduled_remaining, pre_pandemic_scheduled = 0, 0, 0, 0
    routes_information = {}
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        integrity_actual = item["date_range[Integrity - Actual]"]
        integrity_percent = item["date_range[Integrity - Percentage]"]
        system_total += item["date_range[Actual Arrivals]"]
        pre_pandemic_scheduled += item["date_range[Scheduled Arrivals - Pre-Pandemic]"]
        if item["date_range[Scheduled Arrivals]"] is not None:
            system_scheduled += item["date_range[Scheduled Arrivals]"]
        if item["date_range[Remaining Scheduled]"] is not None:
            system_scheduled_remaining += item["date_range[Remaining Scheduled]"]
        if item["date_range[Arrivals Percentage]"] is None:
            arrival_percentage = 0
        else:
            arrival_percentage = item["date_range[Arrivals Percentage]"]
        single_route_information = [item["date_range[Actual Arrivals]"], item["date_range[Scheduled Arrivals]"], arrival_percentage,
                                    item["date_range[Remaining Scheduled]"], item["date_range[Consistent Headways]"], item["date_range[Longest Wait]"],
                                    item["date_range[Actual Arrivals - Morning Peak]"], item["date_range[Actual Arrivals - Evening Peak]"],
                                    item["date_range[Scheduled Arrivals - Morning Peak]"], item["date_range[Scheduled Arrivals - Evening Peak]"],
                                    item["date_range[On-Time Trains]"], item["date_range[Scheduled Arrivals - Pre-Pandemic]"]]
        routes_information[item["date_range[Route]"]
                           ] = single_route_information
    json_file = main_file_path_json + "cta/" + shortened_date + ".json"
    file_data = {
        "Data Provided By": "Brandon McFadden - http://rta-api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "V2 API Information At": "http://rta-api.brandonmcfadden.com",
        "Entity": "cta",
        "Date": shortened_date,
        "LastUpdated": last_refresh,
        "IntegrityChecksPerformed": integrity_actual,
        "IntegrityPercentage": integrity_percent,
        "system": {
            "ActualRuns": system_total,
            "ScheduledRuns": system_scheduled,
            "ScheduledRunsRemaining": system_scheduled_remaining,
            "PercentRun": system_total/system_scheduled,
            "PrePandemicScheduled": pre_pandemic_scheduled,
            "PrePandemicScheduledPercChange": ((system_scheduled+system_scheduled_remaining)-pre_pandemic_scheduled)/pre_pandemic_scheduled
        },
        "routes": {
            "Blue": {
                "ActualRuns": routes_information["Blue"][0],
                "ActualRunsOHareBranch": routes_information["Blue"][0],
                "ActualRunsFPBranch": 0,
                "ScheduledRuns": routes_information["Blue"][1],
                "ScheduledRunsOHareBranch": routes_information["Blue"][1],
                "ScheduledRunsFPBranch": 0,
                "PercentRun": routes_information["Blue"][2],
                "PercentRunOHareBranch": routes_information["Blue"][2],
                "PercentRunFPBranch": 0,
                "RemainingScheduled": routes_information["Blue"][3],
                "Consistent_Headways": routes_information["Blue"][4],
                "LongestWait": routes_information["Blue"][5],
                "ActualRunsMorningPeak": routes_information["Blue"][6],
                "ActualRunsEveningPeak": routes_information["Blue"][7],
                "ScheduledRunsMorningPeak": routes_information["Blue"][8],
                "ScheduledRunsEveningPeak": routes_information["Blue"][9],
                "Trains_On_Time": routes_information["Blue"][10],
                "PrePandemicScheduled": routes_information["Blue"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Blue"][1]+routes_information["Blue"][3])-routes_information["Blue"][11])/routes_information["Blue"][11]
            },
            "Brown": {
                "ActualRuns": routes_information["Brown"][0],
                "ScheduledRuns": routes_information["Brown"][1],
                "PercentRun": routes_information["Brown"][2],
                "RemainingScheduled": routes_information["Brown"][3],
                "Consistent_Headways": routes_information["Brown"][4],
                "LongestWait": routes_information["Brown"][5],
                "ActualRunsMorningPeak": routes_information["Brown"][6],
                "ActualRunsEveningPeak": routes_information["Brown"][7],
                "ScheduledRunsMorningPeak": routes_information["Brown"][8],
                "ScheduledRunsEveningPeak": routes_information["Brown"][9],
                "Trains_On_Time": routes_information["Brown"][10],
                "PrePandemicScheduled": routes_information["Brown"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Brown"][1]+routes_information["Brown"][3])-routes_information["Brown"][11])/routes_information["Brown"][11]
            },
            "Green": {
                "ActualRuns": routes_information["Green"][0],
                "ScheduledRuns": routes_information["Green"][1],
                "PercentRun": routes_information["Green"][2],
                "RemainingScheduled": routes_information["Green"][3],
                "Consistent_Headways": routes_information["Green"][4],
                "LongestWait": routes_information["Green"][5],
                "ActualRunsMorningPeak": routes_information["Green"][6],
                "ActualRunsEveningPeak": routes_information["Green"][7],
                "ScheduledRunsMorningPeak": routes_information["Green"][8],
                "ScheduledRunsEveningPeak": routes_information["Green"][9],
                "Trains_On_Time": routes_information["Green"][10],
                "PrePandemicScheduled": routes_information["Green"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Green"][1]+routes_information["Green"][3])-routes_information["Green"][11])/routes_information["Green"][11]
            },
            "Orange": {
                "ActualRuns": routes_information["Orange"][0],
                "ScheduledRuns": routes_information["Orange"][1],
                "PercentRun": routes_information["Orange"][2],
                "RemainingScheduled": routes_information["Orange"][3],
                "Consistent_Headways": routes_information["Orange"][4],
                "LongestWait": routes_information["Orange"][5],
                "ActualRunsMorningPeak": routes_information["Orange"][6],
                "ActualRunsEveningPeak": routes_information["Orange"][7],
                "ScheduledRunsMorningPeak": routes_information["Orange"][8],
                "ScheduledRunsEveningPeak": routes_information["Orange"][9],
                "Trains_On_Time": routes_information["Green"][10],
                "PrePandemicScheduled": routes_information["Orange"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Orange"][1]+routes_information["Orange"][3])-routes_information["Orange"][11])/routes_information["Orange"][11]
            },
            "Pink": {
                "ActualRuns": routes_information["Pink"][0],
                "ScheduledRuns": routes_information["Pink"][1],
                "PercentRun": routes_information["Pink"][2],
                "RemainingScheduled": routes_information["Pink"][3],
                "Consistent_Headways": routes_information["Pink"][4],
                "LongestWait": routes_information["Pink"][5],
                "ActualRunsMorningPeak": routes_information["Pink"][6],
                "ActualRunsEveningPeak": routes_information["Pink"][7],
                "ScheduledRunsMorningPeak": routes_information["Pink"][8],
                "ScheduledRunsEveningPeak": routes_information["Pink"][9],
                "Trains_On_Time": routes_information["Pink"][10],
                "PrePandemicScheduled": routes_information["Pink"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Pink"][1]+routes_information["Pink"][3])-routes_information["Pink"][11])/routes_information["Pink"][11]
            },
            "Purple": {
                "ActualRuns": routes_information["Purple"][0],
                "ScheduledRuns": routes_information["Purple"][1],
                "PercentRun": routes_information["Purple"][2],
                "RemainingScheduled": routes_information["Purple"][3],
                "Consistent_Headways": routes_information["Purple"][4],
                "LongestWait": routes_information["Purple"][5],
                "ActualRunsMorningPeak": routes_information["Purple"][6],
                "ActualRunsEveningPeak": routes_information["Purple"][7],
                "ScheduledRunsMorningPeak": routes_information["Purple"][8],
                "ScheduledRunsEveningPeak": routes_information["Purple"][9],
                "Trains_On_Time": routes_information["Purple"][10],
                "PrePandemicScheduled": routes_information["Purple"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Purple"][1]+routes_information["Purple"][3])-routes_information["Purple"][11])/routes_information["Purple"][11]
            },
            "Red": {
                "ActualRuns": routes_information["Red"][0],
                "ScheduledRuns": routes_information["Red"][1],
                "PercentRun": routes_information["Red"][2],
                "RemainingScheduled": routes_information["Red"][3],
                "Consistent_Headways": routes_information["Red"][4],
                "LongestWait": routes_information["Red"][5],
                "ActualRunsMorningPeak": routes_information["Red"][6],
                "ActualRunsEveningPeak": routes_information["Red"][7],
                "ScheduledRunsMorningPeak": routes_information["Red"][8],
                "ScheduledRunsEveningPeak": routes_information["Red"][9],
                "Trains_On_Time": routes_information["Red"][10],
                "PrePandemicScheduled": routes_information["Red"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Red"][1]+routes_information["Red"][3])-routes_information["Red"][11])/routes_information["Red"][11]
            },
            "Yellow": {
                "ActualRuns": routes_information["Yellow"][0],
                "ScheduledRuns": routes_information["Yellow"][1],
                "PercentRun": routes_information["Yellow"][2],
                "RemainingScheduled": routes_information["Yellow"][3],
                "Consistent_Headways": routes_information["Yellow"][4],
                "LongestWait": routes_information["Yellow"][5],
                "ActualRunsMorningPeak": routes_information["Yellow"][6],
                "ActualRunsEveningPeak": routes_information["Yellow"][7],
                "ScheduledRunsMorningPeak": routes_information["Yellow"][8],
                "ScheduledRunsEveningPeak": routes_information["Yellow"][9],
                "Trains_On_Time": routes_information["Yellow"][10],
                "PrePandemicScheduled": routes_information["Yellow"][11],
                "PrePandemicScheduledPercChange": ((routes_information["Yellow"][1]+routes_information["Yellow"][3])-routes_information["Yellow"][11])/routes_information["Yellow"][11]
            }
        }
    }

    with open(json_file, 'w', encoding="utf-8") as f:
        print(f"Remaining: {days_old} | Saving Data In: {json_file}")
        json.dump(file_data, f, indent=2)


def parse_response_metra(data, days_old):
    """takes the data from the API and prepares it to add to JSON output"""
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

        with open(json_file, 'w', encoding="utf-8") as f:
            print(f"Remaining: {days_old} | Saving Data In: {json_file}")
            json.dump(file_data, f, indent=2)


bearer_token = get_token()

remaining = 2
last_refresh_time = None

while last_refresh_time is None:
    last_refresh_time = get_last_refresh_time(cta_dataset_id)
    if last_refresh_time is None:
        print("Last Refresh Time is not available, sleeping 60 seconds")
        sleep(60)

while remaining >= 0:
    try:
        parse_response_cta(get_report_data(
            cta_dataset_id, remaining), last_refresh_time, remaining)
    except:  # pylint: disable=bare-except
        print("Failed to grab CTA #", remaining)

    try:
        parse_response_metra(get_report_data(
            metra_dataset_id, remaining), remaining)
    except:  # pylint: disable=bare-except
        print("Failed to grab Metra #", remaining)

    remaining -= 1
    sleep(1)
