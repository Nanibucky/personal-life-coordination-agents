"""
Multi-User Calendar Integration Manager for Agent Nani
Supports multiple calendar providers and user-specific configurations
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import logging

class CalendarProvider(Enum):
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    CALDAV = "caldav"

class UserCalendarManager:
    """
    Manages calendar integrations for multiple users across different providers
    """
    
    def __init__(self, user_data_dir: str = "user_calendar_data"):
        self.user_data_dir = Path(user_data_dir)
        self.user_data_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("UserCalendarManager")
        
        # Google Calendar OAuth scopes
        self.google_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        # Active user sessions cache
        self.active_sessions = {}
    
    def get_user_config_path(self, user_id: str) -> Path:
        """Get the configuration file path for a specific user"""
        return self.user_data_dir / f"{user_id}_calendar_config.json"
    
    def get_user_credentials_path(self, user_id: str, provider: CalendarProvider) -> Path:
        """Get the credentials file path for a specific user and provider"""
        return self.user_data_dir / f"{user_id}_{provider.value}_credentials.json"
    
    async def get_user_calendar_config(self, user_id: str) -> Dict[str, Any]:
        """Get calendar configuration for a specific user"""
        config_path = self.get_user_config_path(user_id)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load user config for {user_id}: {e}")
        
        # Return default configuration
        return {
            "user_id": user_id,
            "primary_provider": None,
            "providers": {},
            "preferences": {
                "timezone": "UTC",
                "working_hours": {"start": "09:00", "end": "17:00"},
                "energy_patterns": {
                    "high": ["09:00-11:00", "14:00-16:00"],
                    "medium": ["11:00-12:00", "16:00-17:00"],
                    "low": ["13:00-14:00", "17:00-18:00"]
                },
                "meeting_preferences": {
                    "max_duration": 60,
                    "buffer_time": 15,
                    "max_back_to_back": 2
                }
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    async def save_user_calendar_config(self, user_id: str, config: Dict[str, Any]) -> bool:
        """Save calendar configuration for a specific user"""
        try:
            config["updated_at"] = datetime.now().isoformat()
            config_path = self.get_user_config_path(user_id)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to save user config for {user_id}: {e}")
            return False
    
    async def setup_google_calendar(self, user_id: str, client_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup Google Calendar integration for a user
        client_config should contain the OAuth 2.0 client configuration
        """
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config,
                scopes=self.google_scopes
            )
            
            # Set redirect URI (you'll need to configure this in Google Cloud Console)
            flow.redirect_uri = "http://localhost:8000/auth/google/callback"
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return {
                "success": True,
                "authorization_url": auth_url,
                "provider": "google",
                "message": "Please visit the authorization URL to complete setup"
            }
            
        except Exception as e:
            self.logger.error(f"Google Calendar setup failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "google"
            }
    
    async def complete_google_auth(self, user_id: str, authorization_code: str, 
                                 client_config: Dict[str, Any]) -> Dict[str, Any]:
        """Complete Google Calendar OAuth authorization"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                client_config,
                scopes=self.google_scopes
            )
            flow.redirect_uri = "http://localhost:8000/auth/google/callback"
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Save credentials
            credentials_path = self.get_user_credentials_path(user_id, CalendarProvider.GOOGLE)
            with open(credentials_path, 'w') as f:
                f.write(credentials.to_json())
            
            # Update user config
            config = await self.get_user_calendar_config(user_id)
            config["providers"]["google"] = {
                "enabled": True,
                "credentials_file": str(credentials_path),
                "setup_date": datetime.now().isoformat()
            }
            
            # Set as primary if no other provider is set
            if not config["primary_provider"]:
                config["primary_provider"] = "google"
            
            await self.save_user_calendar_config(user_id, config)
            
            return {
                "success": True,
                "provider": "google",
                "message": "Google Calendar successfully connected!"
            }
            
        except Exception as e:
            self.logger.error(f"Google Calendar auth completion failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "google"
            }
    
    async def get_user_calendar_service(self, user_id: str, 
                                      provider: CalendarProvider = None) -> Optional[Any]:
        """Get authenticated calendar service for a user"""
        try:
            config = await self.get_user_calendar_config(user_id)
            
            # Determine which provider to use
            if provider is None:
                provider_name = config.get("primary_provider")
                if not provider_name:
                    return None
                provider = CalendarProvider(provider_name)
            
            provider_name = provider.value
            
            # Check if provider is configured
            if provider_name not in config.get("providers", {}):
                return None
            
            if provider == CalendarProvider.GOOGLE:
                return await self._get_google_service(user_id)
            elif provider == CalendarProvider.OUTLOOK:
                return await self._get_outlook_service(user_id)
            # Add more providers as needed
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get calendar service for user {user_id}: {e}")
            return None
    
    async def _get_google_service(self, user_id: str):
        """Get authenticated Google Calendar service"""
        try:
            credentials_path = self.get_user_credentials_path(user_id, CalendarProvider.GOOGLE)
            
            if not credentials_path.exists():
                return None
            
            credentials = Credentials.from_authorized_user_file(str(credentials_path))
            
            # Refresh credentials if necessary
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Save refreshed credentials
                with open(credentials_path, 'w') as f:
                    f.write(credentials.to_json())
            
            # Build and return the service
            service = build('calendar', 'v3', credentials=credentials)
            return service
            
        except Exception as e:
            self.logger.error(f"Failed to get Google Calendar service for user {user_id}: {e}")
            return None
    
    async def _get_outlook_service(self, user_id: str):
        """Get authenticated Outlook Calendar service (placeholder)"""
        # Implement Microsoft Graph API integration
        self.logger.info(f"Outlook integration not yet implemented for user {user_id}")
        return None
    
    async def get_calendar_events(self, user_id: str, start_date: datetime, 
                                end_date: datetime, provider: CalendarProvider = None) -> List[Dict[str, Any]]:
        """Get calendar events for a user within a date range"""
        try:
            service = await self.get_user_calendar_service(user_id, provider)
            
            if not service:
                return []
            
            config = await self.get_user_calendar_config(user_id)
            provider_name = provider.value if provider else config.get("primary_provider", "google")
            
            if provider_name == "google":
                return await self._get_google_events(service, start_date, end_date)
            elif provider_name == "outlook":
                return await self._get_outlook_events(service, start_date, end_date)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get calendar events for user {user_id}: {e}")
            return []
    
    async def _get_google_events(self, service, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get events from Google Calendar"""
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                formatted_events.append({
                    'id': event.get('id'),
                    'title': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                    'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                    'location': event.get('location', ''),
                    'attendees': [att.get('email') for att in event.get('attendees', [])],
                    'provider': 'google'
                })
            
            return formatted_events
            
        except HttpError as e:
            self.logger.error(f"Google Calendar API error: {e}")
            return []
    
    async def create_calendar_event(self, user_id: str, event_details: Dict[str, Any], 
                                  provider: CalendarProvider = None) -> Dict[str, Any]:
        """Create a calendar event for a user"""
        try:
            service = await self.get_user_calendar_service(user_id, provider)
            
            if not service:
                return {"success": False, "error": "Calendar service not available"}
            
            config = await self.get_user_calendar_config(user_id)
            provider_name = provider.value if provider else config.get("primary_provider", "google")
            
            if provider_name == "google":
                return await self._create_google_event(service, event_details)
            elif provider_name == "outlook":
                return await self._create_outlook_event(service, event_details)
            
            return {"success": False, "error": "Unsupported provider"}
            
        except Exception as e:
            self.logger.error(f"Failed to create calendar event for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_google_event(self, service, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Google Calendar event"""
        try:
            event = {
                'summary': event_details.get('title', 'New Event'),
                'description': event_details.get('description', ''),
                'start': {
                    'dateTime': event_details['start_time'],
                    'timeZone': event_details.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': event_details['end_time'],
                    'timeZone': event_details.get('timezone', 'UTC')
                },
                'location': event_details.get('location', ''),
            }
            
            # Add attendees if provided
            if 'attendees' in event_details:
                event['attendees'] = [{'email': email} for email in event_details['attendees']]
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "success": True,
                "event_id": created_event.get('id'),
                "event_url": created_event.get('htmlLink'),
                "provider": "google"
            }
            
        except HttpError as e:
            self.logger.error(f"Google Calendar event creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_free_time_slots(self, user_id: str, duration_minutes: int, 
                                 start_date: datetime, end_date: datetime,
                                 preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find available time slots for a user"""
        try:
            # Get user's existing events
            events = await self.get_calendar_events(user_id, start_date, end_date)
            
            # Get user preferences
            config = await self.get_user_calendar_config(user_id)
            user_prefs = config.get("preferences", {})
            
            # Combine with provided preferences
            if preferences:
                user_prefs.update(preferences)
            
            # Find free slots (simplified algorithm)
            free_slots = []
            current_time = start_date
            
            while current_time < end_date:
                end_time = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any existing events
                has_conflict = False
                for event in events:
                    event_start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
                    
                    if (current_time < event_end and end_time > event_start):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    # Score the time slot based on user preferences
                    score = self._calculate_time_slot_score(current_time, user_prefs)
                    
                    free_slots.append({
                        'start': current_time.isoformat(),
                        'end': end_time.isoformat(),
                        'score': score,
                        'reasoning': self._get_slot_reasoning(current_time, user_prefs)
                    })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            # Sort by score (highest first) and return top slots
            free_slots.sort(key=lambda x: x['score'], reverse=True)
            return free_slots[:10]  # Return top 10 slots
            
        except Exception as e:
            self.logger.error(f"Failed to find free time slots for user {user_id}: {e}")
            return []
    
    def _calculate_time_slot_score(self, slot_time: datetime, preferences: Dict[str, Any]) -> float:
        """Calculate a score for a time slot based on user preferences"""
        score = 0.5  # Base score
        
        hour = slot_time.hour
        time_str = f"{hour:02d}:00"
        
        # Check energy patterns
        energy_patterns = preferences.get("energy_patterns", {})
        for energy_level, time_ranges in energy_patterns.items():
            for time_range in time_ranges:
                start_time, end_time = time_range.split('-')
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                
                if start_hour <= hour < end_hour:
                    if energy_level == "high":
                        score += 0.4
                    elif energy_level == "medium":
                        score += 0.2
                    else:  # low
                        score -= 0.1
                    break
        
        # Check working hours
        working_hours = preferences.get("working_hours", {})
        work_start = int(working_hours.get("start", "09:00").split(':')[0])
        work_end = int(working_hours.get("end", "17:00").split(':')[0])
        
        if work_start <= hour < work_end:
            score += 0.1
        else:
            score -= 0.2
        
        # Avoid lunch time (12-13)
        if 12 <= hour < 13:
            score -= 0.2
        
        return min(1.0, max(0.0, score))
    
    def _get_slot_reasoning(self, slot_time: datetime, preferences: Dict[str, Any]) -> str:
        """Generate reasoning for why a time slot was selected"""
        hour = slot_time.hour
        
        if 9 <= hour < 11:
            return "Morning slot - high energy period, good for focused work"
        elif 14 <= hour < 16:
            return "Afternoon slot - second energy peak, good for meetings"
        elif 11 <= hour < 12:
            return "Late morning - moderate energy, good buffer before lunch"
        elif 16 <= hour < 17:
            return "Late afternoon - winding down period but still productive"
        else:
            return "Outside optimal hours but available if needed"
    
    async def disconnect_calendar_provider(self, user_id: str, provider: CalendarProvider) -> Dict[str, Any]:
        """Disconnect a calendar provider for a user"""
        try:
            config = await self.get_user_calendar_config(user_id)
            provider_name = provider.value
            
            # Remove from providers
            if provider_name in config.get("providers", {}):
                del config["providers"][provider_name]
            
            # Update primary provider if needed
            if config.get("primary_provider") == provider_name:
                remaining_providers = list(config.get("providers", {}).keys())
                config["primary_provider"] = remaining_providers[0] if remaining_providers else None
            
            # Remove credentials file
            credentials_path = self.get_user_credentials_path(user_id, provider)
            if credentials_path.exists():
                credentials_path.unlink()
            
            await self.save_user_calendar_config(user_id, config)
            
            return {
                "success": True,
                "provider": provider_name,
                "message": f"{provider_name.title()} Calendar disconnected successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect {provider.value} for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider.value
            }
    
    async def get_user_calendar_status(self, user_id: str) -> Dict[str, Any]:
        """Get calendar integration status for a user"""
        try:
            config = await self.get_user_calendar_config(user_id)
            
            providers_status = {}
            for provider_name, provider_config in config.get("providers", {}).items():
                providers_status[provider_name] = {
                    "enabled": provider_config.get("enabled", False),
                    "setup_date": provider_config.get("setup_date"),
                    "last_sync": provider_config.get("last_sync", "Never"),
                    "status": "connected" if provider_config.get("enabled") else "disconnected"
                }
            
            return {
                "user_id": user_id,
                "primary_provider": config.get("primary_provider"),
                "providers": providers_status,
                "preferences": config.get("preferences", {}),
                "total_providers": len(providers_status)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get calendar status for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "providers": {},
                "total_providers": 0
            }