#!/usr/bin/env python3
"""
Agent Nani - Main Entry Point
Scheduler & Calendar Management Agent
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from agents.nani_scheduler.src.agent import NaniAgent
from agents.nani_scheduler.src.config_loader import config_loader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Start Agent Nani with proper configuration"""
    print("🗓️  Starting Agent Nani - Scheduler & Calendar Management...")
    
    try:
        # Load configuration
        config = config_loader.load_config()
        logger.info("Configuration loaded successfully")
        
        # Check configuration status
        config_status = config_loader.get_configuration_status()
        
        if not config_status["configuration_loaded"]:
            logger.warning("⚠️  Some configuration is missing:")
            for missing in config_status["missing_configs"]:
                logger.warning(f"  - {missing}")
            print("\n📋 Configuration Status:")
            print(f"✅ Config file: {config_status['details']['config_file']}")
            print(f"{'✅' if config_status['details']['openai_api_key'] else '❌'} OpenAI API Key: {'Configured' if config_status['details']['openai_api_key'] else 'Missing'}")
            print(f"{'✅' if config_status['details']['google_oauth_config'] else '❌'} Google OAuth: {'Configured' if config_status['details']['google_oauth_config'] else 'Missing'}")
            print(f"{'✅' if config_status['details']['weather_api_key'] else '❌'} Weather API: {'Configured' if config_status['details']['weather_api_key'] else 'Missing'}")
        else:
            print("✅ All configuration loaded successfully!")
        
        # Initialize agent
        agent = NaniAgent(config)
        print("✅ Agent Nani initialized successfully!")
        
        # Display available tools
        logger.info("Available tools:")
        logger.info("  - calendar_manager: Multi-user calendar management with Google Calendar integration")
        logger.info("  - schedule_optimizer: Intelligent scheduling optimization")
        logger.info("  - time_tracker: Time tracking and productivity analytics")
        logger.info("  - meeting_assistant: Meeting management and optimization")
        
        await agent.start()
        
    except Exception as e:
        logger.error(f"Failed to start Agent Nani: {e}")
        print(f"❌ Failed to start Agent Nani: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())