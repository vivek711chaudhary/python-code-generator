#!/bin/bash

# Change to the parent directory of the script
cd "$(dirname "$0")/.."

# Check if the Docker image exists
if [[ "$(docker images -q python-code-execution:latest 2> /dev/null)" == "" ]]; then
    echo "Docker image does not exist. Building it first..."
    ./scripts/build_docker_image.sh
fi

# Set up environment variables
export TOGETHER_API_KEY="${TOGETHER_API_KEY:-}"
export API_TIMEOUT="${API_TIMEOUT:-30}"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install fastapi uvicorn docker httpx pydantic
else
    source venv/bin/activate
fi

# Start the API server
echo "Starting API server on port 8002..."
cd app
uvicorn main:app --host 0.0.0.0 --port 8002 --reload 