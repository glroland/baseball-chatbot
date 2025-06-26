import os
import logging
import re
from datetime import datetime
from typing import Dict, Any, List
from pprint import pprint
import psycopg
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
import pybaseball

# Setup Logging
logger = logging.getLogger(__name__)

ENV_DB_CONNECTION_STRING = "DB_CONNECTION_STRING"
ENV_MCP_PORT = "MCP_PORT"
ENV_LOG_LEVEL = "LOG_LEVEL"

mcp = FastMCP("MLB Games MCP Server")

@mcp.tool(
    annotations={
        "title": "Get the schedule and record for a baseball team in a season.",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def get_schedule_and_record(year:int, team_code:str) -> List[Dict[str, Any]]:
    """ Get the schedule and win/loss details for the MLB team identified by the provided
        3 letter team code and the provided season.
    
    Both fields must be provided.

    :param year: Baseball season
    :param team_code: 3 Letter Code for Team (ex. ATL is the Atlanta Braves)
    :returns: List of dictionaries containing team attributes
    """
    logger.info ("Performing Schedule and Record Lookup.  Year=%s TeamCode=%s", year, team_code)

    # validate parameters
    if team_code is None or year is None:
        logger.error("Both Team Code and Year are required fields.")
        raise ValueError("No parameters provided to get_schedule_and_record!")

    pybaseball_data = pybaseball.schedule_and_record(year, team_code)

    results = []

    for index, game in pybaseball_data.iterrows():

        # convert date string to a datetime object
        game_date_str = game["Date"].replace(" (1)", "").replace(" (2)", "")
        game_date = datetime.strptime(game_date_str, "%A, %b %d").replace(year=year)
        slim_game_date_str = game_date.strftime("%m-%d-%Y")

        # build the score string
        score_str = f"{game['R']:.0f}-{game['RA']:.0f}"

        result = {
            "Date": slim_game_date_str,
#            "Team": game["Tm"],
            "Opponent": game["Opp"],
            "Home/Away": game["Home_Away"],
            "Win/Loss": game["W/L"],
            "Score": score_str,
        }
        results.append(result)

    logger.debug("Results: %s", results)
    print ("Results", results)

    return results


sse_app = mcp.sse_app()

@sse_app.route("/health")
async def health_check(request):
    """ Health check endpoint for the MCP Server. """
    # check database connection
    db_connection_string = os.environ[ENV_DB_CONNECTION_STRING]
    with psycopg.connect(db_connection_string) as db_connection:
        with db_connection.cursor() as db_cursor:
            db_cursor.execute("select count(*) from field_pos")

    return JSONResponse({"status": "ok"})

#get_schedule_and_record(year=2023, team_code='ATL')

if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])
    print ("Port: ", port)

    log_level = "info"
    if ENV_LOG_LEVEL in os.environ:
        log_level = os.environ[ENV_LOG_LEVEL]
    print ("Log Level: ", log_level)

    uvicorn.run(sse_app, host="0.0.0.0", port=port, log_level=log_level)
