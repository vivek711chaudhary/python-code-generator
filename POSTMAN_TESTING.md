# Testing the Secure Python Code Execution Service with Postman

This guide will walk you through testing the API endpoints using Postman.

## Prerequisites

1. Make sure the service is running on port 8002
2. [Download and install Postman](https://www.postman.com/downloads/) if you haven't already

## Testing the Health Endpoint

1. Create a new GET request in Postman
2. Set the URL to: `http://localhost:8002/health`
3. Click "Send"
4. Expected response:
   ```json
   {
     "status": "healthy"
   }
   ```

## Testing Code Execution

### 1. Execute Existing Code

1. Create a new POST request in Postman
2. Set the URL to: `http://localhost:8002/execute`
3. Go to the "Headers" tab and add:
   - Key: `Content-Type`
   - Value: `application/json`
4. Go to the "Body" tab, select "raw" and choose "JSON" from the dropdown
5. Add the following JSON:
   ```json
   {
     "code": "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\nresult = fibonacci(10)\nprint(f'Fibonacci(10) = {result}')",
     "timeout": 5,
     "memory_limit": "100m",
     "cpu_limit": 0.5,
     "validate_code": true
   }
   ```
6. Click "Send"
7. Expected response should include:
   ```json
   {
     "stdout": "Fibonacci(10) = 55\n",
     "stderr": "",
     "exit_code": 0,
     "execution_time": 0.123,
     "original_code": "def fibonacci(n):\n    a, b = 0, 1\n...",
     "executed_code": "def fibonacci(n):\n    a, b = 0, 1\n...",
     "validation_result": "The code is safe and efficiently calculates the Fibonacci sequence."
   }
   ```

### 2. Testing Unsafe Code (Should Fail Validation)

1. Create a new POST request to: `http://localhost:8002/execute`
2. Set the headers and body type as before
3. Add the following JSON body:
   ```json
   {
     "code": "import os\nprint('Files in root directory:', os.listdir('/'))",
     "timeout": 5,
     "memory_limit": "100m",
     "cpu_limit": 0.5,
     "validate_code": true
   }
   ```
4. Click "Send"
5. Expected response should be a 400 error with validation failure details

### 3. Generate and Execute Code

1. Create a new POST request to: `http://localhost:8002/generate-and-execute`
2. Set the headers as before
3. Add the following JSON body:
   ```json
   {
     "query": "Calculate the first 10 prime numbers",
     "timeout": 10,
     "memory_limit": "100m",
     "cpu_limit": 0.5
   }
   ```
4. Click "Send"
5. Expected response should include:
   ```json
   {
     "query": "Calculate the first 10 prime numbers",
     "generated_code": "def is_prime(n):\n...",
     "stdout": "First 10 prime numbers: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n",
     "stderr": "",
     "exit_code": 0,
     "execution_time": 0.234,
     "validation_result": "The code is secure and efficiently calculates prime numbers."
   }
   ```

## Testing with More Examples

### Simple Math Operation

```json
{
  "query": "Calculate the factorial of 10",
  "timeout": 5,
  "memory_limit": "100m",
  "cpu_limit": 0.5
}
```

### Text Processing

```json
{
  "query": "Create a function that counts the frequency of words in a text and display the 5 most common words in 'The quick brown fox jumps over the lazy dog. The dog barks and the fox runs away.'",
  "timeout": 5,
  "memory_limit": "100m",
  "cpu_limit": 0.5
}
```

### Data Analysis

```json
{
  "query": "Generate a list of 100 random numbers between 1 and 1000, then calculate their mean, median, mode, and standard deviation",
  "timeout": 10,
  "memory_limit": "100m",
  "cpu_limit": 0.5
}
```

### Simple Game

```json
{
  "query": "Create a text-based rock-paper-scissors game where the computer makes a random choice and then tells me if I won, lost or tied. Let me choose rock.",
  "timeout": 5,
  "memory_limit": "100m",
  "cpu_limit": 0.5
}
```

## Troubleshooting

### Common Issues

1. **Service Not Running**: Make sure the service is running on port 8002. You can check with:
   ```bash
   curl http://localhost:8002/health
   ```

2. **API Key Not Set**: If you get errors about the Together API key, make sure it's properly set:
   ```bash
   export TOGETHER_API_KEY="your-api-key"
   ```

3. **Docker Issues**: If Docker-related errors occur, make sure Docker is running and the image is built:
   ```bash
   docker ps
   docker images | grep python-code-execution
   ```

4. **Timeout Issues**: If requests are timing out, try increasing the timeout value in your request body.

### Enabling Postman Console

To see detailed request and response information in Postman:

1. Click on the "Console" button at the bottom of the Postman window
2. Look for any error messages or status codes
3. Examine the request and response headers and bodies 