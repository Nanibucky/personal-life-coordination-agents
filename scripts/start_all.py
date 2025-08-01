#!/usr/bin/env python3
"""
Start All Script
Launches all agents and the API gateway
"""

import asyncio
import subprocess
import sys
import os
import signal
import time
from typing import List, Dict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from shared.utils.config import config_manager
from shared.utils.logging import setup_logging

class AgentManager:
    """Manages starting and stopping all agents"""
    
    def __init__(self):
        self.logger = setup_logging("agent_manager")
        self.processes: Dict[str, subprocess.Popen] = {}
        self.agent_configs = {
            "bucky": {
                "script": "agents/bucky_shopping/src/main.py",
                "port": 8002,
                "description": "Shopping & Inventory Management"
            },
            "luna": {
                "script": "agents/luna_health/src/main.py",
                "port": 8003,
                "description": "Health & Fitness Tracking"
            },
            "milo": {
                "script": "agents/milo_nutrition/src/main.py",
                "port": 8004,
                "description": "Meal Planning & Nutrition"
            },
            "nani": {
                "script": "agents/nani_scheduler/src/main.py",
                "port": 8005,
                "description": "Scheduling & Calendar Management"
            },
            "api_gateway": {
                "script": "api_gateway/src/main.py",
                "port": 8000,
                "description": "API Gateway"
            }
        }
    
    def start_agent(self, agent_name: str) -> bool:
        """Start a specific agent"""
        if agent_name not in self.agent_configs:
            self.logger.error(f"Unknown agent: {agent_name}")
            return False
        
        if agent_name in self.processes and self.processes[agent_name].poll() is None:
            self.logger.info(f"Agent {agent_name} is already running")
            return True
        
        config = self.agent_configs[agent_name]
        script_path = project_root / config["script"]
        
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False
        
        try:
            # Start the agent process
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[agent_name] = process
            self.logger.info(f"Started {agent_name} ({config['description']}) on port {config['port']}")
            
            # Give it a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                return True
            else:
                stdout, stderr = process.communicate()
                self.logger.error(f"Agent {agent_name} failed to start. stdout: {stdout}, stderr: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_name}: {e}")
            return False
    
    def stop_agent(self, agent_name: str) -> bool:
        """Stop a specific agent"""
        if agent_name not in self.processes:
            self.logger.warning(f"Agent {agent_name} is not running")
            return True
        
        process = self.processes[agent_name]
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=10)
                self.logger.info(f"Stopped agent {agent_name}")
            except subprocess.TimeoutExpired:
                process.kill()
                self.logger.warning(f"Force killed agent {agent_name}")
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent_name}: {e}")
                return False
        
        del self.processes[agent_name]
        return True
    
    def start_all(self) -> bool:
        """Start all agents"""
        self.logger.info("Starting all agents...")
        
        # Start agents in order
        agent_order = ["api_gateway", "bucky", "luna", "milo", "nani"]
        success_count = 0
        
        for agent_name in agent_order:
            if self.start_agent(agent_name):
                success_count += 1
            else:
                self.logger.error(f"Failed to start {agent_name}, stopping all agents")
                self.stop_all()
                return False
        
        self.logger.info(f"Successfully started {success_count}/{len(agent_order)} agents")
        return success_count == len(agent_order)
    
    def stop_all(self):
        """Stop all agents"""
        self.logger.info("Stopping all agents...")
        
        # Stop in reverse order
        for agent_name in reversed(list(self.processes.keys())):
            self.stop_agent(agent_name)
        
        self.logger.info("All agents stopped")
    
    def get_status(self) -> Dict[str, str]:
        """Get status of all agents"""
        status = {}
        for agent_name, config in self.agent_configs.items():
            if agent_name in self.processes:
                process = self.processes[agent_name]
                if process.poll() is None:
                    status[agent_name] = "running"
                else:
                    status[agent_name] = "stopped"
            else:
                status[agent_name] = "not_started"
        return status
    
    def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal, stopping all agents...")
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while True:
                time.sleep(1)
                # Check if any processes have died
                for agent_name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        self.logger.warning(f"Agent {agent_name} has stopped unexpectedly")
                        del self.processes[agent_name]
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.stop_all()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Personal Life Coordination Agents")
    parser.add_argument("--agent", help="Start specific agent only")
    parser.add_argument("--stop", action="store_true", help="Stop all agents")
    parser.add_argument("--status", action="store_true", help="Show status of all agents")
    
    args = parser.parse_args()
    
    manager = AgentManager()
    
    if args.stop:
        manager.stop_all()
    elif args.status:
        status = manager.get_status()
        print("Agent Status:")
        for agent_name, agent_status in status.items():
            print(f"  {agent_name}: {agent_status}")
    elif args.agent:
        if manager.start_agent(args.agent):
            print(f"Agent {args.agent} started successfully")
            manager.wait_for_shutdown()
        else:
            print(f"Failed to start agent {args.agent}")
            sys.exit(1)
    else:
        if manager.start_all():
            print("All agents started successfully")
            print("Press Ctrl+C to stop all agents")
            manager.wait_for_shutdown()
        else:
            print("Failed to start all agents")
            sys.exit(1)

if __name__ == "__main__":
    main()
