#!/usr/bin/env python3
"""
Test Script
Tests basic functionality of the personal life coordination agents
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing imports...")
    
    try:
        # Test shared modules
        from shared.mcp_framework.base_server import BaseMCPServer, BaseMCPTool, ExecutionContext, ExecutionResult
        print("✓ Base server modules imported successfully")
        
        from shared.a2a_protocol.message_router import A2AMessage, A2AResponse, A2AMessageRouter
        print("✓ A2A protocol modules imported successfully")
        
        from shared.utils.config import config_manager
        print("✓ Configuration manager imported successfully")
        
        from shared.utils.logging import setup_logging, AgentLogger, ToolLogger
        print("✓ Logging modules imported successfully")
        
        from shared.utils.helpers import generate_id, merge_dicts, format_duration
        print("✓ Helper utilities imported successfully")
        
        from shared.mcp_framework.context_manager import context_manager
        print("✓ Context manager imported successfully")
        
        from shared.a2a_protocol.auth_manager import auth_manager
        print("✓ Auth manager imported successfully")
        
        from shared.a2a_protocol.workflow_coordinator import WorkflowCoordinator
        print("✓ Workflow coordinator imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from shared.utils.config import config_manager
        
        # Test loading configs for all agents
        agents = ["bucky", "luna", "milo", "nani"]
        for agent in agents:
            config = config_manager.load_config(agent)
            print(f"✓ Loaded config for {agent}: port {config['agent']['port']}")
        
        # Test global config
        global_config = config_manager.get_global_config()
        print(f"✓ Loaded global config: API Gateway port {global_config['api_gateway']['port']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_logging():
    """Test logging setup"""
    print("\nTesting logging...")
    
    try:
        from shared.utils.logging import setup_logging, AgentLogger
        
        # Test basic logging
        logger = setup_logging("test_logger")
        logger.info("Test log message")
        print("✓ Basic logging setup successful")
        
        # Test agent logger
        agent_logger = AgentLogger("test_agent")
        agent_logger.info("Test agent log message")
        print("✓ Agent logging setup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False

def test_a2a_protocol():
    """Test A2A protocol functionality"""
    print("\nTesting A2A protocol...")
    
    try:
        from shared.a2a_protocol.message_router import A2AMessage, A2AResponse
        from shared.a2a_protocol.auth_manager import auth_manager
        
        # Test message creation
        message = A2AMessage(
            from_agent="test_agent",
            to_agent="target_agent",
            intent="test_intent",
            payload={"test": "data"},
            session_id="test_session"
        )
        print("✓ A2A message creation successful")
        
        # Test message serialization
        message_dict = message.to_dict()
        print("✓ A2A message serialization successful")
        
        # Test auth manager
        token = auth_manager.generate_agent_token("test_agent")
        agent_name = auth_manager.validate_agent_token(token)
        print(f"✓ Auth manager test successful: {agent_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ A2A protocol test failed: {e}")
        return False

def test_helpers():
    """Test helper utilities"""
    print("\nTesting helper utilities...")
    
    try:
        from shared.utils.helpers import generate_id, merge_dicts, format_duration
        
        # Test ID generation
        test_id = generate_id("test_")
        print(f"✓ ID generation: {test_id}")
        
        # Test dict merging
        dict1 = {"a": 1, "b": {"c": 2}}
        dict2 = {"b": {"d": 3}, "e": 4}
        merged = merge_dicts(dict1, dict2)
        print(f"✓ Dict merging: {merged}")
        
        # Test duration formatting
        duration = format_duration(3661)  # 1 hour 1 minute 1 second
        print(f"✓ Duration formatting: {duration}")
        
        return True
        
    except Exception as e:
        print(f"✗ Helper utilities test failed: {e}")
        return False

def test_agent_structure():
    """Test that agent files exist and can be imported"""
    print("\nTesting agent structure...")
    
    try:
        # Test Bucky agent
        from agents.bucky_shopping.src.agent import BuckyAgent
        print("✓ Bucky agent imported successfully")
        
        # Test Luna agent
        from agents.luna_health.src.agent import LunaAgent
        print("✓ Luna agent imported successfully")
        
        # Test Milo agent
        from agents.milo_nutrition.src.agent import MiloAgent
        print("✓ Milo agent imported successfully")
        
        # Test Nani agent
        from agents.nani_scheduler.src.agent import NaniAgent
        print("✓ Nani agent imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Agent import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Personal Life Coordination Agents - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Logging", test_logging),
        ("A2A Protocol", test_a2a_protocol),
        ("Helper Utilities", test_helpers),
        ("Agent Structure", test_agent_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"✗ {test_name} test failed")
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to run.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
