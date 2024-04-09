"""GTFS Trip Data Parser by Brandon McFadden"""
import fileinput
import io
import re
import os
from datetime import datetime
import shutil
import zipfile

import requests

directory_path = os.getcwd() + "/gtfs"
stop_times_path = directory_path + "/google_transit/stop_times.txt"
trips_path = directory_path + "/google_transit/trips.txt"
calendar_path = directory_path + "/google_transit/calendar.txt"
output_path = directory_path + "/google_transit/output.txt"
# Providing the folder path
origin = directory_path + "/google_transit/backup/"
target = directory_path + "/google_transit/"

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

count = 1
date_options = []
with open(calendar_path, "r", encoding="utf-8") as file:
    for line in file:
        split_values = line.split(',')
        date_options.append(f"{split_values[8]},{split_values[9][:-1]}")
unique_date_options = list(set(date_options))
for option in unique_date_options:
    print(f"#{count} - {option}")
    count += 1

calendar_line_input = input("Enter the Desired Schedule Period from selection: ")
schedule_date = input("Enter the Schedule Effective Date (mm-dd-yyyy): ")
calendar_regex = re.compile(unique_date_options[int(calendar_line_input)-1] + "|service_id", re.MULTILINE)
stop_times_regex = re.compile(
    r',30001,|,30002,|,30003,|,30004,|,30005,|,30006,|,30007,|,30008,|,30009,|,30010,|,30011,|,30012,|,30013,|,30014,|,30015,|,30016,|,30017,|,30018,|,30019,|,30020,|,30021,|,30022,|,30023,|,30024,|,30025,|,30026,|,30027,|,30028,|,30029,|,30030,|,30031,|,30032,|,30033,|,30034,|,30035,|,30036,|,30037,|,30040,|,30041,|,30042,|,30043,|,30044,|,30045,|,30046,|,30047,|,30048,|,30049,|,30050,|,30051,|,30052,|,30053,|,30054,|,30055,|,30056,|,30057,|,30058,|,30059,|,30060,|,30061,|,30062,|,30063,|,30064,|,30065,|,30066,|,30067,|,30068,|,30069,|,30070,|,30071,|,30072,|,30073,|,30074,|,30075,|,30076,|,30077,|,30078,|,30079,|,30080,|,30081,|,30082,|,30083,|,30084,|,30085,|,30086,|,30087,|,30088,|,30089,|,30090,|,30091,|,30092,|,30093,|,30094,|,30095,|,30096,|,30099,|,30100,|,30101,|,30102,|,30103,|,30104,|,30105,|,30106,|,30107,|,30108,|,30109,|,30110,|,30111,|,30112,|,30113,|,30114,|,30115,|,30116,|,30117,|,30118,|,30119,|,30120,|,30121,|,30122,|,30125,|,30126,|,30127,|,30128,|,30129,|,30130,|,30131,|,30132,|,30133,|,30134,|,30135,|,30136,|,30137,|,30138,|,30139,|,30140,|,30141,|,30142,|,30143,|,30144,|,30145,|,30146,|,30147,|,30148,|,30149,|,30150,|,30151,|,30152,|,30153,|,30154,|,30155,|,30156,|,30157,|,30158,|,30159,|,30160,|,30161,|,30162,|,30163,|,30164,|,30165,|,30166,|,30167,|,30168,|,30169,|,30170,|,30171,|,30172,|,30173,|,30174,|,30175,|,30176,|,30177,|,30178,|,30179,|,30180,|,30181,|,30182,|,30183,|,30184,|,30185,|,30186,|,30187,|,30188,|,30189,|,30190,|,30191,|,30192,|,30193,|,30194,|,30195,|,30196,|,30197,|,30198,|,30199,|,30200,|,30201,|,30202,|,30203,|,30204,|,30205,|,30206,|,30207,|,30208,|,30209,|,30210,|,30211,|,30212,|,30213,|,30214,|,30215,|,30216,|,30217,|,30218,|,30219,|,30220,|,30221,|,30222,|,30223,|,30224,|,30225,|,30226,|,30227,|,30228,|,30229,|,30230,|,30231,|,30232,|,30233,|,30234,|,30235,|,30236,|,30237,|,30238,|,30239,|,30240,|,30241,|,30242,|,30243,|,30244,|,30245,|,30246,|,30247,|,30248,|,30249,|,30250,|,30251,|,30252,|,30253,|,30254,|,30255,|,30256,|,30257,|,30258,|,30259,|,30260,|,30261,|,30262,|,30263,|,30264,|,30265,|,30266,|,30267,|,30268,|,30269,|,30270,|,30271,|,30272,|,30273,|,30274,|,30275,|,30276,|,30277,|,30278,|,30279,|,30280,|,30281,|,30282,|,30283,|,30284,|,30285,|,30286,|,30287,|,30288,|,30289,|,30290,|,30291,|,30292,|,30293,|,30294,|,30295,|,30296,|,30297,|,30298,|,30374,|,30375,|,30381,|,30382,|,30383,|,30384,|,30385,|,30386,|trip_id', re.MULTILINE)
trips_regex = re.compile(
    r'Red|Blue|Brn|G|Org|P|Pink|Y|service_id', re.MULTILINE)
weekday_calendar_ids = []
saturday_calendar_ids = []
sunday_calendar_ids = []
weekday_trip_ids = []
saturday_trip_ids = []
sunday_trip_ids = []


