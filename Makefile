#LLAMA_STACK_URL := https://my-llama-stack-my-llama-stack.apps.ocp.home.glroland.com
#LLAMA_STACK_URL := http://envision:8321
LLAMA_STACK_URL := http://localhost:8321
LLAMA_STACK_MODEL := ollama/llama3.1:8b
#LLAMA_STACK_MODEL := meta-llama/Llama-3.3-70B-Instruct
#LLAMA_STACK_MODEL := gpt-4.1-mini
LLAMA_STACK_MODEL := azure_openai/o4-mini
EMBEDDING_MODEL := text-embedding-3-large

IMAGE_REGISTRY := registry.home.glroland.com/baseball
IMAGE_TAG := manual-1

LOCAL_PORT_CHATBOT := 8080

BASEBALL_DB_CONNECTION_STRING = postgresql://baseball_app:baseball123@db.home.glroland.com:5432/baseball_db
AGENT_WEATHER_URL = https://baseball-chatbot-agent-weather-baseball-chatbot.apps.ocp.home.glroland.com/sse
AGENT_TEAM_URL = https://baseball-chatbot-agent-team-baseball-chatbot.apps.ocp.home.glroland.com/sse
AGENT_GAME_URL = https://baseball-chatbot-agent-game-baseball-chatbot.apps.ocp.home.glroland.com/sse

install:
	pip install -r requirements.txt
	pip install -r chatbot/requirements.txt
	pip install -r agent-weather/requirements.txt
	pip install -r agent-team/requirements.txt
	pip install -r agent-game/requirements.txt

run.chatbot:
	cd chatbot/src && LLAMA_STACK_URL=$(LLAMA_STACK_URL) LLAMA_STACK_MODEL=$(LLAMA_STACK_MODEL) AGENT_WEATHER_URL=$(AGENT_WEATHER_URL) AGENT_TEAM_URL=$(AGENT_TEAM_URL) AGENT_GAME_URL=$(AGENT_GAME_URL) streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port $(LOCAL_PORT_CHATBOT)

run.agent_weather:
	cd agent-weather/src && python mcp_server.py

run.agent_team:
	cd agent-team/src && MCP_PORT=8080 DB_CONNECTION_STRING=$(BASEBALL_DB_CONNECTION_STRING) python mcp_server.py

run.agent_game:
	cd agent-game/src && MCP_PORT=8080 DB_CONNECTION_STRING=$(BASEBALL_DB_CONNECTION_STRING) python mcp_server.py

build:
	cd chatbot && podman build . --platform=linux/amd64 -t chatbot:latest
	cd agent-weather && podman build . --platform=linux/amd64 -t agent-weather:latest
	cd agent-team && podman build . --platform=linux/amd64 -t agent-team:latest
	cd agent-game && podman build . --platform=linux/amd64 -t agent-game:latest

publish:
	podman tag chatbot:latest $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman tag agent-weather:latest $(IMAGE_REGISTRY)/agent-weather:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-weather:$(IMAGE_TAG)
	podman tag agent-team:latest $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
	podman tag agent-game:latest $(IMAGE_REGISTRY)/agent-game:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-game:$(IMAGE_TAG)
