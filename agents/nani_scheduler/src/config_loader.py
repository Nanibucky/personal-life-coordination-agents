"""
Configuration Loader for Nani Agent
Loads configuration from environment variables and files
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Try to import python-dotenv, fall back to manual loading
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)

class NaniConfigLoader:
    """Load and manage Nani's configuration from multiple sources"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.credentials_dir = Path(__file__).parent.parent / "credentials"
        self.project_root = Path(__file__).parent.parent.parent.parent
        self._load_environment_variables()
    
    def _load_environment_variables(self):
        """Load environment variables from .env file"""
        env_file = self.project_root / ".env"
        
        if DOTENV_AVAILABLE and env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        elif env_file.exists():
            # Manual loading if python-dotenv is not available
            self._manual_load_env(env_file)
        else:
            logger.warning(f"Environment file not found at {env_file}")
    
    def _manual_load_env(self, env_file: Path):
        """Manually load environment variables from file"""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            logger.info(f"Manually loaded environment variables from {env_file}")
        except Exception as e:
            logger.error(f"Failed to manually load environment variables: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Load complete configuration from YAML and environment variables"""
        try:
            # Ensure environment variables are loaded
            self._load_environment_variables()
            
            # Load base config from YAML
            config_path = self.config_dir / "config.yaml"
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Override with environment variables
            self._apply_environment_overrides(config)
            
            # Load API keys and credentials
            self._load_credentials(config)
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_environment_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration"""
        
        # AI Configuration
        if os.getenv("OPENAI_API_KEY"):
            config.setdefault("ai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        
        # Database Configuration
        if os.getenv("DATABASE_URL"):
            config.setdefault("database", {})["url"] = os.getenv("DATABASE_URL")
        
        if os.getenv("REDIS_URL"):
            config.setdefault("redis", {})["url"] = os.getenv("REDIS_URL")
        
        # External APIs
        if os.getenv("OPENWEATHER_API_KEY"):
            config.setdefault("external_apis", {}).setdefault("weather_api", {})["api_key"] = os.getenv("OPENWEATHER_API_KEY")
        
        # Google Calendar
        google_config = config.setdefault("external_apis", {}).setdefault("google_calendar", {})
        if os.getenv("GOOGLE_CLIENT_ID"):
            google_config["client_id"] = os.getenv("GOOGLE_CLIENT_ID")
        if os.getenv("GOOGLE_CLIENT_SECRET"):
            google_config["client_secret"] = os.getenv("GOOGLE_CLIENT_SECRET")
        if os.getenv("GOOGLE_REDIRECT_URI"):
            google_config["redirect_uri"] = os.getenv("GOOGLE_REDIRECT_URI")
        
        # Outlook
        outlook_config = config.setdefault("external_apis", {}).setdefault("outlook", {})
        if os.getenv("OUTLOOK_CLIENT_ID"):
            outlook_config["client_id"] = os.getenv("OUTLOOK_CLIENT_ID")
        if os.getenv("OUTLOOK_CLIENT_SECRET"):
            outlook_config["client_secret"] = os.getenv("OUTLOOK_CLIENT_SECRET")
    
    def _load_credentials(self, config: Dict[str, Any]) -> None:
        """Load OAuth and API credentials"""
        try:
            # Load Google OAuth client configuration
            google_oauth_path = self.credentials_dir / "google_oauth_client.json"
            if google_oauth_path.exists():
                with open(google_oauth_path, 'r') as f:
                    google_oauth = json.load(f)
                
                # Override with environment variables if available
                if os.getenv("GOOGLE_CLIENT_ID"):
                    google_oauth["web"]["client_id"] = os.getenv("GOOGLE_CLIENT_ID")
                if os.getenv("GOOGLE_CLIENT_SECRET"):
                    google_oauth["web"]["client_secret"] = os.getenv("GOOGLE_CLIENT_SECRET")
                
                config.setdefault("credentials", {})["google_oauth"] = google_oauth
                logger.info("Loaded Google OAuth configuration")
            else:
                logger.warning("Google OAuth client configuration not found")
        
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
    
    def get_google_oauth_config(self) -> Optional[Dict[str, Any]]:
        """Get Google OAuth configuration for calendar setup"""
        config = self.load_config()
        return config.get("credentials", {}).get("google_oauth")
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return os.getenv("OPENAI_API_KEY")
    
    def get_weather_api_key(self) -> Optional[str]:
        """Get OpenWeather API key"""
        return os.getenv("OPENWEATHER_API_KEY")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate that required configuration is present"""
        validation_results = {
            "openai_api_key": bool(self.get_openai_api_key()),
            "google_oauth_config": bool(self.get_google_oauth_config()),
            "weather_api_key": bool(self.get_weather_api_key()),
            "config_file": (self.config_dir / "config.yaml").exists()
        }
        
        return validation_results
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get detailed configuration status for debugging"""
        validation = self.validate_configuration()
        
        status = {
            "configuration_loaded": all(validation.values()),
            "details": validation,
            "missing_configs": [k for k, v in validation.items() if not v],
            "config_sources": {
                "config_dir": str(self.config_dir),
                "credentials_dir": str(self.credentials_dir),
                "env_vars_loaded": {
                    "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
                    "GOOGLE_CLIENT_ID": bool(os.getenv("GOOGLE_CLIENT_ID")),
                    "GOOGLE_CLIENT_SECRET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
                    "OPENWEATHER_API_KEY": bool(os.getenv("OPENWEATHER_API_KEY"))
                }
            }
        }
        
        return status

# Global config loader instance
config_loader = NaniConfigLoader()