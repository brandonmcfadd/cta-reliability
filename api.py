"""cta-reliability API by Brandon McFadden"""
import os  # Used to retrieve secrets in .env file
import json
from dotenv import load_dotenv  # Used to Load Env Var
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from fastapi import Response

app = FastAPI()
security = HTTPBasic()

# Load .env variables
load_dotenv()

main_file_path = os.getenv('FILE_PATH')
main_file_path_json = os.getenv('FILE_PATH_JSON')


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
    html_content = """
    <html>
        <head>
            <title>CTA Reliability API</title>
        </head>
        <body>
            <h1>Welcome to the CTA Reliability API</h1>
            <p>To Retrieve the data use http://ctareliability.brandonmcfadden.com/api/v1/get_daily_results/{date}</p>
            <p>Example: http://ctareliability.brandonmcfadden.com/api/v1/get_daily_results/2023-01-20</p>
	    <p>Authentication is required to use this endpoint. Please fill out the contact form at https://brandonmcfadden.com/contact to request one.</p>
        </body>
    </html>
    """
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
    "Tells API to Direct User"
    return("Please go to http://ctareliability.brandonmcfadden.com/api for information about the API.")

@app.get("/api/", response_class=HTMLResponse)
async def documentation():
    """Tells API to Display Root"""
    return generate_html_response_intro()


@app.get("/api/v1/get_daily_results/{date}")
async def return_results_for_date(date: str, token: str = Depends(get_current_username)):
    """Used to retrieve results"""
    try:
        json_file = main_file_path_json + date + ".json"
        results = open(json_file, 'r', encoding="utf-8")
        return Response(content=results.read(), media_type="application/json")
    except:  # pylint: disable=bare-except
        return generate_html_response_error(date)