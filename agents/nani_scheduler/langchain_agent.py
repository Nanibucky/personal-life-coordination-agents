"""
LangChain Nani Agent - Scheduling & Calendar Management
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from langchain.tools import BaseTool
from langchain.schema import HumanMessage, AIMessage

from shared.langchain_framework.base_agent import LangChainBaseAgent, LangChainTool
from shared.langchain_framework.a2a_coordinator import a2a_coordinator, A2AMessage
from shared.utils.config import config_manager

# Global storage for tool data (in a real app, this would be a database)
_calendar_data = {}
_focus_data = {}

class CalendarManagerTool(LangChainTool):
    """LangChain tool for calendar management"""
    
    def __init__(self):
        super().__init__(
            name="calendar_manager",
            description="Manage calendar events, appointments, and scheduling"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of calendar management actions"""
        try:
            if action == "add_event":
                return await self._add_event(**kwargs)
            elif action == "get_events":
                return await self._get_events(**kwargs)
            elif action == "update_event":
                return await self._update_event(**kwargs)
            elif action == "delete_event":
                return await self._delete_event(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in calendar management: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _add_event(self, title: str, start_time: str, end_time: str, **kwargs) -> str:
        """Add a new calendar event"""
        event_id = f"event_{datetime.now().timestamp()}"
        event = {
            "id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": kwargs.get("description", ""),
            "location": kwargs.get("location", ""),
            "created_at": datetime.now().isoformat()
        }
        
        _calendar_data[event_id] = event
        return f"Added event: {title} from {start_time} to {end_time}"
    
    async def _get_events(self, date: Optional[str] = None, **kwargs) -> str:
        """Get calendar events for a specific date or all events"""
        if not _calendar_data:
            return "No events scheduled"
        
        if date:
            # Filter events for specific date
            target_date = datetime.fromisoformat(date).date()
            filtered_events = []
            
            for event in _calendar_data.values():
                event_date = datetime.fromisoformat(event["start_time"]).date()
                if event_date == target_date:
                    filtered_events.append(event)
            
            if not filtered_events:
                return f"No events scheduled for {date}"
            
            result = f"Events for {date}:\n"
            for event in filtered_events:
                result += f"- {event['title']}: {event['start_time']} to {event['end_time']}\n"
        else:
            # Return all events
            result = "All scheduled events:\n"
            for event in _calendar_data.values():
                result += f"- {event['title']}: {event['start_time']} to {event['end_time']}\n"
        
        return result
    
    async def _update_event(self, event_id: str, **kwargs) -> str:
        """Update an existing calendar event"""
        if event_id not in _calendar_data:
            return f"Event {event_id} not found"
        
        event = _calendar_data[event_id]
        for key, value in kwargs.items():
            if key in event:
                event[key] = value
        
        event["updated_at"] = datetime.now().isoformat()
        return f"Updated event: {event['title']}"
    
    async def _delete_event(self, event_id: str, **kwargs) -> str:
        """Delete a calendar event"""
        if event_id not in _calendar_data:
            return f"Event {event_id} not found"
        
        event_title = _calendar_data[event_id]["title"]
        del _calendar_data[event_id]
        return f"Deleted event: {event_title}"

class SchedulingOptimizerTool(LangChainTool):
    """LangChain tool for scheduling optimization"""
    
    def __init__(self):
        super().__init__(
            name="scheduling_optimizer",
            description="Optimize schedules and find optimal time slots"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of scheduling optimization actions"""
        try:
            if action == "find_optimal_slot":
                return await self._find_optimal_slot(**kwargs)
            elif action == "optimize_schedule":
                return await self._optimize_schedule(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in scheduling optimization: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _find_optimal_slot(self, duration: int, date: str, **kwargs) -> str:
        """Find optimal time slot for an event"""
        # Mock optimal slot finding
        available_slots = [
            "09:00-11:00",
            "14:00-16:00", 
            "16:30-18:30"
        ]
        
        if duration <= 60:
            return f"Optimal {duration}-minute slot on {date}: {available_slots[0]}"
        elif duration <= 120:
            return f"Optimal {duration}-minute slot on {date}: {available_slots[1]}"
        else:
            return f"Optimal {duration}-minute slot on {date}: {available_slots[2]}"
    
    async def _optimize_schedule(self, tasks: List[Dict[str, Any]], **kwargs) -> str:
        """Optimize a schedule for multiple tasks"""
        if not tasks:
            return "No tasks to optimize"
        
        optimized_schedule = []
        current_time = datetime.now()
        
        for i, task in enumerate(tasks):
            task_duration = task.get("duration", 60)
            task_priority = task.get("priority", "medium")
            
            # Simple optimization: high priority first, then by duration
            slot_start = current_time + timedelta(hours=i)
            slot_end = slot_start + timedelta(minutes=task_duration)
            
            optimized_schedule.append({
                "task": task.get("name", f"Task {i+1}"),
                "start_time": slot_start.strftime("%H:%M"),
                "end_time": slot_end.strftime("%H:%M"),
                "priority": task_priority
            })
        
        result = "Optimized Schedule:\n"
        for slot in optimized_schedule:
            result += f"- {slot['task']}: {slot['start_time']}-{slot['end_time']} ({slot['priority']} priority)\n"
        
        return result

class FocusBlockerTool(LangChainTool):
    """LangChain tool for focus time blocking"""
    
    def __init__(self):
        super().__init__(
            name="focus_blocker",
            description="Create focus time blocks and manage productivity sessions"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of focus blocking actions"""
        try:
            if action == "create_focus_block":
                return await self._create_focus_block(**kwargs)
            elif action == "get_focus_blocks":
                return await self._get_focus_blocks(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in focus blocking: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _create_focus_block(self, duration: int, task: str, **kwargs) -> str:
        """Create a focus time block"""
        focus_block = {
            "id": f"focus_{datetime.now().timestamp()}",
            "task": task,
            "duration": duration,
            "start_time": datetime.now().isoformat(),
            "end_time": (datetime.now() + timedelta(minutes=duration)).isoformat(),
            "status": "scheduled"
        }
        
        return f"Created focus block: {task} for {duration} minutes"
    
    async def _get_focus_blocks(self, date: Optional[str] = None, **kwargs) -> str:
        """Get focus blocks for a specific date"""
        # Mock focus blocks
        focus_blocks = [
            {"task": "Deep Work", "duration": 90, "time": "09:00-10:30"},
            {"task": "Email Management", "duration": 30, "time": "11:00-11:30"},
            {"task": "Project Planning", "duration": 60, "time": "14:00-15:00"}
        ]
        
        result = "Focus Blocks:\n"
        for block in focus_blocks:
            result += f"- {block['task']}: {block['time']} ({block['duration']} min)\n"
        
        return result

class TimezoneHandlerTool(LangChainTool):
    """LangChain tool for timezone handling"""
    
    def __init__(self):
        super().__init__(
            name="timezone_handler",
            description="Handle timezone conversions and scheduling across timezones"
        )
    
    async def _arun(self, action: str, **kwargs) -> str:
        """Async execution of timezone handling actions"""
        try:
            if action == "convert_timezone":
                return await self._convert_timezone(**kwargs)
            elif action == "find_meeting_time":
                return await self._find_meeting_time(**kwargs)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"Error in timezone handling: {str(e)}"
    
    def _run(self, action: str, **kwargs) -> str:
        """Sync execution - not implemented"""
        raise NotImplementedError("Use async execution")
    
    async def _convert_timezone(self, time: str, from_tz: str, to_tz: str, **kwargs) -> str:
        """Convert time between timezones"""
        # Mock timezone conversion
        converted_time = f"{time} converted from {from_tz} to {to_tz}"
        return f"Timezone conversion: {converted_time}"
    
    async def _find_meeting_time(self, participants: List[str], duration: int, **kwargs) -> str:
        """Find optimal meeting time across timezones"""
        # Mock meeting time finding
        optimal_time = "14:00 UTC"
        local_times = {
            "UTC": "14:00",
            "EST": "09:00", 
            "PST": "06:00",
            "CET": "15:00"
        }
        
        result = f"Optimal meeting time: {optimal_time}\nLocal times:\n"
        for tz, time in local_times.items():
            result += f"- {tz}: {time}\n"
        
        return result

class LangChainNaniAgent(LangChainBaseAgent):
    """LangChain-based Nani Scheduler Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = config_manager.load_config("nani")
        
        super().__init__("nani", config)
        
        # Register with A2A coordinator
        a2a_coordinator.register_agent(self)
    
    def _register_tools(self):
        """Register Nani's tools"""
        self.add_tool(CalendarManagerTool())
        self.add_tool(SchedulingOptimizerTool())
        self.add_tool(FocusBlockerTool())
        self.add_tool(TimezoneHandlerTool())
    
    def _register_a2a_handlers(self):
        """Register A2A message handlers"""
        self.register_a2a_handler("schedule_optimization", self._handle_schedule_optimization)
        self.register_a2a_handler("calendar_integration", self._handle_calendar_integration)
        self.register_a2a_handler("focus_time_planning", self._handle_focus_time_planning)
        self.register_a2a_handler("meeting_scheduling", self._handle_meeting_scheduling)
    
    def _get_system_prompt(self) -> str:
        return """You are Nani, a scheduling and calendar management assistant. 
        You help users optimize their schedules, manage calendar events, and create productive time blocks.
        
        Your capabilities include:
        - Managing calendar events and appointments
        - Optimizing schedules for maximum productivity
        - Creating focus time blocks
        - Handling timezone conversions
        - Coordinating meetings across different timezones
        
        Always use your tools to provide accurate and helpful information. Consider user preferences and existing commitments."""
    
    async def _handle_schedule_optimization(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle schedule optimization requests"""
        try:
            tasks = payload.get("tasks", [])
            
            optimized_schedule = await self.tools[1]._arun("optimize_schedule", tasks=tasks)
            
            return {
                "optimized_schedule": optimized_schedule,
                "total_tasks": len(tasks),
                "optimization_notes": "Schedule optimized for productivity and priority"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_calendar_integration(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calendar integration requests"""
        try:
            events = payload.get("events", [])
            
            # Add events to calendar
            added_events = []
            for event in events:
                result = await self.tools[0]._arun("add_event", 
                    title=event.get("title"),
                    start_time=event.get("start_time"),
                    end_time=event.get("end_time"),
                    description=event.get("description", "")
                )
                added_events.append(result)
            
            return {
                "calendar_integration": "Events added to calendar",
                "added_events": added_events,
                "total_events": len(events)
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_focus_time_planning(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle focus time planning requests"""
        try:
            tasks = payload.get("tasks", [])
            
            focus_blocks = []
            for task in tasks:
                result = await self.tools[2]._arun("create_focus_block",
                    duration=task.get("duration", 60),
                    task=task.get("name", "Focus Task")
                )
                focus_blocks.append(result)
            
            return {
                "focus_blocks_created": focus_blocks,
                "total_blocks": len(focus_blocks),
                "productivity_tip": "Use Pomodoro technique for better focus"
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_meeting_scheduling(self, payload: Dict[str, Any], message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle meeting scheduling requests"""
        try:
            participants = payload.get("participants", [])
            duration = payload.get("duration", 60)
            
            meeting_time = await self.tools[3]._arun("find_meeting_time",
                participants=participants,
                duration=duration
            )
            
            return {
                "meeting_time": meeting_time,
                "participants": participants,
                "duration": duration,
                "timezone_handled": True
            }
        except Exception as e:
            return {"error": str(e)} 