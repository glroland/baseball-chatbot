FROM registry.access.redhat.com/ubi9/python-311:9.5-1745945598

# Configuration
ENV LLAMA_STACK_URL "http://envision:8321"
ENV LLAMA_STACK_MODEL "meta-llama/Llama-3.2-11B-Vision-Instruct"
ENV EMBEDDING_MODEL "sentence-transformers/all-mpnet-base-v2"
ENV AGENT_WEATHER_URL "https://baseball-chatbot-agent-weather-baseball-chatbot.apps.ocp.home.glroland.com/sse"
ENV AGENT_TEAM_URL "https://baseball-chatbot-agent-team-baseball-chatbot.apps.ocp.home.glroland.com/sse"

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