def regex_runner(pattern, filename, runtype="none"):
    """Takes a regex pattern and only keeps matching lines"""
    matched = re.compile(pattern).search
    with fileinput.FileInput(filename, inplace=1) as file:
        count = 0
        for line in file:
            if matched(line):  # save lines that match
                split_line = line.split(',')
                line_striped = line.rstrip()
                if runtype == "triptime":
                    if count == 0:
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},trip_time", end='\n')
                    elif split_line[1] in weekday_calendar_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},weekday", end='\n')
                    elif split_line[1] in saturday_calendar_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},saturday", end='\n')
                    elif split_line[1] in sunday_calendar_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},sunday", end='\n')
                    count += 1
                elif runtype == "stoptime":
                    if count == 0:
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},trip_time", end='\n')
                    elif split_line[0] in weekday_trip_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},weekday", end='\n')
                    elif split_line[0] in saturday_trip_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},saturday", end='\n')
                    elif split_line[0] in sunday_trip_ids:  # save lines that match
                        # this goes to filename due to inplace=1
                        print(f"{line_striped},sunday", end='\n')
                    count += 1
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
            ids += "|" + (split_line[column])
        count += 1
        if path == calendar_path:
            if split_line[1] == "1":
                weekday_calendar_ids.append(split_line[0])
            elif split_line[6] == "1":
                saturday_calendar_ids.append(split_line[0])
            elif split_line[7] == "1":
                sunday_calendar_ids.append(split_line[0])
        elif path == trips_path:
            if split_line[9] == "weekday\n":
                weekday_trip_ids.append(split_line[2])
            elif split_line[9] == "saturday\n":
                saturday_trip_ids.append(split_line[2])
            elif split_line[9] == "sunday\n":
                sunday_trip_ids.append(split_line[2])
    return ids


def lcount(keyword1, keyword2, fname):
    """line counter based on two keyword matches"""
    with open(fname, 'r') as fin:
        return sum([1 for line in fin if keyword1 in line and keyword2 in line])

def file_rename(path, date):
    os.rename(path,f"{path[:-4]}_{date}.txt")

def run_output():
    """bread and butter"""
    station_ids = ["30072","30073","30179","30180","30070","30071","30381","30382","30215","30216","30040","30041","30164","30241","30064","30065","30297","30298","System"]
    station_names = ["Blue Line (O'Hare - IB)", "Blue Line (O'Hare - OB)", "Blue Line (Congress - IB)", "Blue Line (Congress - OB)", "Brown Line (Kimball)", "Brown Line (Loop)", "Green Line (Harlem)", "Green Line (63rd)",
                     "Orange Line (Loop)", "Orange Line (Midway)", "Pink Line (Loop)", "Pink Line (54th)", "Purple Line (Southbound)", "Purple Line (Northbound)", "Red Line (Northbound)", "Red Line (Southbound)", "Yellow Line (Outbound)", "Yellow Line (Inbound)", "Systemwide"]
    line_names = [["Blue","Brown","Green","Orange","Pink","Purple","Red","Yellow"]]
    table = [["Line Name","Single Weekday","All Weekdays","Saturday","Sunday","Total"]]
    weekday_departures = 0
    saturday_departures = 0
    sunday_departures = 0
    systemwide_departures = 0
    for (station_id, station_name) in zip(station_ids, station_names):
        weekday = lcount(station_id, "weekday", stop_times_path)
        saturday = lcount(station_id, "saturday", stop_times_path)
        sunday = lcount(station_id, "sunday", stop_times_path)
        if station_id != "30179" and station_id != "30180":
            weekday_departures += weekday
            saturday_departures += saturday
            sunday_departures += sunday
            systemwide_departures += weekday * 5 + saturday + sunday
        if station_id == "System":
            table.append(["","","","","",""])
            table.append([station_name, weekday_departures, weekday_departures * 5, saturday_departures, sunday_departures, systemwide_departures])
        else:
            table.append([station_name, weekday, weekday * 5, saturday, sunday, (weekday * 5) + saturday + sunday])
    output_line = f"Outputting Data to '{output_path}' and console - Blue Line (Congress) excluded from Systemwide to prevent duplicates\nWeekday Total Reflects single day total, Total Reflects 5 Day Weekday + Weekend\n"
    print(output_line)
    with open(output_path, 'w') as output_file:
        output_file.write(output_line + "\n\n")
        count = 0
        for row in table:
            output_file.write('| {:^26} | {:^14} | {:^12} | {:^8} | {:^6} | {:^6} |\n'.format(*row))
            print('| {:^26} | {:^14} | {:^12} | {:^8} | {:^6} | {:^6}  |'.format(*row))



print("Performing Regex Cleanup on 'calendar.txt'")
regex_runner(calendar_regex, calendar_path)

print("Performing Regex Cleanup on 'stop_times.txt'")
regex_runner(stop_times_regex, stop_times_path)

print("Performing Regex Cleanup on 'trips.txt'")
regex_runner(trips_regex, trips_path)
service_ids = get_ids(calendar_path, 0)

print("Adding Time Of Week Information on 'trips.txt'")
regex_runner(service_ids, trips_path, "triptime")
trip_ids = get_ids(trips_path, 2)

print("Adding Time Of Week Information on 'stop_times.txt'")
regex_runner(trip_ids, stop_times_path, "stoptime")

run_output()

file_rename(calendar_path, schedule_date)
file_rename(output_path, schedule_date)
file_rename(stop_times_path, schedule_date)
file_rename(trips_path, schedule_date)