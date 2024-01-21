"""cta-reliability API by Brandon McFadden"""
from datetime import datetime, timedelta
import os  # Used to retrieve secrets in .env file
import time
import json
import logging
from logging.handlers import RotatingFileHandler
import secrets
from dotenv import load_dotenv  # Used to Load Env Var
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi import Response
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from dateutil.relativedelta import relativedelta
import apihtml

app = FastAPI(docs_url=None)
security = HTTPBasic()

# Load .env variables
load_dotenv()

main_file_path = os.getenv('FILE_PATH')
wmata_main_file_path = os.getenv('WMATA_FILE_PATH')
main_file_path_7000 = os.getenv('FILE_PATH_7000')
main_file_path_amtrak = os.getenv('FILE_PATH_AMTRAK')
main_file_path_json = main_file_path + "train_arrivals/json/"
wmata_main_file_path_json = wmata_main_file_path + "train_arrivals/json/"
main_file_path_csv = main_file_path + "train_arrivals/csv/"
main_file_path_csv_month = main_file_path + "train_arrivals/csv_month/"
deploy_secret = os.getenv('DEPLOY_SECRET')
api_auth_key = os.getenv('API_AUTH_KEY')


def get_date(date_type):
    """formatted date shortcut"""
    if date_type == "short":
        date = datetime.strftime(datetime.now(), "%Y%m%d")
    elif date_type == "hour":
        date = datetime.strftime(datetime.now(), "%H")
    elif date_type == "api-today":
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    elif date_type == "api-yesterday":
        date = datetime.strftime(datetime.now()-timedelta(days=1), "%Y-%m-%d")
    elif date_type == "api-today-est":
        date = datetime.strftime(datetime.now()+timedelta(hours=1), "%Y-%m-%d")
    elif date_type == "api-yesterday-est":
        date = datetime.strftime(
            datetime.now()-timedelta(days=1)+timedelta(hours=1), "%Y-%m-%d")
    elif date_type == "api-last-month":
        date = datetime.strftime(
            datetime.now()-relativedelta(months=1), "%Y-%m")
    elif date_type == "api-last-month-est":
        date = datetime.strftime(
            datetime.now()-relativedelta(months=1)+timedelta(hours=1), "%Y-%m")
    elif date_type == "current":
        date = datetime.strftime(datetime.now(), "%d %b %Y %H:%M:%S")
    elif date_type == "code-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%z")
    return date


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Used to verify Creds"""
    file = open(file=main_file_path + '.tokens',
                mode='r',
                encoding='utf-8')
    tokens = json.load(file)
    try:
        if credentials.username in tokens:
            is_correct_username = True
        else:
            is_correct_username = False
            reason = "Incorrect username or password"
    except:  # pylint: disable=bare-except
        is_correct_username = False
        reason = "Incorrect username or password"

    try:
        if credentials.password == tokens[credentials.username]["password"]:
            is_correct_password = True
        else:
            is_correct_password = False
            reason = "Incorrect username or password"
    except:  # pylint: disable=bare-except
        is_correct_password = False
        reason = "Incorrect username or password"

    try:
        if tokens[credentials.username]["disabled"] == "True":
            is_enabled = False
            reason = "Account Disabled"
        else:
            is_enabled = True
    except:  # pylint: disable=bare-except
        is_enabled = True
        reason = "Account Disabled"

    if not (is_correct_username and is_correct_password and is_enabled):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=reason,
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def generate_html_response_intro():
    """Used for Root Page"""
    html_content = apihtml.MAIN_PAGE
    return HTMLResponse(content=html_content, status_code=200)


def generate_html_response_error(date, endpoint, current_time):
    """Used for Error Page"""
    html_content = f"""
    <html>
        <head>
            <title>CTA Reliability API Error</title>
        </head>
        <body>
            <h1>Error In CTA Reliability API Request</h1>
            <p>Current System Time: {current_time}</p>
            <p>Endpoint: {endpoint}{date}<br>
            Unable to retrieve results for the date {date}<br><br>
            If you are using the 'get_train_arrivals_by_day' endpoint, please note that data for the previous day is not loaded until ~01:00 CST.</p>
            <p></p>
            <p>Please refer to the documentation for assistance: <a href="https://brandonmcfadden.com">RTA API Documentation</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.on_event("startup")
