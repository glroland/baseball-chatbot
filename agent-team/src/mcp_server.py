import os
import logging
from typing import Dict, Any, List
from pprint import pprint
import psycopg
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

# Setup Logging
logger = logging.getLogger(__name__)

ENV_DB_CONNECTION_STRING = "DB_CONNECTION_STRING"
ENV_MCP_PORT = "MCP_PORT"

mcp = FastMCP("MLB Baseball Teams MCP Server")

@mcp.tool(
    annotations={
        "title": "Search for Major League Baseball teams",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def find_mlb_baseball_teams(team_name:str = None, city:str = None, year:int = None, league:str = None) -> List[Dict[str, Any]]:
    """ Search for a Major League Baseball teams using the information provided.
    
    At least one field must be provided.  
    
    No assumptions should be made about the year.  Leave it blank when not explicitly provided by the user.

    :param team_name: Name of the team (optional)
    :param city: City name / location of the team (optional)
    :param year: Season in which to search for (optional)
    :param league: American or National League (optional)
    :returns: List of dictionaries containing team attributes
    """
    logger.info ("Performing Team Search.  TeamName=%s City=%s Year=%s League=%s", team_name, city, year, league)

    # validate parameters
    if team_name is None and city is None and year is None and league is None:
        logger.error("At least one search parameter must be specified.")
        raise ValueError("No search parameter specified!")

    # build query
    sql = "select season_year, team_code, league, team_location, team_name from team where "
    prev = False
    if team_name is not None and len(team_name) > 0:
        sql += f"upper(team_name) like upper('%{team_name}%') "
        prev = True
    if city is not None and len(city) > 0:
        if prev:
            sql += "and "
        prev = True
        sql += f"upper(team_location) like upper('%{city}%') "
    if year is not None:
        if prev:
            sql += "and "
        prev = True
        sql += f"season_year = {year} "
    if league is not None and len(league) > 0:
        if prev:
            sql += "and "
        prev = True
        league_code = league[0]
        sql += f"upper(league) = upper('{league_code}') "
    logger.debug ("Generated SQL for search - ", sql)

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
                league = record[2]
                if record[2] == "A":
                    league = "American League"
                elif record[2] == "N":
                    league = "National League"
                result = {
                    "Season": record[0],
                    "League": league,
                    "Location": record[3],
                    "Name": record[4]
                }
                results.append(result)
    
    logger.debug("Results: %s", results)
    print ("Results", results)

    return results


def convert_hand_code_to_description(hand_code):
    """ Convert the hand code to a description.
    :param hand_code: Hand code (L, R, B)
    :returns: Hand description (Left, Right, Both)
    """
    if hand_code == "L":
        return "Left"
    elif hand_code == "R":
        return "Right"
    elif hand_code == "B":
        return "Both"
    else:
        return "Unknown"


@mcp.tool(
    annotations={
        "title": "Search Major League Baseball team rosters",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def search_mlb_rosters(team_name:str = None,
                       year:int = None,
                       position:str = None,
                       name:str = None) -> List[Dict[str, Any]]:
    """ Search the Major League Baseball team rosters using the information provided.

    At least one search parameter must be provided.

    No assumptions should be made about the year.  Leave it blank when not explicitly provided by the user.

    :param team_name: Name of the team (optional)
    :param year: Season in which to search for (optional)
    :param position: Field position (optional)
    :param name: Player name (optional)
    :returns: List of dictionaries containing matching player attributes
    """
    logger.info ("Performing Roster Search.  TeamName=%s Year=%s Position=%s Name=%s", team_name, year, position, name)

    # validate parameters
    if team_name is None and year is None and position is None and name is None:
        logger.error("At least one search parameter must be specified.")
        raise ValueError("No search parameter specified!")

    # build query
    sql = """
        select roster.season_year, team_name, first_name, last_name, field_pos_desc, throw_hand, batting_hand
        from roster, team, field_pos
        where roster.team_code = team.team_code
        and roster.season_year = team.season_year
        and roster.position = field_pos.field_pos_cd
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
    """ Health check endpoint for the FastAPI app. """
    # check database connection
    db_connection_string = os.environ[ENV_DB_CONNECTION_STRING]
    with psycopg.connect(db_connection_string) as db_connection:
        with db_connection.cursor() as db_cursor:
            db_cursor.execute("select count(*) from field_pos")

    return JSONResponse({"status": "ok"})


#search_mlb_rosters(team_name='Braves', year=2023, position = "pitcher", name = "strider")
#search_mlb_rosters(team_name='Braves', year=2023, position = "pitcher", name = "spencer strider")
#search_mlb_rosters(team_name='Braves', year=None, position = None, name = "Ozuna")
#search_mlb_rosters(team_name='Atlanta Braves', year=None, position = None, name = "Ozuna")
#search_mlb_rosters(team_name=None, year=None, position = "Pitcher", name = "Chris Sale")


if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])

    uvicorn.run(sse_app, host="0.0.0.0", port=port)
