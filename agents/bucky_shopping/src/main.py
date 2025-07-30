#!/usr/bin/env python3
"""
Agent Bucky - Main Entry Point
Shopping & Inventory Management Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.bucky_shopping.src.agent import BuckyAgent

async def main():
    """Start Agent Bucky"""
    print("🛒 Starting Agent Bucky - Shopping & Inventory Management...")
    
    config = {
        "ai": {
            "model": "gpt-4",
            "temperature": 0.25,
            "system_prompt": """You are Bucky, an expert shopping and inventory management agent. 
            You excel at tracking pantry inventory, finding the best deals across stores, optimizing 
            shopping routes, and coordinating with other agents to ensure optimal household management. 
            You work collaboratively to minimize costs and maximize efficiency.""",
            "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        },
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql://plc_user:plc_password@localhost:5432/plc_agents")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0")
        },
        "external_apis": {
            "kroger": {
                "api_key": os.getenv("KROGER_API_KEY", "your-kroger-key"),
                "client_id": os.getenv("KROGER_CLIENT_ID", "your-kroger-client-id")
            },
            "instacart": {
                "api_key": os.getenv("INSTACART_API_KEY", "your-instacart-key")
            },
            "walmart": {
                "api_key": os.getenv("WALMART_API_KEY", "your-walmart-key")
            },
            "maps": {
                "api_key": os.getenv("GOOGLE_MAPS_API_KEY", "your-maps-key")
            }
        }
    }
    
    agent = BuckyAgent(config)
    print("✅ Agent Bucky initialized successfully!")
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())