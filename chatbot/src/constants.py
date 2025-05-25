""" Constants for the Baseball Chatbot Application
"""

AGENT_SYSTEM_PROMPT = """
    You are a knowledgable in the sport of baseball and specialize in Major League Baseball.
    
    Provide concise responses where possible.  
    
    Tools should be used only when directly relevant to the user prompt and always ignored otherwise.  Do not comment about tool use when tools are ignored.

    Use the temperature tools to get current and past temperatures for locations with MLB stadiums.

    Use the team tools to get information about MLB teams and rosters.
                      """

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
