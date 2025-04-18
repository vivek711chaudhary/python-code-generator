# Testing the Code Execution Service

This document outlines the different ways to test the service.

## Quick Testing Options

### 1. Command-line Testing

Test all endpoints with a single command:

```bash
./scripts/run_api_tests.sh
```

This will:
- Check if the service is running
- Test the health endpoint
- Execute several Python code examples 
- Test code generation and execution
- Save all responses to a temporary directory

### 2. Postman Testing (GUI)

For a graphical interface to test the API:

1. Open Postman
2. Import `Code_Execution_API.postman_collection.json`
3. Use the pre-configured requests to test all endpoints

For detailed Postman instructions, see `POSTMAN_TESTING.md`.

### 3. Python Test Script

Use the Python test script for more flexibility:

```bash
# Test all functionality
python scripts/test_api.py

# Test only code execution
python scripts/test_api.py --test-type code

# Test code generation with a custom query
python scripts/test_api.py --test-type query --query "Calculate the Fibonacci sequence up to 100"
```

## Sample Test Cases

### Execute Endpoint

```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "timeout": 5,
    "memory_limit": "100m",
    "cpu_limit": 0.5,
    "validate_code": false
  }'
```

### Generate and Execute Endpoint

```bash
curl -X POST http://localhost:8002/generate-and-execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the first 10 prime numbers",
    "timeout": 10,
    "memory_limit": "100m",
    "cpu_limit": 0.5
  }'
```

### Health Check

```bash
curl http://localhost:8002/health
```

## Troubleshooting

- **Service Not Running**: Make sure the service is running on port 8002
- **Connection Refused**: Check that Docker is running
- **Validation Failures**: Ensure your Together API key is properly set
- **Timeouts**: Try increasing the timeout value in your requests 