"""
Configuration loader utility with environment variable substitution
Handles loading JSON configs with ${VAR_NAME} substitution
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Union

class ConfigLoader:
    """Configuration loader with environment variable substitution"""
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    
    @staticmethod
    def substitute_env_vars(value: str) -> str:
        """Substitute environment variables in a string"""
        def replace_var(match):
            var_name = match.group(1)
            # Handle default values: ${VAR_NAME:default_value}
            if ':' in var_name:
                var_name, default = var_name.split(':', 1)
                return os.getenv(var_name, default)
            else:
                env_value = os.getenv(var_name)
                if env_value is None:
                    print(f"⚠️  Warning: Environment variable '{var_name}' not set")
                    return f"MISSING_{var_name}"
                return env_value
        
        return ConfigLoader.ENV_VAR_PATTERN.sub(replace_var, value)
    
    @staticmethod
    def process_config_value(value: Any) -> Any:
        """Recursively process configuration values for env var substitution"""
        if isinstance(value, str):
            return ConfigLoader.substitute_env_vars(value)
        elif isinstance(value, dict):
            return {k: ConfigLoader.process_config_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [ConfigLoader.process_config_value(item) for item in value]
        else:
            return value
    
    @staticmethod
    def load_json_config(config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration with environment variable substitution"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                raw_config = json.load(f)
            
            # Process environment variable substitutions
            processed_config = ConfigLoader.process_config_value(raw_config)
            
            return processed_config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading config file {config_path}: {e}")
    
    @staticmethod
    def load_agent_config(agent_name: str, config_filename: str = "tool_config.json") -> Dict[str, Any]:
        """Load configuration for a specific agent"""
        # Determine the base path (assumes this script is in shared/utils/)
        base_path = Path(__file__).parent.parent.parent
        config_path = base_path / "agents" / agent_name / "config" / config_filename
        
        return ConfigLoader.load_json_config(config_path)
    
    @staticmethod
    def validate_required_keys(config: Dict[str, Any], required_keys: list, context: str = "") -> list:
        """Validate that required configuration keys are present and not placeholder values"""
        missing_keys = []
        placeholder_patterns = ["YOUR_", "MISSING_", "your_", "DEMO_KEY", ""]
        
        def check_nested_key(obj: Any, key_path: str) -> bool:
            """Check if a nested key has a valid value"""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{key_path}.{k}" if key_path else k
                    if k in required_keys or current_path in required_keys:
                        if isinstance(v, str):
                            if not v or any(pattern in v for pattern in placeholder_patterns):
                                return False
                    if not check_nested_key(v, current_path):
                        return False
            return True
        
        for key in required_keys:
            if '.' in key:
                # Handle nested keys like "tool.api_key"
                parts = key.split('.')
                current = config
                try:
                    for part in parts:
                        current = current[part]
                    
                    if isinstance(current, str):
                        if not current or any(pattern in current for pattern in placeholder_patterns):
                            missing_keys.append(f"{context}.{key}" if context else key)
                except (KeyError, TypeError):
                    missing_keys.append(f"{context}.{key}" if context else key)
            else:
                # Handle top-level keys
                if not check_nested_key(config, ""):
                    # More detailed checking for specific tools
                    for tool_name, tool_config in config.items():
                        if isinstance(tool_config, dict) and key in tool_config:
                            value = tool_config[key]
                            if isinstance(value, str) and (not value or any(pattern in value for pattern in placeholder_patterns)):
                                missing_keys.append(f"{tool_name}.{key}")
        
        return missing_keys
    
    @staticmethod
    def get_configuration_summary(agent_name: str) -> Dict[str, Any]:
        """Get a summary of the agent's configuration status"""
        try:
            config = ConfigLoader.load_agent_config(agent_name)
            
            summary = {
                "agent_name": agent_name,
                "config_loaded": True,
                "tools": {},
                "total_configs": 0,
                "configured_count": 0,
                "missing_count": 0
            }
            
            placeholder_patterns = ["YOUR_", "MISSING_", "your_", "DEMO_KEY", ""]
            
            for tool_name, tool_config in config.items():
                if isinstance(tool_config, dict):
                    tool_summary = {
                        "total_keys": 0,
                        "configured_keys": 0,
                        "missing_keys": []
                    }
                    
                    for key, value in tool_config.items():
                        if isinstance(value, str) and ('api_key' in key.lower() or 'client_id' in key.lower() or 'secret' in key.lower()):
                            tool_summary["total_keys"] += 1
                            summary["total_configs"] += 1
                            
                            if value and not any(pattern in value for pattern in placeholder_patterns):
                                tool_summary["configured_keys"] += 1
                                summary["configured_count"] += 1
                            else:
                                tool_summary["missing_keys"].append(key)
                                summary["missing_count"] += 1
                    
                    summary["tools"][tool_name] = tool_summary
            
            return summary
            
        except Exception as e:
            return {
                "agent_name": agent_name,
                "config_loaded": False,
                "error": str(e),
                "tools": {},
                "total_configs": 0,
                "configured_count": 0,
                "missing_count": 0
            }

def main():
    """Test the configuration loader"""
    print("🔧 Configuration Loader Test")
    print("=" * 40)
    
    agents = ["bucky_shopping", "luna_health", "milo_nutrition", "nani_scheduler"]
    
    for agent in agents:
        print(f"\n📋 Testing {agent}:")
        try:
            summary = ConfigLoader.get_configuration_summary(agent)
            print(f"   Status: {'✅ Loaded' if summary['config_loaded'] else '❌ Failed'}")
            if summary['config_loaded']:
                print(f"   Configured: {summary['configured_count']}/{summary['total_configs']} API keys")
                if summary['missing_count'] > 0:
                    print(f"   ⚠️  Missing: {summary['missing_count']} configurations")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    main()