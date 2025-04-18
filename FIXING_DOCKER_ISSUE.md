# Fixing the Docker Execution Issue

If you're encountering the error:
```
python: can't open file '/code/python': [Errno 2] No such file or directory
```

This document explains the fix that has been implemented to resolve this issue.

## The Issue

The issue was related to how the Python code was executed inside the Docker container. When the `command=["python", "/code/code.py"]` was being passed to the container, it was misinterpreting the argument structure.

## The Solution

We've implemented the following changes to fix the issue:

1. **Added a run script**: Added a `run_code.sh` script to the Docker image that properly executes the Python code.

2. **Modified the Dockerfile**: Updated the Dockerfile to use the `run_code.sh` script as the entrypoint.

3. **Updated the FastAPI code**: Changed the Docker container creation to use an empty command array, letting the entrypoint script handle the Python code execution.

## How to Apply the Fix

1. **Rebuild the Docker image**:
   ```bash
   ./scripts/build_docker_image.sh
   ```

2. **Restart the service**:
   ```bash
   ./scripts/deploy.sh
   ```

3. **Verify the fix**:
   ```bash
   ./scripts/verify_fix.sh
   ```

## Testing Your Code

Once you've applied the fix, you can test the service using:

```bash
./scripts/test_api.py --test-type query --query "Calculate the factorial of 10"
```

The output should now show successful code execution with no errors about missing files.

## Understanding the Changes

1. **run_code.sh**: This script checks if `/code/code.py` exists and runs it if it does, otherwise it passes the arguments to Python.

2. **Dockerfile**: The ENTRYPOINT was changed from `["python"]` to `["/usr/local/bin/run_code.sh"]`.

3. **main.py**: The command parameter in the `container.run()` call was changed from `["python", "/code/code.py"]` to `[]`.

These changes ensure that Python correctly interprets the command and finds the code file to execute. 