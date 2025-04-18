# Quick Start Guide

This guide helps you quickly set up and run the Secure Python Code Execution Service.

## Running Locally on Port 8002

1. Make sure you have Docker installed:
```bash
docker --version
```

2. Set your Together API key:
```bash
export TOGETHER_API_KEY="your-together-api-key"
export API_TIMEOUT=30
```

3. Build the Docker image:
```bash
cd code-execution-service
./scripts/build_docker_image.sh
```

4. Start the service:
```bash
./scripts/start_api.sh
```

The service will be available at http://localhost:8002

## Testing the Service

Once the service is running, you can test it:

```bash
# Run all tests
./scripts/test_api.py

# Test with a specific query
./scripts/test_api.py --test-type query --query "Calculate the sum of the first 100 prime numbers"
```

### Testing with Postman

For GUI-based testing, you can use Postman:

1. Import the Postman collection:
   ```bash
   # Open Postman and import this file
   code-execution-service/Code_Execution_API.postman_collection.json
   ```

2. Use the ready-made requests to test all endpoints

3. For detailed instructions, see:
   ```bash
   cat code-execution-service/POSTMAN_TESTING.md
   ```

### Automated API Testing

Run the automated test script to test all endpoints:

```bash
./scripts/run_api_tests.sh
```

## Using the Deployment Script

For more deployment options, use the deployment script:

```bash
# Local deployment (default)
./scripts/deploy.sh

# Docker deployment
./scripts/deploy.sh --mode docker

# Systemd service deployment
sudo ./scripts/deploy.sh --mode systemd
```

## API Endpoints

- Generate and Execute Code: `POST /generate-and-execute`
- Execute Existing Code: `POST /execute`
- Health Check: `GET /health`

## Sample API Request

Using curl to make a request:

```bash
curl -X POST http://localhost:8002/generate-and-execute \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the first 10 prime numbers"}'
```

## Troubleshooting

- If the service doesn't start, check Docker is running
- Verify your Together API key is correctly set
- Check the error logs with `docker logs code-execution-api` (if using Docker mode)
- Make sure port 8002 is not already in use

## Environment Variables

- `TOGETHER_API_KEY`: Your Together AI API key
- `API_TIMEOUT`: Timeout for API calls (default: 30)
- `PORT`: Port to run the service on (default: 8002)

For more detailed information, see the README.md file. 