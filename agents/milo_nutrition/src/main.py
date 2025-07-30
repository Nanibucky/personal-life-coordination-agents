#!/usr/bin/env python3
"""
Agent Milo - Main Entry Point
Meal Planning & Nutrition Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.milo_nutrition.src.agent import MiloAgent

async def main():
    """Start Agent Milo"""
    print("🍽️ Starting Agent Milo - Meal Planning & Nutrition...")
    
    config = {
        "ai": {
            "model": "gpt-4",
            "temperature": 0.3,
            "system_prompt": """You are Milo, an expert meal planning and nutrition agent. 
            You excel at creating personalized meal plans, analyzing nutrition, discovering recipes 
            based on available ingredients, and coordinating with other agents to ensure optimal 
            nutrition and meal preparation. You work collaboratively to optimize health, budget, 
            and time efficiency.""",
            "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        },
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql://plc_user:plc_password@localhost:5432/plc_agents")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0")
        },
        "external_apis": {
            "spoonacular": {
                "api_key": os.getenv("SPOONACULAR_API_KEY", "your-spoonacular-key"),
                "base_url": "https://api.spoonacular.com"
            },
            "edamam": {
                "app_id": os.getenv("EDAMAM_APP_ID", "your-edamam-id"),
                "app_key": os.getenv("EDAMAM_APP_KEY", "your-edamam-key")
            },
            "usda": {
                "api_key": os.getenv("USDA_API_KEY", "your-usda-key"),
                "base_url": "https://api.nal.usda.gov"
            }
        }
    }
    
    agent = MiloAgent(config)
    print("✅ Agent Milo initialized successfully!")
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())