async def startup():
    """Tells API to Prep redis for Rate Limit"""
    redis_value = redis.from_url(
        "redis://localhost", encoding="utf-8", decode_responses=True)
    # Logging Information
    logger = logging.getLogger("uvicorn.access")
    log_filename = main_file_path + '/logs/api-service.log'
    logging.basicConfig(level=logging.INFO)
    handler = RotatingFileHandler(log_filename, maxBytes=10e6, backupCount=10)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    await FastAPILimiter.init(redis_value)


@app.middleware("http")
async def check_for_header(request: Request, call_next):
    """makes sure the request came through the Express Proxy"""
    try:
        proxy_header = request.headers.get('x-api-proxy')
        if proxy_header == api_auth_key:
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        else:
            return HTMLResponse(status_code=403, content="Missing Required Header. Are you using the right Address?")
    except:  # pylint: disable=bare-except
        return HTMLResponse(status_code=403, content="Missing Required Header. Are you using the right Address?")


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=1))], response_class=RedirectResponse, status_code=302)
async def read_root():
    """Tells API to Display Root"""
    return "https://brandonmcfadden.com/transit-api"


@app.get("/api/", dependencies=[Depends(RateLimiter(times=2, seconds=1))], response_class=RedirectResponse, status_code=302)
async def documentation():
    """Tells API to Display Root"""
    return "https://brandonmcfadden.com/transit-api"


