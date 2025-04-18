#!/usr/bin/env python3
import requests
import json
import sys
import time

# API endpoints
API_URL_EXECUTE = "http://localhost:8002/execute"
API_URL_GENERATE = "http://localhost:8002/generate-and-execute"

# Test code samples
SAFE_CODE = """
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

result = fibonacci(20)
print(f"Fibonacci(20) = {result}")
"""

UNSAFE_CODE = """
import os
import socket

# Try to access files
try:
    print("Files in root:", os.listdir("/"))
except Exception as e:
    print(f"File access error: {e}")

# Try to make a network connection
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.google.com", 80))
    print("Network connection successful")
    s.close()
except Exception as e:
    print(f"Network connection error: {e}")
"""

# Test queries
TEST_QUERIES = [
    "Calculate the first 10 prime numbers and display them",
    "Create a simple text-based game where I guess a random number between 1 and 100",
    "Analyze the Collatz conjecture for starting values from 1 to 20 and show which number takes the most steps to reach 1"
]

def test_code_execution(code, validate=True):
    """Test executing Python code through the API"""
    data = {
        "code": code,
        "timeout": 5,
        "memory_limit": "100m",
        "cpu_limit": 0.5,
        "validate_code": validate
    }
    
    try:
        print(f"Sending request to execute code...")
        response = requests.post(API_URL_EXECUTE, json=data)
        response.raise_for_status()
        result = response.json()
        
        print("\n=== EXECUTION RESULT ===")
        print(f"Exit code: {result['exit_code']}")
        print(f"Execution time: {result['execution_time']:.4f} seconds")
        
        if result.get('validation_result'):
            print(f"\nValidation result: {result['validation_result']}")
        
        print("\n=== STDOUT ===")
        print(result['stdout'] or "(empty)")
        
        print("\n=== STDERR ===")
        print(result['stderr'] or "(empty)")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\nAPI Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

def test_query_execution(query):
    """Test generating and executing code from a query (combined generation and validation)"""
    data = {
        "query": query,
        "timeout": 10,
        "memory_limit": "200m",
        "cpu_limit": 0.5
    }
    
    print(f"\n\n=== Testing Query Execution ===")
    print(f"Query: {query}")
    
    try:
        print("Sending request to generate, validate, and execute code...")
        start_time = time.time()
        response = requests.post(API_URL_GENERATE, json=data)
        response.raise_for_status()
        result = response.json()
        total_time = time.time() - start_time
        
        print(f"Total API time (including generation and validation): {total_time:.2f} seconds")
        print("\n=== GENERATED CODE ===")
        print(result['generated_code'])
        
        print("\n=== EXECUTION RESULT ===")
        print(f"Exit code: {result['exit_code']}")
        print(f"Execution time: {result['execution_time']:.4f} seconds")
        
        if result.get('validation_result'):
            print(f"\nValidation result: {result['validation_result']}")
        
        print("\n=== STDOUT ===")
        print(result['stdout'] or "(empty)")
        
        print("\n=== STDERR ===")
        print(result['stderr'] or "(empty)")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\nAPI Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None

if __name__ == "__main__":
    # Check if API is running
    try:
        health_check = requests.get("http://localhost:8002/health")
        if health_check.status_code != 200:
            print("API is not responding correctly. Make sure it's running.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to API. Make sure it's running on http://localhost:8002")
        sys.exit(1)
    
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test Secure Python Code Execution API')
    parser.add_argument('--test-type', choices=['code', 'query', 'all'], default='all',
                        help='Type of test to run: code, query, or all')
    parser.add_argument('--query', type=str, help='Custom query to execute')
    args = parser.parse_args()
    
    print("========================================================")
    print("TESTING SECURE PYTHON CODE EXECUTION SERVICE")
    print("--------------------------------------------------------")
    print("This service uses a unified approach to generate and validate")
    print("code in a single API call, improving efficiency and reliability.")
    print("========================================================\n")
    
    if args.test_type in ['code', 'all']:
        print("\n=== Testing Safe Code ===")
        test_code_execution(SAFE_CODE)
        
        print("\n\n=== Testing Unsafe Code ===")
        test_code_execution(UNSAFE_CODE)
    
    if args.test_type in ['query', 'all']:
        if args.query:
            test_query_execution(args.query)
        else:
            # Test with sample queries
            for query in TEST_QUERIES:
                test_query_execution(query)
                time.sleep(1)  # Small delay between tests 