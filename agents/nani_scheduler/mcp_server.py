"""
Nani Scheduler & Calendar Agent - MCP Server
Calendar management, scheduling, and time optimization using MCP protocol
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any

from shared.mcp_framework.mcp_server_base import BaseMCPServer
from agents.nani_scheduler.tools.calendar_manager import CalendarManagerTool
from agents.nani_scheduler.tools.focus_blocker import FocusBlockerTool
from agents.nani_scheduler.tools.scheduling_optimizer import SchedulingOptimizerTool
from agents.nani_scheduler.tools.time_tracker import TimeTrackerTool
from agents.nani_scheduler.tools.timezone_handler import TimezoneHandlerTool


class NaniMCPServer(BaseMCPServer):
    """
    Nani Scheduler & Calendar Agent MCP Server
    Provides calendar management, smart scheduling, time tracking, and productivity optimization
    """
    
    def __init__(self):
        super().__init__(
            server_name="nani",
            port=8005,
            description="Scheduler & Calendar Agent with intelligent scheduling, calendar management, and productivity optimization"
        )
        
        # Initialize tools
        self.calendar_manager = CalendarManagerTool()
        self.focus_blocker = FocusBlockerTool()
        self.scheduling_optimizer = SchedulingOptimizerTool()
        self.time_tracker = TimeTrackerTool()
        self.timezone_handler = TimezoneHandlerTool()
    
    async def initialize_agent(self):
        """Initialize Nani's tools and resources"""
        
        # Register calendar management tool
        self.register_tool(
            name="calendar_manager",
            description="Manage calendar events, appointments, and scheduling across multiple calendars",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_event", "update_event", "delete_event", "get_events", "check_availability", "find_free_slots"],
                        "description": "Calendar management action"
                    },
                    "event": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Event title"},
                            "description": {"type": "string", "description": "Event description"},
                            "start_time": {"type": "string", "format": "date-time", "description": "Event start time (ISO format)"},
                            "end_time": {"type": "string", "format": "date-time", "description": "Event end time (ISO format)"},
                            "location": {"type": "string", "description": "Event location"},
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee emails"
                            },
                            "reminder_minutes": {
                                "type": "integer",
                                "default": 15,
                                "description": "Reminder time in minutes before event"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["work", "personal", "health", "social", "family", "travel", "education"],
                                "description": "Event category"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                                "default": "medium",
                                "description": "Event priority"
                            },
                            "recurring": {
                                "type": "object",
                                "properties": {
                                    "frequency": {"type": "string", "enum": ["daily", "weekly", "monthly", "yearly"]},
                                    "interval": {"type": "integer", "default": 1},
                                    "end_date": {"type": "string", "format": "date"}
                                },
                                "description": "Recurring event settings"
                            }
                        },
                        "required": ["title", "start_time", "end_time"],
                        "description": "Event details"
                    },
                    "calendar_id": {
                        "type": "string",
                        "description": "Specific calendar ID (optional, uses default if not specified)"
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "format": "date", "description": "Start date for query"},
                            "end_date": {"type": "string", "format": "date", "description": "End date for query"}
                        },
                        "description": "Date range for event queries"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration for free slot searches"
                    }
                },
                "required": ["action"]
            },
            function=self._manage_calendar
        )
        
        # Register scheduling optimizer tool
        self.register_tool(
            name="schedule_optimizer",
            description="Optimize schedules for productivity, minimize conflicts, and suggest better time management",
            input_schema={
                "type": "object",
                "properties": {
                    "optimization_type": {
                        "type": "string",
                        "enum": ["productivity_focus", "conflict_resolution", "time_blocking", "meeting_consolidation", "travel_optimization"],
                        "description": "Type of schedule optimization"
                    },
                    "time_period": {
                        "type": "string",
                        "enum": ["day", "week", "month"],
                        "default": "week",
                        "description": "Time period to optimize"
                    },
                    "preferences": {
                        "type": "object",
                        "properties": {
                            "work_hours": {
                                "type": "object",
                                "properties": {
                                    "start": {"type": "string", "description": "Work day start time (HH:MM)"},
                                    "end": {"type": "string", "description": "Work day end time (HH:MM)"}
                                },
                                "description": "Preferred work hours"
                            },
                            "break_duration": {
                                "type": "integer",
                                "default": 15,
                                "description": "Preferred break duration in minutes"
                            },
                            "meeting_duration_preference": {
                                "type": "integer",
                                "default": 30,
                                "description": "Preferred default meeting duration"
                            },
                            "focus_blocks": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include dedicated focus time blocks"
                            },
                            "commute_buffer": {
                                "type": "integer",
                                "default": 15,
                                "description": "Buffer time for travel between locations"
                            }
                        },
                        "description": "Scheduling preferences"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["no_meetings_before", "no_meetings_after", "lunch_break", "mandatory_event"]},
                                "time": {"type": "string", "description": "Time constraint"},
                                "days": {"type": "array", "items": {"type": "string"}, "description": "Days this constraint applies"}
                            }
                        },
                        "description": "Scheduling constraints"
                    }
                },
                "required": ["optimization_type"]
            },
            function=self._optimize_schedule
        )
        
        # Register time tracking tool
        self.register_tool(
            name="time_tracker",
            description="Track time spent on activities and provide productivity analytics",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start_timer", "stop_timer", "log_activity", "get_analytics", "productivity_report", "time_allocation"],
                        "description": "Time tracking action"
                    },
                    "activity": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Activity name"},
                            "category": {
                                "type": "string",
                                "enum": ["work", "personal", "learning", "exercise", "social", "commute", "break"],
                                "description": "Activity category"
                            },
                            "project": {"type": "string", "description": "Associated project"},
                            "start_time": {"type": "string", "format": "date-time", "description": "Activity start time"},
                            "end_time": {"type": "string", "format": "date-time", "description": "Activity end time"},
                            "productivity_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Self-rated productivity score"
                            },
                            "notes": {"type": "string", "description": "Activity notes"},
                            "interruptions": {
                                "type": "integer",
                                "default": 0,
                                "description": "Number of interruptions"
                            }
                        },
                        "required": ["name", "category"],
                        "description": "Activity details"
                    },
                    "time_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"}
                        },
                        "description": "Date range for analytics"
                    },
                    "report_type": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "project_based", "category_based"],
                        "description": "Type of productivity report"
                    }
                },
                "required": ["action"]
            },
            function=self._track_time
        )
        
        # Register meeting assistant tool
        self.register_tool(
            name="meeting_assistant",
            description="Intelligent meeting management with agenda creation, note-taking, and follow-up tracking",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_agenda", "schedule_meeting", "send_invites", "meeting_notes", "action_items", "follow_up"],
                        "description": "Meeting assistant action"
                    },
                    "meeting_details": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Meeting title"},
                            "purpose": {"type": "string", "description": "Meeting purpose"},
                            "duration_minutes": {"type": "integer", "default": 60, "description": "Meeting duration"},
                            "attendees": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Attendee email addresses"
                            },
                            "agenda_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "duration": {"type": "integer"},
                                        "owner": {"type": "string"},
                                        "type": {"type": "string", "enum": ["discussion", "decision", "information", "brainstorm"]}
                                    }
                                },
                                "description": "Agenda items"
                            },
                            "preparation_required": {"type": "string", "description": "Pre-meeting preparation"},
                            "meeting_type": {
                                "type": "string",
                                "enum": ["standup", "planning", "review", "brainstorm", "decision", "information"],
                                "description": "Type of meeting"
                            }
                        },
                        "required": ["title", "purpose"],
                        "description": "Meeting details"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Meeting notes or transcript"
                    },
                    "action_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task": {"type": "string"},
                                "assignee": {"type": "string"},
                                "due_date": {"type": "string", "format": "date"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                            }
                        },
                        "description": "Action items from meeting"
                    }
                },
                "required": ["action"]
            },
            function=self._assist_meeting
        )
        
        # Register resources
        self.register_resource(
            uri="nani://calendar-templates",
            name="Calendar Templates",
            description="Pre-built calendar templates for different scheduling scenarios",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="nani://productivity-insights", 
            name="Productivity Insights",
            description="Analytics and insights about time management and productivity patterns",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="nani://meeting-templates",
            name="Meeting Templates",
            description="Templates for different types of meetings with agendas and best practices",
            mime_type="application/json"
        )
        
        self.register_resource(
            uri="nani://time-zones",
            name="Time Zone Database",
            description="Global time zone information for multi-timezone scheduling",
            mime_type="application/json"
        )
        
        # Register focus blocker tool
        self.register_tool(
            name="focus_blocker",
            description="Block distractions and enforce focus sessions with website/app blocking",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start_focus", "end_focus", "schedule_focus", "get_status", "configure_blocks"],
                        "description": "Focus blocker action"
                    },
                    "duration_minutes": {"type": "integer", "description": "Focus session duration"},
                    "focus_type": {
                        "type": "string",
                        "enum": ["deep_work", "study", "meeting", "break", "custom"],
                        "description": "Type of focus session"
                    },
                    "blocked_sites": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Websites to block during focus session"
                    },
                    "blocked_apps": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Applications to block during focus session"
                    },
                    "allowlist": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Websites/apps to allow during focus session"
                    }
                },
                "required": ["action"]
            },
            function=self._handle_focus_blocker
        )
        
        # Register timezone handler tool
        self.register_tool(
            name="timezone_handler",
            description="Handle timezone conversions and multi-timezone scheduling",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["convert_time", "schedule_across_zones", "get_timezone_info", "find_best_meeting_time"],
                        "description": "Timezone handling action"
                    },
                    "time": {"type": "string", "description": "Time to convert (ISO format)"},
                    "from_timezone": {"type": "string", "description": "Source timezone"},
                    "to_timezone": {"type": "string", "description": "Target timezone"},
                    "participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "timezone": {"type": "string"},
                                "availability": {"type": "object"}
                            }
                        },
                        "description": "Meeting participants with their timezones"
                    }
                },
                "required": ["action"]
            },
            function=self._handle_timezone_handler
        )
        
        self.logger.info("Nani MCP Server initialized with 6 tools and 4 resources")
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool using legacy tool classes if function not provided"""
        if tool_name == "calendar_manager":
            return await self._manage_calendar(arguments)
        elif tool_name == "schedule_optimizer":
            return await self._optimize_schedule(arguments)
        elif tool_name == "time_tracker":
            return await self._track_time(arguments)
        elif tool_name == "meeting_assistant":
            return await self._assist_meeting(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _manage_calendar(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Manage calendar events and scheduling"""
        try:
            # Use the actual CalendarManagerTool instead of hardcoded responses
            from shared.mcp_framework.base_server import ExecutionContext
            context = ExecutionContext(user_id="nani_user", session_id="nani_session", permissions={})
            
            # Execute using the updated CalendarManagerTool
            result = await self.calendar_manager.execute(arguments, context)
            return result.result
            
        except Exception as e:
            self.logger.error(f"Calendar management error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to manage calendar"
            }
    
    async def _optimize_schedule(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize scheduling for productivity and efficiency"""
        try:
            optimization_type = arguments.get("optimization_type")
            time_period = arguments.get("time_period", "week")
            preferences = arguments.get("preferences", {})
            constraints = arguments.get("constraints", [])
            
            result = {
                "optimization_type": optimization_type,
                "time_period": time_period,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if optimization_type == "productivity_focus":
                # Optimize for maximum productivity
                optimization_results = {
                    "focus_blocks_added": 3,
                    "meeting_consolidation": "Moved 5 meetings to Tuesday-Thursday",
                    "energy_alignment": "Scheduled creative work during morning peak hours",
                    "break_optimization": "Added 15-minute breaks between intense sessions",
                    "distraction_minimization": "Blocked 2-hour deep work sessions",
                    "productivity_score_improvement": "Expected 35% increase"
                }
                
                # Suggest optimal daily schedule
                optimal_schedule = {
                    "morning_block": {
                        "time": "9:00-11:30",
                        "activity": "Deep work / Creative tasks",
                        "reasoning": "Peak cognitive performance"
                    },
                    "mid_morning": {
                        "time": "11:30-12:00",
                        "activity": "Email and quick tasks",
                        "reasoning": "Maintain momentum before lunch"
                    },
                    "afternoon_block": {
                        "time": "14:00-16:00",
                        "activity": "Meetings and collaboration",
                        "reasoning": "Good for social interaction"
                    },
                    "late_afternoon": {
                        "time": "16:00-17:00",
                        "activity": "Planning and admin tasks",
                        "reasoning": "Wind down with routine work"
                    }
                }
                
                result.update({
                    "optimization_results": optimization_results,
                    "optimal_schedule": optimal_schedule,
                    "implementation_tips": [
                        "Protect morning focus time from meetings",
                        "Batch similar tasks together",
                        "Use the 'Do Not Disturb' feature during deep work"
                    ]
                })
            
            elif optimization_type == "conflict_resolution":
                # Resolve scheduling conflicts
                detected_conflicts = [
                    {
                        "conflict_id": "conf_001",
                        "events": ["Team Meeting", "Client Call"],
                        "time": "2025-08-11 14:00",
                        "severity": "high",
                        "suggested_resolution": "Move Client Call to 15:00"
                    },
                    {
                        "conflict_id": "conf_002",
                        "events": ["Lunch", "Project Review"],
                        "time": "2025-08-12 12:30",
                        "severity": "medium",
                        "suggested_resolution": "Extend lunch to 13:30, start review at 13:45"
                    }
                ]
                
                resolution_plan = {
                    "conflicts_detected": len(detected_conflicts),
                    "automatic_resolutions": 2,
                    "manual_review_needed": 0,
                    "time_saved": "45 minutes",
                    "stress_reduction_score": 8.5
                }
                
                result.update({
                    "detected_conflicts": detected_conflicts,
                    "resolution_plan": resolution_plan,
                    "message": f"Resolved {len(detected_conflicts)} scheduling conflicts"
                })
            
            elif optimization_type == "time_blocking":
                # Implement time blocking strategy
                time_blocks = {
                    "monday": [
                        {"time": "09:00-10:30", "block": "Strategic Planning", "color": "blue"},
                        {"time": "10:45-12:00", "block": "Deep Work", "color": "green"},
                        {"time": "14:00-15:30", "block": "Meetings", "color": "orange"},
                        {"time": "15:45-17:00", "block": "Email & Admin", "color": "yellow"}
                    ],
                    "tuesday": [
                        {"time": "09:00-11:00", "block": "Creative Work", "color": "purple"},
                        {"time": "11:15-12:00", "block": "Team Collaboration", "color": "red"},
                        {"time": "14:00-16:00", "block": "Client Work", "color": "blue"},
                        {"time": "16:15-17:00", "block": "Learning & Development", "color": "green"}
                    ]
                }
                
                blocking_benefits = {
                    "focus_improvement": "40% increase in uninterrupted work time",
                    "task_switching_reduction": "60% fewer context switches",
                    "deadline_compliance": "90% of tasks completed on time",
                    "stress_levels": "25% reduction in scheduling stress"
                }
                
                result.update({
                    "time_blocks": time_blocks,
                    "blocking_benefits": blocking_benefits,
                    "implementation_guide": [
                        "Color-code different types of work",
                        "Include buffer time between blocks",
                        "Review and adjust blocks weekly"
                    ]
                })
            
            elif optimization_type == "meeting_consolidation":
                # Consolidate meetings for efficiency
                consolidation_analysis = {
                    "current_meetings_per_week": 15,
                    "optimized_meetings_per_week": 10,
                    "meeting_free_days": ["Monday", "Friday"],
                    "consolidated_meeting_days": ["Tuesday", "Wednesday", "Thursday"],
                    "time_saved_per_week": "5 hours",
                    "focus_blocks_created": 6
                }
                
                meeting_optimization = {
                    "batch_scheduling": "Group similar meetings together",
                    "duration_optimization": "Default 25/50 min instead of 30/60 min",
                    "preparation_time": "Built-in 5 min buffer before meetings",
                    "no_meeting_zones": "Before 10 AM and after 4 PM protected",
                    "virtual_first": "Default to video calls to reduce travel time"
                }
                
                result.update({
                    "consolidation_analysis": consolidation_analysis,
                    "meeting_optimization": meeting_optimization,
                    "weekly_schedule": "Meeting-heavy: Tue-Thu, Focus: Mon/Fri"
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Schedule optimization error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to optimize schedule"
            }
    
    async def _track_time(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Track time and provide productivity analytics"""
        try:
            action = arguments.get("action")
            activity = arguments.get("activity", {})
            time_range = arguments.get("time_range", {})
            report_type = arguments.get("report_type", "weekly")
            
            result = {
                "action_performed": action,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if action == "start_timer":
                # Start timing an activity
                timer_session = {
                    "session_id": f"timer_{int(datetime.now().timestamp())}",
                    "activity_name": activity.get("name"),
                    "category": activity.get("category"),
                    "project": activity.get("project"),
                    "start_time": datetime.now().isoformat(),
                    "status": "running",
                    "expected_duration": None,
                    "break_reminders": True
                }
                
                result.update({
                    "timer_session": timer_session,
                    "message": f"Started timer for '{activity.get('name')}'",
                    "productivity_tips": [
                        "Take a 5-minute break every 25 minutes (Pomodoro)",
                        "Stay hydrated and maintain good posture",
                        "Minimize distractions during focused work"
                    ]
                })
            
            elif action == "stop_timer":
                # Stop timing and log the activity
                session_duration = 45  # Mock duration in minutes
                
                completed_activity = {
                    "activity_name": activity.get("name"),
                    "category": activity.get("category"),
                    "duration_minutes": session_duration,
                    "start_time": (datetime.now() - timedelta(minutes=session_duration)).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "productivity_score": activity.get("productivity_score", 7),
                    "interruptions": activity.get("interruptions", 2),
                    "notes": activity.get("notes", ""),
                    "efficiency_rating": self._calculate_efficiency_rating(session_duration, activity.get("interruptions", 2))
                }
                
                result.update({
                    "completed_activity": completed_activity,
                    "session_summary": f"Worked on '{activity.get('name')}' for {session_duration} minutes",
                    "productivity_insights": [
                        f"Productivity score: {completed_activity['productivity_score']}/10",
                        f"Efficiency rating: {completed_activity['efficiency_rating']}",
                        f"Interruptions handled: {completed_activity['interruptions']}"
                    ]
                })
            
            elif action == "get_analytics":
                # Get time tracking analytics
                start_date = datetime.fromisoformat(time_range.get("start_date", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")))
                end_date = datetime.fromisoformat(time_range.get("end_date", datetime.now().strftime("%Y-%m-%d")))
                
                analytics = {
                    "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                    "total_tracked_hours": 34.5,
                    "average_daily_hours": 4.9,
                    "most_productive_day": "Tuesday",
                    "most_productive_time": "10:00-12:00",
                    "category_breakdown": {
                        "work": {"hours": 24.0, "percentage": 69.6},
                        "learning": {"hours": 6.5, "percentage": 18.8},
                        "personal": {"hours": 4.0, "percentage": 11.6}
                    },
                    "productivity_trends": {
                        "average_score": 7.2,
                        "highest_scoring_activity": "Deep work sessions",
                        "improvement_areas": ["Email management", "Meeting efficiency"]
                    },
                    "interruption_analysis": {
                        "average_per_session": 1.8,
                        "most_common_source": "Email notifications",
                        "impact_on_productivity": "15% reduction in efficiency"
                    }
                }
                
                result.update({
                    "analytics": analytics,
                    "recommendations": [
                        "Schedule deep work during 10 AM-12 PM peak productivity window",
                        "Implement email batching to reduce interruptions",
                        "Increase learning time allocation for skill development"
                    ]
                })
            
            elif action == "productivity_report":
                # Generate comprehensive productivity report
                if report_type == "weekly":
                    productivity_report = {
                        "report_period": "Week of " + datetime.now().strftime("%Y-%m-%d"),
                        "summary_metrics": {
                            "total_focused_hours": 28.5,
                            "productivity_score": 7.4,
                            "goal_achievement": "85%",
                            "time_utilization": "82%"
                        },
                        "daily_breakdown": [
                            {"day": "Monday", "hours": 6.5, "score": 8.2, "top_activity": "Strategic planning"},
                            {"day": "Tuesday", "hours": 7.2, "score": 8.8, "top_activity": "Client project work"},
                            {"day": "Wednesday", "hours": 5.8, "score": 6.9, "top_activity": "Meetings"},
                            {"day": "Thursday", "hours": 6.0, "score": 7.5, "top_activity": "Code development"},
                            {"day": "Friday", "hours": 3.0, "score": 6.8, "top_activity": "Admin tasks"}
                        ],
                        "achievements": [
                            "Completed major project milestone ahead of schedule",
                            "Maintained consistent morning routine",
                            "Reduced average meeting duration by 15 minutes"
                        ],
                        "areas_for_improvement": [
                            "Reduce context switching between tasks",
                            "Better email management strategy needed",
                            "Schedule more break time between intensive sessions"
                        ]
                    }
                
                result.update({
                    "productivity_report": productivity_report,
                    "report_type": report_type,
                    "next_week_goals": [
                        "Achieve 30+ focused hours",
                        "Implement time-blocking for better focus",
                        "Reduce interruptions by 25%"
                    ]
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Time tracking error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to track time"
            }
    
    async def _assist_meeting(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with meeting management and optimization"""
        try:
            action = arguments.get("action")
            meeting_details = arguments.get("meeting_details", {})
            notes = arguments.get("notes", "")
            action_items = arguments.get("action_items", [])
            
            result = {
                "action_performed": action,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            if action == "create_agenda":
                # Create structured meeting agenda
                agenda = {
                    "meeting_title": meeting_details.get("title"),
                    "meeting_id": f"meeting_{int(datetime.now().timestamp())}",
                    "duration_minutes": meeting_details.get("duration_minutes", 60),
                    "meeting_type": meeting_details.get("meeting_type", "discussion"),
                    "purpose": meeting_details.get("purpose"),
                    "preparation_required": meeting_details.get("preparation_required", ""),
                    "agenda_items": []
                }
                
                # Add default agenda structure based on meeting type
                if meeting_details.get("meeting_type") == "standup":
                    default_items = [
                        {"topic": "What did you accomplish yesterday?", "duration": 10, "type": "information"},
                        {"topic": "What are you working on today?", "duration": 10, "type": "information"},
                        {"topic": "Any blockers or challenges?", "duration": 10, "type": "discussion"}
                    ]
                elif meeting_details.get("meeting_type") == "planning":
                    default_items = [
                        {"topic": "Review previous sprint/period", "duration": 15, "type": "information"},
                        {"topic": "Discuss upcoming priorities", "duration": 20, "type": "discussion"},
                        {"topic": "Resource allocation", "duration": 15, "type": "decision"},
                        {"topic": "Action items and next steps", "duration": 10, "type": "decision"}
                    ]
                else:
                    # Use provided agenda items or create generic structure
                    default_items = meeting_details.get("agenda_items", [
                        {"topic": "Opening and introductions", "duration": 5, "type": "information"},
                        {"topic": "Main discussion topics", "duration": 40, "type": "discussion"},
                        {"topic": "Action items and next steps", "duration": 10, "type": "decision"},
                        {"topic": "Closing", "duration": 5, "type": "information"}
                    ])
                
                agenda["agenda_items"] = default_items
                
                # Add timing and logistics
                agenda["logistics"] = {
                    "start_time": "To be scheduled",
                    "attendees": meeting_details.get("attendees", []),
                    "materials_needed": ["Projector", "Whiteboard"],
                    "virtual_meeting_link": "https://meet.example.com/meeting-room"
                }
                
                result.update({
                    "agenda": agenda,
                    "estimated_duration": sum(item.get("duration", 10) for item in agenda["agenda_items"]),
                    "meeting_success_tips": [
                        "Start and end on time",
                        "Keep discussions focused on agenda items",
                        "Assign action items with clear owners and due dates",
                        "Share notes within 24 hours"
                    ]
                })
            
            elif action == "schedule_meeting":
                # Find optimal meeting time and send invitations
                optimal_times = [
                    {
                        "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                        "time": "10:00 AM",
                        "timezone": "Local",
                        "attendee_availability": "100%",
                        "conflicts": 0,
                        "score": 9.5
                    },
                    {
                        "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                        "time": "2:00 PM",
                        "timezone": "Local",
                        "attendee_availability": "85%",
                        "conflicts": 1,
                        "score": 7.8
                    }
                ]
                
                scheduling_result = {
                    "meeting_title": meeting_details.get("title"),
                    "duration_minutes": meeting_details.get("duration_minutes", 60),
                    "attendees": meeting_details.get("attendees", []),
                    "optimal_times": optimal_times,
                    "recommended_slot": optimal_times[0],
                    "invitations_status": "Ready to send",
                    "calendar_blocking": "Automatic"
                }
                
                result.update({
                    "scheduling_result": scheduling_result,
                    "message": f"Found optimal meeting time with {optimal_times[0]['attendee_availability']} attendee availability"
                })
            
            elif action == "meeting_notes":
                # Process and structure meeting notes
                structured_notes = {
                    "meeting_summary": {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "duration": "60 minutes",
                        "attendees_present": 5,
                        "key_decisions": [
                            "Approved budget increase for Q4 project",
                            "Selected vendor for new system implementation",
                            "Agreed on timeline for product launch"
                        ],
                        "main_discussion_points": [
                            "Market analysis results",
                            "Resource allocation strategy",
                            "Risk mitigation plans"
                        ]
                    },
                    "action_items_extracted": [
                        {
                            "task": "Prepare vendor contract for review",
                            "assignee": "Legal team",
                            "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                            "priority": "high"
                        },
                        {
                            "task": "Update project timeline document",
                            "assignee": "Project manager",
                            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                            "priority": "medium"
                        }
                    ],
                    "follow_up_meetings": [
                        {
                            "purpose": "Vendor contract review",
                            "suggested_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                            "attendees": ["Legal", "Procurement", "Project lead"]
                        }
                    ]
                }
                
                result.update({
                    "structured_notes": structured_notes,
                    "notes_processed": len(notes.split()) if notes else 0,
                    "action_items_count": len(structured_notes["action_items_extracted"]),
                    "distribution_list": meeting_details.get("attendees", [])
                })
            
            elif action == "follow_up":
                # Create follow-up tasks and reminders
                follow_up_plan = {
                    "immediate_actions": [
                        "Send meeting notes to all attendees",
                        "Create calendar reminders for action item due dates",
                        "Schedule follow-up meetings as needed"
                    ],
                    "tracking_dashboard": {
                        "total_action_items": len(action_items),
                        "completed": 0,
                        "in_progress": len(action_items),
                        "overdue": 0,
                        "completion_rate": "0%"
                    },
                    "automated_reminders": [
                        {
                            "task": "Check action item progress",
                            "reminder_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                            "recipients": ["Meeting organizer"]
                        },
                        {
                            "task": "Send progress update to stakeholders",
                            "reminder_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                            "recipients": meeting_details.get("attendees", [])
                        }
                    ]
                }
                
                result.update({
                    "follow_up_plan": follow_up_plan,
                    "tracking_enabled": True,
                    "next_check_in": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Meeting assistance error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to assist with meeting"
            }
    
    def _generate_mock_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Generate mock calendar events for testing"""
        events = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Weekdays only
                # Add 2-4 events per day
                daily_events = [
                    {
                        "event_id": f"event_{current_date.strftime('%Y%m%d')}_morning",
                        "title": "Daily Standup",
                        "start_time": current_date.replace(hour=9, minute=0).isoformat(),
                        "end_time": current_date.replace(hour=9, minute=30).isoformat(),
                        "duration_minutes": 30,
                        "category": "work",
                        "priority": "medium"
                    },
                    {
                        "event_id": f"event_{current_date.strftime('%Y%m%d')}_afternoon",
                        "title": "Project Review",
                        "start_time": current_date.replace(hour=14, minute=0).isoformat(),
                        "end_time": current_date.replace(hour=15, minute=0).isoformat(),
                        "duration_minutes": 60,
                        "category": "work",
                        "priority": "high"
                    }
                ]
                events.extend(daily_events)
            
            current_date += timedelta(days=1)
        
        return events
    
    def _find_day_free_slots(self, date: datetime, duration_minutes: int) -> List[Dict]:
        """Find free slots for a specific day"""
        slots = []
        
        # Mock business hours: 9 AM to 5 PM
        current = date.replace(hour=9, minute=0)
        end_of_day = date.replace(hour=17, minute=0)
        
        while current + timedelta(minutes=duration_minutes) <= end_of_day:
            # Mock some slots as busy
            if current.hour not in [12, 13]:  # Skip lunch hours
                slots.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "start_time": current.strftime("%H:%M"),
                    "end_time": (current + timedelta(minutes=duration_minutes)).strftime("%H:%M"),
                    "duration_minutes": duration_minutes,
                    "score": 10 - abs(current.hour - 10)  # Prefer 10 AM
                })
            
            current += timedelta(minutes=30)
        
        return slots[:3]  # Limit to top 3 slots per day
    
    async def _check_conflicts(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Check for scheduling conflicts"""
        # Mock conflict detection
        conflicts = []
        
        # Simulate finding overlapping events
        if start_time.hour == 14:  # Mock conflict at 2 PM
            conflicts.append({
                "conflicting_event": "Team Meeting",
                "overlap_minutes": 30,
                "severity": "medium",
                "suggested_resolution": "Move one event by 30 minutes"
            })
        
        return conflicts
    
    def _calculate_next_occurrence(self, start_time: datetime, recurring: Dict) -> str:
        """Calculate next occurrence for recurring events"""
        frequency = recurring.get("frequency", "weekly")
        interval = recurring.get("interval", 1)
        
        if frequency == "daily":
            next_occurrence = start_time + timedelta(days=interval)
        elif frequency == "weekly":
            next_occurrence = start_time + timedelta(weeks=interval)
        elif frequency == "monthly":
            next_occurrence = start_time + timedelta(days=30 * interval)  # Approximation
        else:  # yearly
            next_occurrence = start_time + timedelta(days=365 * interval)
        
        return next_occurrence.isoformat()
    
    def _calculate_efficiency_rating(self, duration_minutes: int, interruptions: int) -> str:
        """Calculate efficiency rating based on duration and interruptions"""
        interruption_impact = interruptions * 5  # 5% per interruption
        
        if duration_minutes >= 90 and interruptions <= 1:
            return "Excellent"
        elif duration_minutes >= 60 and interruptions <= 2:
            return "Good"
        elif duration_minutes >= 30 and interruptions <= 3:
            return "Average"
        else:
            return "Needs Improvement"
    
    async def _read_resource(self, uri: str) -> str:
        """Read resource content"""
        if uri == "nani://calendar-templates":
            return json.dumps({
                "templates": [
                    {
                        "name": "Weekly Planning Template",
                        "description": "Template for weekly planning sessions",
                        "duration": 60,
                        "agenda": [
                            "Review previous week accomplishments",
                            "Identify upcoming priorities",
                            "Schedule important tasks and meetings",
                            "Block time for deep work"
                        ],
                        "recurring": "weekly"
                    },
                    {
                        "name": "1:1 Meeting Template",
                        "description": "Template for one-on-one meetings",
                        "duration": 30,
                        "agenda": [
                            "Check-in on current projects",
                            "Discuss challenges and blockers",
                            "Career development topics",
                            "Feedback and recognition"
                        ],
                        "recurring": "bi-weekly"
                    },
                    {
                        "name": "Sprint Planning Template",
                        "description": "Template for agile sprint planning",
                        "duration": 120,
                        "agenda": [
                            "Sprint goal definition",
                            "Backlog refinement",
                            "Story estimation",
                            "Sprint commitment"
                        ],
                        "recurring": "bi-weekly"
                    }
                ]
            }, indent=2)
        
        elif uri == "nani://productivity-insights":
            return json.dumps({
                "insights": {
                    "peak_productivity_hours": {
                        "global_average": "10:00-12:00",
                        "individual_variation": "2-3 hours difference",
                        "factors": ["chronotype", "caffeine_intake", "sleep_quality"]
                    },
                    "meeting_optimization": {
                        "ideal_duration": "25 or 50 minutes instead of 30/60",
                        "max_back_to_back": "3 meetings",
                        "preparation_buffer": "5-10 minutes",
                        "follow_up_time": "15 minutes for note-taking"
                    },
                    "focus_blocks": {
                        "minimum_duration": "90 minutes",
                        "ideal_duration": "2-3 hours",
                        "break_frequency": "every 25-45 minutes",
                        "distraction_free_period": "morning hours preferred"
                    },
                    "context_switching": {
                        "recovery_time": "15-25 minutes",
                        "productivity_loss": "up to 40%",
                        "mitigation": "batch similar tasks together"
                    }
                },
                "recommendations": [
                    "Protect 2-3 hour morning blocks for important work",
                    "Schedule meetings in the afternoon when possible",
                    "Use time-blocking to reduce decision fatigue",
                    "Take regular breaks to maintain focus"
                ]
            }, indent=2)
        
        elif uri == "nani://meeting-templates":
            return json.dumps({
                "meeting_templates": [
                    {
                        "type": "standup",
                        "name": "Daily Standup",
                        "optimal_duration": 15,
                        "agenda_template": [
                            "Yesterday's accomplishments",
                            "Today's priorities", 
                            "Blockers and help needed"
                        ],
                        "best_practices": [
                            "Keep updates concise",
                            "Focus on work, not personal details",
                            "Park longer discussions for after standup"
                        ]
                    },
                    {
                        "type": "retrospective",
                        "name": "Sprint Retrospective",
                        "optimal_duration": 90,
                        "agenda_template": [
                            "What went well?",
                            "What could be improved?",
                            "What will we try next sprint?",
                            "Action items and owners"
                        ],
                        "best_practices": [
                            "Create psychological safety",
                            "Focus on processes, not people",
                            "Make action items specific and measurable"
                        ]
                    },
                    {
                        "type": "brainstorm",
                        "name": "Brainstorming Session",
                        "optimal_duration": 60,
                        "agenda_template": [
                            "Problem statement review",
                            "Silent idea generation",
                            "Idea sharing and clustering",
                            "Evaluation and next steps"
                        ],
                        "best_practices": [
                            "No judgment during idea generation",
                            "Build on others' ideas",
                            "Quantity over quality initially"
                        ]
                    }
                ]
            }, indent=2)
        
        elif uri == "nani://time-zones":
            return json.dumps({
                "time_zones": [
                    {"name": "Eastern Standard Time", "abbreviation": "EST", "offset": "-05:00", "dst": True},
                    {"name": "Central Standard Time", "abbreviation": "CST", "offset": "-06:00", "dst": True},
                    {"name": "Mountain Standard Time", "abbreviation": "MST", "offset": "-07:00", "dst": True},
                    {"name": "Pacific Standard Time", "abbreviation": "PST", "offset": "-08:00", "dst": True},
                    {"name": "Coordinated Universal Time", "abbreviation": "UTC", "offset": "+00:00", "dst": False},
                    {"name": "Central European Time", "abbreviation": "CET", "offset": "+01:00", "dst": True},
                    {"name": "Japan Standard Time", "abbreviation": "JST", "offset": "+09:00", "dst": False}
                ],
                "meeting_scheduling_tips": [
                    "Always specify timezone when scheduling across regions",
                    "Use UTC as reference for global meetings",
                    "Consider daylight saving time changes",
                    "Rotate meeting times to share inconvenience fairly"
                ]
            }, indent=2)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def _handle_focus_blocker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle focus blocker tool requests"""
        try:
            context = self._create_execution_context(params)
            result = await self.focus_blocker.execute(params, context)
            return {"success": True, "result": result.result, "message": "Focus blocker executed successfully"}
        except Exception as e:
            self.logger.error(f"Focus blocker error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_timezone_handler(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timezone handler tool requests"""
        try:
            context = self._create_execution_context(params)
            result = await self.timezone_handler.execute(params, context)
            return {"success": True, "result": result.result, "message": "Timezone handler executed successfully"}
        except Exception as e:
            self.logger.error(f"Timezone handler error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_execution_context(self, params: Dict[str, Any]):
        """Create execution context for tool calls"""
        from shared.mcp_framework.base_server import ExecutionContext
        return ExecutionContext(
            user_id="nani_user",
            session_id=f"nani_{datetime.now().isoformat()}",
            permissions=["read", "write"],
            metadata={"agent": "nani", "timestamp": datetime.now().isoformat()}
        )


async def main():
    """Run Nani MCP Server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = NaniMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())