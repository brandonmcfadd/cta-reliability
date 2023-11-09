"""GTFS Trip Data Parser by Brandon McFadden"""
import fileinput
import re
import os
from datetime import datetime
import shutil
import requests, zipfile, io

directory_path = os.getcwd() + "/gtfs"
stop_times_path = directory_path + "/powerbi/export/stop_times.txt"
trips_path = directory_path + "/powerbi/export/trips.txt"
calendar_path = directory_path + "/powerbi/export/calendar.txt"

# Providing the folder path
origin = directory_path + "/powerbi/import/"
target = directory_path + "/powerbi/export/"

# Download new package
print("Downloading Updated GTFS Package")
r = requests.get("https://www.transitchicago.com/downloads/sch_data/google_transit.zip")
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall(origin)

# Fetching the list of all the files
files = os.listdir(origin)

# Fetching all the files to directory
file_names = ["calendar.txt", "stop_times.txt", "trips.txt"]
for file_name in files:
   if file_name in file_names:
       shutil.copy(origin+file_name, target+file_name)
print("Files are copied successfully")

schedule_date = input("Enter the Schedule Effective Date (mm-dd-yyyy): ")
calendar_line_input = input("Enter the Desired Schedule Period (20231106,20240131): ") + "|service_id"
calendar_regex = re.compile(calendar_line_input, re.MULTILINE)
stop_times_regex = re.compile(
    r',30072,|,30073,|,30070,|,30071,|,30381,|,30382,|,30215,|,30216,|,30040,|,30041,|,30164,|,30241,|,30064,|,30065,|,30297,|,30298,|trip_id', re.MULTILINE)
trips_regex = re.compile(
    r'Red|Blue|Brn|G|Org|P|Pink|Y|service_id', re.MULTILINE)

calendar_ids = []
weekday_trip_ids = []
saturday_trip_ids = []
sunday_trip_ids = []


def regex_runner(pattern, filename, runtype="None"):
    """Takes a regex pattern and only keeps matching lines"""
    matched = re.compile(pattern).search
    with fileinput.FileInput(filename, inplace=True) as file:
        for line in file:
            if matched(line):  # save lines that match
                split_line = line.split(',')
                if runtype=="stop_times":
                    if split_line[3] == "30070": # Brown - Kimball
                        modified_line = f"{split_line[0]}1,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30071": # Brown - Loop
                        modified_line = f"{split_line[0]}2,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30215": # Orange - Loop
                        modified_line = f"{split_line[0]}1,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30216": # Orange - Midway
                        modified_line = f"{split_line[0]}2,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30040": # Pink - Loop
                        modified_line = f"{split_line[0]}1,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30041": # Pink - 54th
                        modified_line = f"{split_line[0]}2,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30164": # Purple - Southbound
                        modified_line = f"{split_line[0]}1,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30241": # Purple - Northbound
                        modified_line = f"{split_line[0]}2,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30297": # Yellow - Outbound
                        modified_line = f"{split_line[0]}1,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    elif split_line[3] == "30298": # Yellow - Inbound
                        modified_line = f"{split_line[0]}2,{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                    else:
                        modified_line = f"{split_line[0]},{split_line[1]},{split_line[2]},{split_line[3]},{split_line[4]},{split_line[5]},{split_line[6]},{split_line[7]}"
                        print(f"{modified_line}", end='')
                elif runtype=="trips":
                    if split_line[0] == "Brn": # Brown
                        modified_line_1 = f"{split_line[0]},{split_line[1]},{split_line[2]}1,0,{split_line[4]},{split_line[5]},0,{split_line[7]},{split_line[8]}"
                        modified_line_2 = f"{split_line[0]},{split_line[1]},{split_line[2]}2,1,{split_line[4]},{split_line[5]},1,{split_line[7]},{split_line[8]}"
                        print(f"{modified_line_1}", end='')
                        print(f"{modified_line_2}", end='')
                    elif split_line[0] == "Org": # Orange
                        modified_line_1 = f"{split_line[0]},{split_line[1]},{split_line[2]}1,0,{split_line[4]},{split_line[5]},0,{split_line[7]},{split_line[8]}"
                        modified_line_2 = f"{split_line[0]},{split_line[1]},{split_line[2]}2,1,{split_line[4]},{split_line[5]},1,{split_line[7]},{split_line[8]}"
                        print(f"{modified_line_1}", end='')
                        print(f"{modified_line_2}", end='')
                    elif split_line[0] == "Pink": # Pink
                        modified_line_1 = f"{split_line[0]},{split_line[1]},{split_line[2]}1,0,{split_line[4]},{split_line[5]},0,{split_line[7]},{split_line[8]}"
                        modified_line_2 = f"{split_line[0]},{split_line[1]},{split_line[2]}2,1,{split_line[4]},{split_line[5]},1,{split_line[7]},{split_line[8]}"
                        print(f"{modified_line_1}", end='')
                        print(f"{modified_line_2}", end='')
                    elif split_line[0] == "P": # Purple
                        modified_line_1 = f"{split_line[0]},{split_line[1]},{split_line[2]}1,0,{split_line[4]},{split_line[5]},0,{split_line[7]},{split_line[8]}"
                        modified_line_2 = f"{split_line[0]},{split_line[1]},{split_line[2]}2,1,{split_line[4]},{split_line[5]},1,{split_line[7]},{split_line[8]}"
                        print(f"{modified_line_1}", end='')
                        print(f"{modified_line_2}", end='')
                    elif split_line[0] == "Y": # Yellow
                        modified_line_1 = f"{split_line[0]},{split_line[1]},{split_line[2]}1,0,{split_line[4]},{split_line[5]},0,{split_line[7]},{split_line[8]}"
                        modified_line_2 = f"{split_line[0]},{split_line[1]},{split_line[2]}2,1,{split_line[4]},{split_line[5]},1,{split_line[7]},{split_line[8]}"
                        print(f"{modified_line_1}", end='')
                        print(f"{modified_line_2}", end='')
                    else:
                        # this goes to filename due to inplace=1
                        print(line, end='')
                else:
                    # this goes to filename due to inplace=1
                    print(line, end='')


def get_ids(path, column):
    """extracts items from columns that match"""
    # Using readlines()
    file1 = open(path, 'r')
    lines = file1.readlines()
    ids = ''
    count = 0
    # Strips the newline character
    for line in lines:
        split_line = line.split(',')
        if count == 0:
            ids += (split_line[column])
        else:
            ids += ",|," + (split_line[column])
        count += 1
    return ids

def file_rename(path, date):
    os.rename(path,f"{path[:-4]}_{date}.txt")

print("Performing Regex Cleanup on 'calendar.txt'")
regex_runner(calendar_regex, calendar_path)
service_ids = get_ids(calendar_path, 0)

print("Performing Regex Cleanup on 'stop_times.txt'")
regex_runner(stop_times_regex, stop_times_path, runtype="stop_times")

print("Performing Regex Cleanup on 'trips.txt'")
regex_runner(service_ids, trips_path, runtype="trips")
file_rename(calendar_path, schedule_date)
file_rename(stop_times_path, schedule_date)
file_rename(trips_path, schedule_date)