@app.get("/api/v1/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_json + "cta/" + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/v1/get_daily_results/"
        return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(
            main_file_path_json + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            json_file = main_file_path_json + "cta/" + date + ".json"
            results = open(json_file, 'r', encoding="utf-8")
            return Response(content=results.read(), media_type="application/json")
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/v2/cta/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/metra/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_metra_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(
            main_file_path_json + "metra/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            json_file = main_file_path_json + "metra/" + date + ".json"
            results = open(json_file, 'r', encoding="utf-8")
            return Response(content=results.read(), media_type="application/json")
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/v2/metra/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/get_train_arrivals_by_day/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(
            main_file_path_csv + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            csv_file = main_file_path_csv + "cta/" + date + ".csv"
            print(csv_file)
            results = open(csv_file, 'r', encoding="utf-8")
            return StreamingResponse(
                results,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=cta-arrivals-{date}.csv"}
            )
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/get_train_arrivals_by_month/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date_month_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "yesterday":
        date = get_date("api-last-month")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(
            main_file_path_csv_month + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            csv_file = main_file_path_csv_month + "cta/" + date + ".csv"
            print(csv_file)
            results = open(csv_file, 'r', encoding="utf-8")
            return StreamingResponse(
                results,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=cta-arrivals-{date}.csv"}
            )
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/headways", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_special_station_json(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "train_arrivals/json/special-station.json"
        print(json_file)
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/v2/cta/headways"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))


@app.get("/api/7000-series-tracker/get", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def get_7000_series_information(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_7000 + "7000-series.json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/7000-series-tracker"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))


@app.post("/api/7000-series-tracker/{Name}/{RunNumber}", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def save_7000_series_information(Name: str, RunNumber: int, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_7000 + "7000-series.json"
        input_data = {"DateTime": get_date(
            "code-time"), "Submitter": Name, "RunNumber": RunNumber}
        with open(json_file, 'r', encoding="utf-8") as fp:
            json_file_loaded = json.load(fp)
            if get_date("api-today") in json_file_loaded:
                json_file_loaded[get_date("api-today")].append(input_data)
            else:
                json_file_loaded = {**json_file_loaded,
                                    **{get_date("api-today"): []}}
                json_file_loaded[get_date("api-today")].append(input_data)
        with open(json_file, 'w', encoding="utf-8") as fp2:
            json.dump(json_file_loaded, fp2, indent=4,  separators=(',', ': '))
        return input_data
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/7000-series-tracker"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))


@app.get("/api/sorting_information/get", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def get_sort_information(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "sorting_information/sort_info.json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/sorting_information/get"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))


@app.get("/api/v2/metra/holiday_trains/", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_holiday_trains_metra(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "train_arrivals/special/tweeted_metra_trains.json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/v2/metra/holiday_trains/"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))


@app.get("/api/v2/wmata/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_wmata_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today-est")
    elif date == "yesterday":
        date = get_date("api-yesterday-est")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(
            wmata_main_file_path_json) if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            json_file = wmata_main_file_path_json + date + ".json"
            results = open(json_file, 'r', encoding="utf-8")
            return Response(content=results.read(), media_type="application/json")
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/v2/wmata/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/transit/get_daily_results/", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_transit(agency: str, date: str = None, availability: bool = False, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today" and (agency == "cta" or agency == "metra"):
        date = get_date("api-today")
    elif date == "yesterday" and (agency == "cta" or agency == "metra"):
        date = get_date("api-yesterday")
    if date == "today" and agency == "wmata":
        date = get_date("api-today-est")
    elif date == "yesterday" and agency == "wmata":
        date = get_date("api-yesterday-est")
    if availability is True and agency == "cta":
        files_available = sorted((f for f in os.listdir(
            main_file_path_json + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    elif availability is True and agency == "wmata":
        files_available = sorted((f for f in os.listdir(
            wmata_main_file_path_json) if not f.startswith(".")), key=str.lower)
        return files_available
    elif availability is True and agency == "metra":
        files_available = sorted((f for f in os.listdir(
            main_file_path_json + "metra/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            if agency == "cta":
                json_file = main_file_path_json + "cta/" + date + ".json"
                results = open(json_file, 'r', encoding="utf-8")
                return Response(content=results.read(), media_type="application/json")
            if agency == "metra":
                json_file = main_file_path_json + "metra/" + date + ".json"
                results = open(json_file, 'r', encoding="utf-8")
                return Response(content=results.read(), media_type="application/json")
            elif agency == "wmata":
                json_file = wmata_main_file_path_json + date + ".json"
                results = open(json_file, 'r', encoding="utf-8")
                return Response(content=results.read(), media_type="application/json")
            else:
                endpoint = "https://brandonmcfadden.com/api/transit/get_daily_results/"
                return generate_html_response_error(date, endpoint, get_date("current"))
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/transit/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/transit/get_train_arrivals_by_day/", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date(agency: str, date: str = None, availability: bool = False, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today" and (agency == "cta" or agency == "metra"):
        date = get_date("api-today")
    elif date == "yesterday" and (agency == "cta" or agency == "metra"):
        date = get_date("api-yesterday")
    if date == "today" and agency == "wmata":
        date = get_date("api-today-est")
    elif date == "yesterday" and agency == "wmata":
        date = get_date("api-yesterday-est")
    if availability is True and agency == "wmata":
        return "Unavailable"
    elif availability is True and agency == "cta":
        files_available = sorted((f for f in os.listdir(
            main_file_path_csv + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    elif availability is True and agency == "metra":
        return "Unavailable"
    else:
        try:
            if agency == "cta":
                csv_file = main_file_path_csv + "cta/" + date + ".csv"
                print(csv_file)
                results = open(csv_file, 'r', encoding="utf-8")
                return StreamingResponse(
                    results,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=cta-arrivals-{date}.csv"}
                )
            if agency == "metra":
                return "Unavailable"
            elif agency == "wmata":
                return "Unavailable"
            else:
                endpoint = "https://brandonmcfadden.com/api/transit/get_train_arrivals_by_day/"
                return generate_html_response_error(date, endpoint, get_date("current"))
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/transit/get_train_arrivals_by_day/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/transit/get_train_arrivals_by_month/", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date_month(agency: str, date: str = None, availability: bool = False, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today" and (agency == "cta" or agency == "metra"):
        date = get_date("api-today")
    elif date == "yesterday" and (agency == "cta" or agency == "metra"):
        date = get_date("api-last-month")
    if date == "today" and agency == "wmata":
        date = get_date("api-today-est")
    elif date == "yesterday" and agency == "wmata":
        date = get_date("api-last-month-est")
    if availability is True and agency == "wmata":
        return "Unavailable"
    elif availability is True and agency == "cta":
        files_available = sorted((f for f in os.listdir(
            main_file_path_csv + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    elif availability is True and agency == "metra":
        return "Unavailable"
    else:
        try:
            if agency == "cta":
                csv_file = main_file_path_csv_month + "cta/" + date + ".csv"
                print(csv_file)
                results = open(csv_file, 'r', encoding="utf-8")
                return StreamingResponse(
                    results,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=cta-arrivals-{date}.csv"}
                )
            if agency == "metra":
                return "Unavailable"
            elif agency == "wmata":
                return "Unavailable"
            else:
                endpoint = "https://brandonmcfadden.com/api/transit/get_train_arrivals_by_month/"
                return generate_html_response_error(date, endpoint, get_date("current"))
        except:  # pylint: disable=bare-except
            endpoint = "https://brandonmcfadden.com/api/transit/get_train_arrivals_by_month/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.post("/api/user_management", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def add_user_to_api(type: str, username: str, auth_token: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        if auth_token == deploy_secret:
            json_file = main_file_path + ".tokens"
            with open(json_file, 'r', encoding="utf-8") as fp:
                json_file_loaded = json.load(fp)
            if type == "add":
                password = secrets.token_urlsafe(32)
                input_data = {"password": password, "disabled": "False"}
                return_text = {"DateTime": get_date(
                    "code-time"), "Status": "", "Username": "", "Password": "", "Disabled": ""}
                if username in json_file_loaded:
                    return_text["Username"] = username
                    return_text["Status"] = "Exists"
                    return_text["Password"] = json_file_loaded[username]["password"]
                    return_text["Disabled"] = json_file_loaded[username]["disabled"]
                    json_file_loaded[username]["disabled"] = "False"
                else:
                    return_text["Username"] = username
                    return_text["Password"] = password
                    return_text["Disabled"] = "False"
                    return_text["Status"] = "Added"
                    json_file_loaded[username] = input_data
            elif type == "remove":
                if username in json_file_loaded:
                    json_file_loaded.pop(username, None)
                else:
                    return {"username":username,"Status": "Failed to Remove User. User Does Not Exist."}
                return_text = {"username":username,"Status": "Removed User."}
            with open(json_file, 'w', encoding="utf-8") as fp2:
                json.dump(json_file_loaded, fp2, indent=4,
                          separators=(',', ': '))
            return return_text
        else:
            endpoint = "https://brandonmcfadden.com/api/add_user"
            return generate_html_response_error(get_date("current"), endpoint, get_date("current"))
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/add_user"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))

@app.post("/api/amtrak/post", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def amtrak_trips(auth_token: str, type:str, date: str, train: str, origin :str = None, destination:str = None, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        if auth_token == deploy_secret:
            json_file = main_file_path_amtrak + "amtrak.json"
            with open(json_file, 'r', encoding="utf-8") as fp:
                json_file_loaded = json.load(fp)
            train_id = f"{date}-{train}"
            if type == "add":
                if train_id in json_file_loaded:
                    return_text = {"Status":"Train Already Present","TrainDetails":json_file_loaded[train_id]}
                else:
                    train_input = {"Date":date,"Train":train,"Origin":origin.upper(),"Destination":destination.upper()}
                    json_file_loaded[train_id] = train_input
                    return_text = {"Status":"Train Added","TrainDetails":train_input}
            elif type == "remove":
                if train_id in json_file_loaded:
                    train_input = json_file_loaded[train_id]
                    json_file_loaded.pop(train_id, None)
                else:
                    return {"Status": "Failed to Remove Train. Train does not exist.","TrainDetails":train_input}
                return_text = {"Status":"Train Removed","TrainDetails":train_input}
            with open(json_file, 'w', encoding="utf-8") as fp2:
                json.dump(json_file_loaded, fp2, indent=4,
                          separators=(',', ': '))
            return return_text
        else:
            endpoint = "https://brandonmcfadden.com/api/amtrak/post"
            return generate_html_response_error(get_date("current"), endpoint, get_date("current"))
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/amtrak/post"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))

@app.get("/api/amtrak/get", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def get_amtrak_trips(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_amtrak + "amtrak.json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "https://brandonmcfadden.com/api/amtrak/get"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))
