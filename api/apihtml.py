MAIN_PAGE = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>
    Transit Reliability API</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="API Available to gather Actual, Scheduled and Percent Completed for runs on the CTA/Metra/WMATA System.">
    <style>
    body {background-color:#ffffff;background-repeat:no-repeat;background-position:top left;background-attachment:fixed;}
    h1{font-family:Arial, sans-serif;color:#000000;background-color:#ffffff;}
    p {font-family:Georgia, serif;font-size:14px;font-style:normal;font-weight:normal;color:#000000;background-color:#ffffff;}
    pre code {
    background-color: #eee;
    border: 2px solid #999;
    display: block;
    padding: 1px;
    width: 1000px;
    }
    </style>
    </head>
    <body>
    <h1>Welcome to the Transit Reliability API</h1>
    <p>You can use this API to query by date and return the number of runs that were observed on the system vs the number scheduled and calculated percentage of those completed runs.
    <br>Additionally, you can obtain a copy of the raw data being used by my PowerBi reports for your own analysis.</p>
    <p><b>Authentication is required to use this API:</b> Please fill out the contact form at https://brandonmcfadden.com/contact to request an API key.</p>
    <p><b>Rate Limit:</b> All API Endpoints have a 2 requests per second limit - please keep this in mind and be gentle :)</p>
    <p></p>
    <h2>V2 (Supports CTA, Metra and WMATA)</h2>
    <h3>Daily Results</h3>
    <h4>Returns back combined value calculations for each of the available lines comparing scheduled service values to actual service values.</h4>
    <p>Endpoint: http://api.brandonmcfadden.com/api/v2/cta/get_daily_results/{yyyy-mm-dd}
    <br>Example: http://api.brandonmcfadden.com/api/v2/cta/get_daily_results/2023-01-20</p>
    <p>Endpoint: http://api.brandonmcfadden.com/api/v2/metra/get_daily_results/{yyyy-mm-dd}
    <br>Example: http://api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-20</p>
    <p>Endpoint: http://api.brandonmcfadden.com/api/v2/wmata/get_daily_results/{yyyy-mm-dd}
    <br>Example: http://api.brandonmcfadden.com/api/v2/wmata/get_daily_results/2023-12-06</p>
    <h3>Train Arrivals (by day)</h3>
    <h4>Returns back the raw arrival data as a csv file. This file contains all of the arrivals being used in the <a href="https://brandonmcfadden.com/cta-reliability">PowerBi Reports</a>.<br>
    Arrival data for the previous day is loaded at ~01:00 CST.</h4>
    <p>Endpoint: http://api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/{yyyy-mm-dd}
    <br>Example: http://api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_day/2023-01-20</p>
    <h3>Train Arrivals (by month)</h3>
    <h4>Returns back the raw arrival data as a csv file. This file contains all of the arrivals being used in the <a href="https://brandonmcfadden.com/cta-reliability">PowerBi Reports</a>.<br>
    Arrival data for the previous month is loaded at ~01:00 CST on the first day of the following month.</h4>
    <p>Endpoint: http://api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_month/{yyyy-mm}
    <br>Example: http://api.brandonmcfadden.com/api/v2/cta/get_train_arrivals_by_month/2023-01</p>
    <p><b>Note:</b> All Endpoints also allow the options /today and /yesterday in lieu of the date (with the exception of 'get_train_arrivals_by_day', which does not include data for the current day)</p>
    <h2>Data Availability:</h2>
    <p>CTA: June 20, 2022 through Current Day
    <br>Metra: January 18, 2023 through Current Day</p>
    <p></p>
    <h2>Example cURL Request</h2>
    <pre>
    <code>
    curl --location --request GET 
        'http://api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-25'
        --header 'Authorization: Basic {base64 encoded username:password}'

    Example:
    curl --location --request GET 
        'http://api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-25'
        --header 'Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ='
    </code>
    </pre>
    <h2>CTA Results Response Example</h2>
    <pre>
    <code>
    {
        "Data Provided By": "Brandon McFadden - http://api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "V2 API Information At": "http://api.brandonmcfadden.com",
        "Entity": "cta",
        "Date": "2023-01-24",
        "IntegrityChecksPerformed": 1439,
        "IntegrityPercentage": 0.9993055555555556,
        "system": {
            "ActualRuns": 1210,
            "ScheduledRuns": 1633,
            "PercentRun": 0.7409675443968157
        },
        "routes": {
            "Blue": {
                "ActualRuns": 233,
                "ScheduledRuns": 340,
                "PercentRun": 0.6852941176470588
            },
            "Brown": {
                "ActualRuns": 108,
                "ScheduledRuns": 187,
                "PercentRun": 0.5775401069518716
            },
            "Green": {
                "ActualRuns": 214,
                "ScheduledRuns": 252,
                "PercentRun": 0.8492063492063492
            },
            "Orange": {
                "ActualRuns": 117,
                "ScheduledRuns": 144,
                "PercentRun": 0.8125
            },
            "Pink": {
                "ActualRuns": 92,
                "ScheduledRuns": 118,
                "PercentRun": 0.7796610169491526
            },
            "Purple": {
                "ActualRuns": 94,
                "ScheduledRuns": 132,
                "PercentRun": 0.7121212121212122
            },
            "Red": {
                "ActualRuns": 299,
                "ScheduledRuns": 368,
                "PercentRun": 0.8125
            },
            "Yellow": {
                "ActualRuns": 53,
                "ScheduledRuns": 92,
                "PercentRun": 0.5760869565217391
            }
        }
    }
    </code>
    </pre>
    <h2>Metra Results Response Example</h2>
    <pre>
    <code>
    {
        "Data Provided By": "Brandon McFadden - http://api.brandonmcfadden.com",
        "Reports Acccessible At": "https://brandonmcfadden.com/cta-reliability",
        "V2 API Information At": "http://api.brandonmcfadden.com",
        "Entity": "metra",
        "Date": "2023-01-24",
        "IntegrityChecksPerformed": 96,
        "IntegrityPercentage": 1.0,
        "system": {
            "ActualRuns": 411,
            "ScheduledRuns": 616,
            "PercentRun": 0.6672077922077922
        },
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
    <h2>CTA Arrivals Response Example</h2>
  <pre>
  <code>
  Station_ID,Stop_ID,Station_Name,Destination,Route,Run_Number,Prediction_Time,Arrival_Time,Headway,Time_Of_Week,Time_Of_Day
  41020,30197,Logan Square,O'Hare,Blue,225,2023-02-08T00:10:00,2023-02-08T00:11:00,20.0,Weekday,Night
  41020,30198,Logan Square,Forest Park,Blue,104,2023-02-08T05:37:00,2023-02-08T05:38:00,12.0,Weekday,Morning
  41020,30198,Logan Square,UIC-Halsted,Blue,127,2023-02-08T17:06:00,2023-02-08T17:07:00,12.0,Weekday,Afternoon
  41440,30278,Addison,Loop,Brown,422,2023-02-08T17:59:00,2023-02-08T18:00:00,5.0,Weekday,Evening
  41360,30266,California,Harlem/Lake,Green,604,2023-02-08T11:11:00,2023-02-08T11:12:00,12.0,Weekday,Morning
  ....
  </code>
  </pre>
    </body>
    </html>
    """

ERROR_PAGE = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>
    Transit Reliability API</title>
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
    <p>To Retrieve the data use http://api.brandonmcfadden.com/api/v1/get_daily_results/{date}</p>
    <p>Example: http://api.brandonmcfadden.com/api/v1/get_daily_results/2023-01-20</p>
    <p></p>
    <h2>V2 (Supports CTA & Metra)</h2>
    <p>Example: http://api.brandonmcfadden.com/api/v2/cta/get_daily_results/2023-01-20</p>
    <p>Example: http://api.brandonmcfadden.com/api/v2/metra/get_daily_results/2023-01-20</p>
    <p></p>
    <p>Data Availability:</p>
    <p>CTA: June 20, 2022 through Current Day</p>
    <p>Metra: January 18, 2022 through Current Day</p>
    <p></p>
    </body>
    </html>
    """