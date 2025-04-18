#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:8002"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create a temporary directory for outputs
test_dir=$(mktemp -d)
echo "Test outputs will be saved to $test_dir"

# Function to make API requests and save responses
function test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local http_code
    local response_file="$test_dir/${name}.json"
    
    echo -e "${YELLOW}Running test: ${name}${NC}"
    
    if [ "$method" == "GET" ]; then
        # For GET requests
        http_code=$(curl -s -o "$response_file" -w "%{http_code}" \
            -X "$method" \
            "$API_URL$endpoint")
    else
        # For POST requests with data
        http_code=$(curl -s -o "$response_file" -w "%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_URL$endpoint")
    fi
    
    # Check HTTP response code
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ Test passed with status code: $http_code${NC}"
    else
        echo -e "${RED}✗ Test failed with status code: $http_code${NC}"
    fi
    
    # Display a summary of the response
    echo "Response summary:"
    if [ -f "$response_file" ]; then
        # Show the first few lines of the response
        head -n 15 "$response_file" | cat
        
        # If response is longer, indicate there's more
        lines=$(wc -l < "$response_file")
        if [ "$lines" -gt 15 ]; then
            echo "... (response truncated, full response in $response_file)"
        fi
    else
        echo "No response received"
    fi
    
    echo "----------------------------------------"
}

# Check if the service is running
echo "Checking if the service is running..."
if ! curl -s "$API_URL/health" > /dev/null; then
    echo -e "${RED}Error: Service does not appear to be running at $API_URL${NC}"
    echo "Make sure the service is running with:"
    echo "  ./scripts/deploy.sh"
    exit 1
fi

# Run the tests

# 1. Health Check
test_api "health_check" "GET" "/health" ""

# 2. Execute Code - Fibonacci
test_api "execute_fibonacci" "POST" "/execute" '{
    "code": "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\nresult = fibonacci(10)\nprint(f\"Fibonacci(10) = {result}\")",
    "timeout": 5,
    "memory_limit": "100m",
    "cpu_limit": 0.5,
    "validate_code": true
}'

# 3. Execute Code - Hello World (Skip Validation)
test_api "execute_hello_world" "POST" "/execute" '{
    "code": "print(\"Hello, World!\")",
    "timeout": 5,
    "memory_limit": "100m",
    "cpu_limit": 0.5,
    "validate_code": false
}'

# 4. Execute Code - Unsafe (Should Fail Validation)
test_api "execute_unsafe" "POST" "/execute" '{
    "code": "import os\nprint(\"Files in root directory:\", os.listdir(\"/\"))",
    "timeout": 5,
    "memory_limit": "100m",
    "cpu_limit": 0.5,
    "validate_code": true
}'

# 5. Generate and Execute - Prime Numbers
test_api "generate_prime_numbers" "POST" "/generate-and-execute" '{
    "query": "Calculate the first 10 prime numbers",
    "timeout": 10,
    "memory_limit": "100m",
    "cpu_limit": 0.5
}'

# 6. Generate and Execute - Factorial
test_api "generate_factorial" "POST" "/generate-and-execute" '{
    "query": "Calculate the factorial of 10",
    "timeout": 5,
    "memory_limit": "100m",
    "cpu_limit": 0.5
}'

# Summary
echo -e "${GREEN}Tests completed.${NC}"
echo "Response files saved to: $test_dir"
echo "To view full responses, examine the JSON files in this directory." 