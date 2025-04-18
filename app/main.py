from fastapi import FastAPI, HTTPException, BackgroundTasks
import subprocess
import tempfile
import os
import uuid
import shutil
import asyncio
from pydantic import BaseModel
import logging
from typing import Optional
import docker
import json

from services.code_manager import generate_and_validate_code, validate_existing_code

app = FastAPI(title="Secure Python Code Execution API")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Docker client
docker_client = docker.from_env()

# Define request models
class CodeExecutionRequest(BaseModel):
    code: str
    timeout: int = 10  # Default timeout in seconds
    memory_limit: str = "100m"  # Default memory limit
    cpu_limit: float = 0.5  # Default CPU limit (half a core)
    validate_code: bool = True  # Whether to validate code with Together AI

class QueryExecutionRequest(BaseModel):
    query: str
    timeout: int = 15  # Default timeout in seconds
    memory_limit: str = "100m"  # Default memory limit
    cpu_limit: float = 0.5  # Default CPU limit (half a core)

# Define response models
class CodeExecutionResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    original_code: str
    executed_code: str
    validation_result: Optional[str] = None

class QueryExecutionResponse(BaseModel):
    query: str
    generated_code: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    validation_result: Optional[str] = None

@app.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    Execute Python code in an isolated Docker container.
    
    The code is executed in a secure environment with:
    - No network access
    - Limited CPU and memory resources
    - Execution timeout
    - No access to host filesystem
    """
    execution_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix=f"code_exec_{execution_id}_")
    
    original_code = request.code
    executed_code = original_code
    validation_result = None
    
    try:
        # Validate code if requested
        if request.validate_code:
            logger.info(f"Validating code with ID: {execution_id}")
            executed_code, is_safe, validation_result = await validate_existing_code(request.code)
            
            if not is_safe:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Code validation failed: {validation_result}"
                )
        
        # Write code to temporary file
        code_file_path = os.path.join(temp_dir, "code.py")
        with open(code_file_path, "w") as f:
            f.write(executed_code)
        
        logger.info(f"Executing code with ID: {execution_id}")
        
        # Run in Docker container
        start_time = asyncio.get_event_loop().time()
        
        try:
            container = docker_client.containers.run(
                image="python-code-execution:latest",
                command=["python", "/code/code.py"],
                volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
                mem_limit=request.memory_limit,
                cpu_quota=int(100000 * request.cpu_limit),  # Docker CPU quota in microseconds
                network_mode="none",  # Disable networking
                detach=True,
                remove=False,  # We'll remove it manually to ensure cleanup
                read_only=True,  # Read-only filesystem
                cap_drop=["ALL"],  # Drop all capabilities
                security_opt=["no-new-privileges:true"],  # Prevent privilege escalation
            )
            
            # Wait for execution with timeout
            try:
                container.wait(timeout=request.timeout)
            except:
                logger.warning(f"Execution timed out for ID: {execution_id}")
            
            logs = container.logs(stdout=True, stderr=True)
            exit_code = container.attrs['State']['ExitCode']
            
            # Try to get separate stdout/stderr if available
            try:
                stdout_logs = container.logs(stdout=True, stderr=False).decode('utf-8')
            except:
                stdout_logs = ""
                
            try:
                stderr_logs = container.logs(stdout=False, stderr=True).decode('utf-8')
            except:
                stderr_logs = ""
                
            # If separate logs failed, use combined logs
            if not stdout_logs and not stderr_logs:
                stdout_logs = logs.decode('utf-8')
                stderr_logs = ""
                
            # Clean up container
            try:
                container.remove(force=True)
            except:
                logger.error(f"Failed to remove container for ID: {execution_id}")
                
        except Exception as e:
            logger.error(f"Container execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
            
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        return CodeExecutionResponse(
            stdout=stdout_logs,
            stderr=stderr_logs,
            exit_code=exit_code,
            execution_time=execution_time,
            original_code=original_code,
            executed_code=executed_code,
            validation_result=validation_result
        )
        
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Failed to remove temporary directory: {str(e)}")

@app.post("/generate-and-execute", response_model=QueryExecutionResponse)
async def generate_and_execute_code(request: QueryExecutionRequest):
    """
    Generate Python code from a query and execute it securely.
    
    This endpoint:
    1. Generates and validates Python code based on the user query using Together AI
    2. Executes the code in a secure Docker container
    3. Returns the execution results
    """
    execution_id = str(uuid.uuid4())
    logger.info(f"Processing query execution with ID: {execution_id}")
    
    # Generate and validate code in a single step
    logger.info(f"Generating and validating code for query: {request.query}")
    generated_code, is_safe, validation_result = await generate_and_validate_code(request.query)
    
    if not generated_code:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate code from query"
        )
        
    if not is_safe:
        logger.warning(f"Generated code for query '{request.query}' was deemed unsafe: {validation_result}")
        raise HTTPException(
            status_code=400,
            detail=f"Generated code validation failed: {validation_result}"
        )
        
    # Execute the validated code
    temp_dir = tempfile.mkdtemp(prefix=f"query_exec_{execution_id}_")
    
    try:
        # Write code to temporary file
        code_file_path = os.path.join(temp_dir, "code.py")
        with open(code_file_path, "w") as f:
            f.write(generated_code)
        
        logger.info(f"Executing generated code")
        
        # Run in Docker container
        start_time = asyncio.get_event_loop().time()
        
        try:
            container = docker_client.containers.run(
                image="python-code-execution:latest",
                command=["python", "/code/code.py"],
                volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
                mem_limit=request.memory_limit,
                cpu_quota=int(100000 * request.cpu_limit),
                network_mode="none",
                detach=True,
                remove=False,
                read_only=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
            )
            
            # Wait for execution with timeout
            try:
                container.wait(timeout=request.timeout)
            except:
                logger.warning(f"Execution timed out for ID: {execution_id}")
            
            logs = container.logs(stdout=True, stderr=True)
            exit_code = container.attrs['State']['ExitCode']
            
            # Get stdout/stderr
            try:
                stdout_logs = container.logs(stdout=True, stderr=False).decode('utf-8')
            except:
                stdout_logs = ""
                
            try:
                stderr_logs = container.logs(stdout=False, stderr=True).decode('utf-8')
            except:
                stderr_logs = ""
                
            # If separate logs failed, use combined logs
            if not stdout_logs and not stderr_logs:
                stdout_logs = logs.decode('utf-8')
                stderr_logs = ""
                
            # Clean up container
            try:
                container.remove(force=True)
            except:
                logger.error(f"Failed to remove container for ID: {execution_id}")
                
        except Exception as e:
            logger.error(f"Container execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
            
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        return QueryExecutionResponse(
            query=request.query,
            generated_code=generated_code,
            stdout=stdout_logs,
            stderr=stderr_logs,
            exit_code=exit_code,
            execution_time=execution_time,
            validation_result=validation_result
        )
        
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Failed to remove temporary directory: {str(e)}")

@app.get("/health")
async def health_check():
    """Endpoint to check if the service is running."""
    return {"status": "healthy"} 