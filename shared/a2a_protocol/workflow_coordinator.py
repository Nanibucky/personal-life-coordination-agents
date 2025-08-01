"""
Workflow Coordinator
Manages multi-agent workflow execution and coordination
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

from .message_router import A2AMessage, A2AMessageRouter
from ..mcp_framework.context_manager import context_manager

@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    agent_name: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"  # pending, running, completed, failed, skipped

@dataclass
class WorkflowDefinition:
    """Workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 3600  # 1 hour default

class WorkflowCoordinator:
    """Coordinates multi-agent workflow execution"""
    
    def __init__(self, message_router: A2AMessageRouter):
        self.message_router = message_router
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.step_results: Dict[str, Dict[str, Any]] = {}
        self.workflow_callbacks: Dict[str, List[Callable]] = {}
    
    def register_workflow(self, workflow_def: WorkflowDefinition):
        """Register a workflow definition"""
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
    
    def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]]) -> str:
        """Create a new workflow definition"""
        workflow_id = str(uuid.uuid4())
        
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                step_id=str(uuid.uuid4()),
                agent_name=step_data["agent"],
                tool_name=step_data["tool"],
                parameters=step_data.get("parameters", {}),
                dependencies=step_data.get("dependencies", []),
                timeout=step_data.get("timeout", 300),
                max_retries=step_data.get("max_retries", 3)
            )
            workflow_steps.append(step)
        
        workflow_def = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps
        )
        
        self.register_workflow(workflow_def)
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, user_id: str, 
                              session_id: str, parameters: Dict[str, Any]) -> str:
        """Execute a workflow"""
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_def = self.workflow_definitions[workflow_id]
        execution_id = f"{workflow_id}_{uuid.uuid4().hex[:8]}"
        
        # Initialize workflow execution
        self.active_workflows[execution_id] = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "session_id": session_id,
            "parameters": parameters,
            "status": "running",
            "current_step": 0,
            "started_at": datetime.now(),
            "steps_completed": 0,
            "steps_failed": 0
        }
        
        # Initialize step results
        self.step_results[execution_id] = {}
        
        # Start workflow execution in background
        asyncio.create_task(self._execute_workflow_background(execution_id))
        
        return execution_id
    
    async def _execute_workflow_background(self, execution_id: str):
        """Execute workflow in background"""
        try:
            workflow_data = self.active_workflows[execution_id]
            workflow_def = self.workflow_definitions[workflow_data["workflow_id"]]
            
            # Execute steps in dependency order
            completed_steps = set()
            failed_steps = set()
            
            while len(completed_steps) < len(workflow_def.steps) and len(failed_steps) == 0:
                # Find steps that can be executed
                executable_steps = []
                for step in workflow_def.steps:
                    if step.step_id in completed_steps or step.step_id in failed_steps:
                        continue
                    
                    # Check if dependencies are met
                    if all(dep in completed_steps for dep in step.dependencies):
                        executable_steps.append(step)
                
                if not executable_steps:
                    # No executable steps, check for deadlock
                    remaining_steps = [s for s in workflow_def.steps 
                                     if s.step_id not in completed_steps and s.step_id not in failed_steps]
                    if remaining_steps:
                        raise Exception(f"Workflow deadlock detected: {remaining_steps}")
                    break
                
                # Execute steps in parallel
                tasks = []
                for step in executable_steps:
                    task = asyncio.create_task(self._execute_step(execution_id, step))
                    tasks.append((step, task))
                
                # Wait for all tasks to complete
                for step, task in tasks:
                    try:
                        result = await asyncio.wait_for(task, timeout=step.timeout)
                        if result["success"]:
                            completed_steps.add(step.step_id)
                            self.step_results[execution_id][step.step_id] = result
                            workflow_data["steps_completed"] += 1
                        else:
                            failed_steps.add(step.step_id)
                            workflow_data["steps_failed"] += 1
                    except asyncio.TimeoutError:
                        failed_steps.add(step.step_id)
                        workflow_data["steps_failed"] += 1
                        self.step_results[execution_id][step.step_id] = {
                            "success": False,
                            "error": "Step execution timeout"
                        }
            
            # Update workflow status
            if len(failed_steps) > 0:
                workflow_data["status"] = "failed"
                workflow_data["error"] = f"Failed steps: {failed_steps}"
            else:
                workflow_data["status"] = "completed"
            
            workflow_data["completed_at"] = datetime.now()
            
            # Trigger workflow completion callback
            self._trigger_workflow_callback(execution_id, workflow_data["status"])
            
        except Exception as e:
            workflow_data = self.active_workflows[execution_id]
            workflow_data["status"] = "failed"
            workflow_data["error"] = str(e)
            workflow_data["completed_at"] = datetime.now()
            
            self._trigger_workflow_callback(execution_id, "failed")
    
    async def _execute_step(self, execution_id: str, step: WorkflowStep) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            step.status = "running"
            
            # Create message to agent
            message = A2AMessage(
                from_agent="workflow_coordinator",
                to_agent=step.agent_name,
                intent=f"execute_tool_{step.tool_name}",
                payload={
                    "tool_name": step.tool_name,
                    "parameters": step.parameters,
                    "workflow_execution_id": execution_id,
                    "step_id": step.step_id
                },
                session_id=self.active_workflows[execution_id]["session_id"]
            )
            
            # Send message to agent
            response = await self.message_router.send_message(message)
            
            if response.success:
                step.status = "completed"
                return {
                    "success": True,
                    "result": response.data,
                    "step_id": step.step_id,
                    "agent": step.agent_name,
                    "tool": step.tool_name
                }
            else:
                step.status = "failed"
                return {
                    "success": False,
                    "error": response.error,
                    "step_id": step.step_id,
                    "agent": step.agent_name,
                    "tool": step.tool_name
                }
                
        except Exception as e:
            step.status = "failed"
            return {
                "success": False,
                "error": str(e),
                "step_id": step.step_id,
                "agent": step.agent_name,
                "tool": step.tool_name
            }
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        if execution_id not in self.active_workflows:
            return None
        
        workflow_data = self.active_workflows[execution_id]
        workflow_def = self.workflow_definitions[workflow_data["workflow_id"]]
        
        # Calculate progress
        total_steps = len(workflow_def.steps)
        completed_steps = workflow_data["steps_completed"]
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            **workflow_data,
            "progress": progress,
            "total_steps": total_steps,
            "workflow_name": workflow_def.name,
            "workflow_description": workflow_def.description
        }
    
    def register_workflow_callback(self, event_type: str, callback: Callable):
        """Register a callback for workflow events"""
        if event_type not in self.workflow_callbacks:
            self.workflow_callbacks[event_type] = []
        self.workflow_callbacks[event_type].append(callback)
    
    def _trigger_workflow_callback(self, execution_id: str, status: str):
        """Trigger workflow completion callback"""
        if status in self.workflow_callbacks:
            workflow_data = self.active_workflows[execution_id]
            for callback in self.workflow_callbacks[status]:
                try:
                    callback(execution_id, workflow_data)
                except Exception as e:
                    print(f"Error in workflow callback: {e}")
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up completed workflows older than specified age"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        workflows_to_remove = []
        for execution_id, workflow_data in self.active_workflows.items():
            if workflow_data["status"] in ["completed", "failed"]:
                completed_at = workflow_data.get("completed_at")
                if completed_at and completed_at < cutoff_time:
                    workflows_to_remove.append(execution_id)
        
        for execution_id in workflows_to_remove:
            del self.active_workflows[execution_id]
            if execution_id in self.step_results:
                del self.step_results[execution_id]
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        total_workflows = len(self.active_workflows)
        running_workflows = sum(1 for w in self.active_workflows.values() if w["status"] == "running")
        completed_workflows = sum(1 for w in self.active_workflows.values() if w["status"] == "completed")
        failed_workflows = sum(1 for w in self.active_workflows.values() if w["status"] == "failed")
        
        return {
            "total_workflows": total_workflows,
            "running_workflows": running_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": completed_workflows / total_workflows if total_workflows > 0 else 0
        }
