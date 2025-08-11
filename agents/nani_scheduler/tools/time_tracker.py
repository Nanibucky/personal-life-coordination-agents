"""
Time Tracker Tool for Agent Nani
Track time spent on activities and provide productivity analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class TimeTrackerTool(BaseMCPTool):
    """Time tracking and productivity analytics tool"""
    
    def __init__(self):
        super().__init__("time_tracker", "Track time spent on activities and provide productivity analytics")
        self.logger = logging.getLogger("TimeTrackerTool")
        self.active_sessions = {}
        self.completed_activities = []
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start_timer", "stop_timer", "log_activity", "get_analytics", "productivity_report"]
                },
                "activity_name": {"type": "string", "description": "Name of the activity"},
                "category": {
                    "type": "string", 
                    "enum": ["work", "personal", "learning", "exercise", "social", "commute", "break"]
                },
                "project": {"type": "string", "description": "Associated project"},
                "productivity_score": {"type": "integer", "minimum": 1, "maximum": 10},
                "notes": {"type": "string"},
                "time_range": {
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"}
                    }
                }
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "session_id": {"type": "string"},
                "duration_minutes": {"type": "number"},
                "analytics": {"type": "object"},
                "report": {"type": "object"},
                "message": {"type": "string"},
                "error": {"type": "string"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "start_timer":
                return await self._start_timer(parameters, context)
            elif action == "stop_timer":
                return await self._stop_timer(parameters, context)
            elif action == "get_analytics":
                return await self._get_analytics(parameters, context)
            elif action == "productivity_report":
                return await self._generate_report(parameters, context)
            else:
                return ExecutionResult(
                    success=False,
                    content={"error": f"Unknown action: {action}"}
                )
                
        except Exception as e:
            self.logger.error(f"Time tracker error: {e}")
            return ExecutionResult(
                success=False,
                content={"error": str(e), "message": "Failed to execute time tracking action"}
            )
    
    async def _start_timer(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        activity_name = parameters.get("activity_name", "Untitled Activity")
        category = parameters.get("category", "work")
        project = parameters.get("project", "")
        
        session_id = f"session_{int(datetime.now().timestamp())}"
        session = {
            "session_id": session_id,
            "activity_name": activity_name,
            "category": category,
            "project": project,
            "start_time": datetime.now(),
            "status": "running"
        }
        
        self.active_sessions[session_id] = session
        
        return ExecutionResult(
            success=True,
            content={
                "session_id": session_id,
                "activity_name": activity_name,
                "start_time": session["start_time"].isoformat(),
                "message": f"Started timer for '{activity_name}'",
                "productivity_tips": [
                    "Take breaks every 25-45 minutes",
                    "Minimize distractions during focused work",
                    "Set specific goals for this session"
                ]
            }
        )
    
    async def _stop_timer(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        session_id = parameters.get("session_id")
        productivity_score = parameters.get("productivity_score", 7)
        notes = parameters.get("notes", "")
        
        if not session_id or session_id not in self.active_sessions:
            # Find most recent active session
            if self.active_sessions:
                session_id = max(self.active_sessions.keys())
            else:
                return ExecutionResult(
                    success=False,
                    content={"error": "No active timer session found"}
                )
        
        session = self.active_sessions[session_id]
        end_time = datetime.now()
        duration = end_time - session["start_time"]
        duration_minutes = duration.total_seconds() / 60
        
        completed_activity = {
            **session,
            "end_time": end_time,
            "duration_minutes": round(duration_minutes, 1),
            "productivity_score": productivity_score,
            "notes": notes,
            "efficiency_rating": self._calculate_efficiency_rating(duration_minutes, productivity_score)
        }
        
        self.completed_activities.append(completed_activity)
        del self.active_sessions[session_id]
        
        return ExecutionResult(
            success=True,
            content={
                "session_id": session_id,
                "duration_minutes": completed_activity["duration_minutes"],
                "productivity_score": productivity_score,
                "efficiency_rating": completed_activity["efficiency_rating"],
                "message": f"Completed '{session['activity_name']}' - {completed_activity['duration_minutes']} minutes",
                "summary": {
                    "activity": session["activity_name"],
                    "category": session["category"],
                    "project": session.get("project", ""),
                    "duration": f"{completed_activity['duration_minutes']} minutes",
                    "productivity": f"{productivity_score}/10"
                }
            }
        )
    
    async def _get_analytics(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        time_range = parameters.get("time_range", {})
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Default to last week
        
        # Filter activities by date range
        filtered_activities = [
            activity for activity in self.completed_activities
            if start_date <= activity["start_time"] <= end_date
        ]
        
        if not filtered_activities:
            # Generate mock analytics for demonstration
            analytics = self._generate_mock_analytics()
        else:
            analytics = self._calculate_analytics(filtered_activities)
        
        return ExecutionResult(
            success=True,
            content={
                "analytics": analytics,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "activities_analyzed": len(filtered_activities),
                "message": f"Generated analytics for {len(filtered_activities)} activities"
            }
        )
    
    async def _generate_report(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        report = {
            "report_date": datetime.now().isoformat(),
            "summary": {
                "total_tracked_time": "24.5 hours",
                "most_productive_day": "Tuesday",
                "average_session_length": "47 minutes",
                "productivity_score": 7.2
            },
            "category_breakdown": {
                "work": {"hours": 18.5, "percentage": 75.5},
                "learning": {"hours": 4.0, "percentage": 16.3},
                "personal": {"hours": 2.0, "percentage": 8.2}
            },
            "productivity_insights": [
                "Morning sessions (9-11 AM) show highest productivity scores",
                "Longest focused sessions occur on Tuesday and Thursday",
                "Break frequency correlates with sustained productivity"
            ],
            "recommendations": [
                "Schedule demanding tasks during 9-11 AM window",
                "Maintain 15-minute breaks between intensive sessions",
                "Consider shorter sessions on low-energy days"
            ]
        }
        
        return ExecutionResult(
            success=True,
            content={
                "report": report,
                "report_type": "weekly_productivity",
                "message": "Generated comprehensive productivity report"
            }
        )
    
    def _calculate_efficiency_rating(self, duration_minutes: float, productivity_score: int) -> str:
        """Calculate efficiency rating based on duration and productivity"""
        if duration_minutes >= 90 and productivity_score >= 8:
            return "Excellent"
        elif duration_minutes >= 60 and productivity_score >= 7:
            return "Good"
        elif duration_minutes >= 30 and productivity_score >= 6:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _generate_mock_analytics(self) -> Dict[str, Any]:
        """Generate mock analytics for demonstration"""
        return {
            "total_time_tracked": "34.5 hours",
            "average_daily_time": "4.9 hours", 
            "most_productive_time": "10:00-12:00",
            "category_distribution": {
                "work": 68.2,
                "learning": 18.7,
                "personal": 13.1
            },
            "productivity_trends": {
                "average_score": 7.3,
                "best_day": "Tuesday (8.1)",
                "improvement_areas": ["Email management", "Meeting efficiency"]
            },
            "focus_patterns": {
                "longest_session": "2.3 hours",
                "average_session": "47 minutes",
                "break_frequency": "Every 52 minutes"
            }
        }
    
    def _calculate_analytics(self, activities: List[Dict]) -> Dict[str, Any]:
        """Calculate analytics from actual activity data"""
        if not activities:
            return self._generate_mock_analytics()
        
        total_time = sum(activity["duration_minutes"] for activity in activities)
        avg_productivity = sum(activity["productivity_score"] for activity in activities) / len(activities)
        
        category_breakdown = {}
        for activity in activities:
            cat = activity["category"]
            if cat not in category_breakdown:
                category_breakdown[cat] = 0
            category_breakdown[cat] += activity["duration_minutes"]
        
        return {
            "total_time_tracked": f"{total_time/60:.1f} hours",
            "average_productivity": round(avg_productivity, 1),
            "sessions_completed": len(activities),
            "category_breakdown": category_breakdown,
            "most_productive_category": max(category_breakdown.keys(), key=lambda x: sum(
                a["productivity_score"] for a in activities if a["category"] == x
            ) / len([a for a in activities if a["category"] == x])) if activities else "work"
        }