#!/usr/bin/env python3
"""
MCP Server for managing a Docker container with persistent storage.
Exposes tools for an agent to execute commands and manage files in the container.
"""
import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("docker-container-manager")

# Constants
CONTAINER_NAME = "managed-container"
PERSISTENT_MOUNT_POINT = "/data"  # Inside the container where the volume is mounted

# Setup logging (write to stderr for STDIO servers)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

def run_docker_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        return result
    except Exception as e:
        logger.error(f"Error running docker command {' '.join(cmd)}: {e}")
        raise

def _get_container_info() -> Dict[str, Any]:
    """Get the managed container info as a dictionary, raising an error if not found or not running."""
    try:
        # Get container info as JSON
        result = run_docker_command([
            "docker", "inspect", CONTAINER_NAME
        ])
        
        if result.returncode != 0:
            if "No such object" in result.stderr or "not found" in result.stderr.lower():
                raise Exception(f"Container {CONTAINER_NAME} not found. Is docker-compose up?")
            else:
                raise Exception(f"Error inspecting container: {result.stderr}")
        
        # Parse JSON (inspect returns a list)
        container_list = json.loads(result.stdout)
        if not container_list:
            raise Exception(f"Container {CONTAINER_NAME} not found")
            
        container_info = container_list[0]
        
        # Check if container is running
        state = container_info.get('State', {})
        if state.get('Status') != "running":
            raise Exception(f"Container {CONTAINER_NAME} is not running (status: {state.get('Status')})")
            
        return container_info
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing container info: {e}")
    except Exception as e:
        raise Exception(f"Error accessing container: {e}")

@mcp.tool()
async def execute_command(command: str) -> str:
    """
    Execute a shell command in the managed container with root privileges.
    
    Args:
        command: The shell command to execute
        
    Returns:
        The combined stdout and stderr output of the command
    """
    logger.info(f"Executing command in container: {command}")
    try:
        # Execute command in the container using docker exec
        result = run_docker_command([
            "docker", "exec",
            "--user", "root",
            "--privileged",
            CONTAINER_NAME,
            "sh", "-c", command
        ])
        
        output_str = result.stdout + result.stderr
        
        if result.returncode != 0:
            logger.warning(f"Command exited with code {result.returncode}: {output_str}")
            return f"Command failed with exit code {result.returncode}:\n{output_str}"
        else:
            logger.info(f"Command executed successfully: {output_str[:100]}{'...' if len(output_str) > 100 else ''}")
            return output_str.strip()
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return f"Error executing command: {str(e)}"

