"""
Calendar Manager Tool for Agent Nani
Multi-user calendar management with real provider integrations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult
from agents.nani_scheduler.src.user_calendar_manager import UserCalendarManager, CalendarProvider

class CalendarManagerTool(BaseMCPTool):
    """Multi-user calendar management with real provider integrations"""
    
    def __init__(self):
        super().__init__("calendar_manager", "Multi-user calendar management with Google Calendar, Outlook, and other providers")
        self.user_calendar_manager = UserCalendarManager()
        self.logger = logging.getLogger("CalendarManagerTool")
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "get_events", "create_event", "update_event", "delete_event", 
                        "find_free_time", "setup_provider", "get_calendar_status",
                        "disconnect_provider", "parse_natural_language"
                    ]
                },
                "user_id": {"type": "string", "description": "Unique identifier for the user"},
                "provider": {"type": "string", "enum": ["google", "outlook", "apple", "caldav"]},
                "start_date": {"type": "string", "format": "date-time"},
                "end_date": {"type": "string", "format": "date-time"},
                "natural_query": {"type": "string", "description": "Natural language scheduling request"},
                "event_details": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "location": {"type": "string"},
                        "attendees": {"type": "array", "items": {"type": "string"}},
                        "start_time": {"type": "string", "format": "date-time"},
                        "end_time": {"type": "string", "format": "date-time"},
                        "timezone": {"type": "string", "default": "UTC"}
                    }
                },
                "duration_minutes": {"type": "integer", "default": 60},
                "client_config": {
                    "type": "object",
                    "description": "OAuth client configuration for provider setup"
                },
                "authorization_code": {"type": "string", "description": "OAuth authorization code"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "preferred_times": {"type": "array", "items": {"type": "string"}},
                        "avoid_times": {"type": "array", "items": {"type": "string"}},
                        "buffer_minutes": {"type": "integer", "default": 15},
                        "energy_patterns": {"type": "object"},
                        "working_hours": {"type": "object"}
                    }
                }
            },
            "required": ["action", "user_id"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "events": {"type": "array"},
                "free_slots": {"type": "array"},
                "created_event": {"type": "object"},
                "calendar_status": {"type": "object"},
                "authorization_url": {"type": "string"},
                "provider_info": {"type": "object"},
                "parsed_request": {"type": "object"},
                "message": {"type": "string"},
                "error": {"type": "string"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        user_id = parameters["user_id"]
        
        try:
            if action == "get_events":
                result = await self._get_user_events(user_id, parameters, context)
            elif action == "create_event":
                result = await self._create_user_event(user_id, parameters, context)
            elif action == "find_free_time":
                result = await self._find_user_free_time(user_id, parameters, context)
            elif action == "setup_provider":
                result = await self._setup_calendar_provider(user_id, parameters, context)
            elif action == "get_calendar_status":
                result = await self._get_user_calendar_status(user_id, context)
            elif action == "disconnect_provider":
                result = await self._disconnect_calendar_provider(user_id, parameters, context)
            elif action == "parse_natural_language":
                result = await self._parse_natural_language_request(user_id, parameters, context)
            else:
                return ExecutionResult(
                    success=False, 
                    error=f"Unknown action: {action}", 
                    execution_time=0.0
                )
            
            execution_time = 1.0 if action in ["setup_provider", "create_event"] else 0.5
            
            return ExecutionResult(
                success=result.get("success", True),
                result=result,
                execution_time=execution_time,
                context_updates={
                    "last_calendar_action": datetime.utcnow().isoformat(),
                    "user_id": user_id
                }
            )
        
        except Exception as e:
            self.logger.error(f"Calendar operation failed for user {user_id}: {e}")
            return ExecutionResult(
                success=False, 
                error=str(e), 
                execution_time=0.0,
                result={"success": False, "error": str(e)}
            )
    
    async def _get_user_events(self, user_id: str, parameters: Dict[str, Any], 
                             context: ExecutionContext) -> Dict[str, Any]:
        """Get calendar events for a user within specified date range"""
        try:
            start_date = datetime.fromisoformat(parameters.get("start_date", datetime.utcnow().isoformat()))
            end_date = datetime.fromisoformat(parameters.get("end_date", (datetime.utcnow() + timedelta(days=7)).isoformat()))
            provider = CalendarProvider(parameters["provider"]) if "provider" in parameters else None
            
            events = await self.user_calendar_manager.get_calendar_events(
                user_id, start_date, end_date, provider
            )
            
            return {
                "success": True,
                "events": events,
                "total_count": len(events),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e), "events": []}
    
    async def _create_user_event(self, user_id: str, parameters: Dict[str, Any], 
                               context: ExecutionContext) -> Dict[str, Any]:
        """Create a calendar event for a specific user"""
        try:
            event_details = parameters.get("event_details", {})
            provider = CalendarProvider(parameters["provider"]) if "provider" in parameters else None
            
            result = await self.user_calendar_manager.create_calendar_event(
                user_id, event_details, provider
            )
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _find_user_free_time(self, user_id: str, parameters: Dict[str, Any], 
                                 context: ExecutionContext) -> Dict[str, Any]:
        """Find available time slots for a specific user"""
        try:
            duration_minutes = parameters.get("duration_minutes", 60)
            start_date = datetime.fromisoformat(parameters.get("start_date", datetime.utcnow().isoformat()))
            end_date = datetime.fromisoformat(parameters.get("end_date", (datetime.utcnow() + timedelta(days=7)).isoformat()))
            preferences = parameters.get("preferences", {})
            
            free_slots = await self.user_calendar_manager.find_free_time_slots(
                user_id, duration_minutes, start_date, end_date, preferences
            )
            
            return {
                "success": True,
                "free_slots": free_slots,
                "duration_minutes": duration_minutes,
                "search_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e), "free_slots": []}
    
    async def _setup_calendar_provider(self, user_id: str, parameters: Dict[str, Any], 
                                     context: ExecutionContext) -> Dict[str, Any]:
        """Setup calendar provider integration for a user"""
        try:
            provider_name = parameters.get("provider", "google")
            client_config = parameters.get("client_config", {})
            authorization_code = parameters.get("authorization_code")
            
            if provider_name == "google":
                if authorization_code:
                    # Complete OAuth flow
                    result = await self.user_calendar_manager.complete_google_auth(
                        user_id, authorization_code, client_config
                    )
                else:
                    # Start OAuth flow
                    result = await self.user_calendar_manager.setup_google_calendar(
                        user_id, client_config
                    )
                return result
            else:
                return {
                    "success": False,
                    "error": f"Provider {provider_name} not yet supported",
                    "supported_providers": ["google"]
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_user_calendar_status(self, user_id: str, context: ExecutionContext) -> Dict[str, Any]:
        """Get calendar integration status for a user"""
        try:
            status = await self.user_calendar_manager.get_user_calendar_status(user_id)
            return {"success": True, "calendar_status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _disconnect_calendar_provider(self, user_id: str, parameters: Dict[str, Any], 
                                          context: ExecutionContext) -> Dict[str, Any]:
        """Disconnect a calendar provider for a user"""
        try:
            provider = CalendarProvider(parameters["provider"])
            result = await self.user_calendar_manager.disconnect_calendar_provider(user_id, provider)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _parse_natural_language_request(self, user_id: str, parameters: Dict[str, Any], 
                                            context: ExecutionContext) -> Dict[str, Any]:
        """Parse natural language scheduling requests"""
        try:
            query = parameters.get("natural_query", "")
            
            # Simple NLP parsing - in production, would use more sophisticated NLP
            parsed_request = await self._parse_scheduling_query(query)
            
            return {
                "success": True,
                "parsed_request": parsed_request,
                "original_query": query
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _parse_scheduling_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language scheduling query into structured data"""
        import re
        from dateutil.parser import parse as parse_date
        from dateutil.relativedelta import relativedelta
        
        query_lower = query.lower()
        
        # Extract event title
        title_patterns = [
            r'schedule (?:a )?(.+?) (?:for|at|on|tomorrow|next|today)',
            r'book (?:a )?(.+?) (?:for|at|on|tomorrow|next|today)',
            r'create (?:a )?(.+?) (?:event|meeting|appointment)'
        ]
        
        title = "New Event"
        for pattern in title_patterns:
            match = re.search(pattern, query_lower)
            if match:
                title = match.group(1).strip().title()
                break
        
        # Extract timing
        now = datetime.utcnow()
        start_time = None
        duration = 60  # Default 1 hour
        
        # Time patterns
        if "tomorrow" in query_lower:
            match = re.search(r'tomorrow (?:at )?(\d{1,2}):?(\d{0,2})?\s*(am|pm)?', query_lower)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                period = match.group(3)
                
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                
                start_time = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif "next week" in query_lower:
            start_time = now + timedelta(days=7)
        
        elif "today" in query_lower:
            match = re.search(r'today (?:at )?(\d{1,2}):?(\d{0,2})?\s*(am|pm)?', query_lower)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                period = match.group(3)
                
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                
                start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Duration patterns
        duration_match = re.search(r'(\d+)\s*(?:hour|hr)s?', query_lower)
        if duration_match:
            duration = int(duration_match.group(1)) * 60
        
        duration_match = re.search(r'(\d+)\s*(?:minute|min)s?', query_lower)
        if duration_match:
            duration = int(duration_match.group(1))
        
        # Default start time if not found
        if start_time is None:
            start_time = now + timedelta(hours=1)
        
        end_time = start_time + timedelta(minutes=duration)
        
        return {
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration,
            "timezone": "UTC",
            "description": f"Event created from: {query}",
            "confidence": 0.8  # Parsing confidence score
        }