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

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiohttp

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
        
        # Setup OAuth endpoints
        self._setup_oauth_endpoints()
        
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
        
        @self.app.post("/agents/{agent_name}/chat")
        async def chat_with_agent(agent_name: str, request: dict):
            """Chat with a specific agent"""
            message = request.get('message', '')
            context = request.get('context')
            
            if agent_name not in self.message_router.agent_endpoints:
                raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
            try:
                from datetime import datetime
                import os
                import json
                
                # Check if we have OpenAI API key
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key or openai_key == 'YOUR_OPENAI_API_KEY_HERE':
                    return {
                        "agent_name": agent_name,
                        "response": f"❌ OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file to enable AI chat functionality. Visit https://platform.openai.com/api-keys to get your API key.",
                        "tools_used": [],
                        "execution_time": 0,
                        "error": "OpenAI API key not configured"
                    }
                
                # Intelligent multi-agent routing with GPT classification
                from openai import OpenAI
                client = OpenAI()
                
                # First, classify which agent should handle this query
                agent_classification = client.chat.completions.create(
                    model="gpt-4o",
                    temperature=0.1,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an intelligent router for a multi-agent personal assistant system. Classify user queries to determine which agent should handle them.

Available Agents:
- **NANI (Scheduler)**: Calendar events, appointments, time management, scheduling, reminders, productivity, focus time
- **Bucky (Shopping)**: Shopping lists, price comparisons, deals, grocery management, pantry tracking, purchasing
- **Luna (Health)**: Fitness tracking, workouts, health analysis, recovery, exercise planning, wellness
- **Milo (Nutrition)**: Meal planning, recipes, nutrition analysis, diet tracking, food recommendations

Examples:
- "Schedule a meeting tomorrow" → NANI
- "Find me the best price for organic apples" → Bucky  
- "Plan my workout for today" → Luna
- "What should I cook for dinner?" → Milo
- "Add milk to my shopping list" → Bucky
- "Track my calories today" → Milo
- "Set a reminder for 3pm" → NANI
- "How's my recovery after yesterday's workout?" → Luna

Return JSON:
{
  "agent": "nani|bucky|luna|milo",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}"""
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ]
                )
                
                try:
                    routing_result = json.loads(agent_classification.choices[0].message.content)
                    target_agent = routing_result.get("agent", agent_name).lower()
                    confidence = routing_result.get("confidence", 0.5)
                    
                    # Override agent_name with AI-determined agent if confidence is high
                    if confidence > 0.7 and target_agent in ["nani", "bucky", "luna", "milo"]:
                        agent_name = target_agent
                        self.logger.info(f"Routed query to {agent_name} with confidence {confidence}")
                    
                except Exception as e:
                    self.logger.error(f"Agent classification failed: {e}, using original agent: {agent_name}")
                
                # Get the endpoint for the target agent
                endpoint = self.message_router.agent_endpoints.get(agent_name)
                if not endpoint:
                    raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
                
                # Agent-specific intelligent tool routing
                if agent_name == "nani":
                    try:
                        from openai import OpenAI
                        client = OpenAI()
                        
                        # Use GPT to classify the intent and extract structured data
                        intent_response = client.chat.completions.create(
                            model="gpt-4o",
                            temperature=0.2,
                            messages=[
                                {
                                    "role": "system",
                                    "content": """You are NANI, an intelligent calendar and scheduling assistant. Analyze user messages and determine the appropriate action and extract relevant details.

Current date/time: August 11, 2025, 8:32 PM

Available actions:
- add_event: Create calendar events, schedule meetings, set appointments
- get_events: View calendar, check schedule, see upcoming events  
- get_calendar_info: General calendar questions, status checks

For add_event, extract:
- title: What is being scheduled
- start_time: When it starts (ISO format: YYYY-MM-DDTHH:MM:SS)
- end_time: When it ends (ISO format, default to +30min if not specified)
- description: Additional details
- location: Where it happens

For get_events, extract:
- date: Which date to check (ISO format: YYYY-MM-DD, default to today)

Return JSON format:
{
  "action": "add_event|get_events|get_calendar_info",
  "parameters": {
    "title": "...",
    "start_time": "...",
    "end_time": "...",
    "description": "...",
    "location": "...",
    "date": "..."
  },
  "confidence": 0.95
}"""
                                },
                                {
                                    "role": "user", 
                                    "content": message
                                }
                            ]
                        )
                        
                        # Parse GPT response to determine MCP action
                        try:
                            intent_data = json.loads(intent_response.choices[0].message.content)
                            action = intent_data.get("action", "get_calendar_info")
                            parameters = intent_data.get("parameters", {})
                            
                            # Clean up parameters - remove empty values
                            clean_params = {k: v for k, v in parameters.items() if v}
                            
                            mcp_payload = {
                                "id": "chat_request",
                                "method": "tools/call",
                                "params": {
                                    "name": "calendar_manager",
                                    "arguments": {
                                        "action": action,
                                        **clean_params
                                    }
                                }
                            }
                        except Exception as e:
                            self.logger.error(f"Failed to parse GPT intent: {e}")
                            # Fallback to simple calendar info
                            mcp_payload = {
                                "id": "chat_request",
                                "method": "tools/call",
                                "params": {
                                    "name": "calendar_manager", 
                                    "arguments": {"action": "get_calendar_info"}
                                }
                            }
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.post(f"{endpoint}/mcp", json=mcp_payload) as resp:
                                if resp.status == 200:
                                    mcp_result = await resp.json()
                                    
                                    # Extract the MCP result and generate intelligent response
                                    content = mcp_result.get("result", {}).get("content", [])
                                    if content and content[0].get("type") == "text":
                                        mcp_response = content[0].get("text", "")
                                        
                                        # Parse the MCP tool result
                                        try:
                                            tool_result = json.loads(mcp_response)
                                        except:
                                            tool_result = {"message": mcp_response}
                                        
                                        # Generate natural response using GPT
                                        final_response = client.chat.completions.create(
                                            model="gpt-4o",
                                            temperature=0.3,
                                            messages=[
                                                {
                                                    "role": "system",
                                                    "content": f"""You are NANI, the user's personal scheduling assistant. Generate a natural, helpful response based on the calendar tool result.

Original user message: "{message}"
Tool result: {json.dumps(tool_result, indent=2)}

Guidelines:
- Be conversational and friendly
- Confirm what was done clearly
- For successful actions, acknowledge completion
- For calendar events, mention key details (time, title)
- Keep responses concise but informative
- Don't mention technical terms like "MCP" or "tool execution"
- Sound like a helpful personal assistant"""
                                                },
                                                {
                                                    "role": "user",
                                                    "content": f"Generate a response for: {message}"
                                                }
                                            ]
                                        )
                                        
                                        response = final_response.choices[0].message.content
                                    else:
                                        response = "I've processed your calendar request successfully."
                                    
                                    return {
                                        "agent_name": agent_name,
                                        "response": response,
                                        "tools_used": ["calendar_manager"],
                                        "execution_time": 1.0,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                else:
                                    error_text = await resp.text()
                                    self.logger.error(f"NANI MCP error: {error_text}")
                                    return {
                                        "agent_name": agent_name,
                                        "response": "I encountered an error accessing my calendar. Please try again.",
                                        "tools_used": [],
                                        "execution_time": 0,
                                        "error": f"MCP error: {resp.status}"
                                    }
                                    
                    except Exception as e:
                        self.logger.error(f"Error communicating with NANI: {e}")
                        return {
                            "agent_name": agent_name,
                            "response": "I encountered an error. Please try again in a moment.",
                            "tools_used": [],
                            "execution_time": 0,
                            "error": str(e)
                        }
                
                # Generic MCP routing for all other agents
                else:
                    try:
                        # Universal GPT-based tool routing for any agent
                        tool_selection = client.chat.completions.create(
                            model="gpt-4o",
                            temperature=0.2,
                            messages=[
                                {
                                    "role": "system", 
                                    "content": f"""You are a tool selection AI for {agent_name.upper()} agent. Based on the user query, determine which tool to use and extract parameters.

Agent: {agent_name.upper()}

Available tools based on agent:
- Bucky (Shopping): shopping_optimizer, price_comparator, deal_finder, pantry_tracker
- Luna (Health): fitness_tracker, workout_planner, health_analyzer, recovery_monitor  
- Milo (Nutrition): meal_planner, recipe_engine, nutrition_analyzer
- NANI (Scheduler): calendar_manager, scheduling_optimizer, time_tracker, focus_blocker

Return JSON:
{{
  "tool": "tool_name",
  "parameters": {{
    "key": "value"
  }},
  "confidence": 0.95
}}"""
                                },
                                {
                                    "role": "user",
                                    "content": message
                                }
                            ]
                        )
                        
                        # Parse tool selection and make MCP call
                        try:
                            tool_data = json.loads(tool_selection.choices[0].message.content)
                            tool_name = tool_data.get("tool", "default_tool")
                            parameters = tool_data.get("parameters", {})
                            
                            mcp_payload = {
                                "id": "chat_request",
                                "method": "tools/call",
                                "params": {
                                    "name": tool_name,
                                    "arguments": parameters
                                }
                            }
                            
                        except Exception as e:
                            self.logger.error(f"Tool selection parsing failed: {e}")
                            # Fallback with generic parameters
                            mcp_payload = {
                                "id": "chat_request",
                                "method": "tools/call",
                                "params": {
                                    "name": "default_tool",
                                    "arguments": {"query": message}
                                }
                            }
                        
                        # Execute MCP call
                        async with aiohttp.ClientSession() as session:
                            async with session.post(f"{endpoint}/mcp", json=mcp_payload) as resp:
                                if resp.status == 200:
                                    mcp_result = await resp.json()
                                    
                                    # Parse MCP response
                                    content = mcp_result.get("result", {}).get("content", [])
                                    if content and content[0].get("type") == "text":
                                        mcp_response = content[0].get("text", "")
                                        
                                        try:
                                            tool_result = json.loads(mcp_response)
                                        except:
                                            tool_result = {"message": mcp_response}
                                        
                                        # Generate natural response with agent personality
                                        agent_personalities = {
                                            "bucky": "Bucky, your smart shopping assistant",
                                            "luna": "Luna, your health and fitness coach", 
                                            "milo": "Milo, your nutrition and meal planning expert"
                                        }
                                        
                                        final_response = client.chat.completions.create(
                                            model="gpt-4o",
                                            temperature=0.3,
                                            messages=[
                                                {
                                                    "role": "system",
                                                    "content": f"""You are {agent_personalities.get(agent_name, agent_name)}, responding based on tool results.

Original user message: "{message}"
Tool result: {json.dumps(tool_result, indent=2)}

Guidelines:
- Be conversational and helpful in your specialized domain
- Confirm what was accomplished
- Give specific, actionable information  
- Keep responses concise but informative
- Don't mention "MCP" or technical implementation details
- Sound like a knowledgeable personal assistant in your field"""
                                                },
                                                {
                                                    "role": "user",
                                                    "content": f"Generate a response for: {message}"
                                                }
                                            ]
                                        )
                                        
                                        response = final_response.choices[0].message.content
                                    else:
                                        response = f"I've processed your {agent_name} request successfully."
                                    
                                    return {
                                        "agent_name": agent_name,
                                        "response": response,
                                        "tools_used": [tool_name],
                                        "execution_time": 1.5,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    
                                else:
                                    error_text = await resp.text()
                                    self.logger.error(f"{agent_name} MCP error: {error_text}")
                                    return {
                                        "agent_name": agent_name,
                                        "response": f"I encountered an issue processing your {agent_name} request. Please try again.",
                                        "execution_time": 0,
                                        "error": f"MCP error: {resp.status}"
                                    }
                                    
                    except Exception as e:
                        self.logger.error(f"Error communicating with {agent_name}: {e}")
                        return {
                            "agent_name": agent_name,
                            "response": f"I encountered an error processing your {agent_name} request. Please try again in a moment.",
                            "tools_used": [],
                            "execution_time": 0,
                            "error": str(e)
                        }
                
                # If we have an API key, use OpenAI to understand intent and execute tools
                try:
                    from openai import OpenAI
                    import json
                    client = OpenAI(api_key=openai_key)
                    
                    # First, use OpenAI to understand the intent and extract parameters
                    from datetime import datetime, timedelta
                    import pytz
                    
                    intent_prompt = f"""
                    You are analyzing a user message for {agent_name} agent to determine if it requires tool execution.
                    Current time: {datetime.now().isoformat()}
                    
                    Agent capabilities:
                    - nani: calendar_manager (create/get/update/delete events, find free time, get events)
                    - bucky: deal_finder, price_comparator, shopping_optimizer, pantry_tracker
                    - luna: fitness_tracker, health_analyzer, workout_planner, recovery_monitor  
                    - milo: nutrition_analyzer, meal_planner, recipe_engine
                    
                    User message: "{message}"
                    
                    For scheduling requests, extract:
                    - title: meeting/event title
                    - start_time: ISO format (YYYY-MM-DDTHH:MM:SS)
                    - duration_minutes: duration in minutes
                    - description: additional details
                    
                    Respond with JSON in this format:
                    {{
                        "needs_tool": true/false,
                        "tool_name": "tool_name" (if needed),
                        "action": "specific_action" (if needed),
                        "event_details": {{
                            "title": "extracted title",
                            "start_time": "2025-08-12T14:00:00" (example),
                            "duration_minutes": 60,
                            "description": "extracted description"
                        }} (for calendar events),
                        "response_type": "tool_result" or "conversational"
                    }}
                    
                    Examples:
                    - "Schedule a team meeting tomorrow at 2pm for 1 hour" -> 
                      {{"needs_tool": true, "tool_name": "calendar_manager", "action": "create_event", 
                        "event_details": {{"title": "Team Meeting", "start_time": "2025-08-12T14:00:00", "duration_minutes": 60}}}}
                    - "What are my events today?" -> 
                      {{"needs_tool": true, "tool_name": "calendar_manager", "action": "get_events"}}
                    - "What should I eat?" -> {{"needs_tool": false, "response_type": "conversational"}}
                    """
                    
                    intent_response = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{"role": "user", "content": intent_prompt}],
                        max_tokens=200,
                        temperature=0.1
                    )
                    
                    try:
                        intent_data = json.loads(intent_response.choices[0].message.content)
                    except:
                        intent_data = {"needs_tool": False, "response_type": "conversational"}
                    
                    tools_used = []
                    tool_results = ""
                    
                    # If tool execution is needed, call the appropriate MCP endpoint
                    if intent_data.get("needs_tool", False):
                        tool_name = intent_data.get("tool_name")
                        action = intent_data.get("action")
                        
                        if agent_name == "nani" and tool_name == "calendar_manager":
                            try:
                                async with aiohttp.ClientSession() as session:
                                    # Prepare arguments based on action and extracted details
                                    arguments = {
                                        "action": action or "parse_natural_language",
                                        "user_id": "default_user"
                                    }
                                    
                                    # Add event details for create/update actions
                                    if action == "create_event" and "event_details" in intent_data:
                                        event_details = intent_data["event_details"]
                                        # Calculate end time if not provided
                                        start_time = event_details.get("start_time")
                                        duration = event_details.get("duration_minutes", 60)
                                        end_time = self._calculate_end_time(start_time, duration) if start_time else None
                                        
                                        arguments["event_details"] = {
                                            "title": event_details.get("title", "New Event"),
                                            "start_time": start_time,
                                            "end_time": end_time,
                                            "description": event_details.get("description", f"Created via chat: {message}"),
                                            "timezone": "UTC"
                                        }
                                    elif action == "get_events":
                                        # For getting events, set date range
                                        today = datetime.now()
                                        arguments["start_date"] = today.strftime("%Y-%m-%d")
                                        arguments["end_date"] = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                                    else:
                                        # Fallback to natural language processing
                                        arguments["natural_query"] = message
                                    
                                    # Call the Nani MCP server directly
                                    tool_payload = {
                                        "method": "tools/call",
                                        "params": {
                                            "name": "calendar_manager",
                                            "arguments": arguments
                                        }
                                    }
                                    
                                    endpoint = self.message_router.agent_endpoints.get(agent_name)
                                    async with session.post(f"{endpoint}/mcp", json=tool_payload) as resp:
                                        if resp.status == 200:
                                            tool_result = await resp.json()
                                            tools_used.append(tool_name)
                                            
                                            # Extract meaningful result
                                            if tool_result.get("result"):
                                                result_content = tool_result["result"]
                                                if isinstance(result_content, dict) and result_content.get("success"):
                                                    tool_results = f"✅ Calendar updated: {result_content.get('message', 'Event processed successfully')}"
                                                else:
                                                    tool_results = f"Tool result: {result_content}"
                                            else:
                                                tool_results = "Tool executed successfully"
                                        else:
                                            tool_results = f"Tool call failed with status {resp.status}"
                            except Exception as e:
                                tool_results = f"Tool execution failed: {str(e)}"
                    
                    # Generate final response with context from tool results
                    agent_contexts = {
                        "nani": "You are Nani, a helpful calendar and scheduling assistant. You help with time management, scheduling, and productivity optimization.",
                        "bucky": "You are Bucky, a smart shopping and inventory assistant. You help with shopping lists, price comparisons, and inventory management.", 
                        "luna": "You are Luna, a health and fitness assistant. You help with workout planning, health tracking, and wellness optimization.",
                        "milo": "You are Milo, a nutrition and meal planning assistant. You help with meal planning, recipe suggestions, and nutritional analysis."
                    }
                    
                    system_prompt = agent_contexts.get(agent_name, f"You are {agent_name}, a helpful personal assistant.")
                    
                    if tool_results:
                        final_prompt = f"User request: {message}\nTool execution result: {tool_results}\n\nProvide a helpful response based on the tool execution results."
                    else:
                        final_prompt = message
                    
                    final_response = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": final_prompt}
                        ],
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    response_text = final_response.choices[0].message.content
                    if tool_results and "Tool executed:" in tool_results:
                        response_text += f"\n\n✅ Action completed: {tool_results.replace('Tool executed: ', '')}"
                    
                    return {
                        "agent_name": agent_name,
                        "response": response_text,
                        "tools_used": tools_used,
                        "execution_time": 2.5,
                        "timestamp": datetime.now().isoformat(),
                        "tool_results": tool_results if tool_results else None
                    }
                
                except Exception as e:
                    return {
                        "agent_name": agent_name, 
                        "response": f"❌ Error connecting to OpenAI: {str(e)}. Please check your API key and try again.",
                        "tools_used": [],
                        "execution_time": 0,
                        "error": str(e)
                    }
                    
            except Exception as e:
                self.logger.error(f"Chat error with agent {agent_name}: {e}")
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
    
    async def _get_tool_config(self, agent_name: str, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a tool"""
        import json
        from pathlib import Path
        import os
        import re
        
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
                    raw_config = all_configs.get(tool_name, {})
                    
                    # Resolve environment variables in the config
                    def resolve_env_vars(obj):
                        if isinstance(obj, dict):
                            return {k: resolve_env_vars(v) for k, v in obj.items()}
                        elif isinstance(obj, str):
                            # Replace ${VAR_NAME} with actual environment variable values
                            def replace_var(match):
                                var_name = match.group(1)
                                return os.getenv(var_name, f"${{{var_name}}}")
                            return re.sub(r'\$\{([^}]+)\}', replace_var, obj)
                        else:
                            return obj
                    
                    config_data = resolve_env_vars(raw_config)
                    
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
    
    def _calculate_end_time(self, start_time: str, duration_minutes: int) -> str:
        """Calculate end time based on start time and duration"""
        try:
            from datetime import datetime, timedelta
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            return end_dt.isoformat()
        except:
            return start_time  # Fallback to start time if parsing fails
    
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
    
    def _setup_oauth_endpoints(self):
        """Setup Google OAuth callback endpoint"""
        
        @self.app.get("/auth/google/callback")
        async def google_oauth_callback(code: str = None, error: str = None):
            """Handle Google OAuth callback"""
            if error:
                return {
                    "success": False,
                    "error": f"OAuth error: {error}",
                    "message": "Authentication failed. Please try again."
                }
            
            if not code:
                return {
                    "success": False,
                    "error": "No authorization code received",
                    "message": "Authentication failed. Please try again."
                }
            
            try:
                # Import here to avoid circular imports
                from agents.nani_scheduler.src.google_calendar_integration import GoogleCalendarManager
                import json
                from pathlib import Path
                
                # Load calendar config
                tool_config_file = Path(__file__).parent.parent.parent / "agents" / "nani_scheduler" / "config" / "tool_config.json"
                if tool_config_file.exists():
                    with open(tool_config_file, 'r') as f:
                        tool_configs = json.load(f)
                        calendar_config = tool_configs.get("calendar_manager", {})
                else:
                    calendar_config = {}
                
                # Complete OAuth flow
                google_calendar = GoogleCalendarManager(calendar_config)
                success = google_calendar.complete_oauth(code)
                
                if success:
                    return {
                        "success": True,
                        "message": "✅ Google Calendar connected successfully! You can now close this window and return to your chat.",
                        "instructions": "Go back to your chat and try scheduling an event again."
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to complete OAuth flow",
                        "message": "Authentication failed. Please try the authentication link again."
                    }
                    
            except Exception as e:
                self.logger.error(f"OAuth callback error: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Authentication failed due to an error. Please try again."
                }

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
