#!/usr/bin/env python3
"""
Agent Nani - Main Entry Point
Scheduler & Calendar Management Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.nani_scheduler.src.agent import NaniAgent

async def main():
    """Start Agent Nani"""
    print("🗓️  Starting Agent Nani - Scheduler & Calendar Management...")
    
    config = {
        "ai": {
            "model": "gpt-4",
            "temperature": 0.2,
            "system_prompt": """You are Nani, an expert scheduling and calendar management agent. 
            You excel at optimizing time allocation, managing complex calendars, and coordinating 
            schedules across multiple domains. You work collaboratively with other agents to 
            ensure optimal life coordination.""",
            "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        },
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql://plc_user:plc_password@localhost:5432/plc_agents")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0")
        }
    }
    
    agent = NaniAgent(config)
    print("✅ Agent Nani initialized successfully!")
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())