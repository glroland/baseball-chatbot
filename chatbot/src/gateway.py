import os
import logging
from typing import List

logger = logging.getLogger(__name__)

ENV_DEFAULT_MODEL = "DEFAULT_MODEL"

class Gateway:

    model_name = None

    def get_selected_model(self) -> str:
        """ Gets the name of the selected model.
        
            Returns: selected model
        """
        if self.model_name is None:
            self.model_name = self.get_preferred_default_model()
        return self.model_name
    
    def get_models(self) -> List[str]:
        """ Gets all models available from the service provider.
        
            Returns: List of models
        """
        msg = "get_models() is not implemented!"
        logger.error(msg)
        raise NotImplementedError(msg)

    def get_preferred_default_model(self) -> str:
        """ Gets the preferred model to use as the default from the provider.

            Returns: preferred default model to use
        """
        msg = "get_preferred_default_model() is not implemented!"
        logger.error(msg)
        raise NotImplementedError(msg)

    def connect(self):
        """ Connects to the remote service provider. """
        msg = "connect() is not implemented!"
        logger.error(msg)
        raise NotImplementedError(msg)

    def get_default_model(self, all_models: List[str] = None) -> str:
        """ Gets the configured default model to use.
        
            all_models - list of all models (optional)

            Returns: default model
        """
        default_model = None
        if not ENV_DEFAULT_MODEL in os.environ:
            logger.warning("Default model has not been set via environment variable.")
            if all_models is not None and len(all_models) > 0:
                preferred_default_model = self.get_preferred_default_model()
                if preferred_default_model in all_models:
                    default_model = preferred_default_model
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

    def on_model_change(self, new_model_name: str):
        """ Called in the event of a model change.

            new_model_name - new model name
        """
        logger.info("Selected model change.")
        self.model_name = new_model_name
