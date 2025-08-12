"""
MCP Client Implementation
For agents to communicate with MCP servers
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import aiohttp
import uuid


class MCPClientError(Exception):
    """MCP Client specific errors"""
    pass


class MCPClient:
    """
    MCP Client for agents to communicate with MCP servers
    All tool access must go through this client
    """
    
    def __init__(self, server_url: str, agent_name: str):
        self.server_url = server_url.rstrip('/')
        self.agent_name = agent_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(f"mcp_client_{agent_name}")
        self.capabilities = {}
        self.available_tools = {}
        self.available_resources = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    async def connect(self):
        """Connect to the MCP server"""
        self.session = aiohttp.ClientSession()
        await self.initialize()
        await self.refresh_capabilities()
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an MCP request to the server"""
        if not self.session:
            raise MCPClientError("Client not connected. Call connect() first.")
        
        request_id = str(uuid.uuid4())
        request_data = {
            "method": method,
            "id": request_id
        }
        
        if params:
            request_data["params"] = params
        
        try:
            async with self.session.post(
                f"{self.server_url}/mcp",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise MCPClientError(f"HTTP {response.status}: {await response.text()}")
                
                result = await response.json()
                
                if "error" in result:
                    raise MCPClientError(f"MCP Error: {result['error']}")
                
                return result.get("result", {})
                
        except aiohttp.ClientError as e:
            raise MCPClientError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid JSON response: {str(e)}")
    
    async def initialize(self):
        """Initialize connection with the MCP server"""
        client_info = {
            "clientInfo": {
                "name": self.agent_name,
                "version": "1.0.0"
            },
            "protocolVersion": "2024-11-05"
        }
        
        result = await self._make_request("initialize", client_info)
        self.capabilities = result.get("capabilities", {})
        
        self.logger.info(f"Initialized MCP connection for {self.agent_name}")
        self.logger.info(f"Server capabilities: {self.capabilities}")
        
        return result
    
    async def refresh_capabilities(self):
        """Refresh available tools and resources from server"""
        # Get available tools
        try:
            tools_result = await self._make_request("tools/list")
            self.available_tools = {
                tool["name"]: tool for tool in tools_result.get("tools", [])
            }
            self.logger.info(f"Available tools: {list(self.available_tools.keys())}")
        except Exception as e:
            self.logger.warning(f"Could not fetch tools: {str(e)}")
        
        # Get available resources
        try:
            resources_result = await self._make_request("resources/list")
            self.available_resources = {
                resource["uri"]: resource for resource in resources_result.get("resources", [])
            }
            self.logger.info(f"Available resources: {list(self.available_resources.keys())}")
        except Exception as e:
            self.logger.warning(f"Could not fetch resources: {str(e)}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server
        This is the ONLY way agents should access tools
        """
        if tool_name not in self.available_tools:
            available = list(self.available_tools.keys())
            raise MCPClientError(f"Tool '{tool_name}' not available. Available tools: {available}")
        
        self.logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
        
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        result = await self._make_request("tools/call", params)
        
        # Extract text content from MCP response
        content = result.get("content", [])
        if content and len(content) > 0 and "text" in content[0]:
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return {"result": content[0]["text"]}
        
        return result
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource from the MCP server"""
        if uri not in self.available_resources:
            available = list(self.available_resources.keys())
            raise MCPClientError(f"Resource '{uri}' not available. Available resources: {available}")
        
        self.logger.info(f"Reading resource: {uri}")
        
        params = {"uri": uri}
        result = await self._make_request("resources/read", params)
        
        # Extract content from MCP response
        contents = result.get("contents", [])
        if contents and len(contents) > 0:
            return contents[0].get("text", "")
        
        return ""
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        result = await self._make_request("tools/list")
        return result.get("tools", [])
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources"""
        result = await self._make_request("resources/list")
        return result.get("resources", [])
    
    async def ping(self) -> bool:
        """Ping the MCP server to check connectivity"""
        try:
            await self._make_request("ping")
            return True
        except Exception as e:
            self.logger.error(f"Ping failed: {str(e)}")
            return False
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool"""
        return self.available_tools.get(tool_name, {}).get("inputSchema")
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        return tool_name in self.available_tools
    
    def is_resource_available(self, uri: str) -> bool:
        """Check if a resource is available"""
        return uri in self.available_resources
