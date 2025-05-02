LLAMA_STACK_URL := http://envision:8321
LLAMA_STACK_MODEL := meta-llama/Llama-3.2-11B-Vision-Instruct
EMBEDDING_MODEL := sentence-transformers/all-mpnet-base-v2

IMAGE_REGISTRY := registry.home.glroland.com/baseball
IMAGE_TAG := 2

LOCAL_PORT_CHATBOT := 8080

install:
	pip install -r requirements.txt
	pip install -r chatbot/requirements.txt
	pip install -r agent-schedule/requirements.txt
	pip install -r agent-team/requirements.txt

run.chatbot:
	cd chatbot/src && LLAMA_STACK_URL=$(LLAMA_STACK_URL) LLAMA_STACK_MODEL=$(LLAMA_STACK_MODEL) streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port $(LOCAL_PORT_CHATBOT)

run.agent_schedule:
	cd agent-schedule/src && python mcp_server.py

run.agent_team:
	cd agent-team/src && python mcp_server.py

build:
	cd chatbot && podman build . --platform=linux/amd64 -t chatbot:latest
	cd agent-schedule && podman build . --platform=linux/amd64 -t agent-schedule:latest
	cd agent-team && podman build . --platform=linux/amd64 -t agent-team:latest

publish:
	podman tag chatbot:latest $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman tag agent-schedule:latest $(IMAGE_REGISTRY)/agent-schedule:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-schedule:$(IMAGE_TAG)
	podman tag agent-team:latest $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent-team:$(IMAGE_TAG)
