"""
MCP Server Base Implementation
Compliant with Model Context Protocol specification
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    function: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True


class MCPRequest(BaseModel):
    """MCP Request format"""
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP Response format"""
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPResource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mimeType: str


class BaseMCPServer(ABC):
    """
    Base class for MCP-compliant agent servers
    """
    
    def __init__(self, server_name: str, port: int, description: str = ""):
        self.server_name = server_name
        self.port = port
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.app = FastAPI(
            title=f"MCP Server - {server_name}",
            description=description,
            version="1.0.0"
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.logger = logging.getLogger(f"mcp_server_{server_name}")
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup MCP-compliant routes"""
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
            """Main MCP request handler"""
            try:
                if request.method == "initialize":
                    return await self._handle_initialize(request)
                elif request.method == "tools/list":
                    return await self._handle_list_tools(request)
                elif request.method == "tools/call":
                    return await self._handle_call_tool(request)
                elif request.method == "resources/list":
                    return await self._handle_list_resources(request)
                elif request.method == "resources/read":
                    return await self._handle_read_resource(request)
                else:
                    return MCPResponse(
                        id=request.id,
                        error={"code": -32601, "message": f"Method not found: {request.method}"}
                    )
            except Exception as e:
                self.logger.error(f"MCP request error: {e}")
                return MCPResponse(
                    id=request.id,
                    error={"code": -32603, "message": f"Internal error: {str(e)}"}
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server_name": self.server_name,
                "mcp_version": "1.0.0",
                "tools_count": len(self.tools),
                "resources_count": len(self.resources),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/info")
        async def server_info():
            """Server information endpoint"""
            return {
                "server_name": self.server_name,
                "description": self.description,
                "port": self.port,
                "tools": list(self.tools.keys()),
                "resources": list(self.resources.keys()),
                "capabilities": self._get_capabilities()
            }
    
    async def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP initialize request"""
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": "1.0.0",
                "capabilities": self._get_capabilities(),
                "serverInfo": {
                    "name": self.server_name,
                    "version": "1.0.0",
                    "description": self.description
                }
            }
        )
    
    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request"""
        tools_list = []
        for tool_name, tool in self.tools.items():
            tools_list.append({
                "name": tool_name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        
        return MCPResponse(
            id=request.id,
            result={"tools": tools_list}
        )
    
    async def _handle_call_tool(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request"""
        if not request.params:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Invalid params"}
            )
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if tool_name not in self.tools:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Tool not found: {tool_name}"}
            )
        
        try:
            tool = self.tools[tool_name]
            if tool.function:
                result = await tool.function(arguments)
            else:
                result = await self._execute_tool(tool_name, arguments)
            
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ],
                    "isError": False
                }
            )
        except Exception as e:
            self.logger.error(f"Tool execution error: {e}")
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Error executing tool: {str(e)}"
                        }
                    ],
                    "isError": True
                }
            )
    
    async def _handle_list_resources(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/list request"""
        resources_list = []
        for resource_uri, resource in self.resources.items():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mimeType
            })
        
        return MCPResponse(
            id=request.id,
            result={"resources": resources_list}
        )
    
    async def _handle_read_resource(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/read request"""
        if not request.params:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Invalid params"}
            )
        
        uri = request.params.get("uri")
        if uri not in self.resources:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Resource not found: {uri}"}
            )
        
        try:
            content = await self._read_resource(uri)
            return MCPResponse(
                id=request.id,
                result={
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": self.resources[uri].mimeType,
                            "text": content
                        }
                    ]
                }
            )
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={"code": -32603, "message": f"Error reading resource: {str(e)}"}
            )
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities"""
        return {
            "tools": {"listChanged": True},
            "resources": {"subscribe": True, "listChanged": True}
        }
    
    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], 
                     function: Optional[Callable] = None):
        """Register a new tool"""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            function=function
        )
        self.logger.info(f"Registered tool: {name}")
    
    def register_resource(self, uri: str, name: str, description: str, mime_type: str):
        """Register a new resource"""
        self.resources[uri] = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )
        self.logger.info(f"Registered resource: {uri}")
    
    @abstractmethod
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def _read_resource(self, uri: str) -> str:
        """Read a resource - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def initialize_agent(self):
        """Initialize agent-specific tools and resources"""
        pass
    
    async def start(self):
        """Start the MCP server"""
        await self.initialize_agent()
        self.logger.info(f"Starting MCP server {self.server_name} on port {self.port}")
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self):
        """Run the MCP server"""
        asyncio.run(self.start())


class MCPClient:
    """
    MCP Client for communicating with MCP servers
    """
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.logger = logging.getLogger("mcp_client")
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> MCPResponse:
        """Send MCP request to server"""
        import httpx
        
        request = MCPRequest(
            method=method,
            params=params,
            id=str(uuid.uuid4())
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.server_url}/mcp",
                    json=request.dict(),
                    timeout=30.0
                )
                response.raise_for_status()
                return MCPResponse(**response.json())
        except Exception as e:
            self.logger.error(f"MCP request failed: {e}")
            raise
    
    async def initialize(self) -> MCPResponse:
        """Initialize connection with server"""
        return await self.send_request("initialize")
    
    async def list_tools(self) -> MCPResponse:
        """List available tools"""
        return await self.send_request("tools/list")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """Call a tool"""
        return await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
    
    async def list_resources(self) -> MCPResponse:
        """List available resources"""
        return await self.send_request("resources/list")
    
    async def read_resource(self, uri: str) -> MCPResponse:
        """Read a resource"""
        return await self.send_request("resources/read", {"uri": uri})