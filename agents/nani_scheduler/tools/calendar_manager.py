"""
Calendar Manager Tool for Agent Nani
Manages calendar operations with external calendar systems
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class CalendarManagerTool(BaseMCPTool):
    """Manages calendar operations with external calendar systems"""
    
    def __init__(self):
        super().__init__("calendar_manager", "Comprehensive calendar management and synchronization")
        self.cached_events = {}
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get_events", "create_event", "update_event", "delete_event", "find_free_time"]
                },
                "start_date": {"type": "string", "format": "date-time"},
                "end_date": {"type": "string", "format": "date-time"},
                "event_details": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "location": {"type": "string"},
                        "attendees": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "duration_minutes": {"type": "integer"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "preferred_times": {"type": "array", "items": {"type": "string"}},
                        "avoid_times": {"type": "array", "items": {"type": "string"}},
                        "buffer_minutes": {"type": "integer", "default": 15}
                    }
                }
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "events": {"type": "array"},
                "free_slots": {"type": "array"},
                "created_event": {"type": "object"},
                "conflicts": {"type": "array"},
                "suggestions": {"type": "array"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "get_events":
                result = await self._get_events(
                    parameters.get("start_date"),
                    parameters.get("end_date"),
                    context
                )
            elif action == "create_event":
                result = await self._create_event(
                    parameters.get("event_details", {}),
                    context
                )
            elif action == "find_free_time":
                result = await self._find_free_time(
                    parameters.get("duration_minutes", 60),
                    parameters.get("start_date"),
                    parameters.get("end_date"),
                    parameters.get("preferences", {}),
                    context
                )
            else:
                return ExecutionResult(
                    success=False, 
                    error=f"Unknown action: {action}", 
                    execution_time=0.0
                )
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=0.5,
                context_updates={"last_calendar_sync": datetime.utcnow().isoformat()}
            )
        
        except Exception as e:
            self.logger.error(f"Calendar operation failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _get_events(self, start_date: str, end_date: str, context: ExecutionContext) -> Dict[str, Any]:
        """Get calendar events for specified date range"""
        # Mock implementation - would integrate with Google Calendar API
        events = [
            {
                "id": "event_1",
                "title": "Team Meeting",
                "start": "2025-07-24T10:00:00Z",
                "end": "2025-07-24T11:00:00Z",
                "location": "Conference Room A",
                "attendees": ["john@company.com", "jane@company.com"]
            },
            {
                "id": "event_2",
                "title": "Doctor Appointment",
                "start": "2025-07-24T14:00:00Z",
                "end": "2025-07-24T15:00:00Z",
                "location": "Medical Center",
                "attendees": []
            }
        ]
        
        return {"events": events, "total_count": len(events)}
    
    async def _create_event(self, event_details: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Create a new calendar event"""
        new_event = {
            "id": f"event_{datetime.utcnow().timestamp()}",
            "title": event_details.get("title", "New Event"),
            "description": event_details.get("description", ""),
            "start": event_details.get("start_time"),
            "end": event_details.get("end_time"),
            "location": event_details.get("location", ""),
            "created": datetime.utcnow().isoformat()
        }
        
        return {"created_event": new_event}
    
    async def _find_free_time(self, duration_minutes: int, start_date: str, end_date: str, 
                            preferences: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Find available time slots for scheduling"""
        # Mock implementation of intelligent free time finding
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        free_slots = [
            {
                "start": f"{tomorrow.strftime('%Y-%m-%d')}T09:00:00Z",
                "end": f"{tomorrow.strftime('%Y-%m-%d')}T10:00:00Z",
                "score": 0.95,
                "reasoning": "Morning slot, high energy period, no conflicts"
            },
            {
                "start": f"{tomorrow.strftime('%Y-%m-%d')}T13:00:00Z",
                "end": f"{tomorrow.strftime('%Y-%m-%d')}T14:00:00Z",
                "score": 0.80,
                "reasoning": "After lunch, moderate energy, travel time considered"
            }
        ]
        
        return {"free_slots": free_slots, "duration_minutes": duration_minutes}