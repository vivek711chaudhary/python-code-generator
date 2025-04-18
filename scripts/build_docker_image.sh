#!/bin/bash

# Change to the parent directory of the script
cd "$(dirname "$0")/.."

# Ensure the run_code.sh script is executable
chmod +x dockerfile/run_code.sh

# Build the Docker image
echo "Building Python code execution Docker image..."
docker build -t python-code-execution:latest -f dockerfile/Dockerfile .

# Verify the image was built
if [ $? -eq 0 ]; then
    echo "Image built successfully: python-code-execution:latest"
else
    echo "Error building Docker image"
    exit 1
fi 