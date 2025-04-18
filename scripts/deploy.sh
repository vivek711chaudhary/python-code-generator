#!/bin/bash
set -e

# Default settings
PORT=8002
ENV_FILE=".env"
DEPLOY_MODE="local"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --mode)
            DEPLOY_MODE="$2"
            shift 2
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
done

# Change to the parent directory of the script
cd "$(dirname "$0")/.."
SERVICE_DIR=$(pwd)

echo "Deploying Secure Python Code Execution Service"
echo "---------------------------------------------"
echo "Deployment mode: $DEPLOY_MODE"
echo "Service directory: $SERVICE_DIR"
echo "Port: $PORT"
echo "Environment file: $ENV_FILE"

# Load environment variables if file exists
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE"
    export $(grep -v '^#' $ENV_FILE | xargs)
else
    echo "No environment file found at $ENV_FILE"
    # Check for required environment variables
    if [ -z "$TOGETHER_API_KEY" ]; then
        echo "Error: TOGETHER_API_KEY environment variable is not set"
        echo "Please set it with: export TOGETHER_API_KEY=your-api-key"
        exit 1
    fi
fi

# Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
bash "$SERVICE_DIR/scripts/build_docker_image.sh"

if [ "$DEPLOY_MODE" = "systemd" ]; then
    # Create systemd service file
    SYSTEMD_FILE="/etc/systemd/system/code-execution-service.service"
    echo "Creating systemd service file at $SYSTEMD_FILE"
    
    cat > /tmp/code-execution-service.service << EOF
[Unit]
Description=Secure Python Code Execution Service
After=network.target

[Service]
ExecStart=$SERVICE_DIR/scripts/start_api.sh
WorkingDirectory=$SERVICE_DIR
Environment="TOGETHER_API_KEY=$TOGETHER_API_KEY"
Environment="API_TIMEOUT=${API_TIMEOUT:-30}"
Environment="PORT=$PORT"
Restart=always
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/code-execution-service.service $SYSTEMD_FILE
    
    # Reload systemd and enable service
    echo "Enabling and starting systemd service..."
    sudo systemctl daemon-reload
    sudo systemctl enable code-execution-service
    sudo systemctl restart code-execution-service
    sudo systemctl status code-execution-service
    
    echo "Service deployed with systemd. Check status with: sudo systemctl status code-execution-service"

elif [ "$DEPLOY_MODE" = "docker" ]; then
    # Create a docker-compose.yml file
    echo "Creating docker-compose.yml file"
    
    cat > "$SERVICE_DIR/docker-compose.yml" << EOF
version: '3'

services:
  code-execution-api:
    build:
      context: .
      dockerfile: dockerfile/Dockerfile
    image: code-execution-api
    container_name: code-execution-api
    ports:
      - "$PORT:$PORT"
    volumes:
      - ./app:/app
      - ./requirements.txt:/app/requirements.txt
    environment:
      - TOGETHER_API_KEY=${TOGETHER_API_KEY}
      - API_TIMEOUT=${API_TIMEOUT:-30}
      - PORT=$PORT
    restart: always
    command: sh -c "cd /app && pip install --no-cache-dir -r requirements.txt && python -m uvicorn main:app --host 0.0.0.0 --port $PORT"
EOF

    # Install docker-compose if not available
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing docker-compose..."
        sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Start the service with docker-compose
    echo "Starting service with docker-compose..."
    docker-compose -f "$SERVICE_DIR/docker-compose.yml" up -d
    
    echo "Service deployed with docker-compose. Check logs with: docker-compose -f $SERVICE_DIR/docker-compose.yml logs -f"

else
    # Run in local mode (default)
    echo "Starting service in local mode..."
    
    # Modify the start script to use the specified port
    sed -i "s/--port [0-9]*/--port $PORT/g" "$SERVICE_DIR/scripts/start_api.sh"
    
    # Start the service
    bash "$SERVICE_DIR/scripts/start_api.sh"
fi

echo "Deployment complete!" 