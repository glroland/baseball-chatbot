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
from lls_gateway import lls_connect, lls_create_agent, lls_new_session, lls_streaming_turn_response_generator
from tools import setup_tools, BASEBALL_CHAT_AGENTS

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
    setup_tools(llama_stack_client)
    llama_stack_agent = lls_create_agent(llama_stack_client, AGENT_SYSTEM_PROMPT, BASEBALL_CHAT_AGENTS)
    logger.info("LLama Stack Initialized")

    # Save LLama Stack Connection Info
    st.session_state["llama_stack_client"] = llama_stack_client
    st.session_state["llama_stack_agent"] = llama_stack_agent
    st.session_state["llama_stack_model"] = llama_stack_model

    # Start session
    llama_stack_session_id = lls_new_session(llama_stack_agent)
    st.session_state[SessionStateVariables.SESSION_ID] = llama_stack_session_id

# Retrieve LLama Stack connection info
llama_stack_client = st.session_state["llama_stack_client"]
llama_stack_agent = st.session_state["llama_stack_agent"]
llama_stack_model = st.session_state["llama_stack_model"]
llama_stack_session_id = st.session_state[SessionStateVariables.SESSION_ID]

# Initialize High Level Page Structure
st.set_page_config(page_title=AppUserInterfaceElements.TITLE,
                   page_icon=AppUserInterfaceElements.TAB_ICON,
                   layout="wide")
with st.columns(3)[1]:
    st.title(AppUserInterfaceElements.HEADER)
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

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
