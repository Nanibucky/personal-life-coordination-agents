"""
Enhanced Workflow Orchestrator with Master Coordinator Integration
Intelligent routing and conversation handling
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

from agents.master_coordinator.coordinator import MasterCoordinator, QueryType

logger = logging.getLogger("workflow_orchestrator")

class WorkflowStatus(Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

class EnhancedWorkflowOrchestrator:
    """
    Enhanced orchestrator that uses Master Coordinator for intelligent routing
    """
    
    def __init__(self, agent_registry=None):
        self.coordinator = MasterCoordinator()
        self.agent_registry = agent_registry or {}
        self.active_workflows = {}
        self.workflow_history = []
        self.logger = logger
    
    async def execute_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow with intelligent routing via Master Coordinator
        """
        workflow_id = f"wf_{int(datetime.now().timestamp())}"
        user_query = workflow_data.get('query', '')
        
        try:
            # Create workflow entry
            workflow = {
                'id': workflow_id,
                'status': WorkflowStatus.CREATED,
                'query': user_query,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            self.active_workflows[workflow_id] = workflow
            self._update_workflow_status(workflow_id, WorkflowStatus.ANALYZING)
            
            # Use Master Coordinator to analyze and route
            self.logger.info(f"Analyzing query with Master Coordinator: {user_query}")
            coordination_result = await self.coordinator.process_query(user_query)
            
            routing_decision = coordination_result['routing_decision']
            coordinator_response = coordination_result.get('coordinator_response')
            should_forward = coordination_result['should_forward_to_agents']
            
            # Update workflow with routing decision
            workflow.update({
                'intent': routing_decision['intent'],
                'target_agents': routing_decision['target_agents'],
                'requires_agents': routing_decision['requires_agents'],
                'multi_agent_workflow': routing_decision['multi_agent_workflow']
            })
            
            # Handle conversation-only queries (no agents needed)
            if not should_forward:
                self._update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
                workflow.update({
                    'result': coordinator_response,
                    'execution_type': 'coordinator_only',
                    'primary_agent': 'master_coordinator'
                })
                
                return {
                    'workflow_id': workflow_id,
                    'status': 'completed',
                    'result': coordinator_response,
                    'execution_type': 'conversation',
                    'agents_involved': [],
                    'primary_agent': 'master_coordinator',
                    'message': 'Query handled by Master Coordinator'
                }
            
            # Route to agents
            self._update_workflow_status(workflow_id, WorkflowStatus.ROUTING)
            
            target_agents = routing_decision['target_agents']
            
            if not target_agents:
                self._update_workflow_status(workflow_id, WorkflowStatus.FAILED)
                workflow['error'] = 'No suitable agents found for query'
                return {
                    'workflow_id': workflow_id,
                    'status': 'failed',
                    'error': 'No suitable agents found for query'
                }
            
            # Execute with agents
            self._update_workflow_status(workflow_id, WorkflowStatus.EXECUTING)
            
            if routing_decision['multi_agent_workflow']:
                result = await self._execute_multi_agent_workflow(workflow_id, user_query, target_agents)
            else:
                result = await self._execute_single_agent_workflow(workflow_id, user_query, target_agents[0])
            
            # Complete workflow
            self._update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)
            workflow.update({
                'result': result.get('response', 'Task completed'),
                'primary_agent': result.get('primary_agent', target_agents[0]),
                'agents_used': result.get('agents_used', target_agents)
            })
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'result': result.get('response'),
                'primary_agent': result.get('primary_agent'),
                'agents_involved': target_agents,
                'execution_type': 'multi_agent' if routing_decision['multi_agent_workflow'] else 'single_agent',
                'message': 'Workflow completed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            self._update_workflow_status(workflow_id, WorkflowStatus.FAILED)
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]['error'] = str(e)
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'message': 'Workflow execution failed'
            }
    
    async def _execute_single_agent_workflow(self, workflow_id: str, query: str, agent_name: str) -> Dict[str, Any]:
        """
        Execute workflow with a single agent
        """
        try:
            # Simulate agent interaction (replace with actual agent calls)
            self.logger.info(f"Executing single-agent workflow with {agent_name}")
            
            # Simple, clean responses based on agent capabilities
            responses = {
                'milo': f"I can help you with fitness and health tracking. For your query about \"{query}\", I'll analyze your health data and provide personalized fitness recommendations.",
                'luna': f"I'll help you with meal planning! For \"{query}\", I can suggest nutritious recipes and create meal plans that fit your dietary needs.",
                'bucky': f"I'll handle your shopping needs. For \"{query}\", I can check your inventory and suggest the best stores and deals for what you need.",
                'nani': f"I'll manage your schedule and calendar. For \"{query}\", I can optimize your time slots and coordinate meetings efficiently."
            }
            
            return {
                'response': responses.get(agent_name, f"Agent {agent_name} processed your request successfully"),
                'primary_agent': agent_name,
                'agents_used': [agent_name],
                'execution_time': 1.5
            }
            
        except Exception as e:
            self.logger.error(f"Single agent workflow failed: {e}")
            return {
                'response': f"I encountered an issue while working with {agent_name}: {str(e)}",
                'primary_agent': agent_name,
                'agents_used': [agent_name],
                'error': str(e)
            }
    
    async def _execute_multi_agent_workflow(self, workflow_id: str, query: str, target_agents: List[str]) -> Dict[str, Any]:
        """
        Execute workflow requiring multiple agents with coordination
        """
        try:
            self.logger.info(f"Executing multi-agent workflow with agents: {target_agents}")
            
            # Create orchestrated response
            agent_responses = []
            for agent in target_agents:
                single_result = await self._execute_single_agent_workflow(workflow_id, query, agent)
                agent_responses.append({
                    'agent': agent,
                    'response': single_result['response']
                })
            
            # Coordinate responses
            coordinated_response = await self._coordinate_multi_agent_responses(query, agent_responses)
            
            return {
                'response': coordinated_response,
                'primary_agent': target_agents[0],
                'agents_used': target_agents,
                'coordination': 'multi_agent_orchestration',
                'execution_time': len(target_agents) * 1.5
            }
            
        except Exception as e:
            self.logger.error(f"Multi-agent workflow failed: {e}")
            return {
                'response': f"I encountered an issue coordinating between agents: {str(e)}",
                'primary_agent': target_agents[0] if target_agents else 'unknown',
                'agents_used': target_agents,
                'error': str(e)
            }
    
    async def _coordinate_multi_agent_responses(self, query: str, agent_responses: List[Dict]) -> str:
        """
        Coordinate and synthesize responses from multiple agents
        """
        try:
            coordination_intro = f"🤝 **Multi-Agent Coordination** for: \"{query}\"\n\n"
            
            # Format individual agent responses
            formatted_responses = []
            for response in agent_responses:
                agent_name = response['agent'].title()
                agent_response = response['response']
                formatted_responses.append(f"**{agent_name}**: {agent_response}\n")
            
            # Add coordination summary
            coordination_summary = "\n🎯 **Coordination Summary**: Your specialized agents worked together using the A2A communication protocol to provide comprehensive assistance. Each agent contributed their expertise while maintaining cost efficiency through GPT-4o-mini."
            
            return coordination_intro + "\n".join(formatted_responses) + coordination_summary
            
        except Exception as e:
            return f"Multi-agent coordination completed with some coordination challenges: {str(e)}"
    
    def _update_workflow_status(self, workflow_id: str, status: WorkflowStatus):
        """
        Update workflow status and timestamp
        """
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]['status'] = status
            self.active_workflows[workflow_id]['updated_at'] = datetime.now().isoformat()
            self.logger.info(f"Workflow {workflow_id} status updated to: {status.value}")
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status and results
        """
        if workflow_id not in self.active_workflows:
            return {'error': f'Workflow {workflow_id} not found'}
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            'workflow_id': workflow_id,
            'status': workflow['status'].value if isinstance(workflow['status'], WorkflowStatus) else workflow['status'],
            'result': workflow.get('result'),
            'primary_agent': workflow.get('primary_agent'),
            'agents_involved': workflow.get('target_agents', []),
            'intent': workflow.get('intent'),
            'created_at': workflow['created_at'],
            'updated_at': workflow['updated_at'],
            'error': workflow.get('error')
        }
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """
        Get all active workflows
        """
        return {
            'active_workflows': {
                wf_id: {
                    'status': wf['status'].value if isinstance(wf['status'], WorkflowStatus) else wf['status'],
                    'query': wf.get('query'),
                    'intent': wf.get('intent'),
                    'agents': wf.get('target_agents', []),
                    'created_at': wf['created_at']
                }
                for wf_id, wf in self.active_workflows.items()
            },
            'total_count': len(self.active_workflows),
            'coordinator_status': 'active'
        }
    
    def get_coordinator_status(self) -> Dict[str, Any]:
        """
        Get Master Coordinator status
        """
        return self.coordinator.get_system_status()

# Global orchestrator instance
orchestrator = EnhancedWorkflowOrchestrator()