"""Baseball Chatbot

Digital expert in all things MLB.
"""
import logging
import streamlit as st
from constants import SessionStateVariables
from constants import AppUserInterfaceElements
from constants import CannedGreetings
from constants import MessageAttributes
from constants import Tools
from responses_gateway import ResponsesGateway
from lls_gateway import LLamaStackGateway

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
    handlers=[
        # no need from a docker container - logging.FileHandler("baseball-chatbot.log"),
        logging.StreamHandler()
    ])

def reset_gateway(use_responses: bool):
    """ Reset the gateway and models list.
    
        use_responses - true if the openai responses api should be used
    """
    st.session_state[SessionStateVariables.RESPONSES] = use_responses

    if use_responses:
        logger.info("Initializing OpenAI Client")
        gateway = ResponsesGateway()
    else:
        logger.info("Initializing LLama Stack Client")
        gateway = LLamaStackGateway()
    gateway.connect()
    st.session_state[SessionStateVariables.GATEWAY] = gateway
    logger.info("Client Initialized")

    logger.info("Clearing message history.")
    st.session_state[SessionStateVariables.MESSAGES] = []

    return gateway


# Initialize Streamlit State
if SessionStateVariables.MESSAGES not in st.session_state:
    reset_gateway(False)

# Retrieve connection info
gateway = st.session_state[SessionStateVariables.GATEWAY]
model_name = gateway.get_selected_model()
all_models = gateway.get_models()
all_models.sort()

# Called on a Model Select value change
def on_model_select_change():
    new_model = st.session_state.selected_model_key
    if new_model != model_name:
        print (f"MODEL CHANGED: From {model_name} to {new_model}")

        # clear prior responses
        st.session_state[SessionStateVariables.MESSAGES] = []
        gateway.on_model_change(new_model)

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
    col2a, col2b = st.columns([0.2, 0.8], vertical_alignment="top")
    with col2a:
        st.markdown(":small[Responses API?]")
        is_responses_checked = st.checkbox("Responses",
                                           label_visibility="hidden",
                                           value=st.session_state[SessionStateVariables.RESPONSES])
        if is_responses_checked != st.session_state[SessionStateVariables.RESPONSES]:
            logger.info("Use Responses API checkbox clicked: %s", is_responses_checked)
            reset_gateway(is_responses_checked)
            st.rerun()

    with col2b:
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

    # Process chat
    ai_response = None
    with messages.chat_message(MessageAttributes.ASSISTANT):
        placeholder = st.empty()
        ai_response = gateway.process_user_chat(user_input, placeholder)
    logger.info ("AI Response Message: %s", ai_response)

    # Append AI Response to history
    st.session_state.messages.append(
        {
            MessageAttributes.ROLE: MessageAttributes.ASSISTANT,
            MessageAttributes.CONTENT: ai_response
        }
    )
