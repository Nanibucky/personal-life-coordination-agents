"""
Configuration Management
Handles loading and validation of agent configurations
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Any] = {}
    
    def load_config(self, agent_name: str) -> Dict[str, Any]:
        """Load configuration for a specific agent"""
        if agent_name in self._config_cache:
            return self._config_cache[agent_name]
        
        config_file = self.config_dir / f"{agent_name}.yaml"
        if not config_file.exists():
            # Return default configuration
            return self._get_default_config(agent_name)
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate and merge with defaults
            default_config = self._get_default_config(agent_name)
            merged_config = self._merge_configs(default_config, config)
            
            self._config_cache[agent_name] = merged_config
            return merged_config
            
        except Exception as e:
            print(f"Error loading config for {agent_name}: {e}")
            return self._get_default_config(agent_name)
    
    def _get_default_config(self, agent_name: str) -> Dict[str, Any]:
        """Get default configuration for an agent"""
        defaults = {
            "bucky": {
                "agent": {
                    "name": "bucky",
                    "port": 8002,
                    "description": "Shopping & Inventory Management Agent"
                },
                "database": {
                    "url": os.getenv("DATABASE_URL", "sqlite:///data/bucky.db")
                },
                "tools": {
                    "pantry_tracker": {"enabled": True},
                    "price_comparator": {"enabled": True},
                    "shopping_optimizer": {"enabled": True},
                    "deal_finder": {"enabled": True}
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "luna": {
                "agent": {
                    "name": "luna",
                    "port": 8003,
                    "description": "Health & Fitness Tracking Agent"
                },
                "database": {
                    "url": os.getenv("DATABASE_URL", "sqlite:///data/luna.db")
                },
                "tools": {
                    "fitness_tracker": {"enabled": True},
                    "health_analyzer": {"enabled": True},
                    "workout_planner": {"enabled": True},
                    "recovery_monitor": {"enabled": True}
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "milo": {
                "agent": {
                    "name": "milo",
                    "port": 8004,
                    "description": "Meal Planning & Nutrition Agent"
                },
                "database": {
                    "url": os.getenv("DATABASE_URL", "sqlite:///data/milo.db")
                },
                "tools": {
                    "recipe_engine": {"enabled": True},
                    "nutrition_analyzer": {"enabled": True},
                    "meal_planner": {"enabled": True}
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "nani": {
                "agent": {
                    "name": "nani",
                    "port": 8005,
                    "description": "Scheduling & Calendar Management Agent"
                },
                "database": {
                    "url": os.getenv("DATABASE_URL", "sqlite:///data/nani.db")
                },
                "tools": {
                    "calendar_manager": {"enabled": True},
                    "scheduling_optimizer": {"enabled": True},
                    "timezone_handler": {"enabled": True},
                    "focus_blocker": {"enabled": True}
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
        }
        
        return defaults.get(agent_name, {
            "agent": {
                "name": agent_name,
                "port": 8000,
                "description": f"{agent_name.title()} Agent"
            },
            "database": {
                "url": os.getenv("DATABASE_URL", f"sqlite:///data/{agent_name}.db")
            },
            "tools": {},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        })
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge override configuration with defaults"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        global_config_file = self.config_dir / "global.yaml"
        if global_config_file.exists():
            try:
                with open(global_config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading global config: {e}")
        
        return {
            "api_gateway": {
                "host": "0.0.0.0",
                "port": 8000,
                "cors_origins": ["http://localhost:3000"]
            },
            "database": {
                "url": os.getenv("DATABASE_URL", "sqlite:///data/main.db")
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def save_config(self, agent_name: str, config: Dict[str, Any]):
        """Save configuration for an agent"""
        config_file = self.config_dir / f"{agent_name}.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Update cache
            self._config_cache[agent_name] = config
            
        except Exception as e:
            print(f"Error saving config for {agent_name}: {e}")

# Global config manager instance
config_manager = ConfigManager()
