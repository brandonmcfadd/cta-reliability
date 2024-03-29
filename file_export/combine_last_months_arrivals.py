"""export data for previous days arrivals by Brandon McFadden"""
import os
from datetime import datetime, timedelta
import glob
import pandas as pd
from dotenv import load_dotenv  # Used to Load Env Var
from dateutil.relativedelta import relativedelta


# Load .env variables
load_dotenv()

main_file_path = os.getenv('FILE_PATH')
main_file_path_csv_day = main_file_path + "train_arrivals/csv/"
main_file_path_csv_month = main_file_path + "train_arrivals/csv_month/"


def get_date(date_type, delay):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "file":
        date = datetime.strftime(
            datetime.now()-relativedelta(months=delay), "%Y-%m")
    elif date_type == "year":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%Y")
    elif date_type == "month":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%m")
    elif date_type == "day":
        date = datetime.strftime(datetime.now()-timedelta(days=delay), "%d")
    elif date_type == "longmonth":
        date = datetime.strftime(
            datetime.now()-relativedelta(months=delay), "%B %Y")
    elif date_type == "file-date":
        date = datetime.strftime(
            datetime.now()-relativedelta(months=delay), "%Y-%m")
    return date


def combine_days_to_month(month, agency, sort):
    """takes api response and turns it into usable data without all the extra powerbi stuff"""
    day_path = main_file_path_csv_day + f"{agency}/"
    month_path = main_file_path_csv_month + f"{agency}/"

    file_list = glob.glob(day_path + f"/{month}*.csv")
    excl_list = []
    file_list.sort()

    for file in file_list:
        excl_list.append(pd.read_csv(file))

    excl_merged = pd.DataFrame()

    for excl_file in excl_list:
        excl_merged = pd.concat([excl_merged, excl_file], ignore_index=True)
    excl_merged.sort_values(by=sort)
    excl_merged.to_csv(f'{month_path}/{month}.csv', index=False)


remaining = 1

while remaining > 0:
    last_month = get_date("file-date", remaining)
    combine_days_to_month(last_month, "cta", "Arrival_Time")
    combine_days_to_month(last_month, "metra", "Full_Date_Time")
    print("exporting month:", last_month)
    remaining -= 1
