"""Baseball Chatbot

Digital expert in all things MLB.
"""
import logging
import streamlit as st
from constants import SessionStateVariables
from constants import AppUserInterfaceElements
from constants import CannedGreetings
from constants import MessageAttributes
from constants import AGENT_SYSTEM_PROMPT
from lls_gateway import lls_connect
from lls_gateway import lls_create_agent
from lls_gateway import lls_new_session
from lls_gateway import lls_streaming_turn_response_generator
from lls_gateway import get_all_lls_model_names
from lls_gateway import get_lls_model_name
from tools import BASEBALL_CHAT_AGENTS
from tools import setup_tools

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
    handlers=[
        # no need from a docker container - logging.FileHandler("baseball-chatbot.log"),
        logging.StreamHandler()
    ])

# Initialize Streamlit State
if SessionStateVariables.MESSAGES not in st.session_state:
    st.session_state[SessionStateVariables.MESSAGES] = []

    # Connect to LLama Stack
    logger.info("Initializing LLama Stack")
    llama_stack_client, llama_stack_model = lls_connect()
    llama_stack_all_models = get_all_lls_model_names(llama_stack_client)
    setup_tools(llama_stack_client)
    llama_stack_model_name = get_lls_model_name()
    llama_stack_agent = lls_create_agent(llama_stack_client, llama_stack_model_name, AGENT_SYSTEM_PROMPT, BASEBALL_CHAT_AGENTS)
    logger.info("LLama Stack Initialized")

    # Save LLama Stack Connection Info
    st.session_state["llama_stack_client"] = llama_stack_client
    st.session_state["llama_stack_agent"] = llama_stack_agent
    st.session_state["llama_stack_model"] = llama_stack_model.identifier
    st.session_state["llama_stack_all_models"] = llama_stack_all_models

    # Start session
    llama_stack_session_id = lls_new_session(llama_stack_agent)
    st.session_state[SessionStateVariables.SESSION_ID] = llama_stack_session_id

# Retrieve LLama Stack connection info
llama_stack_client = st.session_state["llama_stack_client"]
llama_stack_agent = st.session_state["llama_stack_agent"]
llama_stack_model = st.session_state["llama_stack_model"]
llama_stack_session_id = st.session_state[SessionStateVariables.SESSION_ID]
llama_stack_all_models = st.session_state["llama_stack_all_models"]

# Called on a Model Select value change
def on_model_select_change():
    new_model = st.session_state.selected_model_key
    llama_stack_model = st.session_state["llama_stack_model"]
    if new_model != llama_stack_model:
        print (f"MODEL CHANGED: From {llama_stack_model} to {new_model}")

        # update model in state
        st.session_state["llama_stack_model"] = new_model
        llama_stack_model = st.session_state["llama_stack_model"]

        # recreate agent
        st.session_state[SessionStateVariables.MESSAGES] = []
        llama_stack_agent = lls_create_agent(llama_stack_client, llama_stack_model, AGENT_SYSTEM_PROMPT, BASEBALL_CHAT_AGENTS)
        st.session_state["llama_stack_agent"] = llama_stack_agent

        # create a new session
        llama_stack_session_id = lls_new_session(llama_stack_agent)
        st.session_state[SessionStateVariables.SESSION_ID] = llama_stack_session_id

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
    index = llama_stack_all_models.index(llama_stack_model)
    option = st.selectbox(
        "Model:",
        options=llama_stack_all_models,
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

    # Invoke Backend API
    response = llama_stack_agent.create_turn(
        session_id=llama_stack_session_id,
        messages=[{"role":"user", "content": user_input}],
        stream=True
    )

    # Capture streaming response
    ai_response = ""
    with messages.chat_message(MessageAttributes.ASSISTANT):
        ai_response = st.write_stream(lls_streaming_turn_response_generator(response))

    # Get AI Response to Latest Inquiry
    logger.info ("AI Response Message: %s", ai_response)

    # Append AI Response to history
    st.session_state.messages.append(
        {
            MessageAttributes.ROLE: MessageAttributes.ASSISTANT,
            MessageAttributes.CONTENT: ai_response
        }
    )
