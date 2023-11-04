"""cta-reliability API by Brandon McFadden"""
from datetime import datetime, timedelta
import os  # Used to retrieve secrets in .env file
import json
import logging
import subprocess
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv  # Used to Load Env Var
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, StreamingResponse
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
main_file_path_json = os.getenv('FILE_PATH_JSON')
main_file_path_csv = os.getenv('FILE_PATH_CSV')
main_file_path_csv_month = os.getenv('FILE_PATH_CSV_MONTH')
deploy_secret = os.getenv('DEPLOY_SECRET')


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
    elif date_type == "api-last-month":
        date = datetime.strftime(datetime.now()-relativedelta(months=1), "%Y-%m")
    elif date_type == "current":
        date = datetime.strftime(datetime.now(), "%d %b %Y %H:%M:%S")
    elif date_type == "code-time":
        date = datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%M:%S%z")
    return date


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Used to verify Creds"""
    file = open(file=main_file_path + 'cta-reliability/.tokens',
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
            <p>Please refer to the documentation for assistance: <a href="http://rta-api.brandonmcfadden.com">RTA API Documentation</a></p>
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
    log_filename = main_file_path + '/cta-reliability/logs/api-service.log'
    logging.basicConfig(level=logging.INFO)
    handler = RotatingFileHandler(log_filename, maxBytes=10e6, backupCount=10)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    await FastAPILimiter.init(redis_value)


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def read_root():
    """Tells API to Display Root"""
    return generate_html_response_intro()


@app.get("/api/", response_class=HTMLResponse, dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def documentation():
    """Tells API to Display Root"""
    return generate_html_response_intro()


@app.get("/api/v1/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_json + "cta/" + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "http://rta-api.brandonmcfadden.com/api/v1/get_daily_results/"
        return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(main_file_path_json + "cta/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            json_file = main_file_path_json + "cta/" + date + ".json"
            results = open(json_file, 'r', encoding="utf-8")
            return Response(content=results.read(), media_type="application/json")
        except:  # pylint: disable=bare-except
            endpoint = "http://rta-api.brandonmcfadden.com/api/v2/cta/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/metra/get_daily_results/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_results_for_date_metra_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(main_file_path_json + "metra/") if not f.startswith(".")), key=str.lower)
        return files_available
    else:
        try:
            json_file = main_file_path_json + "metra/" + date + ".json"
            results = open(json_file, 'r', encoding="utf-8")
            return Response(content=results.read(), media_type="application/json")
        except:  # pylint: disable=bare-except
            endpoint = "http://rta-api.brandonmcfadden.com/api/v2/metra/get_daily_results/"
            return generate_html_response_error(date, endpoint, get_date("current"))


@app.get("/api/v2/cta/get_train_arrivals_by_day/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "yesterday":
        date = get_date("api-yesterday")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(main_file_path_csv + "cta/") if not f.startswith(".")), key=str.lower)
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
            endpoint = "http://rta-api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/"
            return generate_html_response_error(date, endpoint, get_date("current"))

@app.get("/api/v2/cta/get_train_arrivals_by_month/{date}", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_arrivals_for_date_month_cta_v2(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "yesterday":
        date = get_date("api-last-month")
    if date == "availability":
        files_available = sorted((f for f in os.listdir(main_file_path_csv_month + "cta/") if not f.startswith(".")), key=str.lower)
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
            endpoint = "http://rta-api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/"
            return generate_html_response_error(date, endpoint, get_date("current"))

@app.get("/api/v2/cta/headways", dependencies=[Depends(RateLimiter(times=2, seconds=1))])
async def return_special_station_json(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "cta-reliability/train_arrivals/json/special-station.json"
        print(json_file)
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "http://rta-api.brandonmcfadden.com/api/v2/cta/headways"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))

@app.get("/api/7000-series-tracker/get", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def get_7000_series_information(token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "7000-series-tracker/7000-series.json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        endpoint = "http://rta-api.brandonmcfadden.com/api/7000-series-tracker"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))

@app.post("/api/7000-series-tracker/{Name}/{RunNumber}", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def save_7000_series_information(Name: str, RunNumber: int, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path + "7000-series-tracker/7000-series.json"
        input_data = {"DateTime": get_date("code-time"),"Submitter": Name, "RunNumber": RunNumber}
        with open(json_file, 'r', encoding="utf-8") as fp:
            json_file_loaded = json.load(fp)
            if get_date("api-today") in json_file_loaded:
                json_file_loaded[get_date("api-today")].append(input_data)
            else:
                json_file_loaded = {**json_file_loaded, **{get_date("api-today"):[]}}
                json_file_loaded[get_date("api-today")].append(input_data)
        with open(json_file, 'w', encoding="utf-8") as fp2:
            json.dump(json_file_loaded, fp2, indent=4,  separators=(',',': '))
        return input_data
    except:  # pylint: disable=bare-except
        endpoint = "http://rta-api.brandonmcfadden.com/api/7000-series-tracker"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))

@app.post("/api/cta-reliability/production-upgrade/{secret}", dependencies=[Depends(RateLimiter(times=2, seconds=1))], status_code=200)
async def production_upgrade(secret: str, token: str = Depends(get_current_username)):
    """Used to trigger upgrade of cta-reliability"""
    try:
        if str(secret) == str(deploy_secret):
            prod_upgrade = subprocess.run(main_file_path + "cta-reliability/production-upgrade.sh", capture_output=True, check=False)
            output = prod_upgrade.stdout
        else:
            output = "Invalid Secret"
        return output
    except:  # pylint: disable=bare-except
        endpoint = "http://rta-api.brandonmcfadden.com/api/cta-reliability/production-upgrade/"
        return generate_html_response_error(get_date("current"), endpoint, get_date("current"))
