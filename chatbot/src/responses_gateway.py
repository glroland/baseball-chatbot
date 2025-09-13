"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
import streamlit as st
from typing import List
from openai import OpenAI
from gateway import Gateway
from constants import AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ResponsesGateway(Gateway):

    ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
    ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
    ENV_DEFAULT_MODEL = "DEFAULT_MODEL"

    PREFERRED_DEFAULT_MODEL = "openai/gpt-4"

    openai_client : OpenAI
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

        return response_list


    def get_preferred_default_model(self) -> str:
        """ Gets the preferred model to use as the default from the provider.
        
            Returns: preferred default model to use
        """
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

        # get the api key
        if not self.ENV_OPENAI_API_KEY in os.environ:
            msg = "OpenAI API Key is a required environment variable.  'OPENAI_API_KEY' missing."
            logger.error(msg)
            raise ValueError(msg)
        openai_api_key = os.environ[self.ENV_OPENAI_API_KEY]
        logger.info("OpenAI API Key: %s", openai_api_key)

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
        # Employ OpenAI Responses AI
        response_stream = self.openai_client.responses.create(
            model=self.get_selected_model(),
            instructions=AGENT_SYSTEM_PROMPT,
            input=user_input,
            tools=[
                {
                    "type": "mcp",
                    "server_label": "mcp::agent-team",
                    "server_url": "https://baseball-chatbot-agent-team-baseball-chatbot.apps.ocp.home.glroland.com/sse",
                    "require_approval": "never"
                },
                {
                    "type": "mcp",
                    "server_label": "mcp::agent-game",
                    "server_url": "https://baseball-chatbot-agent-game-baseball-chatbot.apps.ocp.home.glroland.com/sse",
                    "require_approval": "never"
                },
                {
                    "type": "mcp",
                    "server_label": "mcp::agent-utilities",
                    "server_url": "https://baseball-chatbot-agent-utilities-baseball-chatbot.apps.ocp.home.glroland.com/sse",
    #                "allowed_tools": ["get_current_temperature", "get_temperature_on_past_date"],
                    "require_approval": "never"
                },
            ],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True,
            previous_response_id=self.previous_response_id,
            parallel_tool_calls=True,
            stream=True
        )

        # Capture response
        ai_response = ""
        for event in response_stream:
            if hasattr(event, "type") and "text.delta" in event.type:
                ai_response += event.delta
                print(event.delta, end="", flush=True)
                with placeholder.container():
                    st.write(ai_response)
            elif hasattr(event, "type") and "response.completed" in event.type:
                self.previous_response_id = event.response.id

        return ai_response
