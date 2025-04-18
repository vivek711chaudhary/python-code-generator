#!/bin/bash
set -e

# Check if we're given a Python file to run
if [ -f "/code/code.py" ]; then
    # Execute the Python file
    python /code/code.py
else
    # If no Python file is provided, run the command as is
    python "$@"
fi 