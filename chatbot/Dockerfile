FROM registry.access.redhat.com/ubi9/python-312:9.6-1760372467

# Configuration
ENV DEFAULT_MODEL "together/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
ENV EMBEDDING_MODEL "sentence-transformers/sentence-transformers/all-mpnet-base-v2"
ENV AGENT_UTILITIES_URL "https://baseball-chatbot-agent-utilities-baseball-chatbot.apps.ocp.home.glroland.com/sse"
ENV AGENT_TEAM_URL "https://baseball-chatbot-agent-team-baseball-chatbot.apps.ocp.home.glroland.com/sse"
ENV AGENT_GAME_URL "https://baseball-chatbot-agent-game-baseball-chatbot.apps.ocp.home.glroland.com/sse"

# By default, listen on port 8080
EXPOSE 8080/tcp

# Set the working directory in the container
WORKDIR /projects

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY ./src/ .

# Specify the command to run on container start
CMD ["streamlit", "run", "./app.py", "--server.port=8080", "--server.address=0.0.0.0"]
