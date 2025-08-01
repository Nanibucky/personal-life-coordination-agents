"""
Context Manager
Manages execution contexts and sessions across the system
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import json

from .base_server import ExecutionContext

@dataclass
class Session:
    """Session information"""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    active_workflows: List[str] = field(default_factory=list)

@dataclass
class WorkflowContext:
    """Workflow execution context"""
    workflow_id: str
    session_id: str
    user_id: str
    agents_involved: List[str]
    current_step: int
    total_steps: int
    parameters: Dict[str, Any]
    results: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"  # running, completed, failed, paused
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ContextManager:
    """Manages execution contexts and sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.workflows: Dict[str, WorkflowContext] = {}
        self.context_callbacks: Dict[str, List[Callable]] = {}
        self.session_timeout = timedelta(hours=24)
        self.workflow_timeout = timedelta(hours=2)
    
    def create_session(self, user_id: str, permissions: Optional[List[str]] = None) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            permissions=permissions or ["read"]
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            # Update last activity
            session.last_activity = datetime.now()
        return session
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if session exists and is not expired"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check if session has expired
        if datetime.now() - session.last_activity > self.session_timeout:
            self.remove_session(session_id)
            return False
        
        return True
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def create_execution_context(self, user_id: str, session_id: str, 
                                permissions: Optional[List[str]] = None) -> ExecutionContext:
        """Create an execution context"""
        return ExecutionContext(
            user_id=user_id,
            session_id=session_id,
            permissions=permissions or ["read"]
        )
    
    def create_workflow_context(self, workflow_id: str, session_id: str, user_id: str,
                               agents_involved: List[str], parameters: Dict[str, Any]) -> WorkflowContext:
        """Create a workflow context"""
        workflow = WorkflowContext(
            workflow_id=workflow_id,
            session_id=session_id,
            user_id=user_id,
            agents_involved=agents_involved,
            current_step=0,
            total_steps=len(agents_involved),
            parameters=parameters
        )
        
        self.workflows[workflow_id] = workflow
        return workflow
    
    def get_workflow_context(self, workflow_id: str) -> Optional[WorkflowContext]:
        """Get workflow context by ID"""
        return self.workflows.get(workflow_id)
    
    def update_workflow_progress(self, workflow_id: str, step: int, result: Any = None):
        """Update workflow progress"""
        workflow = self.get_workflow_context(workflow_id)
        if workflow:
            workflow.current_step = step
            workflow.updated_at = datetime.now()
            if result:
                workflow.results[f"step_{step}"] = result
    
    def complete_workflow(self, workflow_id: str, final_result: Any = None):
        """Mark workflow as completed"""
        workflow = self.get_workflow_context(workflow_id)
        if workflow:
            workflow.status = "completed"
            workflow.current_step = workflow.total_steps
            workflow.updated_at = datetime.now()
            if final_result:
                workflow.results["final"] = final_result
    
    def fail_workflow(self, workflow_id: str, error: str):
        """Mark workflow as failed"""
        workflow = self.get_workflow_context(workflow_id)
        if workflow:
            workflow.status = "failed"
            workflow.updated_at = datetime.now()
            workflow.results["error"] = error
    
    def register_context_callback(self, event_type: str, callback: Callable):
        """Register a callback for context events"""
        if event_type not in self.context_callbacks:
            self.context_callbacks[event_type] = []
        self.context_callbacks[event_type].append(callback)
    
    def trigger_context_event(self, event_type: str, data: Any):
        """Trigger a context event"""
        if event_type in self.context_callbacks:
            for callback in self.context_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in context callback: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
    
    def cleanup_expired_workflows(self):
        """Clean up expired workflows"""
        now = datetime.now()
        expired_workflows = []
        
        for workflow_id, workflow in self.workflows.items():
            if now - workflow.updated_at > self.workflow_timeout:
                expired_workflows.append(workflow_id)
        
        for workflow_id in expired_workflows:
            del self.workflows[workflow_id]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = sum(1 for session in self.sessions.values() 
                            if datetime.now() - session.last_activity < timedelta(minutes=5))
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions
        }
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        total_workflows = len(self.workflows)
        running_workflows = sum(1 for workflow in self.workflows.values() 
                              if workflow.status == "running")
        completed_workflows = sum(1 for workflow in self.workflows.values() 
                                if workflow.status == "completed")
        failed_workflows = sum(1 for workflow in self.workflows.values() 
                             if workflow.status == "failed")
        
        return {
            "total_workflows": total_workflows,
            "running_workflows": running_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows
        }
    
    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """Export session data"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "metadata": session.metadata,
            "permissions": session.permissions,
            "active_workflows": session.active_workflows
        }
    
    def import_session_data(self, session_data: Dict[str, Any]) -> str:
        """Import session data"""
        session = Session(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            created_at=datetime.fromisoformat(session_data["created_at"]),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            metadata=session_data.get("metadata", {}),
            permissions=session_data.get("permissions", []),
            active_workflows=session_data.get("active_workflows", [])
        )
        
        self.sessions[session.session_id] = session
        return session.session_id

# Global context manager instance
context_manager = ContextManager()
