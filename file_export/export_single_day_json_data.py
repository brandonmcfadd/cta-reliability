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
        date = datetime.strftime(datetime.strptime(
            current_date, "%Y-%m-%d"), "%w")
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
    try:
        pre_pandemic_scheduled_change = (
            (system_scheduled+system_scheduled_remaining)-pre_pandemic_scheduled)/pre_pandemic_scheduled
    except:  # pylint: disable=bare-except
        pre_pandemic_scheduled_change = None
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
            "PrePandemicScheduledPercChange": pre_pandemic_scheduled_change
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


def parse_response_metra(data, last_refresh, days_old):
    """takes the data from the API and prepares it to add to JSON output"""
    system_total, system_scheduled, system_scheduled_remaining = 0, 0, 0
    routes_information = {}
    for item in data:
        shortened_date = item["date_range[Dates]"][:10]
        integrity_actual = item["date_range[Integrity - Actual]"]
        integrity_percent = item["date_range[Integrity - Percentage]"]
        system_total += item["date_range[Actual Arrivals]"]
        if item["date_range[Scheduled Arrivals]"] is not None:
            system_scheduled += item["date_range[Scheduled Arrivals]"]
        if item["date_range[Remaining Scheduled]"] is not None:
            system_scheduled_remaining += item["date_range[Remaining Scheduled]"]
        if item["date_range[Arrivals Percentage]"] is None:
            arrival_percentage = 0
        else:
            arrival_percentage = item["date_range[Arrivals Percentage]"]
        single_route_information = [item["date_range[Actual Arrivals]"], item["date_range[Scheduled Arrivals]"], arrival_percentage,
                                    item["date_range[Remaining Scheduled]"], item["date_range[On-Time Trains]"]]
        routes_information[item["date_range[Route]"]
                           ] = single_route_information
    json_file = main_file_path_json + "metra/" + shortened_date + ".json"
    if system_scheduled == 0:
        system_perc_run = 0
    else:
        system_perc_run = system_total/system_scheduled
    file_data = {
        "Data Provided By": "Brandon McFadden - https://brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/metra-reliability",
        "V2 API Information At": "https://brandonmcfadden.com/api",
        "Entity": "metra",
        "Date": shortened_date,
        "LastUpdated": last_refresh,
        "IntegrityChecksPerformed": integrity_actual,
        "IntegrityPercentage": integrity_percent,
        "system": {
            "ActualRuns": system_total,
            "ScheduledRuns": system_scheduled,
            "ScheduledRunsRemaining": system_scheduled_remaining,
            "PercentRun": system_perc_run
        },
        "routes": {
            "BNSF": {
                "ActualRuns": routes_information["BNSF"][0],
                "ScheduledRuns": routes_information["BNSF"][1],
                "PercentRun": routes_information["BNSF"][2],
                "RemainingScheduled": routes_information["BNSF"][3],
                "Trains_On_Time": routes_information["BNSF"][4]
            },
            "HC": {
                "ActualRuns": routes_information["HC"][0],
                "ScheduledRuns": routes_information["HC"][1],
                "PercentRun": routes_information["HC"][2],
                "RemainingScheduled": routes_information["HC"][3],
                "Trains_On_Time": routes_information["HC"][4]
            },
            "MD-N": {
                "ActualRuns": routes_information["MD-N"][0],
                "ScheduledRuns": routes_information["MD-N"][1],
                "PercentRun": routes_information["MD-N"][2],
                "RemainingScheduled": routes_information["MD-N"][3],
                "Trains_On_Time": routes_information["MD-N"][4]
            },
            "MD-W": {
                "ActualRuns": routes_information["MD-W"][0],
                "ScheduledRuns": routes_information["MD-W"][1],
                "PercentRun": routes_information["MD-W"][2],
                "RemainingScheduled": routes_information["MD-W"][3],
                "Trains_On_Time": routes_information["MD-W"][4]
            },
            "ME": {
                "ActualRuns": routes_information["ME"][0],
                "ScheduledRuns": routes_information["ME"][1],
                "PercentRun": routes_information["ME"][2],
                "RemainingScheduled": routes_information["ME"][3],
                "Trains_On_Time": routes_information["ME"][4]
            },
            "NCS": {
                "ActualRuns": routes_information["NCS"][0],
                "ScheduledRuns": routes_information["NCS"][1],
                "PercentRun": routes_information["NCS"][2],
                "RemainingScheduled": routes_information["NCS"][3],
                "Trains_On_Time": routes_information["NCS"][4]
            },
            "RI": {
                "ActualRuns": routes_information["RI"][0],
                "ScheduledRuns": routes_information["RI"][1],
                "PercentRun": routes_information["RI"][2],
                "RemainingScheduled": routes_information["RI"][3],
                "Trains_On_Time": routes_information["RI"][4]
            },
            "SWS": {
                "ActualRuns": routes_information["SWS"][0],
                "ScheduledRuns": routes_information["SWS"][1],
                "PercentRun": routes_information["SWS"][2],
                "RemainingScheduled": routes_information["SWS"][3],
                "Trains_On_Time": routes_information["SWS"][4]
            },
            "UP-N": {
                "ActualRuns": routes_information["UP-N"][0],
                "ScheduledRuns": routes_information["UP-N"][1],
                "PercentRun": routes_information["UP-N"][2],
                "RemainingScheduled": routes_information["UP-N"][3],
                "Trains_On_Time": routes_information["UP-N"][4]
            },
            "UP-NW": {
                "ActualRuns": routes_information["UP-NW"][0],
                "ScheduledRuns": routes_information["UP-NW"][1],
                "PercentRun": routes_information["UP-NW"][2],
                "RemainingScheduled": routes_information["UP-NW"][3],
                "Trains_On_Time": routes_information["UP-NW"][4]
            },
            "UP-W": {
                "ActualRuns": routes_information["UP-W"][0],
                "ScheduledRuns": routes_information["UP-W"][1],
                "PercentRun": routes_information["UP-W"][2],
                "RemainingScheduled": routes_information["UP-W"][3],
                "Trains_On_Time": routes_information["UP-W"][4]
            },
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
            metra_dataset_id, remaining), last_refresh_time, remaining)
    except:  # pylint: disable=bare-except
        print("Failed to grab Metra #", remaining)

    remaining -= 1
    sleep(1)
