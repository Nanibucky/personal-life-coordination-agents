"""
Master Coordinator Agent
Intelligent routing system for A2A communication with intent recognition
"""

import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
from enum import Enum
import os
from pathlib import Path
from openai import AsyncOpenAI

class QueryType(Enum):
    GREETING = "greeting"
    SIMPLE_CONVERSATION = "simple_conversation"
    SCHEDULING = "scheduling"
    HEALTH_FITNESS = "health_fitness"
    NUTRITION = "nutrition"
    SHOPPING = "shopping"
    MULTI_AGENT = "multi_agent"
    UNKNOWN = "unknown"

class UserMemory:
    """
    Manages persistent user memory and context
    """
    
    def __init__(self, memory_file: str = "user_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self._load_memory()
        self.conversation_history = []
        
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "user_profile": {},
            "preferences": {},
            "important_facts": [],
            "conversation_context": [],
            "agent_interactions": {}
        }
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Failed to save memory: {e}")
    
    def update_user_profile(self, key: str, value: str):
        """Update user profile information"""
        self.memory["user_profile"][key] = value
        self._save_memory()
    
    def add_important_fact(self, fact: str):
        """Add an important fact to remember"""
        timestamp = datetime.now().isoformat()
        fact_entry = {
            "fact": fact,
            "timestamp": timestamp
        }
        self.memory["important_facts"].append(fact_entry)
        # Keep only last 50 facts
        if len(self.memory["important_facts"]) > 50:
            self.memory["important_facts"] = self.memory["important_facts"][-50:]
        self._save_memory()
    
    def set_preference(self, category: str, preference: str):
        """Set user preference"""
        self.memory["preferences"][category] = preference
        self._save_memory()
    
    def add_conversation_context(self, query: str, response: str, intent: str):
        """Add conversation context"""
        context_entry = {
            "query": query,
            "response": response,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
        self.memory["conversation_context"].append(context_entry)
        # Keep only last 20 conversations
        if len(self.memory["conversation_context"]) > 20:
            self.memory["conversation_context"] = self.memory["conversation_context"][-20:]
        self._save_memory()
    
    def get_user_name(self) -> Optional[str]:
        """Get user's name"""
        return self.memory["user_profile"].get("name")
    
    def get_context_summary(self) -> str:
        """Get a summary of relevant context for responses"""
        context = []
        
        # Add user name if known
        if name := self.get_user_name():
            context.append(f"User's name is {name}")
        
        # Add recent important facts
        recent_facts = self.memory["important_facts"][-5:]
        for fact_entry in recent_facts:
            context.append(f"Remember: {fact_entry['fact']}")
        
        # Add preferences
        if self.memory["preferences"]:
            prefs = ", ".join([f"{k}: {v}" for k, v in self.memory["preferences"].items()])
            context.append(f"Preferences: {prefs}")
        
        return "; ".join(context) if context else ""
    
    def extract_and_store_info(self, query: str):
        """Extract and store important information from query"""
        query_lower = query.lower()
        
        # Extract name
        name_patterns = [
            r'my name is (\w+)',
            r'i\'?m (\w+)',
            r'call me (\w+)',
            r'i am (\w+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query_lower)
            if match:
                name = match.group(1).capitalize()
                self.update_user_profile("name", name)
                break
        
        # Extract preferences
        if "i like" in query_lower or "i prefer" in query_lower:
            self.add_important_fact(query)
        
        # Extract health info
        if any(word in query_lower for word in ['allergic', 'allergy', 'diet', 'vegetarian', 'vegan']):
            self.add_important_fact(query)
        
        # Extract goals
        if any(phrase in query_lower for phrase in ['my goal', 'want to', 'trying to', 'plan to']):
            self.add_important_fact(query)

class MasterCoordinator:
    """
    Master Coordinator Agent for intelligent query routing and conversation handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger("master_coordinator")
        
        # Initialize memory system
        self.memory = UserMemory()
        
        # Initialize OpenAI client for intelligent responses
        try:
            self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.has_openai = True
        except Exception as e:
            self.logger.warning(f"OpenAI not available: {e}")
            self.openai_client = None
            self.has_openai = False
        
        self.agents = {
            'milo': {'role': 'Fitness & Health', 'tools': ['fitness_tracker', 'health_analyzer']},
            'luna': {'role': 'Meal Planning', 'tools': ['meal_planner', 'recipe_generator']},
            'bucky': {'role': 'Shopping & Inventory', 'tools': ['inventory_manager', 'shopping_optimizer']},
            'nani': {'role': 'Scheduler & Calendar', 'tools': ['calendar_manager', 'scheduling_optimizer']}
        }
        
        # Intent recognition patterns
        self.intent_patterns = {
            QueryType.GREETING: [
                r'\b(hi|hello|hey|good\s+(morning|afternoon|evening)|howdy)\b',
                r'\bhow\s+are\s+you\b',
                r'\bwhat\'?s\s+up\b',
                r'\bgreetings?\b'
            ],
            QueryType.SIMPLE_CONVERSATION: [
                r'\bthank\s+you\b',
                r'\bthanks?\b',
                r'\bbye\b',
                r'\bgoodbye\b',
                r'\bsee\s+you\b',
                r'\bhow\s+does\s+this\s+work\b',
                r'\bwhat\s+can\s+you\s+do\b',
                r'\bhelp\b(?!\s+me\s+(with|plan|schedule|buy))',
                r'\bwho\s+are\s+you\b',
                r'\btell\s+me\s+your\s+name\b',
                r'\bwhat\'?s\s+your\s+name\b',
                r'\bwhat\s+(day|time|date)\s+(is\s+)?it\b',
                r'\bwhat\'?s\s+the\s+(day|time|date)\b',
                r'\btell\s+me\s+(the\s+)?(day|time|date)\b',
                r'\btoday\b(?!\s+(workout|meal|schedule|plan))',
                r'\bwhat\s+(is\s+)?today\b',
                r'\bhow\s+are\s+(you|things)\b',
                r'\bnice\s+to\s+meet\s+you\b',
                r'\bjust\s+(tell|asking|wondering)\b'
            ],
            QueryType.SCHEDULING: [
                r'\b(schedule|calendar|meeting|appointment)\b',
                r'\bplan\s+(my\s+)?(day|week|time|schedule)\b',
                r'\bwhen\s+(should|can)\s+I\s+(workout|meet|schedule)\b',
                r'\bbook\s+a\s+(meeting|appointment)\b',
                r'\bset\s+up\s+a\s+(meeting|appointment|schedule)\b',
                r'\bfree\s+time\s+(for|to)\b',
                r'\bavailable\s+(time|slot)\b',
                r'\bbusiest?\s+(day|time)\b'
            ],
            QueryType.HEALTH_FITNESS: [
                r'\b(workout|exercise|fitness|gym|run|jog|yoga)\s+(plan|routine|program|session)\b',
                r'\b(create|plan|design|build)\s+(workout|exercise|fitness)\b',
                r'\bheart\s+rate\s+(monitor|tracking)\b',
                r'\btrack\s+(steps|fitness|health)\b',
                r'\bweight\s+(loss|gain)\s+(plan|program)\b',
                r'\b(muscle|strength)\s+(building|training)\b',
                r'\bcardio\s+(routine|workout)\b'
            ],
            QueryType.NUTRITION: [
                r'\b(meal|food|recipe)\s+(plan|planning|suggestion)\b',
                r'\b(cook|prepare)\s+(dinner|lunch|breakfast|meal)\b',
                r'\bwhat\s+(should|can)\s+I\s+(eat|cook)\b',
                r'\b(healthy|nutrition)\s+(meal|food|diet)\b',
                r'\bcalorie\s+(count|tracking)\b',
                r'\bprotein\s+(intake|rich)\b',
                r'\bdiet\s+(plan|advice)\b'
            ],
            QueryType.SHOPPING: [
                r'\b(buy|shop|purchase)\s+(groceries|food|ingredients)\b',
                r'\binventory\s+(check|management)\b',
                r'\bpantry\s+(items|stock)\b',
                r'\bneed\s+to\s+(buy|get|shop)\b',
                r'\bshopping\s+list\b',
                r'\brun\s+out\s+of\s+(food|groceries)\b'
            ]
        }
        
        # Conversation responses for non-agent queries
        self.conversation_responses = {
            QueryType.GREETING: [
                "Hello! I'm your Personal Life Coordination system. I'm here to help you manage your meals, health, shopping, and scheduling through my specialized agents.",
                "Hi there! Your agents Milo (fitness), Luna (meals), Bucky (shopping), and Nani (scheduling) are all ready to help. What would you like to work on today?",
                "Good to see you! I coordinate between your personal agents to help with fitness, nutrition, shopping, and scheduling. How can we assist you today?"
            ],
            QueryType.SIMPLE_CONVERSATION: {
                'thank': "You're very welcome! I'm here whenever you need help coordinating your personal life management.",
                'bye': "Goodbye! Your agents will be here whenever you need them. Take care!",
                'help': "I coordinate between 4 specialized agents:\n• **Milo** - Fitness & health tracking\n• **Luna** - Meal planning & nutrition\n• **Bucky** - Shopping & inventory management\n• **Nani** - Scheduling & calendar coordination\n\nJust ask about meals, workouts, shopping, or scheduling!",
                'who': "I'm the Master Coordinator for your Personal Life Coordination system. I intelligently route your requests to the right agents and handle simple conversations without bothering them unnecessarily."
            }
        }
    
    def analyze_intent(self, query: str) -> QueryType:
        """
        Analyze user query to determine intent and required agent(s)
        """
        query_lower = query.lower()
        
        # First check greetings and simple conversation (highest priority)
        for intent_type in [QueryType.GREETING, QueryType.SIMPLE_CONVERSATION]:
            patterns = self.intent_patterns[intent_type]
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent_type
        
        # Then check specific agent domains
        for intent_type in [QueryType.SCHEDULING, QueryType.HEALTH_FITNESS, QueryType.NUTRITION, QueryType.SHOPPING]:
            patterns = self.intent_patterns[intent_type]
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent_type
        
        # Check for multi-agent queries
        matched_types = []
        for intent_type in [QueryType.SCHEDULING, QueryType.HEALTH_FITNESS, QueryType.NUTRITION, QueryType.SHOPPING]:
            patterns = self.intent_patterns[intent_type]
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matched_types.append(intent_type)
                    break
        
        if len(matched_types) > 1:
            return QueryType.MULTI_AGENT
        
        # Default to simple conversation for unmatched queries instead of UNKNOWN
        return QueryType.SIMPLE_CONVERSATION
    
    def determine_target_agents(self, intent: QueryType, query: str) -> List[str]:
        """
        Determine which agents should handle the query based on intent
        """
        # Note: Based on the actual tool mappings discovered:
        # - Milo actually has fitness tools but Luna has meal planning
        # - So we need to route correctly based on actual capabilities
        
        agent_mapping = {
            QueryType.SCHEDULING: ['nani'],
            QueryType.HEALTH_FITNESS: ['milo'],  # Milo has fitness tools
            QueryType.NUTRITION: ['luna'],       # Luna has meal planning tools
            QueryType.SHOPPING: ['bucky'],
            QueryType.MULTI_AGENT: self._analyze_multi_agent_needs(query)
        }
        
        return agent_mapping.get(intent, [])
    
    def _analyze_multi_agent_needs(self, query: str) -> List[str]:
        """
        Analyze complex queries that might need multiple agents
        """
        agents_needed = []
        query_lower = query.lower()
        
        # Check each agent's domain
        if any(word in query_lower for word in ['workout', 'exercise', 'fitness', 'health']):
            agents_needed.append('milo')
        
        if any(word in query_lower for word in ['meal', 'food', 'recipe', 'cook', 'eat']):
            agents_needed.append('luna')
        
        if any(word in query_lower for word in ['buy', 'shop', 'grocery', 'inventory']):
            agents_needed.append('bucky')
        
        if any(word in query_lower for word in ['schedule', 'calendar', 'meeting', 'time']):
            agents_needed.append('nani')
        
        return agents_needed
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main entry point for query processing with intelligent routing and memory
        """
        # Extract and store information from query
        self.memory.extract_and_store_info(query)
        
        intent = self.analyze_intent(query)
        self.logger.info(f"Query intent classified as: {intent.value}")
        
        # Handle non-agent queries directly
        if intent in [QueryType.GREETING, QueryType.SIMPLE_CONVERSATION]:
            response = await self._handle_conversation(query, intent)
            # Store conversation context
            self.memory.add_conversation_context(
                query, 
                response['coordinator_response'], 
                intent.value
            )
            return response
        
        # Route to appropriate agents
        target_agents = self.determine_target_agents(intent, query)
        
        if not target_agents:
            return await self._handle_unknown_query(query)
        
        # Create routing decision
        return {
            'routing_decision': {
                'intent': intent.value,
                'target_agents': target_agents,
                'requires_agents': len(target_agents) > 0,
                'multi_agent_workflow': len(target_agents) > 1,
                'query': query,
                'timestamp': datetime.now().isoformat()
            },
            'coordinator_response': None,
            'should_forward_to_agents': True
        }
    
    async def _handle_conversation(self, query: str, intent: QueryType) -> Dict[str, Any]:
        """
        Handle simple conversations with intelligent OpenAI responses
        """
        # Try to get intelligent response from OpenAI
        if self.has_openai:
            try:
                response = await self._get_intelligent_response(query, intent)
            except Exception as e:
                self.logger.error(f"OpenAI response failed: {e}")
                response = await self._get_fallback_response(query, intent)
        else:
            response = await self._get_fallback_response(query, intent)
        
        return {
            'routing_decision': {
                'intent': intent.value,
                'target_agents': [],
                'requires_agents': False,
                'multi_agent_workflow': False,
                'query': query,
                'timestamp': datetime.now().isoformat()
            },
            'coordinator_response': response,
            'should_forward_to_agents': False
        }
    
    async def _get_intelligent_response(self, query: str, intent: QueryType) -> str:
        """
        Get intelligent response from OpenAI with memory context
        """
        # Get memory context
        context = self.memory.get_context_summary()
        user_name = self.memory.get_user_name()
        
        system_prompt = f"""You are a helpful personal assistant coordinator. You manage 4 specialized agents:
- Milo: Fitness & Health tracking
- Luna: Meal planning & nutrition
- Bucky: Shopping & inventory management  
- Nani: Scheduling & calendar coordination

{f'IMPORTANT CONTEXT: {context}' if context else ''}

For casual conversation, respond naturally and helpfully. Keep responses concise (1-2 sentences max).
{f'Address the user by name ({user_name}) when appropriate.' if user_name else ''}
If asked about the date/time, provide the current information.
If thanked, be gracious. If greeted, be friendly and personal.
Remember previous conversations and user preferences.
Only mention the agents if specifically asked about your capabilities."""

        try:
            # Include recent conversation history for better context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation context
            recent_conversations = self.memory.memory["conversation_context"][-3:]
            for conv in recent_conversations:
                if conv["query"] != query:  # Don't include current query
                    messages.append({"role": "user", "content": conv["query"]})
                    messages.append({"role": "assistant", "content": conv["response"]})
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise e
    
    async def _get_fallback_response(self, query: str, intent: QueryType) -> str:
        """
        Fallback responses when OpenAI is not available (with memory)
        """
        user_name = self.memory.get_user_name()
        name_part = f" {user_name}" if user_name else ""
        
        if intent == QueryType.GREETING:
            import random
            greetings = [
                f"Hello{name_part}! I'm your Personal Life Coordination system. I'm here to help you manage your meals, health, shopping, and scheduling through my specialized agents.",
                f"Hi there{name_part}! Your agents Milo (fitness), Luna (meals), Bucky (shopping), and Nani (scheduling) are all ready to help. What would you like to work on today?",
                f"Good to see you{name_part}! I coordinate between your personal agents to help with fitness, nutrition, shopping, and scheduling. How can we assist you today?"
            ]
            return random.choice(greetings)
        
        elif intent == QueryType.SIMPLE_CONVERSATION:
            query_lower = query.lower()
            
            # Handle name introduction
            if any(phrase in query_lower for phrase in ['my name is', 'i am', 'call me', 'i\'m']):
                if user_name:
                    return f"Nice to meet you, {user_name}! I'll remember that. How can I help you today?"
                else:
                    return "Nice to meet you! I'll remember that. How can I help you today?"
            
            if 'thank' in query_lower:
                return f"You're very welcome{name_part}! I'm here whenever you need help coordinating your personal life management."
            elif any(word in query_lower for word in ['bye', 'goodbye', 'see you']):
                return f"Goodbye{name_part}! Your agents will be here whenever you need them. Take care!"
            elif 'help' in query_lower or 'what can you do' in query_lower:
                return self.conversation_responses[QueryType.SIMPLE_CONVERSATION]['help']
            elif 'who are you' in query_lower:
                return self.conversation_responses[QueryType.SIMPLE_CONVERSATION]['who']
            elif any(word in query_lower for word in ['day', 'date', 'time', 'today']):
                from datetime import datetime
                today = datetime.now()
                return f"Today is {today.strftime('%A, %B %d, %Y')}, {user_name if user_name else 'there'}! The current time is {today.strftime('%I:%M %p')}."
            elif any(phrase in query_lower for phrase in ['your name', 'tell me your name', 'what are you called']):
                return self.conversation_responses[QueryType.SIMPLE_CONVERSATION]['who']
            else:
                return f"I understand{name_part}! Is there anything specific you'd like help with regarding your meals, fitness, shopping, or schedule?"
        
        return f"I'm here to help with whatever you need{name_part}!"
    
    async def _handle_unknown_query(self, query: str) -> Dict[str, Any]:
        """
        Handle queries that don't clearly match any intent
        """
        response = f"""I'm not quite sure how to categorize your request: "{query}"

Let me help by routing it to our general-purpose agent (Milo) who can then coordinate with others if needed. Alternatively, you can be more specific:

• For **meals & nutrition**: "What should I eat for dinner?"
• For **fitness & health**: "Plan my workout routine"  
• For **shopping**: "I need to buy groceries"
• For **scheduling**: "Schedule a meeting tomorrow"

How would you like me to help?"""
        
        return {
            'routing_decision': {
                'intent': 'unknown',
                'target_agents': ['milo'],  # Default to Milo as general coordinator
                'requires_agents': True,
                'multi_agent_workflow': False,
                'query': query,
                'timestamp': datetime.now().isoformat()
            },
            'coordinator_response': response,
            'should_forward_to_agents': True
        }
    
    async def orchestrate_multi_agent_workflow(self, query: str, target_agents: List[str]) -> Dict[str, Any]:
        """
        Orchestrate complex workflows involving multiple agents
        """
        workflow_plan = {
            'workflow_id': f"workflow_{int(datetime.now().timestamp())}",
            'query': query,
            'agents': target_agents,
            'coordination_strategy': self._determine_coordination_strategy(query, target_agents),
            'estimated_steps': len(target_agents) + 1,  # +1 for coordination
            'timestamp': datetime.now().isoformat()
        }
        
        return workflow_plan
    
    def _determine_coordination_strategy(self, query: str, agents: List[str]) -> str:
        """
        Determine how agents should coordinate for multi-agent workflows
        """
        if 'nani' in agents and ('milo' in agents or 'luna' in agents):
            return "schedule_optimization"  # Nani coordinates with health/nutrition
        elif 'milo' in agents and 'luna' in agents:
            return "health_nutrition_sync"  # Milo and Luna coordinate meal/fitness
        elif 'bucky' in agents and 'luna' in agents:
            return "shopping_meal_planning"  # Bucky and Luna coordinate shopping/meals
        else:
            return "sequential_processing"  # Process in order
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current status of the coordination system
        """
        return {
            'coordinator_status': 'active',
            'intent_recognition': 'enabled',
            'memory_system': 'enabled',
            'user_name': self.memory.get_user_name(),
            'stored_facts': len(self.memory.memory["important_facts"]),
            'conversation_history': len(self.memory.memory["conversation_context"]),
            'supported_intents': list(self.intent_patterns.keys()),
            'agent_mappings': self.agents,
            'conversation_handling': 'enabled',
            'multi_agent_orchestration': 'enabled',
            'openai_available': self.has_openai,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of stored memory
        """
        return {
            'user_profile': self.memory.memory["user_profile"],
            'preferences': self.memory.memory["preferences"],
            'recent_facts': [fact['fact'] for fact in self.memory.memory["important_facts"][-5:]],
            'conversation_count': len(self.memory.memory["conversation_context"]),
            'memory_status': 'active'
        }