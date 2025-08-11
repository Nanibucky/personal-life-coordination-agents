"""
Public API Configuration for Nani
Configure Nani to work with free/public APIs and mock data for demonstration
"""

import os
from typing import Dict, Any

class PublicAPIConfig:
    """Configuration for public/free APIs"""
    
    @staticmethod
    def get_free_api_config() -> Dict[str, Any]:
        """Get configuration for free/public APIs"""
        return {
            # Use OpenAI API (already configured)
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o-mini",  # More cost-effective model
                "max_tokens": 1000,
                "temperature": 0.2
            },
            
            # Free weather API (OpenWeatherMap has free tier)
            "weather": {
                "provider": "openweathermap",
                "api_key": "demo_key",  # Replace with actual free API key
                "free_tier_limits": {
                    "calls_per_minute": 60,
                    "calls_per_month": 1000000
                },
                "endpoints": {
                    "current_weather": "https://api.openweathermap.org/data/2.5/weather",
                    "forecast": "https://api.openweathermap.org/data/2.5/forecast"
                }
            },
            
            # Public timezone API
            "timezone": {
                "provider": "worldtimeapi",
                "base_url": "http://worldtimeapi.org/api",
                "free": True,
                "rate_limit": None  # No rate limit for basic usage
            },
            
            # Public holidays API
            "holidays": {
                "provider": "nager.date",
                "base_url": "https://date.nager.at/api/v3",
                "free": True,
                "rate_limit": None
            },
            
            # Mock calendar for demonstration (no external API needed)
            "calendar": {
                "mode": "mock",  # Use mock data for demonstration
                "google_oauth": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "demo_mode": True  # Will work without actual OAuth
                }
            },
            
            # Free productivity tracking (local storage)
            "productivity": {
                "storage": "local",  # Store data locally
                "export_formats": ["json", "csv"]
            }
        }
    
    @staticmethod
    def is_demo_mode() -> bool:
        """Check if running in demo mode with mock data"""
        return os.getenv("NANI_DEMO_MODE", "true").lower() == "true"
    
    @staticmethod
    def get_mock_calendar_events():
        """Generate mock calendar events for demonstration"""
        from datetime import datetime, timedelta
        
        base_date = datetime.now()
        events = []
        
        for i in range(7):  # Next 7 days
            date = base_date + timedelta(days=i)
            if date.weekday() < 5:  # Weekdays only
                events.extend([
                    {
                        "id": f"event_{date.strftime('%Y%m%d')}_1",
                        "title": "Daily Standup",
                        "start": date.replace(hour=9, minute=0),
                        "end": date.replace(hour=9, minute=30),
                        "description": "Team sync meeting",
                        "location": "Conference Room A",
                        "attendees": ["team@company.com"]
                    },
                    {
                        "id": f"event_{date.strftime('%Y%m%d')}_2", 
                        "title": "Focus Block - Deep Work",
                        "start": date.replace(hour=10, minute=0),
                        "end": date.replace(hour=12, minute=0),
                        "description": "Protected time for focused work",
                        "location": "Home Office",
                        "attendees": []
                    },
                    {
                        "id": f"event_{date.strftime('%Y%m%d')}_3",
                        "title": "Project Review",
                        "start": date.replace(hour=14, minute=0), 
                        "end": date.replace(hour=15, minute=0),
                        "description": "Weekly project status review",
                        "location": "Virtual",
                        "attendees": ["manager@company.com"]
                    }
                ])
        
        return events

# Set demo mode by default
os.environ.setdefault("NANI_DEMO_MODE", "true")