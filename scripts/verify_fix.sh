#!/bin/bash
set -e

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

echo "Verifying Docker execution fix..."

# Create a temporary directory and Python test file
TEMP_DIR=$(mktemp -d)
echo 'print("Docker execution test successful!")' > "$TEMP_DIR/code.py"

# Run the Docker container with the test file
echo "Running test container..."
docker run --rm \
    -v "$TEMP_DIR:/code:ro" \
    --read-only \
    --cap-drop=ALL \
    --security-opt=no-new-privileges:true \
    --network=none \
    python-code-execution:latest

# Clean up
rm -rf "$TEMP_DIR"

echo "Verification complete. If you saw 'Docker execution test successful!', the fix worked!" 