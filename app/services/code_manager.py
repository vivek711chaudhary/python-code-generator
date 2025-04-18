import os
import json
from typing import Dict, Any, Tuple, Optional
import httpx
import logging
import re

logger = logging.getLogger(__name__)

# Get API key from environment variable
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

async def generate_and_validate_code(query: str) -> Tuple[str, bool, str]:
    """
    Generates and validates Python code from a user query.
    
    This uses a unified approach to generate and validate in a single API call.
    
    Args:
        query: The user query describing what the code should do
        
    Returns:
        Tuple containing:
        - generated_code: The generated Python code
        - is_safe: Boolean indicating if the code is safe to execute
        - explanation: Explanation of what the code does and any potential issues
    """
    if not TOGETHER_API_KEY:
        logger.warning("TOGETHER_API_KEY not set, skipping code generation")
        return None, False, "API key not configured"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Python programmer that generates secure, "
                                "well-commented Python code based on user queries. "
                                "Generate working Python code that satisfies the user's request, "
                                "but first analyze it for security and efficiency. "
                                "VERY IMPORTANT: YOUR RESPONSE MUST BE VALID JSON in this format:\n"
                                "{\n"
                                "  \"generated_code\": \"FULL_PYTHON_CODE_HERE\",\n"
                                "  \"is_safe\": true_or_false,\n"
                                "  \"explanation\": \"brief explanation of the code and any security considerations\"\n"
                                "}\n\n"
                                "Do not include any explanatory text, headers, or markdown formatting outside of the JSON object."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Write Python code to: {query}\n\n"
                                "Keep in mind that this code will run in a restricted Docker environment with:\n"
                                "- No network access\n"
                                "- No file system access beyond current directory\n"
                                "- Limited CPU and memory\n"
                                "- Execution timeout\n"
                                "- No sudo/admin privileges\n"
                                "- No access to system resources"
                            )
                        }
                    ],
                    "temperature": 0.3,
                    "timeout": API_TIMEOUT
                },
                timeout=API_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the content from the response
            content = result["choices"][0]["message"]["content"]
            
            # Parse the JSON from the content
            try:
                # Find JSON in the content if it's wrapped in text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    json_str = content[json_start:json_end]
                    generation_result = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    logger.warning("Could not find JSON in Together AI response")
                    
                    # Extract code from any markdown code blocks if available
                    if "```python" in content:
                        start = content.find("```python") + len("```python")
                        end = content.rfind("```")
                        if start > 0 and end > start:
                            extracted_code = content[start:end].strip()
                            # Simple heuristic: if the code looks safe (no imports of concerning modules)
                            is_safe = all(unsafe_import not in extracted_code.lower() 
                                         for unsafe_import in ["import os", "import subprocess", "import socket"])
                            return extracted_code, is_safe, "Response was not properly formatted as JSON, but code was extracted"
                    
                    # If we couldn't extract code from a code block, try to find imports and def statements
                    import_pattern = r"import [a-zA-Z0-9_]+"
                    def_pattern = r"def [a-zA-Z0-9_]+\("
                    
                    if re.search(import_pattern, content) and re.search(def_pattern, content):
                        # Treat the entire content as code - risky but better than nothing
                        logger.warning("Treating entire response as code")
                        is_safe = all(unsafe_import not in content.lower() 
                                     for unsafe_import in ["import os", "import subprocess", "import socket"])
                        return content, is_safe, "Treating entire response as code (no JSON structure found)"
                    
                    logger.error("Could not extract code from response")
                    return None, False, "Failed to generate code: Could not parse response"
                
                return (
                    generation_result.get("generated_code", None),
                    generation_result.get("is_safe", False),
                    generation_result.get("explanation", "No explanation provided")
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Together AI response: {content}")
                
                # Extract code from any markdown code blocks if available
                if "```python" in content:
                    start = content.find("```python") + len("```python")
                    end = content.rfind("```")
                    if start > 0 and end > start:
                        extracted_code = content[start:end].strip()
                        # Simple heuristic: if the code looks safe (no imports of concerning modules)
                        is_safe = all(unsafe_import not in extracted_code.lower() 
                                     for unsafe_import in ["import os", "import subprocess", "import socket"])
                        return extracted_code, is_safe, "Response was not properly formatted as JSON, but code was extracted"
                
                # If we couldn't extract code from a code block, try to find imports and def statements
                import_pattern = r"import [a-zA-Z0-9_]+"
                def_pattern = r"def [a-zA-Z0-9_]+\("
                
                if re.search(import_pattern, content) and re.search(def_pattern, content):
                    # Treat the entire content as code - risky but better than nothing
                    logger.warning("Treating entire response as code")
                    is_safe = all(unsafe_import not in content.lower() 
                                 for unsafe_import in ["import os", "import subprocess", "import socket"])
                    return content, is_safe, "Treating entire response as code (no JSON structure found)"
                
                logger.error("Could not extract code from response")
                return None, False, "Failed to generate code: Could not parse response"
                
    except Exception as e:
        logger.error(f"Error generating code with Together AI: {str(e)}")
        return None, False, f"Generation error: {str(e)}"

async def validate_existing_code(code: str) -> Tuple[str, bool, str]:
    """
    Validates and potentially improves existing Python code.
    
    Args:
        code: The Python code to validate
        
    Returns:
        Tuple containing:
        - validated_code: The validated and potentially improved code
        - is_safe: Boolean indicating if the code is safe to execute
        - explanation: Explanation of issues found or improvements made
    """
    if not TOGETHER_API_KEY:
        logger.warning("TOGETHER_API_KEY not set, skipping code validation")
        return code, True, "Validation skipped: API key not configured"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an expert Python security analyst. "
                                "Analyze the given Python code for security issues, and either validate it or improve it. "
                                "VERY IMPORTANT: YOUR RESPONSE MUST BE VALID JSON in this format:\n"
                                "{\n"
                                "  \"validated_code\": \"FULL_PYTHON_CODE_HERE\",\n"
                                "  \"is_safe\": true_or_false,\n"
                                "  \"explanation\": \"brief explanation of issues/improvements\"\n"
                                "}\n\n"
                                "Do not include any explanatory text, headers, or markdown formatting outside of the JSON object."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Review this Python code:\n```python\n{code}\n```"
                        }
                    ],
                    "temperature": 0.2,
                    "timeout": API_TIMEOUT
                },
                timeout=API_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract the content from the response
            content = result["choices"][0]["message"]["content"]
            
            # Parse the JSON from the content
            try:
                # Find JSON in the content if it's wrapped in text
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    json_str = content[json_start:json_end]
                    validation_result = json.loads(json_str)
                else:
                    # Fallback if no JSON found
                    logger.warning("Could not find JSON in Together AI response")
                    
                    # Extract validated code from any markdown code blocks if available
                    if "```python" in content:
                        start = content.find("```python") + len("```python")
                        end = content.rfind("```")
                        if start > 0 and end > start:
                            extracted_code = content[start:end].strip()
                            # Simple heuristic: if the code looks safe (no imports of concerning modules)
                            is_safe = all(unsafe_import not in extracted_code.lower() 
                                         for unsafe_import in ["import os", "import subprocess", "import socket"])
                            return extracted_code, is_safe, "Validation response was not properly formatted as JSON, but code was extracted"
                    
                    # If we get here, we couldn't extract code properly
                    return code, True, "Validation response parsing failed, using original code"
                
                return (
                    validation_result.get("validated_code", code),
                    validation_result.get("is_safe", False),
                    validation_result.get("explanation", "No explanation provided")
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from Together AI response: {content}")
                
                # Extract validated code from any markdown code blocks if available
                if "```python" in content:
                    start = content.find("```python") + len("```python")
                    end = content.rfind("```")
                    if start > 0 and end > start:
                        extracted_code = content[start:end].strip()
                        # Simple heuristic: if the code looks safe (no imports of concerning modules)
                        is_safe = all(unsafe_import not in extracted_code.lower() 
                                     for unsafe_import in ["import os", "import subprocess", "import socket"])
                        return extracted_code, is_safe, "Validation response was not properly formatted as JSON, but code was extracted"
                
                # If we couldn't extract code, use the original but warn
                return code, True, "Using original code: JSON parsing failed"
                
    except Exception as e:
        logger.error(f"Error validating code with Together AI: {str(e)}")
        return code, True, f"Validation error: {str(e)} - using original code" 