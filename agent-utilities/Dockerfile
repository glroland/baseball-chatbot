FROM registry.access.redhat.com/ubi9/python-311:9.6-1750969934

# Configurable variables
ENV MCP_PORT 8080

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
CMD [ "python", "mcp_server.py" ]
