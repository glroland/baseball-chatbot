"""Baseball Chatbot

Digital expert in all things MLB.
"""
import logging
import streamlit as st
from openai import OpenAI
from constants import SessionStateVariables
from constants import AppUserInterfaceElements
from constants import CannedGreetings
from constants import MessageAttributes
from constants import Tools
from constants import AGENT_SYSTEM_PROMPT
from gateway import get_models
from gateway import get_default_model
from gateway import openai_connect

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
    handlers=[
        # no need from a docker container - logging.FileHandler("baseball-chatbot.log"),
        logging.StreamHandler()
    ])

def generate_response(stream):
    """
    Extracts the content from the stream of responses from the OpenAI API.
    Parameters:
        stream: The stream of responses from the OpenAI API.

    """

    for chunk in stream:
        delta = chunk.output[0].delta
        if delta:
            chunk_content = chunk.output[0].delta.content
            yield chunk_content

# Initialize Streamlit State
if SessionStateVariables.MESSAGES not in st.session_state:
    st.session_state[SessionStateVariables.MESSAGES] = []

    # Connect to OpenAI
    logger.info("Initializing OpenAI Client")
    openai_client = openai_connect()
    st.session_state[SessionStateVariables.OPENAI_CLIENT] = openai_client
    all_models = get_models(openai_client)
    st.session_state[SessionStateVariables.ALL_MODELS] = all_models
    default_model_name = get_default_model(all_models)
    st.session_state[SessionStateVariables.MODEL] = default_model_name
    logger.info("OpenAI Initialized")

# Retrieve OpenAI connection info
openai_client = st.session_state[SessionStateVariables.OPENAI_CLIENT]
model_name = st.session_state[SessionStateVariables.MODEL]
all_models = st.session_state[SessionStateVariables.ALL_MODELS]

# Called on a Model Select value change
def on_model_select_change():
    new_model = st.session_state.selected_model_key
    model_name = st.session_state[SessionStateVariables.MODEL]
    if new_model != model_name:
        print (f"MODEL CHANGED: From {model_name} to {new_model}")

        # update model in state
        st.session_state[SessionStateVariables.MODEL] = new_model

        # clear prior responses
        st.session_state[SessionStateVariables.MESSAGES] = []
        if SessionStateVariables.OPENAI_RESPONSES_PREV in st.session_state:
            del st.session_state[SessionStateVariables.OPENAI_RESPONSES_PREV]

# Initialize High Level Page Structure
st.set_page_config(page_title=AppUserInterfaceElements.TITLE,
                   page_icon=AppUserInterfaceElements.TAB_ICON,
                   layout="wide")
st.markdown("""
    <style>
        .stAppHeader {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)
col1, col2 = st.columns(2, vertical_alignment="center")
st.markdown("""
    <style>
        div[data-testid="column"] {
            width: fit-content !important;
            flex: unset;
        }
        div[data-testid="column"] * {
            width: fit-content !important;
        }
    </style>
    """, unsafe_allow_html=True)
with col1:
    st.image("assets/header.png")
with col2:
    index = all_models.index(model_name)
    option = st.selectbox(
        "Model:",
        options=all_models,
        index=index,
        key="selected_model_key",
        on_change=on_model_select_change
    )

# Initialize Chat Box
messages = st.container(height=400)
messages.chat_message(MessageAttributes.ASSISTANT).write(CannedGreetings.INTRO)
for msg in st.session_state.messages:
    messages.chat_message(msg[MessageAttributes.ROLE]).write(msg[MessageAttributes.CONTENT])

# Gather and log user prompt
if user_input := st.chat_input():
    logger.info ("User Input: %s", user_input)
    messages.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    logger.info ("st.session_state.messages - %s", st.session_state.messages)

    # Manage whether there has been previous chats in this conversation
    previous_response_id = None
    if SessionStateVariables.OPENAI_RESPONSES_PREV in st.session_state:
        previous_response_id = st.session_state[SessionStateVariables.OPENAI_RESPONSES_PREV]

    # Employ OpenAI Responses AI
    response_stream = openai_client.responses.create(
        model=model_name,
        instructions=AGENT_SYSTEM_PROMPT,
        input=user_input,
        tools=[
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
        previous_response_id=previous_response_id,
        parallel_tool_calls=True,
        stream=True
    )

    # Capture response
    ai_response = ""
    with messages.chat_message(MessageAttributes.ASSISTANT):
        placeholder = st.empty()
    
        for event in response_stream:
            if hasattr(event, "type") and "text.delta" in event.type:
                ai_response += event.delta
                print(event.delta, end="", flush=True)
                with placeholder.container():
                    st.write(ai_response)
            elif hasattr(event, "type") and "response.completed" in event.type:
                st.session_state[SessionStateVariables.OPENAI_RESPONSES_PREV] = event.response.id

    # Get AI Response to Latest Inquiry
    logger.info ("AI Response Message: %s", ai_response)

    # Append AI Response to history
    st.session_state.messages.append(
        {
            MessageAttributes.ROLE: MessageAttributes.ASSISTANT,
            MessageAttributes.CONTENT: ai_response
        }
    )