@mcp.tool()
async def read_file(file_path: str) -> str:
    """
    Read the contents of a file in the container's persistent storage.
    
    Args:
        file_path: Path to the file (relative to the persistent mount point /data)
        
    Returns:
        The contents of the file as a string
    """
    # Ensure the path is within the persistent storage for safety
    # We'll prepend the persistent mount point if not already an absolute path starting with it
    if not file_path.startswith(PERSISTENT_MOUNT_POINT):
        # If it's an absolute path, we still restrict to the mount point for safety
        # For simplicity, we'll treat all paths as relative to the mount point
        full_path = f"{PERSISTENT_MOUNT_POINT}/{file_path.lstrip('/')}"
    else:
        full_path = file_path
    
    logger.info(f"Reading file: {full_path}")
    try:
        # Read file using docker exec cat command
        result = run_docker_command([
            "docker", "exec",
            CONTAINER_NAME,
            "cat", full_path
        ])
        
        if result.returncode != 0:
            logger.error(f"Failed to read file: {result.stderr}")
            return f"Error reading file: {result.stderr.strip()}"
            
        logger.info(f"Successfully read file ({len(result.stdout)} bytes)")
        return result.stdout
        
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file in the container's persistent storage.
    
    Args:
        file_path: Path to the file (relative to the persistent mount point /data)
        content: The content to write to the file
        
    Returns:
        Success message or error
    """
    # Ensure the path is within the persistent storage
    if not file_path.startswith(PERSISTENT_MOUNT_POINT):
        full_path = f"{PERSISTENT_MOUNT_POINT}/{file_path.lstrip('/')}"
    else:
        full_path = file_path
    
    logger.info(f"Writing to file: {full_path} ({len(content)} bytes)")
    try:
        # Write file using docker exec with sh -c to handle redirection properly
        # Escape single quotes in content for shell safety
        escaped_content = content.replace("'", "'\"'\"'")
        result = run_docker_command([
            "docker", "exec",
            "--user", "root",
            CONTAINER_NAME,
            "sh", "-c", f'printf %s "{escaped_content}" > {full_path}'
        ])
        
        if result.returncode != 0:
            logger.error(f"Failed to write file: {result.stderr}")
            return f"Error writing file: {result.stderr.strip()}"
            
        logger.info(f"Successfully wrote to file: {full_path}")
        return f"Successfully wrote to {full_path}"
        
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        return f"Error writing file: {str(e)}"

@mcp.tool()
async def list_directory(dir_path: str) -> List[str]:
    """
    List the contents of a directory in the container's persistent storage.
    
    Args:
        dir_path: Path to the directory (relative to the persistent mount point /data)
        
    Returns:
        List of filenames and directory names in the specified directory
    """
    # Ensure the path is within the persistent storage
    if not dir_path.startswith(PERSISTENT_MOUNT_POINT):
        full_path = f"{PERSISTENT_MOUNT_POINT}/{dir_path.lstrip('/')}"
    else:
        full_path = dir_path
    
    logger.info(f"Listing directory: {full_path}")
    try:
        # List directory using docker exec ls command
        result = run_docker_command([
            "docker", "exec",
            CONTAINER_NAME,
            "ls", "-la", full_path
        ])
        
        if result.returncode != 0:
            logger.error(f"Failed to list directory: {result.stderr}")
            return [f"Error listing directory: {result.stderr.strip()}"]
            
        output_str = result.stdout
        # Parse the ls -la output to extract just filenames
        lines = output_str.strip().split('\n')
        files = []
        for line in lines:
            # Skip the total line
            if line.startswith('total'):
                continue
            # Extract the filename (last field)
            parts = line.split()
            if len(parts) >= 9:
                filename = parts[8]
                # Handle filenames with spaces (they would be quoted in ls output, but we keep it simple)
                files.append(filename)
            elif len(parts) > 0:
                # Fallback: just take the last part
                files.append(parts[-1])
                
        logger.info(f"Listed {len(files)} items in directory")
        return files
        
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        return [f"Error listing directory: {str(e)}"]

@mcp.tool()
async def get_container_info() -> Dict[str, Any]:
    """
    Get information about the managed container.
    
    Returns:
        Dictionary containing container information (id, status, ports, etc.)
    """
    logger.info("Getting container information")
    try:
        # Get container info using our function
        container_info = _get_container_info()  # This will use the function we defined earlier
        
        # Extract information from the container inspection dict
        # Safely get image information
        image_info = "unknown"
        config = container_info.get('Config', {})
        if config:
            image_info = config.get('Image', 'unknown')
        
        # Get network settings for ports
        network_settings = container_info.get('NetworkSettings', {})
        ports = network_settings.get('Ports', {})
        
        # Get host config
        host_config = container_info.get('HostConfig', {})
        
        info = {
            "id": container_info.get('Id', ''),
            "name": container_info.get('Name', '').lstrip('/'),  # Remove leading slash
            "status": container_info.get('State', {}).get('Status', 'unknown'),
            "image": image_info,
            "ports": ports,
        }
        
        # Host config information
        info["host_config"] = {
            "privileged": host_config.get('Privileged', False),
            "binds": host_config.get('Binds', [])
        }
            
        logger.info(f"Container info retrieved: {info['status']}")
        return info
    except Exception as e:
        logger.error(f"Error getting container info: {e}")
        return {"error": str(e)}

@mcp.tool()
async def check_file_exists(file_path: str) -> bool:
    """
    Check if a file or directory exists in the container's persistent storage.
    
    Args:
        file_path: Path to the file or directory (relative to the persistent mount point /data)
        
    Returns:
        True if the file/directory exists, False otherwise
    """
    # Ensure the path is within the persistent storage
    if not file_path.startswith(PERSISTENT_MOUNT_POINT):
        full_path = f"{PERSISTENT_MOUNT_POINT}/{file_path.lstrip('/')}"
    else:
        full_path = file_path
    
    logger.info(f"Checking if file exists: {full_path}")
    try:
        # Check file/directory existence using docker exec test command
        # We need to use sh -c to properly handle the shell operators
        result = run_docker_command([
            "docker", "exec",
            CONTAINER_NAME,
            "sh", "-c", f"test -e {full_path} && echo 'exists' || echo 'not found'"
        ])
        
        output = result.stdout.strip()
        exists = output == 'exists'
        logger.info(f"File existence check: {full_path} -> {exists}")
        return exists
        
    except Exception as e:
        logger.error(f"Error checking file existence: {e}")
        return False

def main():
    """Initialize and run the server."""
    logger.info("Starting Docker Container Manager MCP Server")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()