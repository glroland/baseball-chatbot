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


@mcp.tool(
    annotations={
        "title": "Get game details such as weather, score and number of plays for individiaul games matching the search parameters",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def search_mlb_games(year:int,
                     team_name_1:str,
                     team_name_2:str = None,
                     month:int = None,
                     day:int = None) -> List[Dict[str, Any]]:
    """ Search for individual Major League Baseball games matching the provided search parameters.

    At least one search parameter must be provided.

    No assumptions should be made about the year.  Do not call the tool in the event a year cannot be provided.

    :param year: Season in which to search for (required)
    :param team_name_1: Name of the first team to match (required)
    :param team_name_2: Name of the second team to match (optional)
    :param month: Month when the game occurred (optional)
    :param day: Day of month when the game occurred (optional)
    :returns: List of dictionaries containing attributes of matching games
    """
    logger.info ("Performing Game Search.  Year=%s TeamName1=%s TeamName2=%s Month=%s Day=%s", year, team_name_1, team_name_2, month, day)

    # validate parameters
    if year is None or year <= 2000 or year > 2024:
        logger.error("Illegal value for year: %s", year)
        raise ValueError(f"Illegal value for year: {year}")
    if team_name_1 is None or len(team_name_1) == 0:
        logger.error("Illegal value for team_name_1: %s", team_name_1)
        raise ValueError(f"Illegal value for team_name_1: {team_name_1}")
    if team_name_2 is not None and len(team_name_2) == 0:
        team_name_2 = None
    if month is not None and (month < 1 or month > 12):
        logger.error("Illegal value for month: %s", month)
        raise ValueError(f"Illegal value for month: {month}")
    if day is not None and (day < 1 or day > 31):
        logger.error("Illegal value for day: %s", day)
        raise ValueError(f"Illegal value for day: {day}")

    # build query
    sql = """
        select game_id, game_date, game_time,
            t_home.team_code t_home_code, t_home.team_location t_home_location, t_home.team_name t_home_name,
            t_visitor.team_code t_visitor_code, t_visitor.team_location t_visitor_location, t_visitor.team_name t_visitor_name,
            score_visitor, score_home,
            night_flag, temperature, sky,
            (select count(*) from game_play where game_play.game_id = game.game_id) num_plays
        from game, team t_home, team t_visitor
        where game.team_home = t_home.team_code
        and date_part('year', game_date) = t_home.season_year
        and game.team_visiting = t_visitor.team_code
        and date_part('year', game_date) = t_visitor.season_year
        and (game.team_home = 'ATL' or game.team_visiting = 'ATL')
        and date_part('year', game_date) >= 2010
        order by game_date desc
        """
    if team_name is not None and len(team_name) > 0:
        sql += f"""
            and (
                upper(team_name) like upper('%{team_name}%')
                or
                upper('%{team_name}%') like '%' || upper(team_location) || '%' || upper(team_name) || '%'
                )
                """
    if year is not None:
        sql += f"and roster.season_year = {year} "
    if position is not None and len(position) > 0:
        sql += f"and upper(field_pos_desc) like upper('%{position}%') "
    if name is not None and len(name) > 0:
        sql += f"""
            and (
                upper('{name}') like '%' || upper(first_name) || '%' || upper(last_name) || '%'
                or
                upper('{name}') like '%' || upper(last_name) || '%'
                )
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
                season = record[0]
                team_name = record[1]
                first_name = record[2]
                last_name = record[3]
                field_pos_desc = record[4]
                throw_hand_code = record[5]
                batting_hand_code = record[6]

                # convert hand codes to descriptions
                throw_hand = convert_hand_code_to_description(throw_hand_code)
                batting_hand = convert_hand_code_to_description(batting_hand_code)

                result = {
                    "Season": season,
                    "Team": team_name,
                    "Name": first_name + " " + last_name,
                    "Position": field_pos_desc,
                    "Throwing Hand": throw_hand,
                    "Batting Hand": batting_hand
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
