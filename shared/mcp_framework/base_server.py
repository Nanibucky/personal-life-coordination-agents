"""
Base MCP Server Implementation
Provides core server functionality for all agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

@dataclass
class ExecutionContext:
    """Context for tool execution"""
    user_id: str
    session_id: str
    permissions: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ExecutionResult:
    """Result of tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseMCPTool:
    """Base class for all MCP tools"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"tool.{name}")
    
    async def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {}
        }

class BaseMCPServer:
    """Base MCP Server for all agents"""
    
    def __init__(self, agent_name: str, port: int, config: Dict[str, Any]):
        self.agent_name = agent_name
        self.port = port
        self.config = config
        self.tools: Dict[str, BaseMCPTool] = {}
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # Initialize FastAPI app
        self.app = FastAPI(title=f"Agent {agent_name}", version="1.0.0")
        self._setup_routes()
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def register_tool(self, tool: BaseMCPTool):
        """Register a tool with the server"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "tools": list(self.tools.keys()),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/tools/{tool_name}/execute")
        async def execute_tool(tool_name: str, request: Dict[str, Any]):
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
            
            tool = self.tools[tool_name]
            context = ExecutionContext(
                user_id=request.get("user_id", "default"),
                session_id=request.get("session_id", "default"),
                permissions=request.get("permissions", ["read"])
            )
            
            try:
                result = await tool.execute(request.get("params", {}), context)
                return {
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "metadata": result.metadata
                }
            except Exception as e:
                self.logger.error(f"Tool execution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tools")
        async def list_tools():
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "schema": tool.get_schema()
                    }
                    for tool in self.tools.values()
                ]
            }
        
        @self.app.post("/a2a/message")
        async def handle_a2a_message(message: Dict[str, Any]):
            """Handle A2A (Agent-to-Agent) messages"""
            try:
                result = await self.process_a2a_message(message)
                return result
            except Exception as e:
                self.logger.error(f"A2A message processing failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "agent": self.agent_name
                }
    
    async def process_a2a_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming A2A messages - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_a2a_message")
    
    async def start(self):
        """Start the server"""
        self.logger.info(f"Starting {self.agent_name} on port {self.port}")
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run(self):
        """Run the server synchronously"""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
