"""export data for previous days arrivals by Brandon McFadden"""
import os
import json
from csv import DictWriter
from datetime import datetime, timedelta
from time import sleep
import pandas as pd
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls


# Load .env variables
load_dotenv()

microsoft_username = os.getenv('MICROSOFT_USERNAME')
microsoft_password = os.getenv('MICROSOFT_PASSWORD')
microsoft_client_id = os.getenv('MICROSOFT_CLIENT_ID')
microsoft_client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
main_file_path_csv = os.getenv('FILE_PATH_CSV')
cta_dataset_id = os.getenv('CTA_DATASET_ID')
metra_dataset_id = os.getenv('METRA_DATASET_ID')

train_arrivals_csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route',
                              'Run_Number', 'Prediction_Time', 'Arrival_Time', 'Headway', 'Time_Of_Week', 'Time_Of_Day', 'Consistent_Interval']


def get_date(date_type, delay):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "file":
        date = datetime.strftime(
            datetime.now()-timedelta(days=delay), "%Y-%m-%d")
    elif date_type == "year":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%Y")
    elif date_type == "month":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%m")
    elif date_type == "day":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%d")
    return date


def get_token():
    """used to get a MS token for PBI API"""
    url = "https://login.microsoftonline.com/common/oauth2/token"

    payload = f"grant_type=password\n&username={microsoft_username}\n&password={microsoft_password}\n&client_id={microsoft_client_id}\n&client_secret={microsoft_client_secret}\n&resource=https://analysis.windows.net/powerbi/api"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=Ar43AgyVlG9Iq2cDNhyCm7TZQxmvAQAAAC18YtsOAAAAM7ttQwEAAADze2LbDgAAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload).json()

    return response.get('access_token')


def get_report_data(dataset, delay):
    """makes call to PBI API to actually get the data we need"""
    url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset}/executeQueries"
    year = get_date("year", delay)
    month = get_date("month", delay)
    day = get_date("day", delay)
    payload = json.dumps({
        "queries": [
            {
                "query": f"EVALUATE FILTER(train_arrivals,train_arrivals[Arrival_Time.Date]=DATE({year},{month},{day}))"
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


def make_clean_train_file(delay):
    """Used to check if file exists"""
    shortened_date = get_date("file", delay)
    csv_file_path = main_file_path_csv + "cta/" + shortened_date + ".csv"
    print(f"Creating Empty File and Adding Headers: {csv_file_path}")
    with open(csv_file_path, 'w+', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=train_arrivals_csv_headers)
        writer_object.writeheader()


def parse_response_cta(data, delay):
    """takes api response and turns it into usable data without all the extra powerbi stuff"""
    make_clean_train_file(delay)
    for item in data:
        shortened_date = get_date("file", delay)
        csv_file_path = main_file_path_csv + "cta/" + shortened_date + ".csv"
        with open(csv_file_path, 'a', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=train_arrivals_csv_headers)
            writer_object.writerow({'Station_ID': item["train_arrivals[Station_ID]"], 'Stop_ID': item["train_arrivals[Stop_ID]"],
                                    'Station_Name': item["train_arrivals[Station_Name]"], 'Destination': item["train_arrivals[Destination]"], 'Route': item["train_arrivals[Route]"],
                                    'Run_Number': item["train_arrivals[Run_Number]"], 'Prediction_Time': item["train_arrivals[Prediction_Time.Date]"][0:10] + item["train_arrivals[Prediction_Time.Time]"][10:],
                                    'Arrival_Time': item["train_arrivals[Arrival_Time_Combined]"], 'Headway': item["train_arrivals[Headway]"], 'Time_Of_Week': item["train_arrivals[Time of Week]"], 'Time_Of_Day': item["train_arrivals[Time Of Day]"], 'Consistent_Interval': item["train_arrivals[Headway Consistency]"]})
    data_frame = pd.read_csv(csv_file_path)
    sorted_data_frame = data_frame.sort_values(
        by=["Route", "Stop_ID", "Arrival_Time"], ascending=True)
    sorted_data_frame.to_csv(csv_file_path, index=False)


bearer_token = get_token()

remaining = 7

while remaining > 0:
    try:
        parse_response_cta(get_report_data(cta_dataset_id, remaining),remaining)
    except: # pylint: disable=bare-except
        print("Failed to grab #", remaining)
    remaining -= 1
    print("total cta remaining:", remaining)
    sleep(1)
