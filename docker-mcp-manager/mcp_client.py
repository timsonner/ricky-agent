#!/usr/bin/env python3
"""
Simple MCP client to test the Docker Container Manager MCP Server
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Server parameters - pointing to our MCP server
    server_params = StdioServerParameters(
        command="python3",
        args=["docker_mcp_server.py"],
        # We're already in the docker-mcp-manager directory
    )
    
    print("Connecting to MCP server...")
    
    # Connect to the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            
            # List available tools
            print("Listing available tools...")
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Test each tool
            print("\n=== Testing MCP Tools ===")
            
            # 1. Get container info
            print("\n1. Getting container info...")
            result = await session.call_tool("get_container_info", {})
            print(f"Container info: {result.content[0].text}")
            
            # 2. Execute a simple command
            print("\n2. Executing 'ls -la /data' command...")
            result = await session.call_tool("execute_command", {"command": "ls -la /data"})
            print(f"Command result: {result.content[0].text}")
            
            # 3. Check if a file exists
            print("\n3. Checking if /data/test.txt exists...")
            result = await session.call_tool("check_file_exists", {"file_path": "/data/test.txt"})
            print(f"File exists: {result.content[0].text}")
            
            # 4. Write a file
            print("\n4. Writing to /data/test.txt...")
            result = await session.call_tool("write_file", {
                "file_path": "/data/test.txt",
                "content": "Hello from MCP client!\nThis is a test file.\nTimestamp: $(date)"
            })
            print(f"Write result: {result.content[0].text}")
            
            # 5. Read the file
            print("\n5. Reading from /data/test.txt...")
            result = await session.call_tool("read_file", {"file_path": "/data/test.txt"})
            print(f"File content:\n{result.content[0].text}")
            
            # 6. List directory
            print("\n6. Listing /data directory...")
            result = await session.call_tool("list_directory", {"dir_path": "/data"})
            print(f"Directory contents: {result.content[0].text}")
            
            print("\n=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())
