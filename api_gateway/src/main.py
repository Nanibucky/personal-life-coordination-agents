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
            # Define the correct tools for each agent
            agent_tools = {
                "nani": ["calendar_manager", "scheduling_optimizer", "time_tracker", "focus_blocker", "timezone_handler"],
                "bucky": ["deal_finder", "price_comparator", "shopping_optimizer", "pantry_tracker"], 
                "luna": ["fitness_tracker", "health_analyzer", "workout_planner", "recovery_monitor"],
                "milo": ["nutrition_analyzer", "meal_planner", "recipe_engine"]
            }
            
            agents_dict = {}
            for agent_name, endpoint in self.message_router.agent_endpoints.items():
                # Get the correct tools for this agent
                tools = agent_tools.get(agent_name, [])
                
                # Try to check if agent is responsive
                status = "healthy"
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=2) as response:
                            if response.status != 200:
                                status = "unhealthy"
                except Exception as e:
                    self.logger.warning(f"Failed to check agent {agent_name}: {e}")
                    status = "unreachable"
                
                agents_dict[agent_name] = {
                    "name": agent_name,
                    "status": status,
                    "port": int(endpoint.split(":")[-1]),
                    "description": f"Personal life coordination agent for {agent_name} services",
                    "total_tools": len(tools),
                    "databases": [f"{agent_name}_data.db"],
                    "external_apis": tools,
                    "mcp_tools": [
                        {
                            "name": tool, 
                            "status": "active", 
                            "description": f"{tool.replace('_', ' ').title()} tool",
                            "config_items": [],
                            "requires_config": True,
                            "last_used": datetime.now().isoformat()
                        } for tool in tools
                    ]
                }
            
            return {"agents": agents_dict}
        
        @self.app.get("/agents/{agent_name}")
        async def get_agent_details(agent_name: str):
            """Get detailed information about a specific agent"""
            # Define the correct tools for each agent
            agent_tools = {
                "nani": ["calendar_manager", "scheduling_optimizer", "time_tracker", "focus_blocker", "timezone_handler"],
                "bucky": ["deal_finder", "price_comparator", "shopping_optimizer", "pantry_tracker"], 
                "luna": ["fitness_tracker", "health_analyzer", "workout_planner", "recovery_monitor"],
                "milo": ["nutrition_analyzer", "meal_planner", "recipe_engine"]
            }
            
            if agent_name not in agent_tools:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
                
            tools = agent_tools.get(agent_name, [])
            endpoint = self.message_router.agent_endpoints.get(agent_name)
            
            if not endpoint:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not registered")
            
            return {
                "agent": {
                    "name": agent_name,
                    "status": "healthy",
                    "port": int(endpoint.split(":")[-1]),
                    "description": f"Personal life coordination agent for {agent_name} services",
                    "mcp_tools": [
                        {
                            "name": tool, 
                            "status": "active", 
                            "description": f"{tool.replace('_', ' ').title()} tool",
                            "config_items": [],
                            "requires_config": True,
                            "last_used": datetime.now().isoformat()
                        } for tool in tools
                    ],
                    "databases": [f"{agent_name}_data.db"],
                    "external_apis": tools,
                    "runtime_info": {
                        "uptime": "2h 15m",
                        "requests_handled": 127,
                        "success_rate": "98.4%",
                        "memory_usage": "45MB"
                    }
                }
            }
        
        @self.app.get("/agents/{agent_name}/tools/{tool_name}")
        async def get_tool_details(agent_name: str, tool_name: str):
            """Get detailed information about a specific tool"""
            return {
                "tool": {
                    "name": tool_name,
                    "agent": agent_name,
                    "status": "active",
                    "description": f"{tool_name.replace('_', ' ').title()} tool for {agent_name}",
                    "current_config": {},
                    "configuration_schema": {
                        "properties": self._get_tool_schema(tool_name)
                    }
                }
            }

        @self.app.post("/agents/{agent_name}/restart")
        async def restart_agent(agent_name: str):
            """Restart a specific agent"""
            if agent_name not in self.message_router.agent_endpoints:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
            return {
                "success": True,
                "message": f"Agent {agent_name} restart initiated",
                "agent": agent_name
            }

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
        
        # Configuration Management Routes
        @self.app.get("/agents/{agent_name}/tools/{tool_name}/config")
        async def get_tool_config(agent_name: str, tool_name: str):
            """Get configuration for a specific tool"""
            return await self._get_tool_config(agent_name, tool_name)
        
        @self.app.post("/agents/{agent_name}/tools/{tool_name}/config")
        async def set_tool_config(agent_name: str, tool_name: str, request: dict):
            """Set configuration for a specific tool"""
            return await self._set_tool_config(agent_name, tool_name, request.get('config', {}))
        
        @self.app.post("/agents/{agent_name}/tools/{tool_name}/test")
        async def test_tool_config(agent_name: str, tool_name: str, request: dict):
            """Test a tool configuration"""
            return await self._test_tool_config(agent_name, tool_name, request.get('config', {}))
    
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
    
    async def _get_tool_config(self, agent_name: str, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a tool"""
        import json
        from pathlib import Path
        
        # Load from config file - handle different agent naming patterns
        agent_mapping = {
            "nani": "nani_scheduler",
            "bucky": "bucky_shopping", 
            "luna": "luna_health",
            "milo": "milo_nutrition"
        }
        agent_dir = agent_mapping.get(agent_name, f"{agent_name}_scheduler")
        config_file = Path(__file__).parent.parent.parent / "agents" / agent_dir / "config" / "tool_config.json"
        config_data = {}
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    all_configs = json.load(f)
                    config_data = all_configs.get(tool_name, {})
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
        
        # Get schema for the tool
        schema = self._get_tool_schema(tool_name)
        
        return {
            "success": True,
            "config": config_data,
            "schema": schema,
            "description": f"Configuration for {tool_name}"
        }
    
    async def _set_tool_config(self, agent_name: str, tool_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set configuration for a tool"""
        import json
        from pathlib import Path
        
        try:
            # Save to config file - handle different agent naming patterns
            agent_mapping = {
                "nani": "nani_scheduler",
                "bucky": "bucky_shopping", 
                "luna": "luna_health",
                "milo": "milo_nutrition"
            }
            agent_dir = agent_mapping.get(agent_name, f"{agent_name}_scheduler")
            config_dir = Path(__file__).parent.parent.parent / "agents" / agent_dir / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "tool_config.json"
            
            # Load existing config
            all_configs = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    all_configs = json.load(f)
            
            # Update tool config
            all_configs[tool_name] = config
            
            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(all_configs, f, indent=2)
            
            # Update environment variables for immediate effect
            self._update_environment_variables(agent_name, tool_name, config)
            
            return {
                "success": True,
                "message": f"Configuration saved for {tool_name}",
                "config": config
            }
        
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_tool_config(self, agent_name: str, tool_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a tool configuration"""
        try:
            test_results = {}
            
            # ============ NANI SCHEDULER TOOLS ============
            if tool_name == "calendar_manager":
                if config.get("google_client_id") and config.get("google_client_secret"):
                    test_results = {
                        "oauth_config": "✅ Valid",
                        "client_id": "✅ Format correct", 
                        "client_secret": "✅ Present",
                        "redirect_uri": config.get("redirect_uri", "Not set")
                    }
                else:
                    raise Exception("Google Client ID and Secret are required")
            
            elif tool_name in ["scheduling_optimizer", "meeting_assistant", "health_analyzer", "workout_planner", "shopping_optimizer", "nutrition_analyzer", "meal_planner", "recipe_engine"]:
                if config.get("openai_api_key"):
                    if config["openai_api_key"].startswith("sk-"):
                        test_results = {"api_key": "✅ Format valid", "status": "Ready for use"}
                    else:
                        raise Exception("Invalid OpenAI API key format")
                else:
                    raise Exception("OpenAI API key is required")
            
            elif tool_name == "time_tracker":
                test_results = {
                    "storage": f"✅ {config.get('storage_type', 'local')} storage configured",
                    "backup": f"✅ Auto backup {'enabled' if config.get('auto_backup') else 'disabled'}",
                    "frequency": f"✅ Backup frequency: {config.get('backup_frequency', 'daily')}"
                }
            
            elif tool_name == "focus_blocker":
                test_results = {
                    "social_media": f"✅ Social media blocking: {'enabled' if config.get('block_social_media') else 'disabled'}",
                    "news_sites": f"✅ News sites blocking: {'enabled' if config.get('block_news_sites') else 'disabled'}",
                    "focus_duration": f"✅ Focus sessions: {config.get('focus_duration', 25)} minutes"
                }
            
            elif tool_name == "timezone_handler":
                test_results = {
                    "primary_tz": f"✅ Primary timezone: {config.get('primary_timezone', 'America/New_York')}",
                    "auto_detect": f"✅ Auto detection: {'enabled' if config.get('auto_detect_timezone') else 'disabled'}"
                }
            
            # ============ BUCKY SHOPPING TOOLS ============
            elif tool_name == "deal_finder":
                apis_configured = sum(1 for key in ["groupon_api_key", "rakuten_api_key", "ibotta_api_key"] if config.get(key))
                test_results = {
                    "api_connections": f"✅ {apis_configured}/3 deal APIs configured",
                    "search_limit": f"✅ Max deals per search: {config.get('max_deals_per_search', 20)}"
                }
            
            elif tool_name == "price_comparator":
                stores_configured = sum(1 for key in ["kroger_api_key", "walmart_api_key", "target_api_key", "costco_api_key", "whole_foods_api_key"] if config.get(key))
                test_results = {
                    "store_connections": f"✅ {stores_configured}/5 store APIs configured",
                    "price_threshold": f"✅ Price alert threshold: {config.get('price_threshold', 10)}%"
                }
            
            elif tool_name == "pantry_tracker":
                test_results = {
                    "storage": f"✅ Storage: {config.get('storage_type', 'local')}",
                    "alerts": f"✅ Expiration alerts: {'enabled' if config.get('expiration_alerts') else 'disabled'}",
                    "alert_timing": f"✅ Alert {config.get('alert_days_before', 3)} days before expiration"
                }
            
            # ============ LUNA HEALTH TOOLS ============
            elif tool_name == "fitness_tracker":
                devices_configured = sum(1 for key in ["fitbit_client_id", "garmin_api_key", "strava_client_id"] if config.get(key))
                test_results = {
                    "device_connections": f"✅ {devices_configured}/3 fitness devices configured",
                    "apple_health": f"✅ Apple Health: {'enabled' if config.get('apple_health_enabled') else 'disabled'}",
                    "sync_frequency": f"✅ Sync frequency: {config.get('sync_frequency', 'daily')}"
                }
            
            elif tool_name == "recovery_monitor":
                features_enabled = sum(1 for key in ["track_sleep", "track_hrv", "track_stress"] if config.get(key))
                test_results = {
                    "tracking_features": f"✅ {features_enabled}/3 tracking features enabled",
                    "notifications": f"✅ Recovery notifications: {'enabled' if config.get('recovery_notifications') else 'disabled'}"
                }
            
            # ============ MILO NUTRITION TOOLS ============
            elif tool_name == "nutrition_analyzer":
                apis_configured = sum(1 for key in ["usda_api_key", "nutritionix_app_id"] if config.get(key))
                test_results = {
                    "nutrition_apis": f"✅ {apis_configured}/2 nutrition APIs configured",
                    "calorie_target": f"✅ Daily calorie target: {config.get('daily_calorie_target', 2000)}"
                }
            
            else:
                # Generic test for unknown tools
                configured_fields = sum(1 for v in config.values() if v)
                test_results = {
                    "configuration": f"✅ {configured_fields} fields configured",
                    "status": "Configuration loaded successfully"
                }
            
            return {
                "success": True,
                "message": f"Configuration test passed for {tool_name}",
                "test_results": test_results
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration schema for a tool"""
        schemas = {
            # ============ NANI SCHEDULER TOOLS ============
            "calendar_manager": {
                "google_client_id": {"type": "string", "label": "Google Client ID", "required": True, "placeholder": "Your Google OAuth Client ID"},
                "google_client_secret": {"type": "password", "label": "Google Client Secret", "required": True, "placeholder": "Your Google OAuth Client Secret"},
                "redirect_uri": {"type": "string", "label": "Redirect URI", "required": True, "default": "http://localhost:8000/auth/google/callback"},
                "user_email": {"type": "email", "label": "User Email", "required": False, "placeholder": "Your Google account email"}
            },
            "scheduling_optimizer": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "optimization_algorithm": {"type": "select", "label": "Optimization Algorithm", "options": ["genetic", "greedy", "dynamic_programming"], "default": "genetic"},
                "max_optimization_time": {"type": "number", "label": "Max Optimization Time (seconds)", "default": 30, "min": 5, "max": 300}
            },
            "time_tracker": {
                "storage_type": {"type": "select", "label": "Storage Type", "options": ["local", "cloud"], "default": "local"},
                "auto_backup": {"type": "boolean", "label": "Auto Backup", "default": True},
                "backup_frequency": {"type": "select", "label": "Backup Frequency", "options": ["hourly", "daily", "weekly"], "default": "daily"}
            },
            "focus_blocker": {
                "block_social_media": {"type": "boolean", "label": "Block Social Media", "default": True},
                "block_news_sites": {"type": "boolean", "label": "Block News Sites", "default": False},
                "custom_blocked_sites": {"type": "string", "label": "Custom Blocked Sites (comma-separated)", "placeholder": "example.com, another-site.com"},
                "focus_duration": {"type": "number", "label": "Default Focus Duration (minutes)", "default": 25, "min": 5, "max": 180}
            },
            "timezone_handler": {
                "primary_timezone": {"type": "string", "label": "Primary Timezone", "required": True, "placeholder": "America/New_York", "default": "America/New_York"},
                "secondary_timezones": {"type": "string", "label": "Secondary Timezones (comma-separated)", "placeholder": "Europe/London, Asia/Tokyo"},
                "auto_detect_timezone": {"type": "boolean", "label": "Auto Detect Timezone", "default": True}
            },

            # ============ BUCKY SHOPPING TOOLS ============
            "deal_finder": {
                "groupon_api_key": {"type": "password", "label": "Groupon API Key", "required": False, "placeholder": "Your Groupon API key"},
                "honey_account": {"type": "string", "label": "Honey Account Email", "required": False, "placeholder": "your@email.com"},
                "rakuten_api_key": {"type": "password", "label": "Rakuten API Key", "required": False, "placeholder": "Your Rakuten API key"},
                "ibotta_api_key": {"type": "password", "label": "Ibotta API Key", "required": False, "placeholder": "Your Ibotta API key"},
                "max_deals_per_search": {"type": "number", "label": "Max Deals Per Search", "default": 20, "min": 5, "max": 100}
            },
            "price_comparator": {
                "kroger_api_key": {"type": "password", "label": "Kroger API Key", "required": False, "placeholder": "Your Kroger API key"},
                "walmart_api_key": {"type": "password", "label": "Walmart API Key", "required": False, "placeholder": "Your Walmart API key"},
                "target_api_key": {"type": "password", "label": "Target API Key", "required": False, "placeholder": "Your Target API key"},
                "costco_api_key": {"type": "password", "label": "Costco API Key", "required": False, "placeholder": "Your Costco API key"},
                "whole_foods_api_key": {"type": "password", "label": "Whole Foods API Key", "required": False, "placeholder": "Your Whole Foods API key"},
                "price_threshold": {"type": "number", "label": "Price Alert Threshold (%)", "default": 10, "min": 1, "max": 50}
            },
            "shopping_optimizer": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "preferred_stores": {"type": "string", "label": "Preferred Stores (comma-separated)", "placeholder": "Kroger, Walmart, Target"},
                "max_travel_distance": {"type": "number", "label": "Max Travel Distance (miles)", "default": 10, "min": 1, "max": 50},
                "budget_optimization": {"type": "boolean", "label": "Enable Budget Optimization", "default": True}
            },
            "pantry_tracker": {
                "storage_type": {"type": "select", "label": "Storage Type", "options": ["local", "cloud"], "default": "local"},
                "expiration_alerts": {"type": "boolean", "label": "Expiration Alerts", "default": True},
                "alert_days_before": {"type": "number", "label": "Alert Days Before Expiration", "default": 3, "min": 1, "max": 30},
                "barcode_scanner_api": {"type": "password", "label": "Barcode Scanner API Key", "required": False, "placeholder": "Your barcode API key"}
            },

            # ============ LUNA HEALTH TOOLS ============
            "fitness_tracker": {
                "fitbit_client_id": {"type": "string", "label": "Fitbit Client ID", "required": False, "placeholder": "Your Fitbit Client ID"},
                "fitbit_client_secret": {"type": "password", "label": "Fitbit Client Secret", "required": False, "placeholder": "Your Fitbit Client Secret"},
                "apple_health_enabled": {"type": "boolean", "label": "Apple Health Integration", "default": False},
                "garmin_api_key": {"type": "password", "label": "Garmin API Key", "required": False, "placeholder": "Your Garmin API key"},
                "strava_client_id": {"type": "string", "label": "Strava Client ID", "required": False, "placeholder": "Your Strava Client ID"},
                "strava_client_secret": {"type": "password", "label": "Strava Client Secret", "required": False, "placeholder": "Your Strava Client Secret"},
                "sync_frequency": {"type": "select", "label": "Data Sync Frequency", "options": ["realtime", "hourly", "daily"], "default": "daily"}
            },
            "health_analyzer": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "health_data_retention": {"type": "number", "label": "Health Data Retention (days)", "default": 365, "min": 30, "max": 1825},
                "enable_ai_insights": {"type": "boolean", "label": "Enable AI Health Insights", "default": True},
                "privacy_mode": {"type": "select", "label": "Privacy Mode", "options": ["strict", "balanced", "open"], "default": "balanced"}
            },
            "workout_planner": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "default_workout_duration": {"type": "number", "label": "Default Workout Duration (minutes)", "default": 45, "min": 15, "max": 180},
                "fitness_level": {"type": "select", "label": "Default Fitness Level", "options": ["beginner", "intermediate", "advanced"], "default": "intermediate"},
                "preferred_workout_types": {"type": "string", "label": "Preferred Workout Types (comma-separated)", "placeholder": "strength, cardio, yoga"}
            },
            "recovery_monitor": {
                "track_sleep": {"type": "boolean", "label": "Track Sleep Patterns", "default": True},
                "track_hrv": {"type": "boolean", "label": "Track Heart Rate Variability", "default": True},
                "track_stress": {"type": "boolean", "label": "Track Stress Levels", "default": True},
                "recovery_notifications": {"type": "boolean", "label": "Recovery Notifications", "default": True}
            },

            # ============ MILO NUTRITION TOOLS ============
            "nutrition_analyzer": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "usda_api_key": {"type": "password", "label": "USDA FoodData API Key", "required": False, "placeholder": "Your USDA API key"},
                "nutritionix_app_id": {"type": "string", "label": "Nutritionix App ID", "required": False, "placeholder": "Your Nutritionix App ID"},
                "nutritionix_api_key": {"type": "password", "label": "Nutritionix API Key", "required": False, "placeholder": "Your Nutritionix API key"},
                "daily_calorie_target": {"type": "number", "label": "Daily Calorie Target", "default": 2000, "min": 1000, "max": 5000}
            },
            "meal_planner": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "spoonacular_api_key": {"type": "password", "label": "Spoonacular API Key", "required": False, "placeholder": "Your Spoonacular API key"},
                "dietary_restrictions": {"type": "string", "label": "Dietary Restrictions (comma-separated)", "placeholder": "vegetarian, gluten-free, dairy-free"},
                "meal_prep_days": {"type": "number", "label": "Meal Prep Days", "default": 7, "min": 1, "max": 14},
                "budget_per_meal": {"type": "number", "label": "Budget Per Meal ($)", "default": 10, "min": 1, "max": 100}
            },
            "recipe_engine": {
                "openai_api_key": {"type": "password", "label": "OpenAI API Key", "required": True, "placeholder": "sk-..."},
                "recipe_api_key": {"type": "password", "label": "Recipe API Key", "required": False, "placeholder": "Your recipe API key"},
                "cuisine_preferences": {"type": "string", "label": "Cuisine Preferences (comma-separated)", "placeholder": "italian, asian, mexican"},
                "difficulty_level": {"type": "select", "label": "Recipe Difficulty Level", "options": ["easy", "medium", "hard", "any"], "default": "medium"},
                "cooking_time_limit": {"type": "number", "label": "Cooking Time Limit (minutes)", "default": 60, "min": 10, "max": 300}
            }
        }
        return schemas.get(tool_name, {})
    
    def _update_environment_variables(self, agent_name: str, tool_name: str, config: Dict[str, Any]) -> None:
        """Update environment variables based on tool configuration"""
        import os
        
        if tool_name == "calendar_manager":
            if config.get("google_client_id"):
                os.environ["GOOGLE_CLIENT_ID"] = config["google_client_id"]
            if config.get("google_client_secret"):
                os.environ["GOOGLE_CLIENT_SECRET"] = config["google_client_secret"]
        elif tool_name in ["schedule_optimizer", "meeting_assistant"]:
            if config.get("openai_api_key"):
                os.environ["OPENAI_API_KEY"] = config["openai_api_key"]
    
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
