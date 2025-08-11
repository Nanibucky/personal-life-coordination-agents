#!/usr/bin/env python3
"""
Nani API Key Setup Script
Interactive script to help configure API keys for Agent Nani
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🗓️  Agent Nani - API Key Configuration Setup")
    print("=" * 60)
    print()

def get_user_input(prompt: str, current_value: str = None, required: bool = True) -> str:
    """Get user input with validation"""
    if current_value and current_value != "your_api_key_here":
        prompt += f" (current: {current_value[:20]}...)"
    
    while True:
        value = input(f"{prompt}: ").strip()
        if value:
            return value
        elif not required:
            return ""
        else:
            print("❌ This field is required. Please enter a value.")

def update_env_file(updates: Dict[str, str]) -> None:
    """Update the .env file with new values"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    # Read current .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key] = value
    
    # Update with new values
    env_content.update(updates)
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.write("# AI API Keys\\n")
        f.write(f"OPENAI_API_KEY={env_content.get('OPENAI_API_KEY', 'your_openai_api_key_here')}\\n")
        f.write(f"ANTHROPIC_API_KEY={env_content.get('ANTHROPIC_API_KEY', 'your_anthropic_api_key_here')}\\n")
        f.write("\\n")
        f.write("# System Configuration\\n")
        f.write(f"LOG_LEVEL={env_content.get('LOG_LEVEL', 'INFO')}\\n")
        f.write(f"API_GATEWAY_HOST={env_content.get('API_GATEWAY_HOST', '0.0.0.0')}\\n")
        f.write(f"API_GATEWAY_PORT={env_content.get('API_GATEWAY_PORT', '8000')}\\n")
        f.write(f"REACT_APP_API_URL={env_content.get('REACT_APP_API_URL', 'http://localhost:8000')}\\n")
        f.write("\\n")
        f.write("# Nani (Scheduler) Configuration\\n")
        f.write(f"GOOGLE_CLIENT_ID={env_content.get('GOOGLE_CLIENT_ID', 'your_google_client_id_here')}\\n")
        f.write(f"GOOGLE_CLIENT_SECRET={env_content.get('GOOGLE_CLIENT_SECRET', 'your_google_client_secret_here')}\\n")
        f.write(f"GOOGLE_REDIRECT_URI={env_content.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')}\\n")
        f.write("\\n")
        f.write("# Weather API (for Nani's weather-aware scheduling)\\n")
        f.write(f"OPENWEATHER_API_KEY={env_content.get('OPENWEATHER_API_KEY', 'your_openweather_api_key_here')}\\n")
        f.write("\\n")
        f.write("# Calendar providers\\n")
        f.write(f"OUTLOOK_CLIENT_ID={env_content.get('OUTLOOK_CLIENT_ID', 'your_outlook_client_id_here')}\\n")
        f.write(f"OUTLOOK_CLIENT_SECRET={env_content.get('OUTLOOK_CLIENT_SECRET', 'your_outlook_client_secret_here')}\\n")
        f.write("\\n")
        f.write("# Database URLs\\n")
        f.write(f"DATABASE_URL={env_content.get('DATABASE_URL', 'postgresql://localhost:5432/nani_scheduler')}\\n")
        f.write(f"REDIS_URL={env_content.get('REDIS_URL', 'redis://localhost:6379')}\\n")

def update_google_oauth_config(client_id: str, client_secret: str) -> None:
    """Update Google OAuth configuration file"""
    credentials_dir = Path(__file__).parent / "credentials"
    oauth_file = credentials_dir / "google_oauth_client.json"
    
    if oauth_file.exists():
        with open(oauth_file, 'r') as f:
            config = json.load(f)
        
        config["web"]["client_id"] = client_id
        config["web"]["client_secret"] = client_secret
        
        with open(oauth_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated Google OAuth configuration: {oauth_file}")

def main():
    """Main setup function"""
    print_banner()
    
    print("This script will help you configure API keys for Agent Nani.")
    print("You'll need to obtain these keys from their respective providers.")
    print()
    
    # Check current environment
    current_env = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID', ''),
        'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET', ''),
        'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY', '')
    }
    
    updates = {}
    
    print("📋 Required API Keys:")
    print()
    
    # OpenAI API Key
    print("1. OpenAI API Key (required for AI functionality)")
    print("   Get your key from: https://platform.openai.com/api-keys")
    openai_key = get_user_input("Enter your OpenAI API key", current_env['OPENAI_API_KEY'])
    if openai_key:
        updates['OPENAI_API_KEY'] = openai_key
    print()
    
    # Google Calendar API
    print("2. Google Calendar API (required for calendar integration)")
    print("   Set up at: https://console.developers.google.com/")
    print("   Enable the Google Calendar API and create OAuth 2.0 credentials")
    google_client_id = get_user_input("Enter your Google Client ID", current_env['GOOGLE_CLIENT_ID'])
    google_client_secret = get_user_input("Enter your Google Client Secret", current_env['GOOGLE_CLIENT_SECRET'])
    if google_client_id:
        updates['GOOGLE_CLIENT_ID'] = google_client_id
    if google_client_secret:
        updates['GOOGLE_CLIENT_SECRET'] = google_client_secret
    print()
    
    # OpenWeather API
    print("3. OpenWeather API (optional, for weather-aware scheduling)")
    print("   Get your key from: https://openweathermap.org/api")
    weather_key = get_user_input("Enter your OpenWeather API key", current_env['OPENWEATHER_API_KEY'], required=False)
    if weather_key:
        updates['OPENWEATHER_API_KEY'] = weather_key
    print()
    
    # Update configuration
    if updates:
        print("💾 Updating configuration...")
        update_env_file(updates)
        
        # Update Google OAuth config if both client ID and secret were provided
        if 'GOOGLE_CLIENT_ID' in updates and 'GOOGLE_CLIENT_SECRET' in updates:
            update_google_oauth_config(updates['GOOGLE_CLIENT_ID'], updates['GOOGLE_CLIENT_SECRET'])
        
        print("✅ Configuration updated successfully!")
        print()
        print("📋 Next steps:")
        print("1. Start the Nani MCP server: python agents/nani_scheduler/mcp_server.py")
        print("2. Use the frontend to interact with Nani")
        print("3. For Google Calendar, you'll need to complete OAuth authorization when first using calendar features")
    else:
        print("ℹ️  No changes made to configuration.")
    
    print()
    print("🎉 Setup complete! Agent Nani is ready to manage your schedule.")

if __name__ == "__main__":
    main()