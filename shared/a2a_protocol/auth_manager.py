"""
A2A Authentication Manager
Handles authentication and authorization for agent-to-agent communication
"""

import hashlib
import hmac
import time
import jwt
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import secrets

class A2AAuthManager:
    """Manages authentication for A2A communication"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.agent_tokens: Dict[str, str] = {}
        self.token_expiry: Dict[str, datetime] = {}
        self.token_duration = timedelta(hours=24)
    
    def generate_agent_token(self, agent_name: str) -> str:
        """Generate a JWT token for an agent"""
        payload = {
            "agent": agent_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + self.token_duration
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        self.agent_tokens[agent_name] = token
        self.token_expiry[agent_name] = payload["exp"]
        
        return token
    
    def validate_agent_token(self, token: str) -> Optional[str]:
        """Validate an agent token and return agent name"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            agent_name = payload.get("agent")
            
            if agent_name and agent_name in self.agent_tokens:
                if self.agent_tokens[agent_name] == token:
                    return agent_name
            
            return None
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_agent_token(self, agent_name: str):
        """Revoke an agent's token"""
        if agent_name in self.agent_tokens:
            del self.agent_tokens[agent_name]
        if agent_name in self.token_expiry:
            del self.token_expiry[agent_name]
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens"""
        now = datetime.utcnow()
        expired_agents = []
        
        for agent_name, expiry in self.token_expiry.items():
            if now > expiry:
                expired_agents.append(agent_name)
        
        for agent_name in expired_agents:
            self.revoke_agent_token(agent_name)
    
    def sign_message(self, message: Dict[str, Any], agent_name: str) -> str:
        """Sign a message with HMAC"""
        message_str = str(sorted(message.items()))
        signature = hmac.new(
            self.secret_key.encode(),
            message_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_message_signature(self, message: Dict[str, Any], signature: str) -> bool:
        """Verify message signature"""
        expected_signature = self.sign_message(message, "")
        return hmac.compare_digest(signature, expected_signature)
    
    def get_agent_permissions(self, agent_name: str) -> List[str]:
        """Get permissions for an agent"""
        # Default permissions for all agents
        base_permissions = ["read", "write", "a2a_communication"]
        
        # Agent-specific permissions
        agent_permissions = {
            "bucky": ["inventory_management", "shopping_optimization"],
            "luna": ["health_tracking", "fitness_planning"],
            "milo": ["meal_planning", "nutrition_analysis"],
            "nani": ["scheduling", "calendar_management"],
            "api_gateway": ["workflow_orchestration", "system_management"]
        }
        
        return base_permissions + agent_permissions.get(agent_name, [])
    
    def check_permission(self, agent_name: str, permission: str) -> bool:
        """Check if an agent has a specific permission"""
        permissions = self.get_agent_permissions(agent_name)
        return permission in permissions
    
    def create_authenticated_message(self, message: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
        """Create an authenticated message"""
        timestamp = int(time.time())
        message_with_timestamp = {
            **message,
            "timestamp": timestamp,
            "agent": agent_name
        }
        
        signature = self.sign_message(message_with_timestamp, agent_name)
        
        return {
            **message_with_timestamp,
            "signature": signature
        }
    
    def verify_authenticated_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Verify an authenticated message and return agent name"""
        if "signature" not in message or "timestamp" not in message or "agent" not in message:
            return None
        
        # Check timestamp (prevent replay attacks)
        timestamp = message["timestamp"]
        current_time = int(time.time())
        if abs(current_time - timestamp) > 300:  # 5 minutes tolerance
            return None
        
        # Verify signature
        signature = message["signature"]
        message_without_signature = {k: v for k, v in message.items() if k != "signature"}
        
        if not self.verify_message_signature(message_without_signature, signature):
            return None
        
        return message["agent"]

# Global auth manager instance
auth_manager = A2AAuthManager()
