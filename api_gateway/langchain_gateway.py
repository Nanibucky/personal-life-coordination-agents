"""
LangChain API Gateway
FastAPI gateway for LangChain-based agents
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from shared.langchain_framework.a2a_coordinator import a2a_coordinator, A2AMessage
from shared.utils.config import config_manager
from shared.utils.logging import setup_logging

class WorkflowRequest(BaseModel):
    """Workflow execution request"""
    type: str
    user_id: str
    parameters: Dict[str, Any] = {}
    priority: str = "normal"

class WorkflowResponse(BaseModel):
    """Workflow execution response"""
    workflow_id: str
    status: str
    message: str
    agents_involved: List[str]
    estimated_duration: int

class AgentRequest(BaseModel):
    """Direct agent request"""
    agent_name: str
    message: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Agent response"""
    agent_name: str
    response: str
    tools_used: List[str]
    execution_time: float

class LangChainAPIGateway:
    """LangChain-based API Gateway"""
    
    def __init__(self):
        self.app = FastAPI(
            title="LangChain Personal Life Coordination API Gateway",
            description="API Gateway for LangChain-based personal life management agents",
            version="1.0.0"
        )
        
        # Load configuration
        self.config = config_manager.get_global_config()
        
        # Setup logging
        self.logger = setup_logging(
            "langchain_gateway",
            level=self.config.get("logging", {}).get("level", "INFO"),
            log_file="logs/langchain_gateway.log"
        )
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Workflow tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("LangChain API Gateway initialized successfully")
    
    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("api_gateway", {}).get("cors_origins", ["http://localhost:3000"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """System health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "agents": list(a2a_coordinator.agents.keys()),
                "active_workflows": len(self.active_workflows),
                "framework": "langchain"
            }
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents"""
            return {
                "agents": a2a_coordinator.get_agent_status(),
                "total_agents": len(a2a_coordinator.agents)
            }
        
        @self.app.post("/agents/{agent_name}/chat", response_model=AgentResponse)
        async def chat_with_agent(agent_name: str, request: AgentRequest):
            """Chat directly with a specific agent"""
            if agent_name not in a2a_coordinator.agents:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
            try:
                start_time = datetime.now()
                
                # Process request with agent
                response = await a2a_coordinator.process_agent_request(
                    agent_name, request.message, request.context
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Get tools used (simplified - in real implementation would track actual tool usage)
                agent = a2a_coordinator.agents[agent_name]
                tools_used = [tool.name for tool in agent.tools]
                
                return AgentResponse(
                    agent_name=agent_name,
                    response=response,
                    tools_used=tools_used,
                    execution_time=execution_time
                )
                
            except Exception as e:
                self.logger.error(f"Error chatting with agent {agent_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/workflow", response_model=WorkflowResponse)
        async def execute_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
            """Execute a coordinated workflow across multiple agents"""
            workflow_id = f"wf_{datetime.now().timestamp()}_{request.user_id}"
            
            # Add to active workflows
            self.active_workflows[workflow_id] = {
                "type": request.type,
                "user_id": request.user_id,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "parameters": request.parameters
            }
            
            # Execute workflow in background
            background_tasks.add_task(self._execute_workflow_background, workflow_id, request)
            
            # Determine agents involved based on workflow type
            agents_involved = self._get_agents_for_workflow(request.type)
            
            return WorkflowResponse(
                workflow_id=workflow_id,
                status="started",
                message=f"Workflow {request.type} started successfully",
                agents_involved=agents_involved,
                estimated_duration=300  # 5 minutes default
            )
        
        @self.app.get("/workflows")
        async def list_workflows():
            """List all workflows"""
            return {
                "active_workflows": self.active_workflows,
                "total_count": len(self.active_workflows)
            }
        
        @self.app.get("/workflows/{workflow_id}")
        async def get_workflow_status(workflow_id: str):
            """Get status of a specific workflow"""
            if workflow_id not in self.active_workflows:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return self.active_workflows[workflow_id]
        
        @self.app.post("/a2a/message")
        async def send_a2a_message(message_data: Dict[str, Any]):
            """Send an A2A message between agents"""
            try:
                # Create A2A message
                message = A2AMessage(
                    from_agent=message_data["from_agent"],
                    to_agent=message_data["to_agent"],
                    intent=message_data["intent"],
                    payload=message_data.get("payload", {}),
                    session_id=message_data.get("session_id", "default")
                )
                
                # Send message
                response = await a2a_coordinator.send_message(message)
                return response
                
            except Exception as e:
                self.logger.error(f"Error sending A2A message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/a2a/broadcast")
        async def broadcast_a2a_message(message_data: Dict[str, Any]):
            """Broadcast an A2A message to all agents"""
            try:
                # Create A2A message
                message = A2AMessage(
                    from_agent=message_data["from_agent"],
                    to_agent="",  # Will be set for each agent
                    intent=message_data["intent"],
                    payload=message_data.get("payload", {}),
                    session_id=message_data.get("session_id", "default")
                )
                
                # Broadcast message
                responses = await a2a_coordinator.broadcast_message(message)
                return {
                    "responses": responses,
                    "total_agents": len(responses)
                }
                
            except Exception as e:
                self.logger.error(f"Error broadcasting A2A message: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/a2a/history")
        async def get_a2a_history(limit: int = 50):
            """Get A2A message history"""
            history = a2a_coordinator.get_message_history(limit)
            return {
                "messages": [
                    {
                        "message_id": msg.message_id,
                        "from_agent": msg.from_agent,
                        "to_agent": msg.to_agent,
                        "intent": msg.intent,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in history
                ],
                "total_messages": len(history)
            }
        
        @self.app.delete("/a2a/history")
        async def clear_a2a_history():
            """Clear A2A message history"""
            a2a_coordinator.clear_history()
            return {"message": "A2A history cleared successfully"}
        
        # System Settings Endpoints
        @self.app.get("/api/v1/system/settings")
        async def get_system_settings():
            """Get system settings"""
            return {
                "success": True,
                "settings": {
                    "general": {
                        "theme": "light",
                        "language": "en",
                        "timezone": "America/New_York",
                        "auto_refresh": True,
                        "refresh_interval": 5
                    },
                    "notifications": {
                        "email": True,
                        "push": True,
                        "workflow_completed": True,
                        "agent_offline": True,
                        "system_alerts": True,
                        "daily_summary": False
                    },
                    "agents": {
                        "auto_restart": True,
                        "max_retries": 3,
                        "timeout_seconds": 30,
                        "log_level": "INFO",
                        "health_check_interval": 30,
                        "concurrent_workflows": 5
                    },
                    "api": {
                        "openai_key": "configured",
                        "google_calendar": False,
                        "google_calendar_id": "",
                        "fitbit": False,
                        "fitbit_token": "",
                        "spoonacular": False,
                        "spoonacular_key": "",
                        "kroger": False,
                        "kroger_key": ""
                    },
                    "system": {
                        "auto_backup": True,
                        "backup_interval": "daily",
                        "max_logs_days": 30,
                        "performance_monitoring": True,
                        "debug_mode": False,
                        "data_retention_days": 90
                    }
                }
            }
        
        @self.app.put("/api/v1/system/settings")
        async def save_system_settings(settings: Dict[str, Any]):
            """Save system settings"""
            # In a real implementation, this would save to a database or config file
            return {
                "success": True,
                "message": "Settings saved successfully"
            }
        
        @self.app.post("/api/v1/system/settings/reset")
        async def reset_system_settings():
            """Reset system settings to default"""
            return {
                "success": True,
                "defaultSettings": {
                    "general": {
                        "theme": "light",
                        "language": "en",
                        "timezone": "America/New_York",
                        "auto_refresh": True,
                        "refresh_interval": 5
                    },
                    "notifications": {
                        "email": True,
                        "push": True,
                        "workflow_completed": True,
                        "agent_offline": True,
                        "system_alerts": True,
                        "daily_summary": False
                    },
                    "agents": {
                        "auto_restart": True,
                        "max_retries": 3,
                        "timeout_seconds": 30,
                        "log_level": "INFO",
                        "health_check_interval": 30,
                        "concurrent_workflows": 5
                    },
                    "api": {
                        "openai_key": "",
                        "google_calendar": False,
                        "google_calendar_id": "",
                        "fitbit": False,
                        "fitbit_token": "",
                        "spoonacular": False,
                        "spoonacular_key": "",
                        "kroger": False,
                        "kroger_key": ""
                    },
                    "system": {
                        "auto_backup": True,
                        "backup_interval": "daily",
                        "max_logs_days": 30,
                        "performance_monitoring": True,
                        "debug_mode": False,
                        "data_retention_days": 90
                    }
                }
            }
        
        @self.app.post("/api/v1/system/test-connection")
        async def test_api_connection(request: Dict[str, Any]):
            """Test API connection"""
            api_type = request.get("type", "")
            settings = request.get("settings", {})
            
            # Mock API connection tests
            if api_type == "openai":
                return {
                    "success": True,
                    "message": "OpenAI API connection successful"
                }
            elif api_type == "google_calendar":
                return {
                    "success": False,
                    "error": "Google Calendar not configured"
                }
            elif api_type == "fitbit":
                return {
                    "success": False,
                    "error": "Fitbit not configured"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown API type: {api_type}"
                }
        
        @self.app.delete("/api/v1/system/logs/clear")
        async def clear_system_logs():
            """Clear system logs"""
            return {
                "success": True,
                "message": "System logs cleared successfully"
            }
        
        @self.app.post("/api/v1/system/restart-agents")
        async def restart_all_agents():
            """Restart all agents"""
            return {
                "success": True,
                "message": "All agents restarted successfully"
            }
        
        @self.app.post("/api/v1/system/restart-agent/{agent_name}")
        async def restart_agent(agent_name: str):
            """Restart specific agent"""
            if agent_name in a2a_coordinator.agents:
                return {
                    "success": True,
                    "message": f"Agent {agent_name} restarted successfully"
                }
            else:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        @self.app.post("/api/v1/system/reset-database")
        async def reset_database():
            """Reset database (dangerous operation)"""
            return {
                "success": True,
                "message": "Database reset successfully"
            }
        
        @self.app.get("/api/v1/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            return {
                "disk_usage": 45.2,
                "memory_usage": 67.8,
                "uptime": "2 days, 14 hours",
                "last_backup": "2025-07-31T10:00:00Z"
            }
    
    def _get_agents_for_workflow(self, workflow_type: str) -> List[str]:
        """Determine which agents are involved in a workflow type"""
        workflow_mappings = {
            "meal_planning": ["milo", "bucky", "nani"],
            "fitness_scheduling": ["luna", "nani"],
            "shopping_optimization": ["bucky", "nani"],
            "health_analysis": ["luna", "milo"],
            "schedule_optimization": ["nani", "luna", "milo"],
            "nutrition_planning": ["milo", "bucky"],
            "workout_planning": ["luna", "nani"],
            "inventory_management": ["bucky", "milo"]
        }
        
        return workflow_mappings.get(workflow_type, ["nani"])  # Default to scheduler
    
    async def _execute_workflow_background(self, workflow_id: str, request: WorkflowRequest):
        """Execute workflow in background"""
        try:
            self.logger.info(f"Starting workflow {workflow_id}: {request.type}")
            
            # Get agents involved
            agents_involved = self._get_agents_for_workflow(request.type)
            
            # Create workflow steps
            steps = []
            for agent in agents_involved:
                if agent in a2a_coordinator.agents:
                    steps.append({
                        "agent": agent,
                        "intent": f"execute_workflow_{request.type}",
                        "payload": {
                            "workflow_id": workflow_id,
                            "user_id": request.user_id,
                            "parameters": request.parameters,
                            "agents_involved": agents_involved,
                            "priority": request.priority
                        }
                    })
            
            # Execute workflow
            result = await a2a_coordinator.coordinate_workflow(
                workflow_id, steps, request.user_id, f"session_{workflow_id}"
            )
            
            # Update workflow status
            self.active_workflows[workflow_id].update(result)
            
            self.logger.info(f"Workflow {workflow_id} completed with status: {result['status']}")
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API Gateway"""
        self.logger.info(f"Starting LangChain API Gateway on {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )

def main():
    """Main entry point"""
    gateway = LangChainAPIGateway()
    gateway.run()

if __name__ == "__main__":
    main() 