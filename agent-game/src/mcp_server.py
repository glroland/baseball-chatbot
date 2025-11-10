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

    pybaseball_data = None
    try:
        pybaseball_data = pybaseball.schedule_and_record(year, team_code)
    except ValueError as e:
        logger.error("Pybaseball threw and exception due to data input.  %s", e)
        return []

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


@mcp.tool(
    annotations={
        "title": "Get game details such as score and number of plays for individual games matching the search parameters",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def search_mlb_games(year:int,
                     team_code_1:str,
                     team_code_2:str = None) -> List[Dict[str, Any]]:
    """ Search for individual Major League Baseball games matching the provided search parameters.

    At least two search parameters must be provided.

    No assumptions should be made about the year.  Do not call the tool in the event a year cannot be provided.

    :param year: Season in which to search for (required)
    :param team_code_1: Three letter team code of the first team to match (required)
    :param team_code_2: Three letter team code of the second team to match (optional)
    :returns: List of dictionaries containing attributes of matching games
    """
    logger.info ("Performing Game Search.  Year=%s TeamName1=%s TeamName2=%s", year, team_code_1, team_code_2)

    # validate parameters
    if year is None or year <= 2000 or year > 2024:
        logger.error("Illegal value for year: %s", year)
        raise ValueError(f"Illegal value for year: {year}")
    if team_code_1 is None or len(team_code_1) != 3:
        logger.error("Illegal value for team_name_1: %s", team_code_1)
        raise ValueError(f"Illegal value for team_name_1: {team_code_1}")
    if team_code_2 is None:
        team_code_2 = team_code_1

    # build query
    sql = f"""
        select game_id, game_date, game_time,
            t_home.team_code t_home_code, t_home.team_location t_home_location, t_home.team_name t_home_name,
            t_visitor.team_code t_visitor_code, t_visitor.team_location t_visitor_location, t_visitor.team_name t_visitor_name,
            score_visitor, score_home,
            (select count(*) from game_play where game_play.game_id = game.game_id) num_plays
        from game, team t_home, team t_visitor
        where game.team_home = t_home.team_code
        and date_part('year', game_date) = t_home.season_year
        and game.team_visiting = t_visitor.team_code
        and date_part('year', game_date) = t_visitor.season_year
        and (game.team_home = '{team_code_1}' or game.team_visiting = '{team_code_1}')
        and (game.team_home = '{team_code_2}' or game.team_visiting = '{team_code_2}')
        and date_part('year', game_date) = {year}
        order by game_date desc
        """
    logger.debug ("Generated SQL for search - ", sql)
    print ("Generated SQL for search: ", sql)

    # get connection string
    if not ENV_DB_CONNECTION_STRING in os.environ:
        raise ValueError("Database Connection String is a required environment variable.  DB_CONNECTION_STRING not set.")
    db_connection_string = os.environ[ENV_DB_CONNECTION_STRING]

    results = []

    # connect to database
    with psycopg.connect(db_connection_string) as db_connection:
        with db_connection.cursor() as db_cursor:

            # execute the dynamically generated sql
            db_cursor.execute(sql)
            for record in db_cursor:
                # collect row data
                game_id = record[0]
                game_date = record[1]
                game_time = record[2]
                t_home_code = record[3]
                t_home_location = record[4]
                t_home_name = record[5]
                t_visitor_code = record[6]
                t_visitor_location = record[7]
                t_visitor_name = record[8]
                score_visitor = record[9]
                score_home = record[10]
                num_plays = record[11]

                result = {
                    "Visitors": t_visitor_code,
                    "Home": t_home_code,
                    "Score": f"{score_visitor}-{score_home}",
                    "Play Count": num_plays
                }
                results.append(result)
    
    logger.debug("Results: %s", results)
    pprint (results)

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

print(get_schedule_and_record(year=2023, team_code='NYY'))

print(search_mlb_games(2023, team_code_1="ATL", team_code_2="BOS"))

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
