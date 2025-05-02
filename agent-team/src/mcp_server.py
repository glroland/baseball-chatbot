import os
import logging
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
import uvicorn
import psycopg

# Setup Logging
logger = logging.getLogger(__name__)

ENV_DB_CONNECTION_STRING = "DB_CONNECTION_STRING"
ENV_MCP_PORT = "MCP_PORT"

mcp = FastMCP("MLB Baseball Teams MCP Server")

@mcp.tool(
    annotations={
        "title": "Search for a Major League Baseball team using the information provided.  At least one field must be provided.",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def find_mlb_baseball_teams(team_name:str = None, city:str = None, year:int = None, league:str = None) -> List[Dict[str, Any]]:
    """ Gets information about a major leage baseball team using the provided search criteria.

    At least one search parameter must be provided.

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
        sql += f"upper(leage) = upper('{league_code}') "
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
                    "Team Code": record[1],
                    "League": league,
                    "Location": record[3],
                    "Name": record[4]
                }
                results.append(result)
    
    logger.debug("Results: %s", results)
    print ("Results", results)

    return results


if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])

    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=port)
