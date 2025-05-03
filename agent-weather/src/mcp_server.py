import os
import logging
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from geopy.geocoders import Nominatim
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import dateparser
from datetime import datetime
import uvicorn

# configurable parameters
ENV_MCP_PORT = "MCP_PORT"

# setup MCP server
mcp_port = 8080
if ENV_MCP_PORT in os.environ:
    mcp_port = int(os.environ[ENV_MCP_PORT])

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Start MCP Server
mcp = FastMCP(name="Weather MCP Server",
              instructions="Tool for getting the temperature or weather on a particular date in the provided location.  The date parameter is optional and defaults to today.",
              host="0.0.0.0",
              port=mcp_port)

def get_current_temp(openmeteo,
                     latitude,
                     longitude,
                     location) -> float:
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m",
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch"
    }
    logger.info("Invoking weather api...  %s", params)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process daily data
    current = response.Current()
    temp = current.Variables(0).Value()

    logger.info("Temp at %s is currently %s", location, temp)
    print ("Temp at", location, "is currently", temp)
    return temp

def get_historic_temp(openmeteo,
                      latitude,
                      longitude,
                      location,
                      date) -> float:
    # format date
    date_parsed = dateparser.parse(date)
    date_formatted_str = date_parsed.strftime("%Y-%m-%d")

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_formatted_str,
        "end_date": date_formatted_str,
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch"
    }
    logger.info("Invoking weather api...  %s", params)
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Process daily data
    daily = response.Daily()
    temp = daily.Variables(0).ValuesAsNumpy()[0]   # max temp

    logger.info("Temp at %s on %s is %s", location, date, temp)
    print ("Temp at", location, "on", date, "is", temp)
    return temp

@mcp.tool(
    annotations={
        "title": "Get the weather for the provided date and location.",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_weather(location: str, date: str = None) -> float:
    """ Gets the weather for the provided location on the specified date.

    :param location: Location
    :param date: Date in which to pull the weather (optional)
    :returns: Temperature as of the provided date
    """
    logger.info ("Getting weather.  Location=%s Date=%s", location, date)

    # validate parameters
    if location is None or len(location) == 0:
        msg = "Location is required but is empty!"
        logger.error(msg)
        raise ValueError(msg)

    # get latitude and longitude for location
    geolocator = Nominatim(user_agent="agent-weather")
    geo_location = geolocator.geocode(location)
    latitude = geo_location.latitude
    longitude = geo_location.longitude
    logger.info("Location %s has a latitude, longitude position of %s, %s", location, latitude, longitude)

    # Setup the Open-Meteo API client with cache and retry on error
    logger.debug("Setting up cache and retries for weather.")
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    temp = None

    # get current temperature
    if date is None or len(date) == 0:
        logger.info("Getting Current Temperature for %s", location)
        temp = get_current_temp(openmeteo,
                                latitude,
                                longitude,
                                location)
    else:

        logger.info("Getting Temperature for %s as of %s", location, date)
        temp = get_historic_temp(openmeteo,
                                 latitude,
                                 longitude,
                                 location,
                                 date)

    logger.debug("Resulting temp is %s", temp)
    return temp

#print (get_weather(location="Atlanta"))
#print (get_weather(location="Atlanta", date="2-1-2025"))

if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])

    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=port, log_level="trace")
