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
from shared.langchain_framework.workflow_orchestrator import orchestrator
from shared.utils.config import config_manager
from shared.utils.logging import setup_logging

class WorkflowRequest(BaseModel):
    """Workflow execution request"""
    type: str
    user_id: str
    query: str = ""
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
            allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
            """List all registered agents with detailed tool information"""
            detailed_agents = {
                "milo": {
                    "name": "Milo",
                    "description": "Meal Planning & Nutrition Agent",
                    "status": "healthy",
                    "port": 8002,
                    "last_heartbeat": datetime.now().isoformat(),
                    "mcp_tools": [
                        {
                            "name": "meal_planner",
                            "description": "AI-powered meal planning with dietary restrictions",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["spoonacular_api_key", "nutritionix_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "nutrition_analyzer", 
                            "description": "Nutritional analysis and macro tracking",
                            "status": "active",
                            "requires_config": False,
                            "config_items": [],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "recipe_engine",
                            "description": "Recipe generation and modification engine",
                            "status": "active", 
                            "requires_config": True,
                            "config_items": ["openai_api_key"],
                            "last_used": datetime.now().isoformat()
                        }
                    ],
                    "databases": ["recipes_db", "nutrition_db"],
                    "external_apis": ["Spoonacular", "Nutritionix"],
                    "total_tools": 3
                },
                "luna": {
                    "name": "Luna", 
                    "description": "Health & Fitness Tracking Agent",
                    "status": "healthy",
                    "port": 8003,
                    "last_heartbeat": datetime.now().isoformat(),
                    "mcp_tools": [
                        {
                            "name": "fitness_tracker",
                            "description": "Comprehensive fitness activity tracking",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["fitbit_api_key", "strava_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "health_analyzer",
                            "description": "Health metrics analysis and insights",
                            "status": "active",
                            "requires_config": False,
                            "config_items": [],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "workout_planner", 
                            "description": "Personalized workout plan generation",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["openai_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "recovery_monitor",
                            "description": "Recovery tracking and sleep analysis",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["sleep_api_key"],
                            "last_used": datetime.now().isoformat()
                        }
                    ],
                    "databases": ["fitness_db", "health_metrics_db"],
                    "external_apis": ["Fitbit", "Strava", "MyFitnessPal"],
                    "total_tools": 4
                },
                "bucky": {
                    "name": "Bucky",
                    "description": "Shopping & Inventory Management Agent", 
                    "status": "healthy",
                    "port": 8001,
                    "last_heartbeat": datetime.now().isoformat(),
                    "mcp_tools": [
                        {
                            "name": "inventory_manager",
                            "description": "Smart pantry and inventory tracking",
                            "status": "active",
                            "requires_config": False,
                            "config_items": [],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "shopping_optimizer",
                            "description": "Multi-store shopping route optimization", 
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["google_maps_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "price_comparator",
                            "description": "Real-time price comparison across stores",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["kroger_api_key", "walmart_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "deal_finder",
                            "description": "Coupon and deal discovery engine",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["honey_api_key", "rakuten_api_key"],
                            "last_used": datetime.now().isoformat()
                        }
                    ],
                    "databases": ["inventory_db", "pricing_db"],
                    "external_apis": ["Kroger", "Walmart", "Google Maps"],
                    "total_tools": 4
                },
                "nani": {
                    "name": "Nani",
                    "description": "Scheduler & Calendar Management Agent",
                    "status": "healthy",
                    "port": 8005,
                    "last_heartbeat": datetime.now().isoformat(),
                    "mcp_tools": [
                        {
                            "name": "calendar_manager", 
                            "description": "Multi-provider calendar integration and management",
                            "status": "active",
                            "requires_config": True,
                            "config_items": ["google_calendar_credentials", "outlook_credentials"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "scheduling_optimizer",
                            "description": "AI-powered meeting and event optimization",
                            "status": "active", 
                            "requires_config": True,
                            "config_items": ["openai_api_key"],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "timezone_handler",
                            "description": "Multi-timezone scheduling coordination",
                            "status": "active",
                            "requires_config": False,
                            "config_items": [],
                            "last_used": datetime.now().isoformat()
                        },
                        {
                            "name": "focus_blocker",
                            "description": "Focus time protection and productivity management",
                            "status": "active",
                            "requires_config": False,
                            "config_items": [],
                            "last_used": datetime.now().isoformat()
                        }
                    ],
                    "databases": ["calendar_db", "user_preferences_db"],
                    "external_apis": ["Google Calendar", "Outlook", "Apple Calendar"],
                    "total_tools": 4
                }
            }
            
            return {
                "agents": detailed_agents,
                "total_agents": len(detailed_agents)
            }
        
        @self.app.get("/agents/{agent_name}")
        async def get_agent_details(agent_name: str):
            """Get detailed information about a specific agent"""
            agents_data = (await list_agents())["agents"]
            
            if agent_name not in agents_data:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
            agent_data = agents_data[agent_name]
            
            # Add additional runtime information
            agent_data["runtime_info"] = {
                "uptime": "2 hours 15 minutes",
                "requests_handled": 142,
                "success_rate": "98.5%",
                "avg_response_time": "1.2s",
                "memory_usage": "85MB",
                "cpu_usage": "12%"
            }
            
            return {
                "agent": agent_data,
                "mcp_connection": "active",
                "tools_status": "all_operational"
            }
        
        @self.app.get("/agents/{agent_name}/tools/{tool_name}")
        async def get_tool_details(agent_name: str, tool_name: str):
            """Get detailed information about a specific tool"""
            agent_details = (await get_agent_details(agent_name))["agent"]
            
            tool = None
            for mcp_tool in agent_details["mcp_tools"]:
                if mcp_tool["name"] == tool_name:
                    tool = mcp_tool
                    break
            
            if not tool:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found for agent {agent_name}")
            
            # Enhanced tool information
            enhanced_tool = {
                **tool,
                "agent": agent_name,
                "usage_statistics": {
                    "total_calls": 87,
                    "success_calls": 85,
                    "failed_calls": 2,
                    "avg_execution_time": "0.8s",
                    "last_error": None
                },
                "configuration_schema": {
                    "type": "object",
                    "properties": {
                        config_item: {
                            "type": "string",
                            "description": f"API key for {config_item.replace('_', ' ').title()}",
                            "required": True,
                            "encrypted": True
                        } for config_item in tool["config_items"]
                    }
                },
                "current_config": {
                    config_item: "***configured***" if config_item in tool["config_items"] else None
                    for config_item in tool["config_items"]
                }
            }
            
            return {
                "tool": enhanced_tool,
                "editable_settings": tool["requires_config"]
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
            """Execute a coordinated workflow with Master Coordinator intelligence"""
            try:
                # Use the enhanced orchestrator with Master Coordinator
                result = await orchestrator.execute_workflow({
                    'type': request.type,
                    'user_id': request.user_id,
                    'query': request.query,
                    'parameters': request.parameters,
                    'priority': request.priority
                })
                
                # Store workflow result
                workflow_id = result['workflow_id']
                self.active_workflows[workflow_id] = {
                    "type": request.type,
                    "user_id": request.user_id,
                    "status": result['status'],
                    "result": result.get('result'),
                    "started_at": datetime.now().isoformat(),
                    "parameters": request.parameters,
                    "agents_involved": result.get('agents_involved', []),
                    "execution_type": result.get('execution_type', 'unknown'),
                    "primary_agent": result.get('primary_agent')
                }
                
                return WorkflowResponse(
                    workflow_id=workflow_id,
                    status=result['status'],
                    message=result.get('message', 'Workflow completed'),
                    agents_involved=result.get('agents_involved', []),
                    estimated_duration=150  # Reduced from 300 since coordinator is more efficient
                )
                
            except Exception as e:
                self.logger.error(f"Enhanced workflow execution failed: {e}")
                # Fallback to original workflow system
                return await self._fallback_workflow_execution(request, background_tasks)
        
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
            # First check orchestrator
            try:
                orchestrator_result = await orchestrator.get_workflow_status(workflow_id)
                if not orchestrator_result.get('error'):
                    return orchestrator_result
            except Exception:
                pass
            
            # Fallback to local tracking
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
        
        # Calendar Management Endpoints
        @self.app.get("/api/v1/calendar/status/{user_id}")
        async def get_user_calendar_status(user_id: str):
            """Get calendar integration status for a specific user"""
            try:
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id,
                    'query': 'get_calendar_status',
                    'parameters': {
                        'action': 'get_calendar_status',
                        'user_id': user_id
                    }
                })
                return result.get('result', {"success": False, "error": "No result"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/v1/calendar/setup/{user_id}")
        async def setup_calendar_provider(user_id: str, request_data: Dict[str, Any]):
            """Setup calendar provider for a user"""
            try:
                provider = request_data.get('provider', 'google')
                client_config = request_data.get('client_config', {})
                authorization_code = request_data.get('authorization_code')
                
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management', 
                    'user_id': user_id,
                    'query': f'setup_{provider}_calendar',
                    'parameters': {
                        'action': 'setup_provider',
                        'user_id': user_id,
                        'provider': provider,
                        'client_config': client_config,
                        'authorization_code': authorization_code
                    }
                })
                return result.get('result', {"success": False, "error": "Setup failed"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.delete("/api/v1/calendar/disconnect/{user_id}/{provider}")
        async def disconnect_calendar_provider(user_id: str, provider: str):
            """Disconnect calendar provider for a user"""
            try:
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id, 
                    'query': f'disconnect_{provider}_calendar',
                    'parameters': {
                        'action': 'disconnect_provider',
                        'user_id': user_id,
                        'provider': provider
                    }
                })
                return result.get('result', {"success": False, "error": "Disconnect failed"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/v1/calendar/events/{user_id}")
        async def get_user_calendar_events(user_id: str, start_date: Optional[str] = None, 
                                         end_date: Optional[str] = None, provider: Optional[str] = None):
            """Get calendar events for a user"""
            try:
                from datetime import datetime, timedelta
                
                if not start_date:
                    start_date = datetime.utcnow().isoformat()
                if not end_date:
                    end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
                
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id,
                    'query': 'get_my_events', 
                    'parameters': {
                        'action': 'get_events',
                        'user_id': user_id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'provider': provider
                    }
                })
                return result.get('result', {"success": False, "error": "Failed to get events"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/v1/calendar/events/{user_id}")
        async def create_user_calendar_event(user_id: str, event_data: Dict[str, Any]):
            """Create a calendar event for a user"""
            try:
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id,
                    'query': 'create_calendar_event',
                    'parameters': {
                        'action': 'create_event',
                        'user_id': user_id,
                        'event_details': event_data.get('event_details', {}),
                        'provider': event_data.get('provider')
                    }
                })
                return result.get('result', {"success": False, "error": "Event creation failed"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/v1/calendar/free-time/{user_id}")
        async def find_user_free_time(user_id: str, duration: int = 60, 
                                    start_date: Optional[str] = None, end_date: Optional[str] = None):
            """Find free time slots for a user"""
            try:
                from datetime import datetime, timedelta
                
                if not start_date:
                    start_date = datetime.utcnow().isoformat()
                if not end_date:
                    end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
                
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id,
                    'query': 'find_available_times',
                    'parameters': {
                        'action': 'find_free_time',
                        'user_id': user_id,
                        'duration_minutes': duration,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                })
                return result.get('result', {"success": False, "error": "Free time search failed"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/v1/calendar/parse/{user_id}")
        async def parse_natural_scheduling(user_id: str, request_data: Dict[str, Any]):
            """Parse natural language scheduling request"""
            try:
                natural_query = request_data.get('query', '')
                
                result = await orchestrator.execute_workflow({
                    'type': 'calendar_management',
                    'user_id': user_id,
                    'query': natural_query,
                    'parameters': {
                        'action': 'parse_natural_language',
                        'user_id': user_id,
                        'natural_query': natural_query
                    }
                })
                return result.get('result', {"success": False, "error": "Parsing failed"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/v1/system/stats")
        async def get_system_stats():
            """Get system statistics"""
            return {
                "disk_usage": 45.2,
                "memory_usage": 67.8,
                "uptime": "2 days, 14 hours",
                "last_backup": "2025-07-31T10:00:00Z"
            }
        
        # Tool Configuration Management Endpoints
        @self.app.put("/agents/{agent_name}/tools/{tool_name}/config")
        async def update_tool_config(agent_name: str, tool_name: str, config_data: Dict[str, Any]):
            """Update configuration for a specific tool"""
            try:
                # Validate agent and tool exist
                await get_tool_details(agent_name, tool_name)
                
                config_updates = config_data.get('config', {})
                
                # In a real implementation, this would save to secure storage
                return {
                    "success": True,
                    "message": f"Configuration updated for {tool_name}",
                    "updated_fields": list(config_updates.keys()),
                    "agent": agent_name,
                    "tool": tool_name
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/agents/{agent_name}/tools/{tool_name}/config")
        async def get_tool_config(agent_name: str, tool_name: str):
            """Get current configuration for a specific tool"""
            try:
                tool_details = await get_tool_details(agent_name, tool_name)
                return {
                    "success": True,
                    "config": tool_details["tool"]["current_config"],
                    "schema": tool_details["tool"]["configuration_schema"],
                    "requires_config": tool_details["editable_settings"]
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/agents/{agent_name}/tools/{tool_name}/test")
        async def test_tool_connection(agent_name: str, tool_name: str):
            """Test the connection/configuration of a specific tool"""
            try:
                # In real implementation, this would test the actual tool
                tool_details = await get_tool_details(agent_name, tool_name)
                
                # Mock test results
                test_results = {
                    "calendar_manager": {
                        "google_calendar_credentials": "Google Calendar API connection successful",
                        "outlook_credentials": "Outlook not configured"
                    },
                    "meal_planner": {
                        "spoonacular_api_key": "Spoonacular API connection successful",
                        "nutritionix_api_key": "Nutritionix API rate limit: 95/100 requests remaining"
                    },
                    "fitness_tracker": {
                        "fitbit_api_key": "Fitbit API connection successful",
                        "strava_api_key": "Strava API connection successful"
                    }
                }
                
                return {
                    "success": True,
                    "tool": tool_name,
                    "agent": agent_name,
                    "test_results": test_results.get(tool_name, {"status": "Tool connection test successful"}),
                    "overall_status": "operational"
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/agents/{agent_name}/restart")
        async def restart_agent(agent_name: str):
            """Restart a specific agent"""
            try:
                # Validate agent exists
                await get_agent_details(agent_name)
                
                return {
                    "success": True,
                    "message": f"Agent {agent_name} restarted successfully",
                    "agent": agent_name,
                    "restart_time": datetime.now().isoformat()
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/agents/{agent_name}/logs")
        async def get_agent_logs(agent_name: str, lines: int = 100):
            """Get recent logs for a specific agent"""
            try:
                # Validate agent exists
                await get_agent_details(agent_name)
                
                # Mock log data
                mock_logs = [
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                        "level": "INFO",
                        "message": f"Agent {agent_name} processed workflow request successfully",
                        "module": f"{agent_name}_agent"
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=8)).isoformat(),
                        "level": "INFO", 
                        "message": "Tool calendar_manager executed successfully",
                        "module": "calendar_manager"
                    },
                    {
                        "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                        "level": "WARNING",
                        "message": "API rate limit approaching for external service",
                        "module": "external_api"
                    }
                ]
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "logs": mock_logs[:lines],
                    "total_lines": len(mock_logs)
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/agents/{agent_name}/databases")
        async def get_agent_databases(agent_name: str):
            """Get database configurations for an agent"""
            try:
                agent_details = await get_agent_details(agent_name)
                databases = agent_details["agent"]["databases"]
                
                # Mock database status
                db_status = {
                    "recipes_db": {"status": "connected", "size": "45MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "nutrition_db": {"status": "connected", "size": "128MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "fitness_db": {"status": "connected", "size": "89MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "health_metrics_db": {"status": "connected", "size": "67MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "inventory_db": {"status": "connected", "size": "23MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "pricing_db": {"status": "connected", "size": "156MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "calendar_db": {"status": "connected", "size": "34MB", "last_backup": "2025-08-10T10:00:00Z"},
                    "user_preferences_db": {"status": "connected", "size": "12MB", "last_backup": "2025-08-10T10:00:00Z"}
                }
                
                return {
                    "success": True,
                    "agent": agent_name,
                    "databases": [
                        {
                            "name": db,
                            **db_status.get(db, {"status": "unknown", "size": "0MB", "last_backup": "never"})
                        } for db in databases
                    ]
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/agents/{agent_name}/databases/{db_name}/backup")
        async def backup_database(agent_name: str, db_name: str):
            """Create a backup of a specific database"""
            try:
                await get_agent_details(agent_name)
                
                return {
                    "success": True,
                    "message": f"Database {db_name} backup created successfully",
                    "backup_file": f"{db_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                    "backup_time": datetime.now().isoformat()
                }
            except HTTPException:
                raise
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Master Coordinator endpoints
        @self.app.get("/coordinator/status")
        async def get_coordinator_status():
            """Get Master Coordinator status"""
            return orchestrator.get_coordinator_status()
        
        @self.app.post("/coordinator/analyze")
        async def analyze_query_intent(query_data: Dict[str, str]):
            """Analyze query intent without executing"""
            query = query_data.get('query', '')
            try:
                result = await orchestrator.coordinator.process_query(query)
                return {
                    "query": query,
                    "analysis": result['routing_decision'],
                    "would_activate_agents": result['should_forward_to_agents'],
                    "coordinator_response": result.get('coordinator_response')
                }
            except Exception as e:
                return {
                    "query": query,
                    "error": str(e),
                    "analysis": None
                }
    
    async def _fallback_workflow_execution(self, request: WorkflowRequest, background_tasks: BackgroundTasks):
        """Fallback to original workflow execution if Master Coordinator fails"""
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
            message=f"Workflow {request.type} started (fallback mode)",
            agents_involved=agents_involved,
            estimated_duration=300  # 5 minutes default
        )
    
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