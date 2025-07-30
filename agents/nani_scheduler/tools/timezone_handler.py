"""
Timezone Handler Tool for Agent Nani
Handle timezone conversions and global scheduling
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import pytz

from shared.mcp_framework.base_server import BaseMCPTool, ExecutionContext, ExecutionResult

class TimezoneHandlerTool(BaseMCPTool):
    """Handle timezone conversions and global scheduling"""
    
    def __init__(self):
        super().__init__("timezone_handler", "Manage timezones for global scheduling coordination")
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["convert_timezone", "find_optimal_meeting_time", "get_timezone_info"]
                },
                "from_timezone": {"type": "string"},
                "to_timezone": {"type": "string"},
                "datetime": {"type": "string", "format": "date-time"},
                "participants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "timezone": {"type": "string"},
                            "working_hours": {"type": "object"}
                        }
                    }
                }
            },
            "required": ["action"]
        }
    
    def get_return_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "converted_time": {"type": "string"},
                "optimal_times": {"type": "array"},
                "timezone_info": {"type": "object"}
            }
        }
    
    async def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        action = parameters["action"]
        
        try:
            if action == "convert_timezone":
                result = await self._convert_timezone(
                    parameters.get("datetime"),
                    parameters.get("from_timezone"),
                    parameters.get("to_timezone")
                )
            elif action == "find_optimal_meeting_time":
                result = await self._find_optimal_meeting_time(
                    parameters.get("participants", [])
                )
            else:
                result = await self._get_timezone_info(parameters.get("timezone"))
            
            return ExecutionResult(success=True, result=result, execution_time=0.3)
            
        except Exception as e:
            self.logger.error(f"Timezone operation failed: {e}")
            return ExecutionResult(success=False, error=str(e), execution_time=0.0)
    
    async def _convert_timezone(self, dt_string: str, from_tz: str, to_tz: str) -> Dict[str, Any]:
        """Convert datetime between timezones"""
        try:
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)
            
            # Parse the datetime string
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            
            # Handle timezone conversion
            if dt.tzinfo is None:
                localized_dt = from_timezone.localize(dt)
            else:
                localized_dt = dt.astimezone(from_timezone)
                
            converted_dt = localized_dt.astimezone(to_timezone)
            
            return {
                "converted_time": converted_dt.isoformat(),
                "original_time": dt_string,
                "from_timezone": from_tz,
                "to_timezone": to_tz
            }
        except Exception as e:
            return {
                "error": f"Timezone conversion failed: {str(e)}",
                "original_time": dt_string,
                "from_timezone": from_tz,
                "to_timezone": to_tz
            }
    
    async def _find_optimal_meeting_time(self, participants: List[Dict]) -> Dict[str, Any]:
        """Find optimal meeting time across multiple timezones"""
        # Mock implementation of multi-timezone optimization
        optimal_times = [
            {
                "utc_time": "2025-07-25T14:00:00Z",
                "local_times": {
                    "US/Eastern": "2025-07-25T10:00:00-04:00",
                    "Europe/London": "2025-07-25T15:00:00+01:00",
                    "Asia/Tokyo": "2025-07-25T23:00:00+09:00"
                },
                "score": 0.92,
                "reasoning": "Optimal overlap during working hours for most participants"
            },
            {
                "utc_time": "2025-07-25T16:00:00Z",
                "local_times": {
                    "US/Eastern": "2025-07-25T12:00:00-04:00",
                    "Europe/London": "2025-07-25T17:00:00+01:00",
                    "Asia/Tokyo": "2025-07-26T01:00:00+09:00"
                },
                "score": 0.78,
                "reasoning": "Acceptable for US/EU, late for Asia"
            }
        ]
        
        return {"optimal_times": optimal_times, "participants_count": len(participants)}
    
    async def _get_timezone_info(self, timezone: str) -> Dict[str, Any]:
        """Get information about a specific timezone"""
        try:
            tz = pytz.timezone(timezone) if timezone else pytz.UTC
            current_time = datetime.now(tz)
            
            return {
                "timezone": str(tz),
                "current_time": current_time.isoformat(),
                "utc_offset": current_time.strftime('%z'),
                "is_dst": bool(current_time.dst())
            }
        except Exception as e:
            return {
                "error": f"Invalid timezone: {str(e)}",
                "timezone": timezone
            }