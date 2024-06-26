"""export data for previous days arrivals by Brandon McFadden"""
import os
import json
from csv import DictWriter
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
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
main_file_path_csv = main_file_path + "train_arrivals/csv/"
cta_dataset_id = os.getenv('CTA_DATASET_ID')
metra_dataset_id = os.getenv('METRA_DATASET_ID')
train_arrivals_table = os.getenv('CTA_PROCESSED_ARRIVALS')
google_credentials_file = main_file_path + os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

cta_train_arrivals_csv_headers = ['Station_ID', 'Stop_ID', 'Station_Name', 'Destination', 'Route',
                                  'Run_Number', 'Prediction_Time', 'Arrival_Time', 'Headway', 'Time_Of_Week', 'Time_Of_Day', 'Consistent_Interval', 'Scheduled_Headway', 'Scheduled_Headway_Check', 'Flags']
metra_train_arrivals_csv_headers = ['Full_Date_Time', 'Simple_Date_Time', 'Time_Of_Week', 'Time_Of_Day', 'Vehicle_Trip_TripID', 'Run_Number', 'Vehicle_Trip_RouteID',
                                    'Vehicle_Trip_StartTime', 'Vehicle_Trip_StartDate', 'Vehicle_Vehicle_ID', 'Destination', 'Stop_Arrival_Time', 'Scheduled_Arrival_Time', 'Stop_Sequence', 'On_Time']


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
    """gets token for PBI service to make API calls under service principal"""
    scope = 'https://analysis.windows.net/powerbi/api/.default'
    client_secret_credential_class = ClientSecretCredential(
        tenant_id=microsoft_tenant_id, client_id=microsoft_client_id, client_secret=microsoft_client_secret)
    access_token_class = client_secret_credential_class.get_token(scope)
    token_string = access_token_class.token
    return token_string


def get_report_data(dataset, delay):
    """makes api call to PBI service to extract data from dataset"""
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{microsoft_workspace_id}/datasets/{dataset}/executeQueries"
    payload = json.dumps({
        "queries": [
            {
                "query": f"EVALUATE FILTER(train_arrivals,train_arrivals[Days Old]={delay})"
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
        return response_json['results'][0].get('tables')[0].get('rows')
    except:  # pylint: disable=bare-except
        print("error in:", response_json)


def add_rows_to_bigquery(row, table_id, delay):
    """Takes a Row as Input and inserts it to the specified Google Big Query Table"""
    credentials = service_account.Credentials.from_service_account_file(
        google_credentials_file, scopes=[
            "https://www.googleapis.com/auth/cloud-platform"],
    )

    client = bigquery.Client(credentials=credentials,
                             project=credentials.project_id,)

    errors = client.insert_rows_json(table_id, row)  # Make an API request.
    if errors:
        print("Encountered errors while inserting rows: %s", errors)
    else:
        print(
            f"Successfully Inserted Row Into Table {table_id} for date {get_date('file', delay)} ({delay} days old)")


def make_clean_train_file(delay, headers, agency):
    """Used to check if file exists"""
    shortened_date = get_date("file", delay)
    csv_file_path = main_file_path_csv + f"{agency}/" + shortened_date + ".csv"
    print(f"Creating Empty File and Adding Headers: {csv_file_path}")
    with open(csv_file_path, 'w+', newline='', encoding='utf8') as csvfile:
        writer_object = DictWriter(
            csvfile, fieldnames=headers)
        writer_object.writeheader()


def parse_response_cta(data, delay):
    """takes api response and turns it into usable data without all the extra powerbi stuff"""
    cta_rows_to_upload = []
    for item in data:
        cta_rows_to_upload.append({'Station_ID': item["train_arrivals[Station_ID]"], 'Stop_ID': item["train_arrivals[Stop_ID]"],
                                   'Station_Name': item["train_arrivals[Station_Name]"], 'Destination': item["train_arrivals[Destination]"], 'Route': item["train_arrivals[Route]"],
                                   'Run_Number': item["train_arrivals[Run_Number]"], 'Prediction_Time': item["train_arrivals[Prediction_Time]"],
                                   'Arrival_Time': item["train_arrivals[Arrival_Time_Combined]"], 'Headway': item["train_arrivals[Headway]"],
                                   'Time_Of_Week': item["train_arrivals[Time of Week]"], 'Time_Of_Day': item["train_arrivals[Time Of Day]"],
                                   'Consistent_Interval': item["train_arrivals[Headway Consistency]"],
                                   'Scheduled_Headway': item["train_arrivals[Scheduled Headway]"],
                                   'Scheduled_Headway_Check': item["train_arrivals[Scheduled Headway Check]"], 'Flags': item["train_arrivals[Flags]"]})
    add_rows_to_bigquery(cta_rows_to_upload, train_arrivals_table, delay)


def parse_response_metra(data, delay):
    """takes api response and turns it into usable data without all the extra powerbi stuff"""
    make_clean_train_file(delay, metra_train_arrivals_csv_headers, "metra")
    for item in data:
        shortened_date = get_date("file", delay)
        csv_file_path = main_file_path_csv + "metra/" + shortened_date + ".csv"
        with open(csv_file_path, 'a', newline='', encoding='utf8') as csvfile:
            writer_object = DictWriter(
                csvfile, fieldnames=metra_train_arrivals_csv_headers)
            writer_object.writerow({'Full_Date_Time': item["train_arrivals[Full_Date_Time]"], 'Simple_Date_Time': item["train_arrivals[Simple_Date_Time]"], 'Time_Of_Week': item["train_arrivals[Time of Week]"], 'Time_Of_Day': item["train_arrivals[Time Of Day]"], 'Vehicle_Trip_TripID': item["train_arrivals[Vehicle_Trip_TripID]"], 'Run_Number': item["train_arrivals[Run Number]"], 'Vehicle_Trip_RouteID': item["train_arrivals[Vehicle_Trip_RouteID]"],
                                    'Vehicle_Trip_StartTime': item["train_arrivals[Vehicle_Trip_StartTime]"], 'Vehicle_Trip_StartDate': item["train_arrivals[Vehicle_Trip_StartDate]"], 'Vehicle_Vehicle_ID': item["train_arrivals[Vehicle_Vehicle_ID]"], 'Destination': item["train_arrivals[Natural Station Name]"], 'Stop_Arrival_Time': item["train_arrivals[Stop_Arrival_Time_Combined]"], 'Scheduled_Arrival_Time': item["train_arrivals[Scheduled Arrival Time]"], 'On_Time': item["train_arrivals[On-Time Check]"]})
    data_frame = pd.read_csv(csv_file_path)
    sorted_data_frame = data_frame.sort_values(
        by=["Vehicle_Trip_RouteID", "Full_Date_Time"], ascending=True)
    sorted_data_frame.to_csv(csv_file_path, index=False)


bearer_token = get_token()

DAYS_OLD = 1

try:
    parse_response_cta(get_report_data(
        cta_dataset_id, DAYS_OLD), DAYS_OLD)
except:  # pylint: disable=bare-except
    print(
        f"Failed to grab {get_date('file', DAYS_OLD)}, ({DAYS_OLD} days old)")
try:
    parse_response_metra(get_report_data(
        metra_dataset_id, DAYS_OLD), DAYS_OLD)
except:  # pylint: disable=bare-except
    print("Failed to grab Metra #", DAYS_OLD)
