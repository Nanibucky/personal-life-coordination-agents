#!/usr/bin/env python3
"""
LangChain System Startup Script
Launches all LangChain agents and the API Gateway
"""

import asyncio
import sys
import os
import signal
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from shared.utils.config import config_manager
from shared.utils.logging import setup_logging
from shared.langchain_framework.a2a_coordinator import a2a_coordinator

class LangChainSystemManager:
    """Manages the LangChain system startup and coordination"""
    
    def __init__(self):
        self.logger = setup_logging("langchain_system_manager")
        self.processes: Dict[str, subprocess.Popen] = {}
        self.agents = {}
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    async def initialize_agents(self):
        """Initialize all LangChain agents"""
        self.logger.info("Initializing LangChain agents...")
        
        try:
            # Import and initialize agents
            from agents.bucky_shopping.langchain_agent import LangChainBuckyAgent
            from agents.luna_health.langchain_agent import LangChainLunaAgent
            from agents.milo_nutrition.langchain_agent import LangChainMiloAgent
            from agents.nani_scheduler.langchain_agent import LangChainNaniAgent
            
            # Create agent instances
            self.agents["bucky"] = LangChainBuckyAgent()
            self.agents["luna"] = LangChainLunaAgent()
            self.agents["milo"] = LangChainMiloAgent()
            self.agents["nani"] = LangChainNaniAgent()
            
            self.logger.info(f"Initialized {len(self.agents)} agents")
            
            # Verify A2A coordinator registration
            registered_agents = list(a2a_coordinator.agents.keys())
            self.logger.info(f"Agents registered with A2A coordinator: {registered_agents}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def start_api_gateway(self):
        """Start the LangChain API Gateway"""
        self.logger.info("Starting LangChain API Gateway...")
        
        try:
            # Start API Gateway in a separate process
            gateway_process = subprocess.Popen([
                sys.executable, 
                str(project_root / "api_gateway" / "langchain_gateway.py")
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes["api_gateway"] = gateway_process
            
            # Wait a moment for startup
            await asyncio.sleep(3)
            
            # Check if process is still running
            if gateway_process.poll() is None:
                self.logger.info("API Gateway started successfully")
            else:
                stdout, stderr = gateway_process.communicate()
                self.logger.error(f"API Gateway failed to start: {stderr.decode()}")
                raise Exception("API Gateway startup failed")
                
        except Exception as e:
            self.logger.error(f"Failed to start API Gateway: {e}")
            raise
    
    async def test_system_connectivity(self):
        """Test system connectivity and A2A communication"""
        self.logger.info("Testing system connectivity...")
        
        try:
            # Test A2A communication
            from shared.langchain_framework.a2a_coordinator import A2AMessage
            
            # Send test message from Bucky to Luna
            test_message = A2AMessage(
                from_agent="system_manager",
                to_agent="bucky",
                intent="test_connectivity",
                payload={"test": "system_connectivity"},
                session_id="startup_test"
            )
            
            response = await a2a_coordinator.send_message(test_message)
            
            if response["success"]:
                self.logger.info("A2A connectivity test passed")
            else:
                self.logger.warning(f"A2A connectivity test failed: {response.get('error')}")
            
            # Test agent tool execution
            for agent_name, agent in self.agents.items():
                try:
                    # Test a simple tool call
                    if agent_name == "bucky":
                        result = await agent.tools[0]._arun("get_inventory")
                        self.logger.info(f"Tool test for {agent_name} passed")
                    elif agent_name == "luna":
                        result = await agent.tools[0]._arun("get_workouts", days=1)
                        self.logger.info(f"Tool test for {agent_name} passed")
                    elif agent_name == "milo":
                        result = await agent.tools[0]._arun("find_recipes", ingredients=["chicken"])
                        self.logger.info(f"Tool test for {agent_name} passed")
                    elif agent_name == "nani":
                        result = await agent.tools[0]._arun("get_events")
                        self.logger.info(f"Tool test for {agent_name} passed")
                except Exception as e:
                    self.logger.warning(f"Tool test for {agent_name} failed: {e}")
            
        except Exception as e:
            self.logger.error(f"System connectivity test failed: {e}")
            raise
    
    async def start_frontend(self):
        """Start the React frontend"""
        self.logger.info("Starting React frontend...")
        
        try:
            frontend_dir = project_root / "frontend"
            
            # Check if node_modules exists
            if not (frontend_dir / "node_modules").exists():
                self.logger.info("Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            
            # Start frontend in development mode
            frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes["frontend"] = frontend_process
            
            # Wait for startup
            await asyncio.sleep(5)
            
            if frontend_process.poll() is None:
                self.logger.info("Frontend started successfully")
            else:
                stdout, stderr = frontend_process.communicate()
                self.logger.error(f"Frontend failed to start: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Failed to start frontend: {e}")
            # Don't raise - frontend is optional
    
    async def run_system(self):
        """Run the complete LangChain system"""
        self.logger.info("Starting LangChain Personal Life Coordination System...")
        
        try:
            # Initialize agents
            await self.initialize_agents()
            
            # Start API Gateway
            await self.start_api_gateway()
            
            # Test connectivity
            await self.test_system_connectivity()
            
            # Start frontend (optional)
            await self.start_frontend()
            
            self.running = True
            self.logger.info("🎉 LangChain system started successfully!")
            self.logger.info("📋 System Status:")
            self.logger.info(f"  - API Gateway: http://localhost:8000")
            self.logger.info(f"  - Frontend: http://localhost:3000")
            self.logger.info(f"  - Agents: {list(self.agents.keys())}")
            self.logger.info("")
            self.logger.info("Press Ctrl+C to shutdown the system")
            
            # Keep the system running
            while self.running:
                await asyncio.sleep(1)
                
                # Check if any processes have died
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        self.logger.error(f"Process {name} has stopped unexpectedly")
                        self.running = False
                        break
                        
        except Exception as e:
            self.logger.error(f"System startup failed: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Shutdown the system gracefully"""
        self.logger.info("Shutting down LangChain system...")
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                self.logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Force killing {name}...")
                process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping {name}: {e}")
        
        # Clear A2A coordinator
        a2a_coordinator.agents.clear()
        
        self.running = False
        self.logger.info("System shutdown complete")

async def main():
    """Main entry point"""
    manager = LangChainSystemManager()
    
    try:
        await manager.run_system()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 