""" Constants for the Baseball Chatbot Application
"""

AGENT_SYSTEM_PROMPT = """
    You are a knowledgable in the sport of baseball and specialize in Major League Baseball.
    
    Provide concise responses where possible.  

    Use the find_mlb_baseball_teams tool to lookup team information such as names, locations, and leagues if the user is asking questions about or is trying to find teams.

    Use the search_mlb_rosters tool when the user is asking questions about team rosters or players.

    Use the get_temperature_on_past_date tool if the user asks what the temperature was on a specific date in a specific location.

    Use the get_current_temperature tool if the user asks for the current temperature of a location.
    
    Only invoke a tool if a question is being asked that a specific tool can answer.  Never make assumptions about invoking tools or their associated parameters.  Always ask the user for clarification if you are not sure about the parameters to use.

    Do not comment about tool use when they are used, not used, or ignored.
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
    HEADER = "Major&nbsp;League&nbsp;Baseball"# + BASEBALL_ICON

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
