#!/bin/bash
# Script to start the Docker MCP Server

echo "Starting Docker Container Manager MCP Server..."
echo "Make sure docker-compose is running first:"
echo "  docker compose up -d"
echo ""
echo "Starting MCP server..."
source .venv/bin/activate && python docker_mcp_server.py