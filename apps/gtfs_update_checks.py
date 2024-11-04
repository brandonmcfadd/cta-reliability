"""cta-reliability by Brandon McFadden - Github: https://github.com/brandonmcfadd/cta-reliability"""
import os  # Used to retrieve secrets in .env file
import json  # Used for JSON Handling
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # Used to Load Env Var
import requests  # Used for API Calls
import hashlib

# Load .env variables
load_dotenv()

# ENV Variables
github_pat = os.getenv('GITHUB_PAT')
github_username = os.getenv('GITHUB_USERNAME')
github_repo = os.getenv('GITHUB_REPO')
main_file_path = os.getenv('FILE_PATH')

def create_github_issue(title,body):
    # GitHub API endpoint for creating issues
    url = f"https://api.github.com/repos/{github_username}/{github_repo}/issues"

    # Issue data
    issue_data = {
        "title": title,
        "body": f"{body}\n@brandonmcfadd",
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
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
        print(f"Old Hash: {str(data['last_hash'])}")
    return str(data["last_hash"])

def read_last_upload_time():
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
        print(f"Last Upload: {str(data['last_schedule_upload_date'])}")
    return str(data["last_hash"])

def update_last_hash_value(website_hash):
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    data["last_hash"] = website_hash
    print(f"New Hash: {website_hash}")
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

def update_last_upload_time(upload_time):
    json_file_path = main_file_path + "train_arrivals/special/store.json"
    with open(json_file_path, "r") as file:
        data = json.load(file)
    data["last_schedule_upload_date"] = upload_time
    print(f"New Upload Time: {upload_time}")
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)
    print("JSON file updated successfully.")

# Function to get the hash of a website's content
def get_website_hash(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        if "www.transitchicago.com - /downloads/sch_data/" in content:
            # Calculate the MD5 hash of the content
            content_hash = hashlib.md5(content.encode()).hexdigest()
            return content_hash
    else:
        print(f"Failed to retrieve content from {url}")
        # return None
    
def get_website_contents(url):
    response = requests.get(url)
    if response.status_code == 200:
        content = response.text
        return content
    else:
        print(f"Failed to retrieve content from {url}")
        return None


def extract_google_transit_data(html_content):
    if "www.transitchicago.com - /downloads/sch_data/" in html_content:
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the specific anchor tag
        target_tag = soup.find('a', href="/downloads/sch_data/google_transit.zip")
        # Extract the previous text before the tag
        previous_text = target_tag.previous_sibling.strip()
        # Split the text and extract the date and time
        date_time = ' '.join(previous_text.split()[:3])
        # Print the result
        return(date_time)

# Define the URL of the website you want to monitor
url = "https://www.transitchicago.com/downloads/sch_data/"

# Initial hash of the website's content
initial_hash = read_last_website_hash()
initial_time = read_last_website_hash

current_hash = get_website_hash(url)
current_upload_time = extract_google_transit_data(get_website_contents(url))
if current_hash != None and current_upload_time != None:
    if current_hash != initial_hash and initial_time != current_upload_time:
        print("Website has changed!")
        # create_github_issue("The CTA Has Uploaded New GTFS Information!",get_website_contents(url))
        # Call the function and print the result
        update_last_hash_value(current_hash)
        update_last_upload_time(current_upload_time)
    else:
        print("Website has not changed.")
    