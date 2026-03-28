# Docker Container Manager MCP Server

An MCP (Model Context Protocol) server that exposes tools to manage a Docker container with persistent storage, allowing AI agents (like opencode) to execute commands and manage files within the container with root privileges.

## Features

- Execute shell commands in a privileged Docker container
- Read and write files in persistent storage
- List directory contents
- Check file/directory existence
- Get container information
- Persistent storage volume for data persistence
- Root privileges for all operations

## Prerequisites

- Docker Engine installed and running
- Docker Compose v2
- Python 3.10 or higher
- `uv` package manager (recommended) or pip

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd docker-mcp-manager
```

### 2. Install dependencies

Using uv (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

### 3. Start the managed container

```bash
docker-compose up -d
```

This will:
- Create and start an Ubuntu 22.04 container in privileged mode
- Mount a persistent volume at `/data` inside the container
- Keep the container running with a `tail -f /dev/null` command

### 4. Verify the container is running

```bash
docker-compose ps
```

You should see the `managed-container` service with status "Up".

### 5. Run the MCP server

```bash
python docker_mcp_server.py
```

The server will start and communicate via stdio (required for MCP STDIO transport).

## Using with OpenCode

To connect this MCP server to OpenCode:

1. Add the MCP server to `opencode.json` in your project root (or `~/.config/opencode/opencode.json` for global config):
   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "mcp": {
       "docker-mcp-manager": {
         "type": "local",
         "command": ["python3", "docker-mcp-manager/docker_mcp_server.py"],
         "enabled": true
       }
     }
   }
   ```
2. Restart OpenCode to load the MCP server

## Using with VS Code

To connect this MCP server to VS Code (GitHub Copilot):

1. Create or edit `.vscode/mcp.json` in your project root:
   ```json
   {
     "servers": {
       "docker-mcp-manager": {
         "type": "stdio",
         "command": "python3",
         "args": ["docker-mcp-manager/docker_mcp_server.py"]
       }
     }
   }
   ```
2. VS Code will prompt you to trust and start the server. You can also run **MCP: List Servers** from the Command Palette to manage it.

## Available Tools

Once connected, the agent will have access to these tools:

### `execute_command`
Run shell commands in the container with root privileges.
- **Parameters**: `command` (string) - The shell command to execute
- **Returns**: Command output (stdout + stderr) or error message

### `read_file`
Read contents of a file from persistent storage.
- **Parameters**: `file_path` (string) - Path relative to `/data` mount point
- **Returns**: File contents as string

### `write_file`
Write content to a file in persistent storage.
- **Parameters**: 
  - `file_path` (string) - Path relative to `/data` mount point
  - `content` (string) - Content to write
- **Returns**: Success message or error

### `list_directory`
List contents of a directory in persistent storage.
- **Parameters**: `dir_path` (string) - Path relative to `/data` mount point
- **Returns**: Array of filenames and directory names

### `check_file_exists`
Check if a file or directory exists.
- **Parameters**: `file_path` (string) - Path relative to `/data` mount point
- **Returns**: Boolean (true if exists)

### `get_container_info`
Get information about the managed container.
- **Parameters**: None
- **Returns**: Object with container details (id, status, image, etc.)

## Persistent Storage

All file operations default to the `/data` directory inside the container, which is mounted to a Docker named volume called `persistent-data`. This ensures data persists across container restarts.

Example file paths:
- `/data/config.json` (absolute inside container)
- `config.json` (relative, resolves to `/data/config.json`)

## Security Notes

- The container runs in privileged mode to provide root access as requested
- All operations are confined to the container filesystem
- The MCP server runs locally and communicates via stdio
- Input validation is performed to prevent obvious injection attempts
- For production use, consider additional security measures based on your threat model

## Development

To run tests (when implemented):
```bash
uv run pytest
```

To format code:
```bash
uv run ruff format .
```

To check types:
```bash
uv run pyrefly check
```

## Troubleshooting

### Container not starting
```bash
docker-compose logs managed-container
```

### MCP server connection issues
Ensure the container is running before starting the MCP server:
```bash
docker-compose ps
```

### Permission denied errors
The container runs in privileged mode and operations execute as root, so permission issues should not occur. If they do, check that the container is actually running in privileged mode:
```bash
docker inspect managed-container --format='{{.HostConfig.Privileged}}'
```

## License

MIT