# Chicago Transit Authority ("CTA") Reliability Tracker

## Overview
This project (and associated PowerBi Report) was created to help provide insight and transparency into the current service levels of the Chicago Transit Authority ("CTA") rail network. Utilizing the CTA API, it can be determined when a train arrives at a specific station along the line. Using this data, the number of arrivals can be determined and compared to the number scheduled via the GTFS feed of published schedules.

## Station Selection 
The station selected along each line is one where all trains, regardless of destination, will arrive. For example, Washington (Dearborn Subway) can capture Forest Park, UIC-Halsted and even runs that terminate at the Rosemont yard. From June 2022 through October 2023, trains that operated around the loop and then return to their originating stations (Brown, Orange, Pink and Purple) were only tracked in one direction. Starting in October, tracking was enabled for both directions for all trains at their respective stations.

### The following stations were selected to monitor each of the 8 CTA Lines in operation:
* Blue - Washington (Dearborn Subway)
    * O'Hare, Jefferson Park, Rosemont bound
    * Forest Park, UIC-Halsted, Racine bound
* Brown - Southport
    * Loop bound
    * Kimball bound
* Green - Cermak-McCormick Place
    * Ashland/63rd & Cottage Grove bound
    * Harlem/Lake bound
* Orange - Halsted
    * Loop bound
    * Midway bound
* Pink - Damen
    * Loop bound
    * 54th/Cermak bound
* Purple - Main
    * Linden bound
    * Howard & Loop bound
* Red - Grand/State
    * Howard bound
    * 95th bound
* Yellow - Oakton-Skokie
    * Dempster-Skokie bound
    * Howard bound

## Equipment
* I use a Google Cloud Compute E2 Micro to run the program 24/7, however the program can be run on theoretically anything capable of running Python scripts.

## Installation
* Create API access token on the [CTA Transit Tracker developer site](https://www.transitchicago.com/developers/traintracker/) 
* Clone the repository on your endpoint of choice with the following `git clone https://github.com/brandonmcfadd/cta-reliability.git`
* Change into the working directory of the cloned repository `cd cta-reliability`
* Install the required dependencies `pip install -r requirements.txt`

## Configuration
* Enable the portions you want to use by changing False to True in the `settings.json` file
* To change the station being monitored modify the Station/Stop Information `map-ids` in the `settings.json` file with the station code(s) you want to use. 
* 'L' Station codes can be found on the following [site](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme) from the City of Chicago's Data Portal.

## Enviornment File
* You'll need to create a .env file in your directory to safely store your secrets.
    * Don't forget to add your .env file to your .gitignore list and never check application secrets, usernames or passwords into a GitHub repo! 
* The following entries are required in your .env file:
    * CTA
        ```
        TRAIN_API_KEY = 'insert key here'
        FILE_PATH = 'full file path/cta-reliability'
        ```
    * Metra
        ```
        METRA_USERNAME = 'metra username'
        METRA_PASSWORD = 'metra password'
        ```

## Running the program
* Once you have everything [Installed](#Installation) and [Configured](#Configuration) Run the main program `python3 main.py`

## Power Bi Report
* You can view the PowerBi Report displaying the data I have collected at:<br>[brandonmcfadden.com/cta-reliability](https://brandonmcfadden.com/cta-reliability)