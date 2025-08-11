"""API Utilities

Utility functions related to connecting with the backend services supporting
the chatbot.
"""
import os
import logging
from typing import List
from openai import OpenAI

logger = logging.getLogger(__name__)

ENV_OPENAI_BASE_URL = "OPENAI_BASE_URL"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_DEFAULT_MODEL = "DEFAULT_MODEL"

PREFERRED_DEFAULT_MODEL = "openai/gpt-4"

def get_models(openai_client : OpenAI) -> List[str]:
    """ Gets a list of all configured models available.

        openai_client - openai client instance

        Returns: list of model names
    """
    models = openai_client.models.list()
    logger.info("All Registered Models: %s", models)

    response_list = []
    for model in models:
        response_list.append(model.id)
    response_list.sort()

    return response_list

def get_default_model(all_models: List[str] = None) -> str:
    """ Gets the configured default model to use.
    
        all_models - list of all models (optional)

    Returns: default model
    """
    default_model = None
    if not ENV_DEFAULT_MODEL in os.environ:
        logger.warning("Default model has not been set via environment variable.")
        if all_models is not None and len(all_models) > 0:
            if PREFERRED_DEFAULT_MODEL in all_models:
                default_model = PREFERRED_DEFAULT_MODEL
            else:
                default_model = all_models[0]
        else:
            msg = "Default model not set and all_models list is empty or not provided!"
            logger.error(msg)
            raise ValueError(msg)
    else:
        default_model = os.environ[ENV_DEFAULT_MODEL]
    logger.info("Default Model: %s", default_model)
    return default_model    

def openai_connect() -> OpenAI:
    """ Connects to an OpenAI compliant service.
    
    Returns OpenAI client
    """
    # get the base url
    openai_base_url = None
    if not ENV_OPENAI_BASE_URL in os.environ:
        logger.warning("OpenAI Endpoint has not been set.  Using OpenAI directly.")
    else:
        openai_base_url = os.environ[ENV_OPENAI_BASE_URL]
        logger.info("OpenAI Compatible Endpoint URL: %s", openai_base_url)

    # get the api key
    if not ENV_OPENAI_API_KEY in os.environ:
        msg = "OpenAI API Key is a required environment variable.  'OPENAI_API_KEY' missing."
        logger.error(msg)
        raise ValueError(msg)
    openai_api_key = os.environ[ENV_OPENAI_API_KEY]
    logger.info("OpenAI API Key: %s", openai_api_key)

    # create client connection
    logger.info("Initializing OpenAI Client")
    openai_client = OpenAI(base_url = openai_base_url,
                           api_key = openai_api_key)
    logger.info("OpenAI Initialized")

    return openai_client
