LLAMA_STACK_URL := https://my-llama-stack-my-llama-stack.apps.ocp.home.glroland.com
#LLAMA_STACK_URL := http://envision:8321
#LLAMA_STACK_URL := http://localhost:8321
EMBEDDING_MODEL := sentence-transformers/sentence-transformers/all-mpnet-base-v2
DEFAULT_MODEL := together/mistralai/Ministral-3-14B-Instruct-2512

IMAGE_REGISTRY := registry.home.glroland.com/baseball
IMAGE_TAG := manual-1

LOCAL_PORT_CHATBOT := 8080

BASEBALL_DB_CONNECTION_STRING = postgresql://baseball_app:baseball123@db.home.glroland.com:5432/baseball_db
AGENT_UTILITIES_URL = https://baseball-chatbot-agent-utilities-baseball-chatbot.apps.ocp.home.glroland.com/mcp
AGENT_TEAM_URL = https://baseball-chatbot-agent-team-baseball-chatbot.apps.ocp.home.glroland.com/mcp
AGENT_GAME_URL = https://baseball-chatbot-agent-game-baseball-chatbot.apps.ocp.home.glroland.com/mcp

install:
	pip install -r requirements.txt
	pip install -r chatbot/requirements.txt
	pip install -r agent-utilities/requirements.txt
	pip install -r agent-team/requirements.txt
	pip install -r agent-game/requirements.txt

run.chatbot:
	cd chatbot/src && OPENAI_BASE_URL=$(LLAMA_STACK_URL)/v1 DEFAULT_MODEL=$(DEFAULT_MODEL) LLAMA_STACK_URL=$(LLAMA_STACK_URL) AGENT_UTILITIES_URL=$(AGENT_UTILITIES_URL) AGENT_TEAM_URL=$(AGENT_TEAM_URL) AGENT_GAME_URL=$(AGENT_GAME_URL) streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port $(LOCAL_PORT_CHATBOT)

run.agent_utilities:
	cd agent-utilities/src && python mcp_server.py

run.agent_team:
	cd agent-team/src && MCP_PORT=8080 DB_CONNECTION_STRING=$(BASEBALL_DB_CONNECTION_STRING) python mcp_server.py

run.agent_game:
	cd agent-game/src && MCP_PORT=8080 DB_CONNECTION_STRING=$(BASEBALL_DB_CONNECTION_STRING) python mcp_server.py

build:
	cd chatbot && podman build . --platform=linux/amd64 -t chatbot:latest
	cd agent-utilities && podman build . --platform=linux/amd64 -t agent-utilities:latest
	cd agent-team && podman build . --platform=linux/amd64 -t agent-team:latest
	cd agent-game && podman build . --platform=linux/amd64 -t agent-game:latest

publish:
	podman tag chatbot:latest $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman tag agent-utilities:latest $(IMAGE_REGISTRY)/agent-utilities:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-utilities:$(IMAGE_TAG)
	podman tag agent-team:latest $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
	podman tag agent-game:latest $(IMAGE_REGISTRY)/agent-game:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-game:$(IMAGE_TAG)
