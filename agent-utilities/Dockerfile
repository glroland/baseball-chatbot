FROM registry.access.redhat.com/ubi9/python-312:9.6-1760372467

# Configurable variables
ENV MCP_PORT 8080
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ENV OTEL_SERVICE_NAME=baseball-chatbot-agent-utilities
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=false

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
CMD [ "opentelemetry-instrument", "--logs_exporter", "none", "--metrics_exporter", "none", "python", "mcp_server.py" ]
