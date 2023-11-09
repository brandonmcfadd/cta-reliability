"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import json  # Used for JSON Handling
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import hashlib

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
        "body": body,
        "assignees": [github_username],
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

def read_last_website_hash():
    json_file_path = main_file_path + "train_arrivals/special/gtfs_checks.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    return str(data["last_hash"])

def update_last_hash_value(website_hash):
    json_file_path = main_file_path + "train_arrivals/special/gtfs_checks.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    data["last_hash"] = website_hash
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

# Function to get the hash of a website's content
def get_website_hash(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        # Calculate the MD5 hash of the content
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return content_hash
    else:
        print(f"Failed to retrieve content from {url}")
        return None
    
def get_website_contents(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        return content
    else:
        print(f"Failed to retrieve content from {url}")
        return None

# Define the URL of the website you want to monitor
url = "https://www.transitchicago.com/downloads/sch_data/"

# Initial hash of the website's content
initial_hash = read_last_website_hash()

current_hash = get_website_hash(url)
if current_hash != initial_hash:
    print("Website has changed!")
    create_github_issue("The CTA Has Uploaded New GTFS Information!",get_website_contents(url))
    update_last_hash_value(current_hash)
else:
    print("Website has not changed.")
