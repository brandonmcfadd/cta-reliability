"""cta-reliability API by Brandon McFadden"""
from datetime import datetime, timedelta
import os  # Used to retrieve secrets in .env file
import json
from dotenv import load_dotenv  # Used to Load Env Var
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from fastapi import Response
import apihtml

app = FastAPI()
security = HTTPBasic()

# Load .env variables
load_dotenv()

main_file_path = os.getenv('FILE_PATH')
main_file_path_json = os.getenv('FILE_PATH_JSON')

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
    return date

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Used to verify Creds"""
    file = open(file=main_file_path + '/cta-reliability/.tokens',
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
    html_content = apihtml.main_page
    return HTMLResponse(content=html_content, status_code=200)


def generate_html_response_error(date):
    """Used for Error Page"""
    html_content = f"""
    <html>
        <head>
            <title>CTA Reliability API</title>
        </head>
        <body>
            <h1>Welcome to the CTA Reliability API</h1>
            <p>Unable to retrieve results for the date {date}</p>
            <p></p>
            <p>To Retrieve the data use http://ctareliability.brandonmcfadden.com/api/v1/get_daily_results/{{date}}</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/")
async def read_root():
    """Tells API to Display Root"""
    return generate_html_response_intro()

@app.get("/api/", response_class=HTMLResponse)
async def documentation():
    """Tells API to Display Root"""
    return generate_html_response_intro()


@app.get("/api/v1/get_daily_results/{date}")
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_json + "cta/" + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        return generate_html_response_error(date)

@app.get("/api/v2/cta/get_daily_results/{date}")
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    try:
        json_file = main_file_path_json + "cta/" + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        return generate_html_response_error(date)

@app.get("/api/v2/metra/get_daily_results/{date}")
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    if date == "today":
        date = get_date("api-today")
    elif date == "yesterday":
        date = get_date("api-yesterday")
    try:
        json_file = main_file_path_json + "metra/" + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        return generate_html_response_error(date)
