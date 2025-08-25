"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
import streamlit as st
from typing import List
from llama_stack_client import LlamaStackClient, Agent, BaseModel
from llama_stack_client.types.shared_params.agent_config import ToolConfig, AgentConfig
from llama_stack_client.types.shared_params.sampling_params import SamplingParams
from gateway import Gateway
from constants import AGENT_SYSTEM_PROMPT
from tools import BASEBALL_CHAT_AGENTS

logger = logging.getLogger(__name__)

class LLamaStackGateway(Gateway):

    ENV_LLAMA_STACK_URL = "LLAMA_STACK_URL"

    PREFERRED_DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

    llama_stack_client = None
    llama_stack_agent = None
    session_id = None

    def get_models(self) -> List[str]:
        """ Gets all models available from the service provider.
        
            Returns: List of models
        """
        lls_models = self.llama_stack_client.models.list()

        response_list = []
        for model in lls_models:
            print (model)
            if model.api_model_type == "llm":
                response_list.append(model.identifier)
        return response_list


    def get_preferred_default_model(self) -> str:
        """ Gets the preferred model to use as the default from the provider.
        
            Returns: preferred default model to use
        """
        return self.PREFERRED_DEFAULT_MODEL


    def on_model_change(self, new_model_name: str):
        """ Called in the event of a model change.
        
            new_model_name - new model name
        """
        super().on_model_change(new_model_name)


    def process_user_chat(self, user_input: str, placeholder) -> str:
        """ Process a chat request.
        
            user_input - user message
            placeholder - streamlit placeholder
            
            Returns: Chat response
        """
        # Invoke Backend API
        response = self.llama_stack_agent.create_turn(
            session_id=self.session_id,
            messages=[{"role":"user", "content": user_input}],
            stream=True
        )

        # Capture streaming response
        ai_response = ""
        st.write_stream(self.lls_streaming_turn_response_generator(response))


    def connect(self):
        """ Connects to the remote service provider. """
        # get backend details
        if not self.ENV_LLAMA_STACK_URL in os.environ:
            msg = "LLama Stack URL is a required environment variable.  'LLAMA_STACK_URL' missing."
            logger.error(msg)
            raise ValueError(msg)
        llama_stack_url = os.environ[self.ENV_LLAMA_STACK_URL]
        logger.info("LLama Stack URL: %s", llama_stack_url)

        # connect to backend
        logger.info("Connecting...")
        self.llama_stack_client = LlamaStackClient(
            base_url=llama_stack_url,
        )
        logger.info("Connected!")

        # Create the agent
        logger.info("Creating agent...")
        sampling_params = SamplingParams(max_tokens=1000,
    #                                    repetition_penalty=1.1,
                                        strategy={
                                            "type": "top_p",
                                            "temperature": 0.1,
                                            "top_p": 0.1
                                        })
        agent_config = AgentConfig(tool_choice="auto",
                                tool_config=ToolConfig(tool_choice = "auto"),
                                toolgroups=BASEBALL_CHAT_AGENTS,
                                model=self.get_selected_model(),
                                instructions=AGENT_SYSTEM_PROMPT,
                                enable_session_persistence=True,
                                sampling_params=sampling_params,
                                max_infer_iters=10)

        self.llama_stack_agent = Agent(
            self.llama_stack_client,
            agent_config=agent_config,
        )
        logger.info("Agent Created.")

        # Create a session
        logger.info("Starting new session.")
        self.session_id = self.llama_stack_agent.create_session(session_name="My Conversation")
        logger.info("Session Created.  Session ID=%s", self.session_id)


    def lls_streaming_turn_response_generator(self, turn_response):
        for response in turn_response:
            if hasattr(response.event, "payload"):
    #            print("PAYLOAD:", response.event.payload)
                if response.event.payload.event_type == "step_progress":
                    if hasattr(response.event.payload.delta, "text"):
                        yield response.event.payload.delta.text
                if response.event.payload.event_type == "step_complete":
                    if response.event.payload.step_details.step_type == "tool_execution":
                        if response.event.payload.step_details.tool_calls:
                            tool_name = str(response.event.payload.step_details.tool_calls[0].tool_name)
                            yield f'\n\n🛠 :grey[_Using "{tool_name}" tool:_]\n\n'
                        else:
                            yield "No tool_calls present in step_details"
            else:
                yield f"Error occurred in the Llama Stack Cluster: {response}"
