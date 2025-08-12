"""
NANI Memory Management System
Handles persistent memory, conversation history, and user context
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class NaniMemoryManager:
    """Manages persistent memory for NANI agent"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.memory_dir = Path(__file__).parent.parent / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # Memory files
        self.conversation_file = self.memory_dir / f"{user_id}_conversations.json"
        self.preferences_file = self.memory_dir / f"{user_id}_preferences.json"
        self.context_file = self.memory_dir / f"{user_id}_context.json"
        
        # Load existing memory
        self.conversations = self._load_conversations()
        self.preferences = self._load_preferences()
        self.context = self._load_context()
        
        logger.info(f"Memory manager initialized for user: {user_id}")
    
    def _load_conversations(self) -> List[Dict[str, Any]]:
        """Load conversation history"""
        if self.conversation_file.exists():
            try:
                with open(self.conversation_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading conversations: {e}")
        return []
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading preferences: {e}")
        return {
            "timezone": "America/New_York",
            "preferred_meeting_duration": 30,
            "work_hours": {"start": "09:00", "end": "17:00"},
            "notification_preferences": {"email": True, "sms": False},
            "communication_style": "professional",
            "scheduling_preferences": {
                "buffer_time": 15,
                "max_back_to_back_meetings": 3,
                "preferred_meeting_times": ["10:00", "14:00", "15:00"]
            }
        }
    
    def _load_context(self) -> Dict[str, Any]:
        """Load current context and state"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading context: {e}")
        return {
            "last_interaction": None,
            "current_projects": [],
            "recent_topics": [],
            "frequent_contacts": {},
            "scheduling_patterns": {},
            "session_count": 0,
            "user_insights": {}
        }
    
    def add_conversation(self, user_message: str, assistant_response: str, 
                        tools_used: List[str] = None, context: Dict = None):
        """Add a conversation turn to memory"""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "assistant_response": assistant_response,
            "tools_used": tools_used or [],
            "context": context or {},
            "session_id": self.context.get("current_session_id", "unknown")
        }
        
        self.conversations.append(conversation_entry)
        
        # Keep only last 100 conversations to manage memory
        if len(self.conversations) > 100:
            self.conversations = self.conversations[-100:]
        
        # Update context based on conversation
        self._update_context_from_conversation(user_message, assistant_response, tools_used)
        
        self._save_conversations()
        logger.info("Conversation added to memory")
    
    def _update_context_from_conversation(self, user_message: str, assistant_response: str, tools_used: List[str]):
        """Update context based on the conversation"""
        self.context["last_interaction"] = datetime.now().isoformat()
        self.context["session_count"] += 1
        
        # Track recent topics
        if "recent_topics" not in self.context:
            self.context["recent_topics"] = []
        
        # Extract topics from user message (simple keyword extraction)
        topics = self._extract_topics(user_message)
        for topic in topics:
            if topic not in self.context["recent_topics"]:
                self.context["recent_topics"].append(topic)
        
        # Keep only recent topics (last 10)
        self.context["recent_topics"] = self.context["recent_topics"][-10:]
        
        # Track frequent contacts mentioned
        contacts = self._extract_contacts(user_message)
        for contact in contacts:
            if contact not in self.context["frequent_contacts"]:
                self.context["frequent_contacts"][contact] = 0
            self.context["frequent_contacts"][contact] += 1
        
        # Track scheduling patterns if calendar tools were used
        if tools_used and "calendar_manager" in tools_used:
            self._update_scheduling_patterns(user_message)
        
        self._save_context()
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics/keywords from message"""
        topics = []
        
        # Common scheduling topics
        scheduling_keywords = ["meeting", "call", "appointment", "reminder", "schedule", "calendar"]
        for keyword in scheduling_keywords:
            if keyword.lower() in message.lower():
                topics.append(keyword)
        
        # Time-related topics
        time_keywords = ["today", "tomorrow", "next week", "morning", "afternoon", "evening"]
        for keyword in time_keywords:
            if keyword.lower() in message.lower():
                topics.append(f"time:{keyword}")
        
        return topics
    
    def _extract_contacts(self, message: str) -> List[str]:
        """Extract contact names from message"""
        contacts = []
        
        # Simple name extraction (names after "with", "call", etc.)
        import re
        patterns = [
            r"(?:call|meeting|appointment|with)\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)(?:\s+at|\s+on)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message)
            contacts.extend(matches)
        
        return list(set(contacts))  # Remove duplicates
    
    def _update_scheduling_patterns(self, message: str):
        """Update scheduling patterns based on user behavior"""
        if "scheduling_patterns" not in self.context:
            self.context["scheduling_patterns"] = {}
        
        # Track preferred times mentioned
        import re
        time_pattern = r"(\d{1,2}):?(\d{2})?\s*(AM|PM|am|pm)?"
        times = re.findall(time_pattern, message)
        
        for time_match in times:
            hour = time_match[0]
            if time_match[2]:  # AM/PM specified
                time_str = f"{hour}:00 {time_match[2].upper()}"
            else:
                time_str = f"{hour}:00"
            
            if time_str not in self.context["scheduling_patterns"]:
                self.context["scheduling_patterns"][time_str] = 0
            self.context["scheduling_patterns"][time_str] += 1
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversations[-limit:] if self.conversations else []
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        return self.preferences.copy()
    
    def update_preferences(self, new_preferences: Dict[str, Any]):
        """Update user preferences"""
        self.preferences.update(new_preferences)
        self._save_preferences()
        logger.info("User preferences updated")
    
    def get_context_summary(self) -> str:
        """Get a summary of user context for the agent"""
        summary = []
        
        if self.context["last_interaction"]:
            last_time = datetime.fromisoformat(self.context["last_interaction"])
            summary.append(f"Last interaction: {last_time.strftime('%Y-%m-%d %H:%M')}")
        
        if self.context["recent_topics"]:
            summary.append(f"Recent topics: {', '.join(self.context['recent_topics'][:5])}")
        
        if self.context["frequent_contacts"]:
            top_contacts = sorted(self.context["frequent_contacts"].items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            contacts = [name for name, _ in top_contacts]
            summary.append(f"Frequent contacts: {', '.join(contacts)}")
        
        if self.context["scheduling_patterns"]:
            top_times = sorted(self.context["scheduling_patterns"].items(), 
                             key=lambda x: x[1], reverse=True)[:2]
            times = [time for time, _ in top_times]
            summary.append(f"Preferred meeting times: {', '.join(times)}")
        
        summary.append(f"Total interactions: {self.context['session_count']}")
        
        return " | ".join(summary) if summary else "New user - no previous interactions"
    
    def get_relevant_memory(self, current_message: str) -> Dict[str, Any]:
        """Get relevant memory context for current message"""
        relevant_conversations = []
        
        # Find related conversations
        message_lower = current_message.lower()
        for conv in self.conversations[-20:]:  # Check last 20 conversations
            if any(word in conv["user_message"].lower() for word in message_lower.split()[:5]):
                relevant_conversations.append({
                    "timestamp": conv["timestamp"],
                    "user_message": conv["user_message"][:100] + "..." if len(conv["user_message"]) > 100 else conv["user_message"],
                    "assistant_response": conv["assistant_response"][:100] + "..." if len(conv["assistant_response"]) > 100 else conv["assistant_response"]
                })
        
        return {
            "context_summary": self.get_context_summary(),
            "user_preferences": self.preferences,
            "relevant_conversations": relevant_conversations[-5:],  # Last 5 relevant
            "current_context": self.context
        }
    
    def _save_conversations(self):
        """Save conversations to file"""
        try:
            with open(self.conversation_file, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
    
    def _save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
    
    def _save_context(self):
        """Save context to file"""
        try:
            with open(self.context_file, 'w') as f:
                json.dump(self.context, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving context: {e}")
    
    def clear_memory(self, keep_preferences: bool = True):
        """Clear memory (for testing or reset)"""
        self.conversations = []
        self.context = self._load_context() if not keep_preferences else {
            "last_interaction": None,
            "current_projects": [],
            "recent_topics": [],
            "frequent_contacts": {},
            "scheduling_patterns": {},
            "session_count": 0,
            "user_insights": {}
        }
        
        if not keep_preferences:
            self.preferences = self._load_preferences()
        
        self._save_conversations()
        self._save_context()
        if not keep_preferences:
            self._save_preferences()
        
        logger.info("Memory cleared")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "total_conversations": len(self.conversations),
            "session_count": self.context.get("session_count", 0),
            "memory_files": {
                "conversations": self.conversation_file.exists(),
                "preferences": self.preferences_file.exists(), 
                "context": self.context_file.exists()
            },
            "last_interaction": self.context.get("last_interaction"),
            "recent_topics_count": len(self.context.get("recent_topics", [])),
            "contacts_tracked": len(self.context.get("frequent_contacts", {}))
        }