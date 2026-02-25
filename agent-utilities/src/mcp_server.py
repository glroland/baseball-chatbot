import os
import logging
import dateparser
from datetime import timedelta, datetime
import uvicorn
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastmcp import FastMCP
from starlette.responses import JSONResponse
from geopy.geocoders import Nominatim
import openmeteo_requests
import requests_cache
from retry_requests import retry

# configurable parameters
ENV_MCP_PORT = "MCP_PORT"
ENV_LOG_LEVEL = "LOG_LEVEL"

# setup MCP server
mcp_port = 8080
if ENV_MCP_PORT in os.environ:
    mcp_port = int(os.environ[ENV_MCP_PORT])

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Start MCP Server
mcp = FastMCP(name="Utilities MCP Server")
mcp_asgi_app = mcp.http_app(path="/", stateless_http=True)

# Create FastAPI application
app = FastAPI(lifespan=mcp_asgi_app.lifespan)
app.mount("/mcp", mcp_asgi_app)
FastAPIInstrumentor.instrument_app(app)

@mcp.tool(
    annotations={
        "title": "Lookup a Past Temperature",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_temperature_on_past_date(location: str, date: str = None) -> float:
    """ Gets the temperature for the provided location on the specified date.

    :param location: Location
    :param date: Date in which to pull the weather (optional)
    :returns: Temperature as of the provided date
    """
    logger.info ("Getting temperature.  Location=%s Date=%s", location, date)

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
    geolocator = Nominatim(user_agent="agent-utilities")
    geo_location = geolocator.geocode(location)
    latitude = geo_location.latitude
    longitude = geo_location.longitude
    logger.info("Location %s has a latitude, longitude position of %s, %s", location, latitude, longitude)

    # Setup the Open-Meteo API client with cache and retry on error
    logger.debug("Setting up cache and retries for weather.")
    cache_session = requests_cache.CachedSession('.weather-cache',
                                                 expire_after = timedelta(hours=1),
                                                 use_temp=True)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # get temperature for date
    logger.info("Getting Temperature for %s as of %s", location, date)
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
        "title": "Get the Current Temperature",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_current_temperature(location: str) -> float:
    """ Gets the temperature for the provided location on the specified date.

    :param location: Location
    :returns: Current weather / temperature
    """
    logger.info ("Getting current temperature for location.  Location=%s", location)

    # validate parameters
    if location is None or len(location) == 0:
        msg = "Location is required but is empty!"
        logger.error(msg)
        raise ValueError(msg)

    # get latitude and longitude for location
    geolocator = Nominatim(user_agent="agent-utilities")
    geo_location = geolocator.geocode(location)
    latitude = geo_location.latitude
    longitude = geo_location.longitude
    logger.info("Location %s has a latitude, longitude position of %s, %s", location, latitude, longitude)

    # Setup the Open-Meteo API client with cache and retry on error
    logger.debug("Setting up cache and retries for weather.")
    cache_session = requests_cache.CachedSession('.weather-cache',
                                                 expire_after = timedelta(hours=1),
                                                 use_temp=True)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # get current temperature
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

@mcp.tool(
    annotations={
        "title": "Get the Current Date and Time",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_current_date_and_time() -> datetime:
    """ Gets the current date and time.
    """
    logger.info ("Getting current date and time.")

    # Return current date and time
    current_date_and_time = datetime.now()

    logger.info("Current Date and Time: %s", current_date_and_time)
    print ("Current Date and Time is ", current_date_and_time)
    return current_date_and_time

@app.get("/health")
async def health_check():
    """ Health check endpoint for the MCP Server. """
    return JSONResponse({"status": "ok"})

if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])
    print ("Port: ", port)

    print ("Testing get_current_temperature...")
    print (get_current_temperature(location="Atlanta"))
    print ()

    print ("Testing get_temperature_on_past_date....")
    print (get_temperature_on_past_date(location="Atlanta", date="2-1-2025"))
    print ()

    print ("Testing get_current_date_and_time...")
    print (get_current_date_and_time())
    print ()

    log_level = "info"
    if ENV_LOG_LEVEL in os.environ:
        log_level = os.environ[ENV_LOG_LEVEL]
    print ("Log Level: ", log_level)

    print ("Starting MCP Server...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=log_level)
