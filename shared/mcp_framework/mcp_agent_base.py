"""
Agent Base Class - ENFORCES MCP-ONLY TOOL ACCESS
All agents must inherit from this class and access tools ONLY through MCP
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from shared.mcp_framework.mcp_client import MCPClient


class AgentError(Exception):
    """Agent-specific errors"""
    pass


class MCPOnlyAgent(ABC):
    """
    Base class for all agents - ENFORCES MCP-ONLY ACCESS
    
    NO DIRECT TOOL ACCESS ALLOWED - ALL TOOLS MUST BE ACCESSED THROUGH MCP
    """
    
    def __init__(self, agent_name: str, mcp_server_url: str):
        self.agent_name = agent_name
        self.mcp_server_url = mcp_server_url
        self.mcp_client: Optional[MCPClient] = None
        self.logger = logging.getLogger(f"agent_{agent_name}")
        
        # Track available tools through MCP
        self.available_tools: Dict[str, Dict[str, Any]] = {}
        self.available_resources: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(f"Initialized {agent_name} agent with MCP-only access")
    
    async def initialize(self):
        """Initialize the agent and connect to MCP server"""
        try:
            # Connect to MCP server
            self.mcp_client = MCPClient(self.mcp_server_url, self.agent_name)
            await self.mcp_client.connect()
            
            # Refresh capabilities from MCP server
            await self._refresh_mcp_capabilities()
            
            # Agent-specific initialization
            await self.agent_initialize()
            
            self.logger.info(f"Agent {self.agent_name} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            raise AgentError(f"Agent initialization failed: {str(e)}")
    
    async def shutdown(self):
        """Shutdown the agent and disconnect from MCP server"""
        try:
            if self.mcp_client:
                await self.mcp_client.disconnect()
            
            await self.agent_shutdown()
            self.logger.info(f"Agent {self.agent_name} shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during agent shutdown: {str(e)}")
    
    # ==================== MCP TOOL ACCESS METHODS ====================
    
    async def use_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        USE A TOOL THROUGH MCP - THE ONLY WAY TO ACCESS TOOLS
        
        Args:
            tool_name: Name of the tool to use
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
            
        Raises:
            AgentError: If tool access fails or tool not available
        """
        if not self.mcp_client:
            raise AgentError("MCP client not initialized. Call initialize() first.")
        
        if not self.mcp_client.is_tool_available(tool_name):
            available = list(self.available_tools.keys())
            raise AgentError(f"Tool '{tool_name}' not available through MCP. Available tools: {available}")
        
        try:
            self.logger.info(f"Using tool '{tool_name}' with arguments: {arguments}")
            result = await self.mcp_client.call_tool(tool_name, arguments)
            
            self.logger.info(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
            raise AgentError(f"Tool execution failed: {str(e)}")
    
    async def read_resource(self, resource_uri: str) -> str:
        """
        READ A RESOURCE THROUGH MCP
        
        Args:
            resource_uri: URI of the resource to read
            
        Returns:
            Resource content
        """
        if not self.mcp_client:
            raise AgentError("MCP client not initialized. Call initialize() first.")
        
        if not self.mcp_client.is_resource_available(resource_uri):
            available = list(self.available_resources.keys())
            raise AgentError(f"Resource '{resource_uri}' not available through MCP. Available resources: {available}")
        
        try:
            self.logger.info(f"Reading resource '{resource_uri}'")
            content = await self.mcp_client.read_resource(resource_uri)
            
            self.logger.info(f"Resource '{resource_uri}' read successfully")
            return content
            
        except Exception as e:
            self.logger.error(f"Resource '{resource_uri}' read failed: {str(e)}")
            raise AgentError(f"Resource read failed: {str(e)}")
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all tools available through MCP"""
        if not self.mcp_client:
            raise AgentError("MCP client not initialized. Call initialize() first.")
        
        return await self.mcp_client.list_tools()
    
    async def list_available_resources(self) -> List[Dict[str, Any]]:
        """List all resources available through MCP"""
        if not self.mcp_client:
            raise AgentError("MCP client not initialized. Call initialize() first.")
        
        return await self.mcp_client.list_resources()
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool"""
        if not self.mcp_client:
            raise AgentError("MCP client not initialized. Call initialize() first.")
        
        return self.mcp_client.get_tool_schema(tool_name)
    
    async def health_check(self) -> bool:
        """Check if MCP connection is healthy"""
        if not self.mcp_client:
            return False
        
        return await self.mcp_client.ping()
    
    # ==================== INTERNAL METHODS ====================
    
    async def _refresh_mcp_capabilities(self):
        """Refresh available tools and resources from MCP server"""
        if self.mcp_client:
            await self.mcp_client.refresh_capabilities()
            self.available_tools = self.mcp_client.available_tools
            self.available_resources = self.mcp_client.available_resources
            
            self.logger.info(f"MCP capabilities refreshed. Tools: {list(self.available_tools.keys())}")
            self.logger.info(f"Resources: {list(self.available_resources.keys())}")
    
    # ==================== ABSTRACT METHODS FOR SUBCLASSES ====================
    
    @abstractmethod
    async def agent_initialize(self):
        """Agent-specific initialization - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def agent_shutdown(self):
        """Agent-specific shutdown - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request - to be implemented by subclasses"""
        pass
    
    # ==================== CONTEXT MANAGER SUPPORT ====================
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()


class AgentCapabilities:
    """Define agent capabilities and their required tools"""
    
    @staticmethod
    def get_required_tools(agent_type: str) -> List[str]:
        """Get required tools for an agent type"""
        tool_requirements = {
            "shopping": ["pantry_tracker", "deal_finder", "price_comparator", "shopping_optimizer"],
            "health": ["fitness_tracker", "health_analyzer", "recovery_monitor", "workout_planner"],
            "nutrition": ["meal_planner", "nutrition_analyzer", "recipe_engine"],
            "scheduler": ["calendar_manager", "scheduling_optimizer", "time_tracker", "focus_blocker", "timezone_handler"]
        }
        
        return tool_requirements.get(agent_type, [])
    
    @staticmethod
    def validate_agent_tools(agent_type: str, available_tools: List[str]) -> Dict[str, Any]:
        """Validate that an agent has all required tools available"""
        required_tools = AgentCapabilities.get_required_tools(agent_type)
        missing_tools = [tool for tool in required_tools if tool not in available_tools]
        
        return {
            "valid": len(missing_tools) == 0,
            "required_tools": required_tools,
            "available_tools": available_tools,
            "missing_tools": missing_tools
        }
