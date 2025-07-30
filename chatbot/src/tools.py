#import os
import logging

#ENV_AGENT_UTILITIES_URL = "AGENT_UTILITIES_URL"
#ENV_AGENT_TEAM_URL = "AGENT_TEAM_URL"
#ENV_AGENT_GAME_URL = "AGENT_GAME_URL"

BASEBALL_AGENT_TEAM = "mcp::agent-team"
BASEBALL_AGENT_UTILITIES = "mcp::agent-utilities"
BASEBALL_AGENT_GAME = "mcp::agent-game"
BASEBALL_CHAT_AGENTS = [BASEBALL_AGENT_TEAM, BASEBALL_AGENT_UTILITIES, BASEBALL_AGENT_GAME, "mcp::ansible-mcp"]

logger = logging.getLogger(__name__)

# def register_mcp_tool(llama_stack_client, all_toolgroups, agent_name, agent_url):
#     """ Registers the specified MCP Tool, provided that it isn't alraedy registered.
    
#         llama_stack_client - LLama Stack Client
#         all_toolgroups - list of all registered tool groups
#         agent_name - name of agent to register
#         agent_url - mcp endpoint of tool
#     """
#     # check to see if already registered
#     for toolgroup in all_toolgroups:
#         if toolgroup.identifier == agent_name:
#             logger.warning("MCP Agent Already Registered!  Name=%s ToolGroup=%s", agent_name, toolgroup)

#             # always unregister
#             logger.warning("Unregistering existing tool before re-registering...  Name=%s", agent_name)
#             llama_stack_client.toolgroups.unregister(toolgroup_id=agent_name)

#     # register agent
#     llama_stack_client.toolgroups.register(
#         toolgroup_id=agent_name,
#         provider_id="model-context-protocol",
#         mcp_endpoint={"uri": agent_url},
#     )

# def setup_tools(llama_stack_client):
#     """ Sets the required agents up in LLama Stack.
#     """
#     # Get configurable values
#     if not ENV_AGENT_TEAM_URL in os.environ:
#         msg = "Team Agent URL is required and cannot be empty!"
#         logger.error(msg)
#         raise ValueError(msg)
#     agent_team_url = os.environ[ENV_AGENT_TEAM_URL]
#     logger.info("Team Agent URL: %s", agent_team_url)
#     if not ENV_AGENT_GAME_URL in os.environ:
#         msg = "Game Agent URL is required and cannot be empty!"
#         logger.error(msg)
#         raise ValueError(msg)
#     agent_game_url = os.environ[ENV_AGENT_GAME_URL]
#     logger.info("Game Agent URL: %s", agent_game_url)
#     if not ENV_AGENT_UTILITIES_URL in os.environ:
#         msg = "Utilities Agent URL is required and cannot be empty!"
#         logger.error(msg)
#         raise ValueError(msg)
#     agent_utilities_url = os.environ[ENV_AGENT_UTILITIES_URL]
#     logger.info("Utilities Agent URL: %s", agent_utilities_url)

#     # Get registered tool groups
#     all_toolgroups = llama_stack_client.toolgroups.list()
#     for toolgroup in all_toolgroups:
#         print (toolgroup)

#     # Register agents
#     register_mcp_tool(llama_stack_client, all_toolgroups, BASEBALL_AGENT_TEAM, agent_team_url)
#     register_mcp_tool(llama_stack_client, all_toolgroups, BASEBALL_AGENT_GAME, agent_game_url)
#     register_mcp_tool(llama_stack_client, all_toolgroups, BASEBALL_AGENT_UTILITIES, agent_utilities_url)
