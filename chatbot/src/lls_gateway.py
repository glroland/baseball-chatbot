"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
from typing import Tuple, List
from llama_stack_client import LlamaStackClient, Agent, BaseModel
from llama_stack_client.types.shared_params.agent_config import ToolConfig, AgentConfig
from llama_stack_client.types.shared_params.sampling_params import SamplingParams

logger = logging.getLogger(__name__)

ENV_LLAMA_STACK_URL = "LLAMA_STACK_URL"
ENV_LLAMA_STACK_MODEL = "LLAMA_STACK_MODEL"

def get_all_lls_model_names(llama_stack_client : LlamaStackClient) -> List[str]:
    """ Gets a list of all configured models available in the LLama Stack runtime.

        llama_stack_client - llama stack client instance

        Returns: list of model names
    """
    lls_models = llama_stack_client.models.list()

    response_list = []
    for model in lls_models:
        print (model)
        if model.api_model_type == "llm":
            response_list.append(model.identifier)
    return response_list

def get_lls_model_name() -> str:
    """ Gets the configured LLama Stack model name to use.
    
        Returns Model Name
    """
    if not ENV_LLAMA_STACK_MODEL in os.environ:
        raise ValueError("LLama Stack Model is a required environment variable.  'LLAMA_STACK_MODEL' missing.")
    llama_stack_model_name = os.environ[ENV_LLAMA_STACK_MODEL]
    if llama_stack_model_name is None:
        raise ValueError ("LLama Stack Model is a required environment variable.  'LLAMA_STACK_MODEL' is None.")
    llama_stack_model_name = llama_stack_model_name.strip()
    if len(llama_stack_model_name) == 0:
        raise ValueError ("LLama Stack Model is a required environment variable.  'LLAMA_STACK_MODEL' an empty string.")
    return llama_stack_model_name

def lls_connect() -> Tuple[LlamaStackClient, BaseModel]:
    """ Connects to the LLama Stack Backend.
    
    Returns client and reference to requested model
    """
    # get backend details
    if not ENV_LLAMA_STACK_URL in os.environ:
        raise ValueError("LLama Stack URL is a required environment variable.  'LLAMA_STACK_URL' missing.")
    llama_stack_url = os.environ[ENV_LLAMA_STACK_URL]
    logger.info("LLama Stack URL: %s", llama_stack_url)

    # connect to backend
    logger.info("Connecting...")
    llama_stack_client = LlamaStackClient(
        base_url=llama_stack_url,
    )
    logger.info("Connected!")

    # get model details
    llama_stack_model_name = get_lls_model_name()
    logger.info("LLama Stack Model: %s", llama_stack_model_name)

    # find model matching name
    logger.info ("Finding Requested LLama Model...")
    llama_stack_model = None
    for model in llama_stack_client.models.list():
        if model.identifier == llama_stack_model_name:
            llama_stack_model = model
            break
    if llama_stack_model is None:
        raise ValueError(f"Model Not Found!  name={llama_stack_model_name}")

    return llama_stack_client, llama_stack_model

def lls_create_agent(llama_stack_client : LlamaStackClient,
                     model_name : str,
                     prompt : str,
                     tools_list : List[str]) -> Agent:
    """ Creates an Agent with access to the provided tools.
    
        Returns reference to new agent
    """
    # validate arguments
    if llama_stack_client is None:
        raise ValueError("llama_stack_client is required and cannot be empty.")
    if prompt is None or len(prompt) == 0:
        raise ValueError("prompt is required and cannot be empty.")
    if model_name is None or len(model_name) == 0:
        raise ValueError("model_name is required and cannot be empty")

    # get configuration
    if llama_stack_client is None:
        logger.warning("tools_list is None instead of an empty array")
        llama_stack_client = []

    # Create the agent
    logger.info("Creating agent...")
    sampling_params = SamplingParams(max_tokens=1000,
                                    repetition_penalty=1.1,
                                    strategy={
                                        "type": "top_p",
                                        "temperature": 0.1,
                                        "top_p": 0.1
                                    })
    agent_config = AgentConfig(tool_choice="auto",
                               tool_config=ToolConfig(tool_choice = "auto"),
                               toolgroups=tools_list,
                               model=model_name,
                               instructions=prompt,
                               enable_session_persistence=True,
                               sampling_params=sampling_params,
                               max_infer_iters=10)

    llama_stack_agent = Agent(
        llama_stack_client,
        agent_config=agent_config,
    )
    logger.info("Agent Created.")

    return llama_stack_agent


def lls_new_session(llama_stack_agent : Agent, session_name : str = "My conversation"):
    """ Creates a new user session within the agent.

        llama_stack_agent - LLama Stack Agent
    """

    # Create a session
    logger.info("Starting new session.  Session Name = %s", session_name)
    session_id = llama_stack_agent.create_session(session_name=session_name)
    logger.info("Session Created.  Session ID=%s", session_id)

    return session_id

def lls_streaming_turn_response_generator(turn_response):
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
