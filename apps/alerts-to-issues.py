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
main_file_path = os.getenv('FILE_PATH') + "cta-reliability/"

def create_github_issue(title,body):
    # GitHub API endpoint for creating issues
    url = f"https://api.github.com/repos/{github_username}/{github_repo}/issues"

    # Issue data
    issue_data = {
        "title": title,
        "body": body
    }

    # Headers with the access token
    headers = {
        "Authorization": f"token {github_pat}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Create the issue
    response = requests.post(url, headers=headers, data=json.dumps(issue_data))

    if response.status_code == 201:
        print("Issue created successfully!")
    else:
        print(f"Failed to create the issue. Status code: {response.status_code}")
        print(response.text)

def get_alerts():
    url = "http://lapi.transitchicago.com/api/1.0/alerts.aspx?routeid=P,Y,Blue,Pink,G,Org,Brn,Red&outputType=JSON&accessibility=false"
    response = requests.request("GET", url)
    return response.json()

def process_alerts(alerts_response):
    for alert in alerts_response["CTAAlerts"]["Alert"]:
        alert_id = int(alert["AlertId"])
        if alert["Impact"] == "Planned Work w/Part Closure" and alert_id > read_last_alert_number():
            create_github_issue(alert["Headline"],alert["ShortDescription"])
            update_last_alert_number(alert_id)

def read_last_alert_number():
    json_file_path = main_file_path + "train_arrivals/special/last_alert.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    return int(data["last_alert"])

def update_last_alert_number(alert_id):
    json_file_path = main_file_path + "train_arrivals/special/last_alert.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    data["last_alert"] = int(alert_id)
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

alerts_to_process = get_alerts()
process_alerts(alerts_to_process)    
