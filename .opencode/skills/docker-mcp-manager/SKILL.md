---
name: docker-mcp-manager
description: A skill for managing a Docker container with persistent storage, providing tools for executing commands and managing files
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: container-management
---
# Docker MCP Manager Skill

This skill provides tools for managing a Docker container with persistent storage. It allows agents to execute commands and manage files within the container.

## What I do

- Execute shell commands in a managed Docker container with root privileges
- Read and write files in the container's persistent storage
- List directory contents in the container
- Get information about the managed container
- Check if files or directories exist in the container

## Available Tools

- `execute_command`: Execute a shell command in the managed container
- `read_file`: Read the contents of a file in the container's persistent storage
- `write_file`: Write content to a file in the container's persistent storage
- `list_directory`: List the contents of a directory in the container's persistent storage
- `get_container_info`: Get information about the managed container
- `check_file_exists`: Check if a file or directory exists in the container's persistent storage

## When to use me

Use this skill when you need to:
- Run commands in an isolated Docker environment
- Persist data between operations in a container
- Manage files within a Docker container from an agent
- Execute privileged operations in a controlled container environment
- Check the status and configuration of a managed container

## Example Usage

```python
# Execute a command in the container
result = await execute_command("ls -la /data")

# Read a file from the container
content = await read_file("path/to/file.txt")

# Write content to a file in the container
await write_file("path/to/file.txt", "Hello, World!")

# List directory contents
files = await list_directory("/data")

# Check container status
info = await get_container_info()

# Check if a file exists
exists = await check_file_exists("path/to/file.txt")
```

## Requirements

- Docker must be installed and running
- A container named "managed-container" must be running with a volume mounted at /data
- The container should be started with appropriate privileges for the tools to work correctly

## Getting Started

To start the managed container:

```bash
docker-compose up -d
```

This will:
- Create and start an Ubuntu 22.04 container in privileged mode
- Mount a persistent volume at `/data` inside the container
- Keep the container running with a `tail -f /dev/null` command

Verify the container is running:
```bash
docker-compose ps
```

You should see the `managed-container` service with status "Up".

## Notes

All file paths are relative to the persistent mount point `/data` inside the container.
Path traversal protection is implemented to ensure operations stay within the allowed directory.