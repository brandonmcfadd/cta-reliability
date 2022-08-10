# Chicago Transit Authority ("CTA") Reliability Tracker

## Overview
This project (and associated PowerBi Report) was created to help provide insight and transparency into the current service levels of the Chicago Transit Authority ("CTA") rail network. Utilizing the CTA API and Train Tracker Map, it can be determined when a train arrives at a specific station along the line. Using this data, the number of arrivals can be determined and compared to the number scheduled via the GTFS feed of published schedules.

## Station Selection 

The station selected along each line is one where all trains, regardless of destination, will arrive. For example, Logan Square can capture Forest Park, UIC-Halsted and even runs that terminate at the Rosemont yard. Trains that operate around the loop and then return to their originating stations (Brown, Orange, Pink and Purple) have only one direction tracked. For trains that do not return to origin (Blue, Red, Green, and Yellow) tracking is done in both directions because these are considered separate trips. 

### The following stations were selected to monitor each of the 8 CTA Lines in operation:
* Blue | Logan Square - O'Hare bound
* Blue | Logan Square - Forest Park & UIC-Halsted bound
* Brown | Addison - Loop bound
* Green | California - Ashland/63rd & Cottage Grove bound
* Green | California - Harlem/Lake bound
* Orange | Halsted - Loop bound
* Pink | Polk - Loop bound
* Purple | South Boulevard - Howard & Loop bound
* Red | Grand/State - Howard bound
* Red | Grand/State - 95th bound
* Yellow | Oakton-Skokie - Dempster-Skokie bound
* Yellow | Oakton-Skokie - Howard bound

## Equipment
The project runs on a [Raspberry Pi 4b](https://shop.pimoroni.com/products/raspberry-pi-4?variant=39576373690451) and the display used is the [Waveshare 2.13inch e-Paper HAT](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT).

## Display Output
The display shows the following information when the program is running:
* Station or Stop Name - example(s) being "Logan Square"
* Line & Destination of the train - example(s) being "Blue to O'Hare" & "Blue to Forrest Park"
* The arrival time of the nearest trains or buses - example being "7min, 16min"

## Installation
* Create API access token on the [CTA Transit Tracker developer site](https://www.transitchicago.com/developers/traintracker/) 
* Create API access token on the [CTA Bus developer site](https://www.transitchicago.com/developers/bustracker/)
* Create API access token on the [Twitter developer site](https://developer.twitter.com/) (You will need a Bearer Token, specifically)
* * (You can opt to just use one, or a combination of different ones - but all three are recommended)
* Clone the repository on your Raspberry Pi with the following `git clone https://github.com/brandonmcfadd/ctapi.git`
* Change into the working directory of the cloned repository `cd ctapi`
* Install the required dependencies `pip install -r requirements.txt`
* Create a file named `.env` in your directory with the following content
    <br>`TRAIN_API_KEY = 'YOUR_TRANSIT_API_KEY'`
    <br>`BUS_API_KEY = 'YOUR_TRANSIT_API_KEY'`
    <br>`HOME_LATITUDE = 'Enter your Latitude'`
    <br>`HOME_LONGITUDE = 'Enter your Longitude'`
    <br>`TWITTER_API_KEY = 'Bearer {Enter Your Key}'`
* Enable the portions you want to use by changing False to True on the following lines:
* * Train Tracker = Line 48
* * Bus Tracker = Line 52
* * Divvy Tracker = Line 58
* * Tweet Lookup = Line 62
* Run the main program `python3 main.py`

## Configuration
* To change the station being displayed modify the Station/Stop Information in `main.py` with the station code(s) you want to use. `Line 49, 52 and 55`
* 'L' Station codes can be found on the following [site](https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme) from the City of Chicago's Data Portal.
* Bus Stop Codes can be found using the [API](https://www.transitchicago.com/assets/1/6/cta_Bus_Tracker_API_Developer_Guide_and_Documentation_20160929.pdf) or via the Route Information Page on the Transit Chicago [site](https://www.transitchicago.com/schedules/)
* Divvy Station Codes can be found using the following [site](https://gbfs.divvybikes.com/gbfs/en/station_information.json)

## Example
![ctapi](./images/IMG_2378.jpg)
![ctapi](./images/IMG_2379.jpg)