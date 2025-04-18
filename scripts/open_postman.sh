#!/bin/bash
set -e

# Get the absolute path to the collection file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION_FILE="$SCRIPT_DIR/../Code_Execution_API.postman_collection.json"

# Check if the collection file exists
if [ ! -f "$COLLECTION_FILE" ]; then
    echo "Error: Postman collection file not found: $COLLECTION_FILE"
    exit 1
fi

echo "Opening Postman with collection: $COLLECTION_FILE"

# Try to detect the operating system and open Postman
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check if Postman is installed
    if command -v postman &> /dev/null; then
        echo "Opening Postman on Linux..."
        postman "$COLLECTION_FILE" &
    else
        echo "Postman not found. Please install Postman or open it manually and import the collection."
        echo "Collection file: $COLLECTION_FILE"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Opening Postman on macOS..."
    if [ -d "/Applications/Postman.app" ]; then
        open -a "Postman" "$COLLECTION_FILE"
    else
        echo "Postman not found. Please install Postman or open it manually and import the collection."
        echo "Collection file: $COLLECTION_FILE"
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows with Git Bash or similar
    echo "Opening Postman on Windows..."
    if [ -d "/c/Program Files/Postman" ]; then
        start "" "/c/Program Files/Postman/Postman.exe" "$COLLECTION_FILE"
    else
        echo "Postman not found. Please install Postman or open it manually and import the collection."
        echo "Collection file: $COLLECTION_FILE"
    fi
else
    echo "Unsupported operating system: $OSTYPE"
    echo "Please open Postman manually and import the collection:"
    echo "Collection file: $COLLECTION_FILE"
fi

echo ""
echo "If Postman didn't open automatically, please:"
echo "1. Open Postman manually"
echo "2. Click 'Import' in the top left"
echo "3. Select 'File' and browse to: $COLLECTION_FILE"
echo "4. Click 'Import' to load the collection" 