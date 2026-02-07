"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
import requests
import streamlit as st
from typing import List
from openai import OpenAI
from gateway import Gateway
from constants import AGENT_SYSTEM_PROMPT, Tools

logger = logging.getLogger(__name__)

class ResponsesGateway(Gateway):

    ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
    ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
    ENV_DEFAULT_MODEL = "DEFAULT_MODEL"
    ENV_AGENT_UTILITIES_URL = "AGENT_UTILITIES_URL"
    ENV_AGENT_TEAM_URL = "AGENT_TEAM_URL"
    ENV_AGENT_GAME_URL = "AGENT_GAME_URL"

    PREFERRED_DEFAULT_MODEL = "openai/gpt-4"

    openai_client : OpenAI
    openai_base_url : str
    openai_api_key : str
    previous_response_id = None

    def get_models(self) -> List[str]:
        """ Gets all models available from the service provider.
        
            Returns: List of models
        """
        models = self.openai_client.models.list()
        logger.info("All Registered Models: %s", models)

        response_list = []
        for model in models:
            response_list.append(model.id)
        response_list.sort()
        logger.info("Model List: %s", response_list)

        return response_list


    def get_preferred_default_model(self) -> str:
        """ Gets the preferred model to use as the default from the provider.
        
            Returns: preferred default model to use
        """
        if self.ENV_DEFAULT_MODEL in os.environ and len(os.environ[self.ENV_DEFAULT_MODEL]) > 0:
            return os.environ[self.ENV_DEFAULT_MODEL]

        return self.PREFERRED_DEFAULT_MODEL


    def connect(self):
        """ Connects to the remote service provider. """
        # get the base url
        openai_base_url = None
        if not self.ENV_OPENAI_BASE_URL in os.environ:
            logger.warning("OpenAI Endpoint has not been set.  Using OpenAI directly.")
        else:
            openai_base_url = os.environ[self.ENV_OPENAI_BASE_URL]
            logger.info("OpenAI Compatible Endpoint URL: %s", openai_base_url)
        self.openai_base_url = openai_base_url

        # get the api key
        if not self.ENV_OPENAI_API_KEY in os.environ:
            msg = "OpenAI API Key is a required environment variable.  'OPENAI_API_KEY' missing."
            logger.error(msg)
            raise ValueError(msg)
        openai_api_key = os.environ[self.ENV_OPENAI_API_KEY]
        logger.info("OpenAI API Key: %s", openai_api_key)
        self.openai_api_key = openai_api_key

        # create client connection
        logger.info("Initializing OpenAI Client")
        openai_client = OpenAI(base_url = openai_base_url,
                            api_key = openai_api_key)
        logger.info("OpenAI Initialized")

        self.openai_client = openai_client


    def on_model_change(self, new_model_name: str):
        """ Called in the event of a model change.
        
            new_model_name - new model name
        """
        super().on_model_change(new_model_name)
        self.previous_response_id = None


    def process_user_chat(self, user_input: str, placeholder) -> str:
        """ Process a chat request.
        
            user_input - user message
            placeholder - streamlit placeholder
            
            Returns: Chat response
        """
        # see if the environment variables were set for the mcp endpoints
        mcp_utilities_url = None
        if self.ENV_AGENT_UTILITIES_URL in os.environ:
            mcp_utilities_url = os.environ[self.ENV_AGENT_UTILITIES_URL]
        mcp_team_url = None
        if self.ENV_AGENT_TEAM_URL in os.environ:
            mcp_team_url = os.environ[self.ENV_AGENT_TEAM_URL]
        mcp_game_url = None
        if self.ENV_AGENT_GAME_URL in os.environ:
            mcp_game_url = os.environ[self.ENV_AGENT_GAME_URL]
        mcp_list = []
        if mcp_utilities_url is not None and len(mcp_utilities_url) > 0 and \
           mcp_team_url is not None and len(mcp_team_url) > 0 and \
           mcp_game_url is not None and len(mcp_game_url) > 0:
            logger.info("MCP Servers provided with ENV Variables.  Adding manually...")

            # create mcp server entry - utilities
            mcp_server_utilities = {
                "type": "mcp",
                "server_label": Tools.BASEBALL_AGENT_UTILITIES,
                "server_url": mcp_utilities_url,
                "require_approval": "never"
            }
            mcp_list.append(mcp_server_utilities)

            # create mcp server entry - team
            mcp_server_team = {
                "type": "mcp",
                "server_label": Tools.BASEBALL_AGENT_TEAM,
                "server_url": mcp_team_url,
                "require_approval": "never"
            }
            mcp_list.append(mcp_server_team)

            # create mcp server entry - game
            mcp_server_game = {
                "type": "mcp",
                "server_label": Tools.BASEBALL_AGENT_GAME,
                "server_url": mcp_game_url,
                "require_approval": "never"
            }
            mcp_list.append(mcp_server_game)
        else:
            logger.info("MCP Servers not provided with ENV variables.  Querying LLama Stack API")
            mcp_list = self.get_all_mcps_as_tools(Tools.ALL)
        logger.info("MCP Server List: %s", mcp_list)

        # Employ OpenAI Responses AI
        response_stream = self.openai_client.responses.create(
            model=self.get_selected_model(),
            instructions=AGENT_SYSTEM_PROMPT,
            input="Question:\n" + user_input,
            tools=mcp_list,
            temperature=0.3,
#            max_output_tokens=int(2048),
            store=True,
            previous_response_id=self.previous_response_id,
            parallel_tool_calls=True,
            stream=True,
        )

        # Capture response
        ai_response = ""
        for event in response_stream:
            logger.info("Event: %s", event)
            if hasattr(event, "type") and "text.delta" in event.type:
                ai_response += event.delta
                with placeholder.container():
                    st.write(ai_response)
            elif hasattr(event, "type") and "response.completed" in event.type:
                self.previous_response_id = event.response.id

        return ai_response


    def get_all_mcps_as_tools(self, match_list = None):
        """ Gets a list of registered mcp servers in the form of responses api tools.
        
            match_list = list of tools to match endpoints against

            Returns: list of mcp servers
        """
        mcp_server_list = []


        # make get request to toolgroups api
        http_response = requests.get(self.openai_base_url + "/toolgroups")
        http_response.raise_for_status()
        json_response = http_response.json()
        logger.info("JSON Response = %s", json_response)
        tool_groups = json_response["data"]
        for tool in tool_groups:
                logger.info("Tool: %s", tool)
                tool_type = tool["type"]
                tool_provider_id = tool["provider_id"]
                if tool_type is not None and tool_type == "tool_group" and\
                   tool_provider_id is not None and tool_provider_id == "model-context-protocol":
        
                    # gather attributes
                    #tool_id = tool["identifier"]
                    tool_provider_resource_id = tool["provider_resource_id"]

                    if match_list is None or len(match_list) == 0 or tool_provider_resource_id in match_list:
                        # gather url
                        tool_mcp_endpoint = tool["mcp_endpoint"]
                        tool_mcp_endpoint_uri = None
                        if tool_mcp_endpoint is not None:
                            tool_mcp_endpoint_uri = tool["mcp_endpoint"]["uri"]
                        if tool_mcp_endpoint_uri is None or len(tool_mcp_endpoint_uri) == 0:
                            logger.error("MCP Server found with empty URL.  %s", tool)
                        else:
                            # create mcp server entry
                            mcp_server = {
                                "type": "mcp",
                                "server_label": tool_provider_resource_id,
                                "server_url": tool_mcp_endpoint_uri,
                                "require_approval": "never"
                            }
                            mcp_server_list.append(mcp_server)
                    else:
                        logger.warning("Skipping Tool as it is not in match list: %s", tool)
                else:
                    logger.info("Skipping Tool as it is not an MCP server: %s", tool)

        logger.info("Resulting Tool List: %s", mcp_server_list)
        return mcp_server_list
