"""
LangChain Base Agent Framework
Base classes for LangChain-based agents
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging
from pathlib import Path

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from ..utils.config import config_manager
from ..utils.logging import setup_logging

class LangChainBaseAgent:
    """Base class for LangChain-based agents"""
    
    def __init__(self, agent_name: str, config: Dict[str, Any]):
        self.agent_name = agent_name
        self.config = config
        self.logger = setup_logging(f"agent.{agent_name}")
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize tools
        self.tools: List[BaseTool] = []
        self._register_tools()
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize agent
        self.agent_executor = self._create_agent()
        
        # A2A message handlers
        self.a2a_handlers: Dict[str, Callable] = {}
        self._register_a2a_handlers()
        
        self.logger.info(f"LangChain agent {agent_name} initialized with {len(self.tools)} tools")
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model"""
        # Get LLM config from environment or config
        model_name = self.config.get("llm", {}).get("model", "gpt-3.5-turbo")
        temperature = self.config.get("llm", {}).get("temperature", 0.1)
        max_tokens = self.config.get("llm", {}).get("max_tokens", 1000)
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def _register_tools(self):
        """Register tools - to be implemented by subclasses"""
        pass
    
    def _register_a2a_handlers(self):
        """Register A2A message handlers - to be implemented by subclasses"""
        pass
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent"""
        # Create system prompt
        system_prompt = self._get_system_prompt()
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt - to be overridden by subclasses"""
        return f"""You are {self.agent_name}, a helpful AI assistant. 
        You have access to various tools to help you accomplish tasks.
        Always use the available tools when appropriate to complete user requests."""
    
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a user message"""
        try:
            # Add context to message if provided
            if context:
                message = f"Context: {context}\n\nUser request: {message}"
            
            # Process with agent
            result = await self.agent_executor.ainvoke({"input": message})
            return result["output"]
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def process_a2a_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process A2A (Agent-to-Agent) messages"""
        try:
            intent = message_data.get("intent", "")
            payload = message_data.get("payload", {})
            
            # Find handler for intent
            if intent in self.a2a_handlers:
                handler = self.a2a_handlers[intent]
                result = await handler(payload, message_data)
                return {
                    "success": True,
                    "data": result,
                    "agent": self.agent_name
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown intent: {intent}",
                    "agent": self.agent_name
                }
                
        except Exception as e:
            self.logger.error(f"A2A message processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        self.logger.info(f"Added tool: {tool.name}")
    
    def register_a2a_handler(self, intent: str, handler: Callable):
        """Register an A2A message handler"""
        self.a2a_handlers[intent] = handler
        self.logger.info(f"Registered A2A handler for intent: {intent}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.agent_name,
            "tools": [tool.name for tool in self.tools],
            "a2a_handlers": list(self.a2a_handlers.keys()),
            "memory_size": len(self.memory.chat_memory.messages) if self.memory.chat_memory else 0
        }
    
    async def clear_memory(self):
        """Clear agent memory"""
        self.memory.clear()
        self.logger.info("Agent memory cleared")

class LangChainTool(BaseTool):
    """Base class for LangChain tools with additional functionality"""
    
    def __init__(self, name: str, description: str = "", **kwargs):
        super().__init__(name=name, description=description, **kwargs)
    
    async def _arun(self, *args, **kwargs) -> str:
        """Async execution - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _arun")
    
    def _run(self, *args, **kwargs) -> str:
        """Sync execution - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _run") 