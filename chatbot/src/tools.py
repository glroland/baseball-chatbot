import os
import logging

ENV_AGENT_WEATHER_URL = "AGENT_WEATHER_URL"
ENV_AGENT_TEAM_URL = "AGENT_TEAM_URL"

BASEBALL_AGENT_TEAM = "agent-team"
BASEBALL_AGENT_WEATHER = "agent-weather"
BASEBALL_CHAT_AGENTS = [BASEBALL_AGENT_TEAM, BASEBALL_AGENT_WEATHER]

logger = logging.getLogger(__name__)

def register_mcp_tool(llama_stack_client, all_toolgroups, agent_name, agent_url):
    """ Registers the specified MCP Tool, provided that it isn't alraedy registered.
    
        llama_stack_client - LLama Stack Client
        all_toolgroups - list of all registered tool groups
        agent_name - name of agent to register
        agent_url - mcp endpoint of tool
    """
    # check to see if already registered
    for toolgroup in all_toolgroups:
        if toolgroup.identifier == agent_name:
            logger.warning("MCP Agent Already Registered!  Name=%s ToolGroup=%s", agent_name, toolgroup)

            # always unregister
            logger.warning("Unregistering existing tool before re-registering...  Name=%s", agent_name)
            llama_stack_client.toolgroups.unregister(toolgroup_id=agent_name)

    # register agent
    llama_stack_client.toolgroups.register(
        toolgroup_id=agent_name,
        provider_id="model-context-protocol",
        mcp_endpoint={"uri": agent_url},
    )

def setup_tools(llama_stack_client):
    """ Sets the required agents up in LLama Stack.
    """
    # Get configurable values
    if not ENV_AGENT_TEAM_URL in os.environ:
        msg = "Agent Team URL is required and cannot be empty!"
        logger.error(msg)
        raise ValueError(msg)
    agent_team_url = os.environ[ENV_AGENT_TEAM_URL]
    logger.info("Team Agent URL: %s", agent_team_url)
    if not ENV_AGENT_WEATHER_URL in os.environ:
        msg = "Agent Weather URL is required and cannot be empty!"
        logger.error(msg)
        raise ValueError(msg)
    agent_weather_url = os.environ[ENV_AGENT_WEATHER_URL]
    logger.info("Weather Agent URL: %s", agent_weather_url)

    # Get registered tool groups
    all_toolgroups = llama_stack_client.toolgroups.list()
    for toolgroup in all_toolgroups:
        print (toolgroup)

    # Register agents
    register_mcp_tool(llama_stack_client, all_toolgroups, BASEBALL_AGENT_TEAM, agent_team_url)
    register_mcp_tool(llama_stack_client, all_toolgroups, BASEBALL_AGENT_WEATHER, agent_weather_url)
