"""
API Gateway - Main Entry Point
Central gateway for coordinating all agents and providing unified API
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from shared.utils.config import config_manager
from shared.utils.logging import setup_logging
from shared.a2a_protocol.message_router import A2AMessage, A2AMessageRouter

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

class AgentStatus(BaseModel):
    """Agent status information"""
    name: str
    status: str
    port: int
    last_heartbeat: str
    tools: List[str]

class APIGateway:
    """Main API Gateway class"""
    
    def __init__(self):
        self.app = FastAPI(
            title="Personal Life Coordination API Gateway",
            description="Central gateway for coordinating personal life management agents",
            version="1.0.0"
        )
        
        # Load configuration
        self.config = config_manager.get_global_config()
        
        # Setup logging
        self.logger = setup_logging(
            "api_gateway",
            level=self.config.get("logging", {}).get("level", "INFO"),
            log_file="logs/api_gateway.log"
        )
        
        # Initialize A2A message router
        self.message_router = A2AMessageRouter()
        self.message_router.logger = self.logger
        
        # Register agent endpoints
        self._register_agents()
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        # Workflow tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("API Gateway initialized successfully")
    
    def _register_agents(self):
        """Register all agent endpoints"""
        agent_configs = {
            "bucky": {"port": 8002, "host": "localhost"},
            "luna": {"port": 8003, "host": "localhost"},
            "milo": {"port": 8004, "host": "localhost"},
            "nani": {"port": 8005, "host": "localhost"}
        }
        
        for agent_name, config in agent_configs.items():
            endpoint = f"http://{config['host']}:{config['port']}"
            self.message_router.register_agent(agent_name, endpoint)
            self.logger.info(f"Registered agent {agent_name} at {endpoint}")
    
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
                "agents": list(self.message_router.agent_endpoints.keys()),
                "active_workflows": len(self.active_workflows)
            }
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents"""
            agents = []
            for agent_name, endpoint in self.message_router.agent_endpoints.items():
                # Try to get agent status
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=5) as response:
                            if response.status == 200:
                                agent_data = await response.json()
                                agents.append(AgentStatus(
                                    name=agent_name,
                                    status="healthy",
                                    port=int(endpoint.split(":")[-1]),
                                    last_heartbeat=datetime.now().isoformat(),
                                    tools=agent_data.get("tools", [])
                                ))
                            else:
                                agents.append(AgentStatus(
                                    name=agent_name,
                                    status="unhealthy",
                                    port=int(endpoint.split(":")[-1]),
                                    last_heartbeat=datetime.now().isoformat(),
                                    tools=[]
                                ))
                except Exception as e:
                    self.logger.warning(f"Failed to check agent {agent_name}: {e}")
                    agents.append(AgentStatus(
                        name=agent_name,
                        status="unreachable",
                        port=int(endpoint.split(":")[-1]),
                        last_heartbeat=datetime.now().isoformat(),
                        tools=[]
                    ))
            
            return {"agents": agents}
        
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
        
        @self.app.post("/agents/{agent_name}/tools/{tool_name}/execute")
        async def execute_agent_tool(agent_name: str, tool_name: str, request: Dict[str, Any]):
            """Execute a specific tool on a specific agent"""
            if agent_name not in self.message_router.agent_endpoints:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
            endpoint = self.message_router.agent_endpoints[agent_name]
            url = f"{endpoint}/tools/{tool_name}/execute"
            
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=request) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            raise HTTPException(
                                status_code=response.status,
                                detail=f"Tool execution failed: {await response.text()}"
                            )
            except Exception as e:
                self.logger.error(f"Failed to execute tool {tool_name} on agent {agent_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
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
            
            # Create coordination message
            message = A2AMessage(
                from_agent="api_gateway",
                to_agent=agents_involved[0],  # Start with first agent
                intent=f"execute_workflow_{request.type}",
                payload={
                    "workflow_id": workflow_id,
                    "user_id": request.user_id,
                    "parameters": request.parameters,
                    "agents_involved": agents_involved,
                    "priority": request.priority
                },
                session_id=workflow_id
            )
            
            # Send message to start workflow
            response = await self.message_router.send_message(message)
            
            if response.success:
                self.logger.info(f"Workflow {workflow_id} started successfully")
                self.active_workflows[workflow_id]["status"] = "running"
            else:
                self.logger.error(f"Workflow {workflow_id} failed to start: {response.error}")
                self.active_workflows[workflow_id]["status"] = "failed"
                self.active_workflows[workflow_id]["error"] = response.error
                
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API Gateway"""
        self.logger.info(f"Starting API Gateway on {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )

def main():
    """Main entry point"""
    gateway = APIGateway()
    gateway.run()

if __name__ == "__main__":
    main()
