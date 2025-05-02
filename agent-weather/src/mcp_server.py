import os
import logging
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
import uvicorn
from geopy.geocoders import Nominatim
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup Logging
logger = logging.getLogger(__name__)

ENV_MCP_PORT = "MCP_PORT"

mcp = FastMCP("Weather MCP Server")

@mcp.tool(
    annotations={
        "title": "Get the weather for the provided date and location.",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_weather(location: str, date: str) -> float:
    """ Gets the weather for the provided location on the specified date.

    :param location: Location
    :param date: Date in which to pull the weather
    :returns: Temperature as of the date and time
    """
    logger.info ("Getting weather.  Location=%s Date=%s", location, date)

    # validate parameters
    if location is None or len(location) == 0:
        msg = "Location is required but is empty!"
        logger.error(msg)
        raise ValueError(msg)
    if date is None or len(date) == 0:
        msg = "Date is required but is empty!"
        logger.error(msg)
        raise ValueError(msg)

    # get latitude and longitude for location
    geolocator = Nominatim(user_agent="agent-weather")
    geo_location = geolocator.geocode(location)
    latitude = geo_location.latitude
    longitude = geo_location.longitude
    logger.info("Location %s has a latitude, longitude position of %s, %s", location, latitude, longitude)


    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date,
        "end_date": date,
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process hourly data. The order of variables needs to be the same as requested.
    response = responses[0]
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_dataframe = pd.DataFrame(data = hourly_data)
    print(hourly_dataframe)

    return hourly_temperature_2m[19]


if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])

    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=port)
