"""
A2A (Agent-to-Agent) Message Protocol
Handles communication between different agents
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class MessageIntent(Enum):
    """Types of A2A message intents"""
    PANTRY_INVENTORY_STATUS = "pantry_inventory_status"
    SHOPPING_TRIP_SCHEDULING = "shopping_trip_scheduling"
    HEALTH_FOOD_RECOMMENDATIONS = "health_food_recommendations"
    GENERATE_SHOPPING_LIST = "generate_shopping_list"
    MEAL_PLANNING_REQUEST = "meal_planning_request"
    FITNESS_SCHEDULE_OPTIMIZATION = "fitness_schedule_optimization"
    CALENDAR_SYNC_REQUEST = "calendar_sync_request"
    WORKOUT_RECOMMENDATION = "workout_recommendation"
    NUTRITION_ANALYSIS = "nutrition_analysis"
    SCHEDULE_CONFLICT_RESOLUTION = "schedule_conflict_resolution"

@dataclass
class A2AMessage:
    """A2A message structure"""
    from_agent: str
    to_agent: str
    intent: str
    payload: Dict[str, Any]
    session_id: str
    message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"  # low, normal, high, urgent
    requires_response: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = f"msg_{self.timestamp.timestamp()}_{hash(self.from_agent)}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "intent": self.intent,
            "payload": self.payload,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "requires_response": self.requires_response,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Create message from dictionary"""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

@dataclass
class A2AResponse:
    """A2A response structure"""
    message_id: str
    from_agent: str
    to_agent: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }

class A2AMessageRouter:
    """Routes A2A messages between agents"""
    
    def __init__(self):
        self.agent_endpoints: Dict[str, str] = {}
        self.message_handlers: Dict[str, callable] = {}
        self.logger = None  # Will be set by the agent
    
    def register_agent(self, agent_name: str, endpoint: str):
        """Register an agent endpoint"""
        self.agent_endpoints[agent_name] = endpoint
    
    def register_handler(self, intent: str, handler: callable):
        """Register a message handler for a specific intent"""
        self.message_handlers[intent] = handler
    
    async def send_message(self, message: A2AMessage) -> A2AResponse:
        """Send a message to another agent"""
        import aiohttp
        
        if message.to_agent not in self.agent_endpoints:
            raise ValueError(f"Agent {message.to_agent} not registered")
        
        endpoint = self.agent_endpoints[message.to_agent]
        url = f"{endpoint}/a2a/message"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=message.to_dict()) as response:
                    if response.status == 200:
                        data = await response.json()
                        return A2AResponse(
                            message_id=message.message_id,
                            from_agent=message.to_agent,
                            to_agent=message.from_agent,
                            success=data.get("success", False),
                            data=data.get("data"),
                            error=data.get("error"),
                            metadata=data.get("metadata")
                        )
                    else:
                        return A2AResponse(
                            message_id=message.message_id,
                            from_agent=message.to_agent,
                            to_agent=message.from_agent,
                            success=False,
                            error=f"HTTP {response.status}: {await response.text()}"
                        )
        except Exception as e:
            return A2AResponse(
                message_id=message.message_id,
                from_agent=message.to_agent,
                to_agent=message.from_agent,
                success=False,
                error=f"Network error: {str(e)}"
            )
    
    async def broadcast_message(self, message: A2AMessage, exclude_self: bool = True) -> List[A2AResponse]:
        """Broadcast a message to all registered agents"""
        responses = []
        for agent_name, endpoint in self.agent_endpoints.items():
            if exclude_self and agent_name == message.from_agent:
                continue
            
            message.to_agent = agent_name
            response = await self.send_message(message)
            responses.append(response)
        
        return responses
