# Secure Python Code Execution Service

A secure API service for generating and executing Python code in an isolated environment.

## Features

- Generates and validates Python code from user queries in a single API call to Together AI
- Executes arbitrary Python code in a sandboxed Docker container
- Provides robust security measures:
  - Network isolation
  - CPU and memory limits
  - Execution timeouts
  - No filesystem access
  - Non-root user execution
- Code validation and improvement using Together AI
- Returns execution results, including stdout, stderr, and exit code

## Setup

### Prerequisites

- Docker
- Python 3.8+
- Together AI API key (for code generation and validation)

### Installation

1. Clone the repository
2. Build the Docker image:

```bash
./scripts/build_docker_image.sh
```

3. Start the API server:

```bash
# Set the Together AI API key for code generation and validation
export TOGETHER_API_KEY="your-together-api-key"
export API_TIMEOUT=30  # Timeout for API calls in seconds

./scripts/start_api.sh
```

The service will start on port 8002 by default.

## Deployment Options

The service can be deployed in several ways using the provided deployment script:

### Local Deployment

For local development and testing:

```bash
# Create a .env file from the template
cp .env.template .env
# Edit the .env file with your Together API key
nano .env

# Run with default settings (port 8002)
./scripts/deploy.sh

# Or specify a custom port
./scripts/deploy.sh --port 9000
```

### Docker Deployment

For containerized deployment:

```bash
./scripts/deploy.sh --mode docker

# Or with custom port and env file
./scripts/deploy.sh --mode docker --port 8080 --env-file /path/to/.env
```

This will create and start a Docker container running the service.

### Systemd Service Deployment

For running as a system service:

```bash
# Deploy as a systemd service (requires sudo)
./scripts/deploy.sh --mode systemd

# Or with custom port
./scripts/deploy.sh --mode systemd --port 8080
```

This creates a systemd service that will automatically start on boot.

## API Usage

The service exposes the following endpoints:

### 1. Generate and Execute Code from Query

**Endpoint:** `POST /generate-and-execute`

This is the primary endpoint for AI agent interaction. It:
1. Generates and validates Python code based on a query/task description in a single API call
2. Executes it in a secure environment
3. Returns the results

**Request Body:**

```json
{
  "query": "Calculate the first 10 prime numbers",
  "timeout": 15,
  "memory_limit": "200m",
  "cpu_limit": 0.5
}
```

**Response:**

```json
{
  "query": "Calculate the first 10 prime numbers",
  "generated_code": "def is_prime(n):\n    if n <= 1:\n        return False\n    if n <= 3:\n        return True\n    if n % 2 == 0 or n % 3 == 0:\n        return False\n    i = 5\n    while i * i <= n:\n        if n % i == 0 or n % (i + 2) == 0:\n            return False\n        i += 6\n    return True\n\nprimes = []\nn = 2\nwhile len(primes) < 10:\n    if is_prime(n):\n        primes.append(n)\n    n += 1\n\nprint(f\"First 10 prime numbers: {primes}\")",
  "stdout": "First 10 prime numbers: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.023,
  "validation_result": "The code is secure and efficient."
}
```

### 2. Execute Provided Python Code

**Endpoint:** `POST /execute`

This endpoint executes provided Python code (rather than generating it from a query).

**Request Body:**

```json
{
  "code": "print('Hello, world!')",
  "timeout": 10,
  "memory_limit": "100m",
  "cpu_limit": 0.5,
  "validate_code": true
}
```

**Response:**

```json
{
  "stdout": "Hello, world!\n",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.234,
  "original_code": "print('Hello, world!')",
  "executed_code": "print('Hello, world!')",
  "validation_result": "Code is safe to execute."
}
```

### 3. Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

## Testing

There are multiple ways to test the service:

### 1. Command-line Testing with Python

```bash
# Test all functionality
python scripts/test_api.py

# Test only code execution
python scripts/test_api.py --test-type code

# Test only query-based code generation and execution
python scripts/test_api.py --test-type query

# Test with a custom query
python scripts/test_api.py --test-type query --query "Calculate factorial of 10"
```

### 2. Automated API Testing with cURL

Run a comprehensive test suite that checks all endpoints:

```bash
./scripts/run_api_tests.sh
```

This will test all API endpoints and save the results to a temporary directory for review.

### 3. Testing with Postman (GUI)

For interactive testing with a graphical interface:

```bash
# Open Postman with our collection (if Postman is installed)
./scripts/open_postman.sh
```

Or manually:

1. Import the provided Postman collection:
   - Open Postman
   - Click "Import" > "File" > Select `Code_Execution_API.postman_collection.json`

2. Once imported, you'll see a collection with ready-to-use requests for:
   - Health check endpoint
   - Execute code endpoint (with several examples)
   - Generate and execute endpoint (with various examples)

3. For detailed instructions on using Postman for testing, see `POSTMAN_TESTING.md`

### 4. Quick Testing with cURL

Test the health endpoint:
```bash
curl http://localhost:8002/health
```

Execute Python code:
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

Generate and execute code:
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

For a complete testing guide, see `TESTING.md`.

## Troubleshooting

### Common Issues

1. **Python Execution Error**: If you see an error like `python: can't open file '/code/python': [Errno 2] No such file or directory`, rebuild the Docker image:

```bash
./scripts/build_docker_image.sh
```

2. **API Key Not Set**: If you get an error related to the Together API key, make sure it's set in your environment:

```bash
export TOGETHER_API_KEY="your-together-api-key"
```

3. **Port Already in Use**: If port 8002 is already in use, you can specify a different port:

```bash
./scripts/deploy.sh --port 8003
```

### Checking Logs

To check the logs of the service when running in Docker mode:

```bash
docker logs code-execution-api
```

## Security Considerations

This service implements multiple layers of protection:

1. **Docker Isolation**: Code runs in a container with minimal privileges
2. **Network Disabled**: No outbound or inbound connections possible
3. **Resource Limits**: Prevents resource exhaustion attacks
4. **Non-root Execution**: Code runs as a non-privileged user
5. **Read-only Filesystem**: Prevents data persistence and manipulation
6. **AI Validation**: Code review before execution with detailed security analysis

## Usage for AI Agents

This service is designed to be used by AI agent systems that need computational capabilities. An agent can:

1. Identify when computation or data processing is needed
2. Formulate a clear query describing the computational task
3. Send the query to the `/generate-and-execute` endpoint
4. Use the results (stdout) in its reasoning or response

The service handles all code generation, security checks, and execution in an optimized way with minimal API calls, allowing the agent to focus on its primary tasks.

## Efficiency Improvements

The service now uses a unified approach to code generation and validation:

- **Single API Call**: Generation and validation happen in one API call to Together AI
- **Structured Response**: The AI returns a structured JSON response with the code, safety assessment, and explanation
- **Fallback Mechanism**: Even if JSON parsing fails, the system attempts to extract usable code
- **Detailed Safety Analysis**: The AI performs in-depth safety checks during generation

## Customization

You can customize the service by modifying:

- Resource limits in the API request
- Docker image in the `Dockerfile`
- AI prompt parameters in the code manager service


export TOGETHER_API_KEY="57f633928de4e409bca9a8fef3584efb2baa67f6359553d8a5817b7d9a456299"
export API_TIMEOUT=30  
