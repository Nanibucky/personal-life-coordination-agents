#!/usr/bin/env python3
"""
Agent Luna - Main Entry Point
Fitness & Health Optimization Agent
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.luna_health.src.agent import LunaAgent

async def main():
    """Start Agent Luna"""
    print("💪 Starting Agent Luna - Fitness & Health Optimization...")
    
    config = {
        "ai": {
            "model": "gpt-4",
            "temperature": 0.3,
            "system_prompt": """You are Luna, an expert health and fitness optimization agent. 
            You excel at analyzing health data, creating personalized workout programs, and 
            optimizing recovery. You work collaboratively with other agents to ensure 
            comprehensive wellness coordination.""",
            "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-key-here")
        },
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql://plc_user:plc_password@localhost:5432/plc_agents")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0")
        },
        "external_apis": {
            "fitbit": {
                "client_id": os.getenv("FITBIT_CLIENT_ID", "your-fitbit-id"), 
                "client_secret": os.getenv("FITBIT_CLIENT_SECRET", "your-fitbit-secret")
            },
            "strava": {
                "client_id": os.getenv("STRAVA_CLIENT_ID", "your-strava-id"), 
                "client_secret": os.getenv("STRAVA_CLIENT_SECRET", "your-strava-secret")
            }
        }
    }
    
    agent = LunaAgent(config)
    print("✅ Agent Luna initialized successfully!")
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())