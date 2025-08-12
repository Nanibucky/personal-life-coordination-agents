"""
Enhanced MCP Server Base Implementation
Fully compliant with Model Context Protocol specification
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class MCPToolCall(BaseModel):
    """MCP Tool call request"""
    name: str
    arguments: Dict[str, Any]


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


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True


class MCPResource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mimeType: str


class MCPCapabilities(BaseModel):
    """MCP Server capabilities"""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


class EnhancedMCPServer(ABC):
    """
    Enhanced MCP Server Base Class
    Fully compliant with MCP specification
    """
    
    def __init__(self, server_name: str, port: int, description: str = ""):
        self.server_name = server_name
        self.port = port
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        self.capabilities = MCPCapabilities(
            tools={"listChanged": True},
            resources={"subscribe": True, "listChanged": True},
            logging={}
        )
        
        # Initialize FastAPI app
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
                self.logger.info(f"Received MCP request: {request.method}")
                
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
                elif request.method == "ping":
                    return MCPResponse(id=request.id, result={})
                else:
                    return MCPResponse(
                        id=request.id,
                        error={
                            "code": -32601,
                            "message": f"Method not found: {request.method}"
                        }
                    )
            except Exception as e:
                self.logger.error(f"Error handling MCP request: {str(e)}")
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server": self.server_name,
                "tools_count": len(self.tools),
                "resources_count": len(self.resources),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP initialize request"""
        client_info = request.params or {}
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities.dict(exclude_none=True),
            "serverInfo": {
                "name": self.server_name,
                "version": "1.0.0",
                "description": self.description
            }
        }
        
        self.logger.info(f"Initialized MCP server for client: {client_info}")
        return MCPResponse(id=request.id, result=result)
    
    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request"""
        tools_list = []
        for tool_name, tool in self.tools.items():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        
        result = {"tools": tools_list}
        return MCPResponse(id=request.id, result=result)
    
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
                error={
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            )
        
        try:
            # Call the tool handler
            if tool_name in self.tool_handlers:
                result = await self.tool_handlers[tool_name](arguments)
            else:
                result = await self._execute_tool_fallback(tool_name, arguments)
            
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
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
        
        result = {"resources": resources_list}
        return MCPResponse(id=request.id, result=result)
    
    async def _handle_read_resource(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/read request"""
        if not request.params or "uri" not in request.params:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Missing resource URI"}
            )
        
        uri = request.params["uri"]
        
        if uri not in self.resources:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": f"Unknown resource: {uri}"}
            )
        
        try:
            content = await self._read_resource_content(uri)
            result = {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": self.resources[uri].mimeType,
                        "text": content
                    }
                ]
            }
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            self.logger.error(f"Error reading resource {uri}: {str(e)}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Resource read error: {str(e)}"
                }
            )
    
    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """Register a tool with the MCP server"""
        tool = MCPTool(
            name=name,
            description=description,
            inputSchema=input_schema
        )
        self.tools[name] = tool
        self.tool_handlers[name] = handler
        self.logger.info(f"Registered tool: {name}")
    
    def register_resource(self, uri: str, name: str, description: str, mime_type: str):
        """Register a resource with the MCP server"""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )
        self.resources[uri] = resource
        self.logger.info(f"Registered resource: {uri}")
    
    @abstractmethod
    async def _execute_tool_fallback(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Fallback method for executing tools if no handler is registered"""
        pass
    
    @abstractmethod
    async def _read_resource_content(self, uri: str) -> str:
        """Read the content of a resource"""
        pass
    
    async def start_server(self):
        """Start the MCP server"""
        await self.initialize_server()
        self.logger.info(f"Starting MCP server '{self.server_name}' on port {self.port}")
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    @abstractmethod
    async def initialize_server(self):
        """Initialize the server with tools and resources"""
        pass
