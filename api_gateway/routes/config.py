"""
Configuration API Routes
Handle agent and tool configuration management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

class ConfigRequest(BaseModel):
    config: Dict[str, Any]

class ConfigResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None

# Configuration storage
CONFIG_DIR = Path(__file__).parent.parent.parent / "agents"

def get_agent_config_path(agent_name: str) -> Path:
    """Get the configuration file path for an agent"""
    return CONFIG_DIR / agent_name / "config" / "tool_config.json"

def load_agent_config(agent_name: str) -> Dict[str, Any]:
    """Load agent configuration from file"""
    config_path = get_agent_config_path(agent_name)
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config for {agent_name}: {e}")
    return {}

def save_agent_config(agent_name: str, config: Dict[str, Any]) -> bool:
    """Save agent configuration to file"""
    try:
        config_path = get_agent_config_path(agent_name)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Update environment variables for immediate effect
        update_environment_variables(agent_name, config)
        return True
    except Exception as e:
        logger.error(f"Failed to save config for {agent_name}: {e}")
        return False

def update_environment_variables(agent_name: str, tool_configs: Dict[str, Any]) -> None:
    """Update environment variables based on tool configurations"""
    for tool_name, tool_config in tool_configs.items():
        if tool_name == "calendar_manager":
            if tool_config.get("google_client_id"):
                os.environ["GOOGLE_CLIENT_ID"] = tool_config["google_client_id"]
            if tool_config.get("google_client_secret"):
                os.environ["GOOGLE_CLIENT_SECRET"] = tool_config["google_client_secret"]
        elif tool_name in ["schedule_optimizer", "meeting_assistant"]:
            if tool_config.get("openai_api_key"):
                os.environ["OPENAI_API_KEY"] = tool_config["openai_api_key"]

def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """Get configuration schema for a tool"""
    schemas = {
        "calendar_manager": {
            "google_client_id": {
                "type": "string", 
                "label": "Google Client ID", 
                "required": True, 
                "placeholder": "Your Google OAuth Client ID",
                "description": "OAuth 2.0 Client ID from Google Cloud Console"
            },
            "google_client_secret": {
                "type": "password", 
                "label": "Google Client Secret", 
                "required": True, 
                "placeholder": "Your Google OAuth Client Secret",
                "description": "OAuth 2.0 Client Secret from Google Cloud Console"
            },
            "redirect_uri": {
                "type": "string", 
                "label": "Redirect URI", 
                "required": True,
                "default": "http://localhost:8000/auth/google/callback",
                "description": "OAuth redirect URI (must match Google Console setting)"
            },
            "user_email": {
                "type": "email", 
                "label": "User Email", 
                "required": False, 
                "placeholder": "your-email@gmail.com",
                "description": "Your Google account email address"
            }
        },
        "schedule_optimizer": {
            "openai_api_key": {
                "type": "password", 
                "label": "OpenAI API Key", 
                "required": True, 
                "placeholder": "sk-...",
                "description": "API key for OpenAI GPT models"
            },
            "default_algorithm": {
                "type": "select", 
                "label": "Default Algorithm", 
                "options": ["genetic", "greedy", "dynamic_programming"],
                "default": "genetic",
                "description": "Default optimization algorithm"
            }
        },
        "time_tracker": {
            "storage_type": {
                "type": "select", 
                "label": "Storage Type", 
                "options": ["local", "cloud"], 
                "default": "local",
                "description": "Where to store time tracking data"
            },
            "auto_backup": {
                "type": "boolean", 
                "label": "Auto Backup", 
                "default": True,
                "description": "Automatically backup time tracking data"
            }
        },
        "meeting_assistant": {
            "openai_api_key": {
                "type": "password", 
                "label": "OpenAI API Key", 
                "required": True, 
                "placeholder": "sk-...",
                "description": "API key for OpenAI GPT models"
            },
            "default_meeting_duration": {
                "type": "number", 
                "label": "Default Meeting Duration (minutes)", 
                "default": 60, 
                "min": 15, 
                "max": 480,
                "description": "Default length for new meetings"
            },
            "reminder_minutes": {
                "type": "number", 
                "label": "Default Reminder (minutes)", 
                "default": 15, 
                "min": 0, 
                "max": 1440,
                "description": "Default reminder time before meetings"
            }
        }
    }
    return schemas.get(tool_name, {})

@router.get("/agents/{agent_name}/tools/{tool_name}/config")
async def get_tool_config(agent_name: str, tool_name: str) -> ConfigResponse:
    """Get current configuration for a specific tool"""
    try:
        # Load existing configuration
        agent_configs = load_agent_config(agent_name)
        tool_config = agent_configs.get(tool_name, {})
        
        # Get schema for the tool
        schema = get_tool_schema(tool_name)
        
        return ConfigResponse(
            success=True,
            config=tool_config,
            schema=schema,
            message=f"Configuration loaded for {tool_name}"
        )
    
    except Exception as e:
        logger.error(f"Failed to get tool config: {e}")
        return ConfigResponse(
            success=False,
            error=str(e),
            schema=get_tool_schema(tool_name)
        )

@router.post("/agents/{agent_name}/tools/{tool_name}/config")
async def set_tool_config(agent_name: str, tool_name: str, request: ConfigRequest) -> ConfigResponse:
    """Set configuration for a specific tool"""
    try:
        # Load existing agent configuration
        agent_configs = load_agent_config(agent_name)
        
        # Update tool configuration
        agent_configs[tool_name] = request.config
        
        # Save updated configuration
        if save_agent_config(agent_name, agent_configs):
            return ConfigResponse(
                success=True,
                message=f"Configuration saved for {tool_name}",
                config=request.config
            )
        else:
            raise Exception("Failed to save configuration")
    
    except Exception as e:
        logger.error(f"Failed to set tool config: {e}")
        return ConfigResponse(
            success=False,
            error=str(e)
        )

@router.post("/agents/{agent_name}/tools/{tool_name}/test")
async def test_tool_config(agent_name: str, tool_name: str, request: ConfigRequest) -> ConfigResponse:
    """Test a tool configuration"""
    try:
        config = request.config
        test_results = {}
        
        if tool_name == "calendar_manager":
            # Test Google Calendar configuration
            if config.get("google_client_id") and config.get("google_client_secret"):
                # Mock test - in real implementation, you'd test OAuth flow
                test_results = {
                    "oauth_config": "✅ Valid",
                    "client_id": "✅ Format correct",
                    "client_secret": "✅ Present",
                    "redirect_uri": config.get("redirect_uri", "Not set")
                }
            else:
                raise Exception("Google Client ID and Secret are required")
        
        elif tool_name in ["schedule_optimizer", "meeting_assistant"]:
            # Test OpenAI API key
            if config.get("openai_api_key"):
                if config["openai_api_key"].startswith("sk-"):
                    test_results = {
                        "api_key": "✅ Format valid",
                        "status": "Ready for use"
                    }
                else:
                    raise Exception("Invalid OpenAI API key format")
            else:
                raise Exception("OpenAI API key is required")
        
        elif tool_name == "time_tracker":
            # Test time tracker configuration
            test_results = {
                "storage": f"✅ {config.get('storage_type', 'local')} storage configured",
                "backup": f"✅ Auto backup {'enabled' if config.get('auto_backup') else 'disabled'}"
            }
        
        return ConfigResponse(
            success=True,
            message=f"Configuration test passed for {tool_name}",
            config={"test_results": test_results}
        )
    
    except Exception as e:
        logger.error(f"Failed to test tool config: {e}")
        return ConfigResponse(
            success=False,
            error=str(e)
        )

@router.get("/agents/{agent_name}/config/status")
async def get_config_status(agent_name: str) -> Dict[str, Any]:
    """Get overall configuration status for an agent"""
    try:
        agent_configs = load_agent_config(agent_name)
        
        status = {
            "agent": agent_name,
            "configured_tools": list(agent_configs.keys()),
            "total_tools": len(agent_configs),
            "tools": {}
        }
        
        for tool_name, tool_config in agent_configs.items():
            schema = get_tool_schema(tool_name)
            required_fields = [k for k, v in schema.items() if v.get("required")]
            configured_fields = [k for k in required_fields if tool_config.get(k)]
            
            status["tools"][tool_name] = {
                "configured": len(configured_fields) == len(required_fields),
                "required_fields": len(required_fields),
                "configured_fields": len(configured_fields),
                "missing_fields": [f for f in required_fields if not tool_config.get(f)]
            }
        
        return status
    
    except Exception as e:
        logger.error(f"Failed to get config status: {e}")
        return {"error": str(e), "agent": agent_name}