""" Constants for the Baseball Chatbot Application
"""

AGENT_SYSTEM_PROMPT = "You are a knowledgable in all things baseball and specialize in Major League Baseball specifically.  Provide concise responses where possible.  Tools should be used when relevant to the user prompt but can be ignored otherwise.  Do not comment about tool use when tools are ignored."

# pylint: disable=too-few-public-methods
class SessionStateVariables:
    """ Session State Variable Names """

    MESSAGES = "messages"
    SESSION_ID = "session_id"

# pylint: disable=too-few-public-methods
class AppUserInterfaceElements:
    """ Application UI Elements """

    TITLE = "MLB Chatbot"

    BASEBALL_ICON = "⚾"
    HEADER = BASEBALL_ICON + " MLB Chatbot " + BASEBALL_ICON

    TAB_ICON = "./assets/tab_icon.ico"

# pylint: disable=too-few-public-methods
class CannedGreetings:
    """ Preestablished Responses """

    INTRO = "Welcome to the Major League!!!  What may I help you with?"

class MessageAttributes:
    """ LLM APU Message Attributes """

    ROLE = "role"
    USER = "user"
    ASSISTANT = "assistant"
    CONTENT = "content"
