main_page = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>
    RTA (CTA/Metra) Reliability API</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="API Available to gather Actual, Scheduled and Percent Completed for runs on the CTA/Metra System.">
    <style>
    body {background-color:#ffffff;background-repeat:no-repeat;background-position:top left;background-attachment:fixed;}
    h1{font-family:Arial, sans-serif;color:#000000;background-color:#ffffff;}
    p {font-family:Georgia, serif;font-size:14px;font-style:normal;font-weight:normal;color:#000000;background-color:#ffffff;}
    pre code {
    background-color: #eee;
    border: 2px solid #999;
    display: block;
    padding: 1px;
    width: 750px;
    }
    </style>
    </head>
    <body>
    <h1>Welcome to the RTA Reliability API</h1>
    <p>You can use this API to query by date and return the number of runs that were observed on the system vs the number scheduled and calculated percentage of those completed runs. </p>
    <p><b>Authentication is required to use this API.</b> Please fill out the contact form at https://brandonmcfadden.com/contact to request an API key.</p>
    <p></p>
    <h2>V1 (Only CTA):</h2>
    <p>To Retrieve the data use http://rta-api.brandonmcfadden.com/api/v1/get_daily_results/{date}</p>
    <p>Example: http://rta-api.brandonmcfadden.com/api/v1/get_daily_results/2023-01-20</p>
    <p></p>
    <h2>V2 (Supports CTA & Metra)</h2>
    <p>Endpoint: http://rta-api.brandonmcfadden.com/api/v2/cta/get_daily_results/{yyyy-mm-dd}
    <br>Example: http://rta-api.brandonmcfadden.com/api/v2/cta/get_daily_results/2023-01-20</p>
    <p>Endpoint: http://rta-api.brandonmcfadden.com/api/v2/metra/get_daily_results/{yyyy-mm-dd}
    <br>Example: http://rta-api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-20</p>
    <p><b>Note:</b> Both Endpoints also the options /today and /yesterday in lieu of the date</p>
    <h2>Data Availability:</h2>
    <p>CTA: June 20, 2022 through Current Day
    <br>Metra: January 18, 2022 through Current Day</p>
    <p></p>
    <h2>Example cURL Request</h2>
    <pre>
    <code>
    curl --location --request GET 
        'http://rta-api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-25'
        --header 'Authorization: Basic {base64 encoded username/password}'
    </code>
    </pre>
    <h2>CTA Response Example</h2>
    <pre>
    <code>
    {
        "Data Provided By": "Brandon McFadden - rta-api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "Entity": "cta",
        "Date": "2023-01-25",
        "IntegrityChecksPerformed": 898,
        "IntegrityPercentage": 0.6236111111111111,
        "routes": {
            "Blue": {
                "ActualRuns": 112,
                "ScheduledRuns": 340,
                "PercentRun": 0.32941176470588235
            },
            "Brown": {
                "ActualRuns": 57,
                "ScheduledRuns": 187,
                "PercentRun": 0.3048128342245989
            },
            "Green": {
                "ActualRuns": 106,
                "ScheduledRuns": 252,
                "PercentRun": 0.42063492063492064
            },
            "Orange": {
                "ActualRuns": 58,
                "ScheduledRuns": 144,
                "PercentRun": 0.4027777777777778
            },
            "Pink": {
                "ActualRuns": 48,
                "ScheduledRuns": 118,
                "PercentRun": 0.4067796610169492
            },
            "Purple": {
                "ActualRuns": 48,
                "ScheduledRuns": 132,
                "PercentRun": 0.36363636363636365
            },
            "Red": {
                "ActualRuns": 169,
                "ScheduledRuns": 368,
                "PercentRun": 0.4592391304347826
            },
            "Yellow": {
                "ActualRuns": 26,
                "ScheduledRuns": 92,
                "PercentRun": 0.2826086956521739
            }
        }
    }
    </code>
    </pre>
    <h2>Metra Response Example</h2>
    <pre>
    <code>
    {
        "Data Provided By": "Brandon McFadden - rta-api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "Entity": "metra",
        "Date": "2023-01-24",
        "IntegrityChecksPerformed": 96,
        "IntegrityPercentage": 1.0,
        "routes": {
            "BNSF": {
                "ActualRuns": 64,
                "ScheduledRuns": 91,
                "PercentRun": 0.7032967032967034
            },
            "HC": {
                "ActualRuns": 6,
                "ScheduledRuns": 6,
                "PercentRun": 1.0
            },
            "MN-N": {
                "ActualRuns": 53,
                "ScheduledRuns": 52,
                "PercentRun": 1.0192307692307692
            },
            "MN-W": {
                "ActualRuns": 51,
                "ScheduledRuns": 52,
                "PercentRun": 0.9807692307692307
            },
            "ME": {
                "ActualRuns": 107,
                "ScheduledRuns": 127,
                "PercentRun": 0.84251968503937
            },
            "NCS": {
                "ActualRuns": 14,
                "ScheduledRuns": 14,
                "PercentRun": 1.0
            },
            "RI": {
                "ActualRuns": 76,
                "ScheduledRuns": 80,
                "PercentRun": 0.95
            },
            "UP-N": {
                "ActualRuns": 12,
                "ScheduledRuns": 70,
                "PercentRun": 0.17142857142857143
            },
            "UP-NW": {
                "ActualRuns": 8,
                "ScheduledRuns": 66,
                "PercentRun": 0.12121212121212122
            },
            "UP-W": {
                "ActualRuns": 20,
                "ScheduledRuns": 58,
                "PercentRun": 0.3448275862068966
            }
        }
    }
    </code>
    </pre>
    </body>
    </html>
    """

error_page = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>
    RTA (CTA/Metra) Reliability API</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="API Available to gather Actual, Scheduled and Percent Completed for runs on the CTA/Metra System.">
    <style>
    body {background-color:#ffffff;background-repeat:no-repeat;background-position:top left;background-attachment:fixed;}
    h1{font-family:Arial, sans-serif;color:#000000;background-color:#ffffff;}
    p {font-family:Georgia, serif;font-size:14px;font-style:normal;font-weight:normal;color:#000000;background-color:#ffffff;}
    </style>
    </head>
    <body>
    <h1>Error in API Call - Please Try Again</h1>
    <p>You can use this API to query by date and return the number of runs that were observed on the system vs the number scheduled and calculated percentage of those completed runs. </p>
    <p></p>
    <h2>V1 (Only CTA):</h2>
    <p>To Retrieve the data use http://rta-api.brandonmcfadden.com/api/v1/get_daily_results/{date}</p>
    <p>Example: http://rta-api.brandonmcfadden.com/api/v1/get_daily_results/2023-01-20</p>
    <p></p>
    <h2>V2 (Supports CTA & Metra)</h2>
    <p>Example: http://rta-api.brandonmcfadden.com/api/v2/cta/get_daily_results/2023-01-20</p>
    <p>Example: http://rta-api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-20</p>
    <p></p>
    <p>Data Availability:</p>
    <p>CTA: June 20, 2022 through Current Day</p>
    <p>Metra: January 18, 2022 through Current Day</p>
    <p></p>
    </body>
    </html>
    """