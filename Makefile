LLAMA_STACK_URL := http://envision:8321
LLAMA_STACK_MODEL := meta-llama/Llama-3.2-11B-Vision-Instruct
EMBEDDING_MODEL := sentence-transformers/all-mpnet-base-v2

IMAGE_REGISTRY := registry.home.glroland.com/baseball
IMAGE_TAG := 1

LOCAL_PORT_CHATBOT := 8080

install:
	pip install -r requirements.txt
	pip install -r chatbot/requirements.txt
	pip install -r agent_schedule/requirements.txt
	pip install -r agent_team/requirements.txt

run.chatbot:
	cd chatbot/src && LLAMA_STACK_URL=$(LLAMA_STACK_URL) LLAMA_STACK_MODEL=$(LLAMA_STACK_MODEL) streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port $(LOCAL_PORT_CHATBOT)

run.agent_schedule:
	cd agent_schedule/src && python mcp_server.py

run.agent_team:
	cd agent_team/src && python mcp_server.py

build:
	cd chatbot && podman build . --platform=linux/amd64 -t chatbot:latest
	cd agent_schedule && podman build . --platform=linux/amd64 -t agent_schedule:latest
	cd agent_team && podman build . --platform=linux/amd64 -t agent_team:latest

publish:
	podman tag chatbot:latest $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/chatbot:$(IMAGE_TAG)
	podman tag agent_schedule:latest $(IMAGE_REGISTRY)/agent_schedule:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent_schedule:$(IMAGE_TAG)
	podman tag agent_team:latest $(IMAGE_REGISTRY)/agent_team:$(IMAGE_TAG)
	podman push $(IMAGE_REGISTRY)/agent_team:$(IMAGE_TAG)
