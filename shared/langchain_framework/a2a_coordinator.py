"""
LangChain A2A Coordinator
Coordinates communication between LangChain agents
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from dataclasses import dataclass

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.agents import AgentExecutor

from .base_agent import LangChainBaseAgent
from ..utils.logging import setup_logging

@dataclass
class A2AMessage:
    """A2A message structure for LangChain agents"""
    from_agent: str
    to_agent: str
    intent: str
    payload: Dict[str, Any]
    session_id: str
    message_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = f"msg_{self.timestamp.timestamp()}_{hash(self.from_agent)}"

class LangChainA2ACoordinator:
    """Coordinates A2A communication between LangChain agents"""
    
    def __init__(self):
        self.agents: Dict[str, LangChainBaseAgent] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.logger = setup_logging("a2a_coordinator")
        self.message_history: List[A2AMessage] = []
    
    def register_agent(self, agent: LangChainBaseAgent):
        """Register a LangChain agent"""
        self.agents[agent.agent_name] = agent
        self.logger.info(f"Registered agent: {agent.agent_name}")
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"Unregistered agent: {agent_name}")
    
    async def send_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Send a message from one agent to another"""
        if message.to_agent not in self.agents:
            return {
                "success": False,
                "error": f"Agent {message.to_agent} not found",
                "message_id": message.message_id
            }
        
        try:
            # Add to message history
            self.message_history.append(message)
            
            # Get target agent
            target_agent = self.agents[message.to_agent]
            
            # Process message with target agent
            result = await target_agent.process_a2a_message({
                "intent": message.intent,
                "payload": message.payload,
                "from_agent": message.from_agent,
                "session_id": message.session_id,
                "message_id": message.message_id
            })
            
            return {
                "success": True,
                "data": result,
                "message_id": message.message_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error sending A2A message: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": message.message_id
            }
    
    async def broadcast_message(self, message: A2AMessage, exclude_sender: bool = True) -> List[Dict[str, Any]]:
        """Broadcast a message to all registered agents"""
        responses = []
        
        for agent_name, agent in self.agents.items():
            if exclude_sender and agent_name == message.from_agent:
                continue
            
            # Create message for this agent
            agent_message = A2AMessage(
                from_agent=message.from_agent,
                to_agent=agent_name,
                intent=message.intent,
                payload=message.payload,
                session_id=message.session_id
            )
            
            response = await self.send_message(agent_message)
            responses.append(response)
        
        return responses
    
    async def coordinate_workflow(self, workflow_id: str, steps: List[Dict[str, Any]], 
                                user_id: str, session_id: str) -> Dict[str, Any]:
        """Coordinate a multi-agent workflow"""
        workflow_results = {
            "workflow_id": workflow_id,
            "status": "running",
            "steps": [],
            "started_at": datetime.now().isoformat()
        }
        
        try:
            for i, step in enumerate(steps):
                step_result = {
                    "step_id": i,
                    "agent": step["agent"],
                    "intent": step["intent"],
                    "payload": step.get("payload", {}),
                    "status": "pending"
                }
                
                # Check if agent exists
                if step["agent"] not in self.agents:
                    step_result["status"] = "failed"
                    step_result["error"] = f"Agent {step['agent']} not found"
                    workflow_results["steps"].append(step_result)
                    continue
                
                # Create message for this step
                message = A2AMessage(
                    from_agent="workflow_coordinator",
                    to_agent=step["agent"],
                    intent=step["intent"],
                    payload=step.get("payload", {}),
                    session_id=session_id
                )
                
                # Send message
                response = await self.send_message(message)
                
                if response["success"]:
                    step_result["status"] = "completed"
                    step_result["result"] = response["data"]
                else:
                    step_result["status"] = "failed"
                    step_result["error"] = response["error"]
                
                workflow_results["steps"].append(step_result)
                
                # Check if workflow should continue
                if step_result["status"] == "failed" and step.get("critical", False):
                    workflow_results["status"] = "failed"
                    workflow_results["error"] = f"Critical step {i} failed"
                    break
            
            # Mark workflow as completed if no failures
            if workflow_results["status"] == "running":
                workflow_results["status"] = "completed"
            
            workflow_results["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
            workflow_results["completed_at"] = datetime.now().isoformat()
        
        return workflow_results
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        status = {}
        for agent_name, agent in self.agents.items():
            status[agent_name] = {
                "name": agent_name,
                "tools": [tool.name for tool in agent.tools],
                "a2a_handlers": list(agent.a2a_handlers.keys()),
                "memory_size": len(agent.memory.chat_memory.messages) if agent.memory.chat_memory else 0
            }
        return status
    
    def get_message_history(self, limit: int = 100) -> List[A2AMessage]:
        """Get recent message history"""
        return self.message_history[-limit:] if self.message_history else []
    
    async def clear_message_history(self):
        """Clear message history"""
        self.message_history.clear()
        self.logger.info("Message history cleared")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a global message handler"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered message handler for type: {message_type}")
    
    async def process_agent_request(self, agent_name: str, request: str, 
                                  context: Optional[Dict[str, Any]] = None) -> str:
        """Process a request through a specific agent"""
        if agent_name not in self.agents:
            return f"Agent {agent_name} not found"
        
        agent = self.agents[agent_name]
        return await agent.process_message(request, context)

# Global A2A coordinator instance
a2a_coordinator = LangChainA2ACoordinator() 