"""
Base Tool Implementation
Base class for all MCP tools used by agents
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from .base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class BaseTool(BaseMCPTool):
    """Enhanced base tool with additional functionality"""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self.logger = logging.getLogger(f"tool.{name}")
        self.metadata: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameter_schema(),
            "returns": self.get_return_schema()
        }
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get parameter schema - to be implemented by subclasses"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        """Get return schema - to be implemented by subclasses"""
        return {
            "type": "object",
            "properties": {}
        }
    
    async def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """Execute the tool with given parameters"""
        start_time = datetime.now()
        
        try:
            # Validate parameters
            self._validate_parameters(params)
            
            # Execute the tool
            result = await self._execute_impl(params, context)
            
            # Record execution
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_execution(params, result, execution_time, context)
            
            return ExecutionResult(
                success=True,
                result=result,
                error=None,
                metadata={
                    "execution_time": execution_time,
                    "tool_name": self.name,
                    "user_id": context.user_id,
                    "session_id": context.session_id
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Tool execution failed: {e}")
            
            # Record failed execution
            self._record_execution(params, None, execution_time, context, error=str(e))
            
            return ExecutionResult(
                success=False,
                result=None,
                error=str(e),
                metadata={
                    "execution_time": execution_time,
                    "tool_name": self.name,
                    "user_id": context.user_id,
                    "session_id": context.session_id
                }
            )
    
    async def _execute_impl(self, params: Dict[str, Any], context: ExecutionContext) -> Any:
        """Implementation of tool execution - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_impl")
    
    def _validate_parameters(self, params: Dict[str, Any]):
        """Validate input parameters"""
        schema = self.get_parameter_schema()
        required = schema.get("required", [])
        
        for field in required:
            if field not in params:
                raise ValueError(f"Required parameter '{field}' is missing")
        
        # Additional validation can be added by subclasses
        self._validate_parameters_impl(params)
    
    def _validate_parameters_impl(self, params: Dict[str, Any]):
        """Additional parameter validation - can be overridden by subclasses"""
        pass
    
    def _record_execution(self, params: Dict[str, Any], result: Any, execution_time: float, 
                         context: ExecutionContext, error: Optional[str] = None):
        """Record tool execution for analytics"""
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": self.name,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "parameters": params,
            "result": result,
            "execution_time": execution_time,
            "success": error is None,
            "error": error
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "last_execution": None
            }
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for record in self.execution_history if record["success"])
        success_rate = successful_executions / total_executions
        
        execution_times = [record["execution_time"] for record in self.execution_history]
        avg_execution_time = sum(execution_times) / len(execution_times)
        
        return {
            "total_executions": total_executions,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "last_execution": self.execution_history[-1]["timestamp"] if self.execution_history else None
        }
    
    def set_metadata(self, key: str, value: Any):
        """Set tool metadata"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get tool metadata"""
        return self.metadata.get(key, default)
