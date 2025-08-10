"""
Agent Nani - Core Agent Implementation
Scheduler & Calendar Management Agent
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.mcp_framework.base_server import BaseMCPServer, ExecutionContext
from shared.a2a_protocol.message_router import A2AMessage
from agents.master_coordinator.coordinator import UserMemory

# Import Nani's tools
from agents.nani_scheduler.tools.calendar_manager import CalendarManagerTool
from agents.nani_scheduler.tools.scheduling_optimizer import SchedulingOptimizerTool
from agents.nani_scheduler.tools.timezone_handler import TimezoneHandlerTool
from agents.nani_scheduler.tools.focus_blocker import FocusTimeBlockerTool

class NaniAgent(BaseMCPServer):
    """Agent Nani - Scheduler & Calendar Management"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("nani", 8001, config)
        
        # Initialize memory system
        self.memory = UserMemory("nani_user_memory.json")
        
        # Register all Nani's tools
        self.register_tool(CalendarManagerTool())
        self.register_tool(SchedulingOptimizerTool()) 
        self.register_tool(TimezoneHandlerTool())
        self.register_tool(FocusTimeBlockerTool())
        
        self.logger.info("Agent Nani initialized with 4 tools and memory system")
    
    async def process_a2a_message(self, message_data: dict) -> Dict[str, Any]:
        """Process incoming A2A messages from other agents"""
        try:
            message = A2AMessage(**message_data)
            self.logger.info(f"Received A2A message: {message.intent} from {message.from_agent}")
            
            if message.intent == "get_optimal_workout_times":
                return await self._handle_workout_scheduling(message)
            elif message.intent == "schedule_meal_prep_sessions":
                return await self._handle_meal_prep_scheduling(message)
            elif message.intent == "plan_shopping_trips":
                return await self._handle_shopping_trip_planning(message)
            else:
                return {
                    "success": False, 
                    "error": f"Unknown intent: {message.intent}",
                    "agent": "nani"
                }
                
        except Exception as e:
            self.logger.error(f"A2A message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "nani"
            }
    
    async def _handle_workout_scheduling(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle workout scheduling requests from Luna"""
        payload = message.payload
        
        # Use calendar manager to find optimal workout times
        calendar_tool = self.tools["calendar_manager"]
        context = ExecutionContext(
            user_id=payload.get("user_id", "default"),
            session_id=message.session_id,
            permissions=["read", "write"]
        )
        
        # Find free time slots for workouts
        free_time_result = await calendar_tool.execute({
            "action": "find_free_time",
            "duration_minutes": 60,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "preferences": {
                "preferred_times": ["06:00", "18:00"],  # Morning or evening
                "buffer_minutes": 30
            }
        }, context)
        
        if free_time_result.success:
            optimal_times = free_time_result.result["free_slots"]
            return {
                "success": True,
                "optimal_workout_times": optimal_times,
                "scheduling_confidence": 0.87,
                "calendar_integration": True,
                "agent": "nani"
            }
        else:
            return {
                "success": False, 
                "error": "Failed to find optimal workout times",
                "agent": "nani"
            }
    
    async def _handle_meal_prep_scheduling(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle meal prep scheduling requests from Milo"""
        payload = message.payload
        meal_plan = payload.get("meal_plan", {})
        
        # Calculate prep time requirements
        prep_sessions = []
        for day, meals in meal_plan.items():
            if isinstance(meals, list):
                total_prep_time = sum(meal.get("prep_time", 30) for meal in meals)
                prep_sessions.append({
                    "day": day,
                    "estimated_duration": total_prep_time,
                    "optimal_time": "Sunday 14:00",  # Would use scheduling optimizer
                    "meal_count": len(meals)
                })
        
        return {
            "success": True,
            "prep_schedule": prep_sessions,
            "total_prep_time": sum(s["estimated_duration"] for s in prep_sessions),
            "kitchen_blocking": True,
            "agent": "nani"
        }
    
    async def _handle_shopping_trip_planning(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle shopping trip planning requests from Bucky"""
        payload = message.payload
        shopping_list = payload.get("shopping_list", [])
        
        # Mock shopping trip optimization
        optimized_trips = [
            {
                "store": "Whole Foods",
                "items": shopping_list[:5] if len(shopping_list) > 5 else shopping_list,
                "optimal_time": "Saturday 09:00",
                "estimated_duration": 45,
                "travel_time": 15
            }
        ]
        
        if len(shopping_list) > 5:
            optimized_trips.append({
                "store": "Costco", 
                "items": shopping_list[5:],
                "optimal_time": "Saturday 10:30",
                "estimated_duration": 30,
                "travel_time": 20
            })
        
        total_time = sum(trip["estimated_duration"] + trip["travel_time"] for trip in optimized_trips)
        
        return {
            "success": True,
            "optimized_routes": optimized_trips,
            "total_time": total_time,
            "fuel_optimization": True,
            "agent": "nani"
        }