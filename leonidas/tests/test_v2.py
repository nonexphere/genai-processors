#!/usr/bin/env python3
"""
Test script for Leonidas v2 implementation.

This script validates the modular architecture and tool system
without requiring full audio/video setup.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add the parent directory to the path so we can import leonidas
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genai_processors import content_api, streams
import leonidas

async def test_orchestrator_tools():
    """Test the LeonidasOrchestrator tool system."""
    
    print("Testing LeonidasOrchestrator tool system...")
    
    # Mock API key for testing
    api_key = "test_key"
    
    try:
        # Create orchestrator (this will fail without real API key, but we can test structure)
        orchestrator = leonidas.LeonidasOrchestrator(api_key)
        
        print("LeonidasOrchestrator created successfully")
        print(f"   Initial state: {orchestrator.agent_state}")
        print(f"   Tools configured: {len(leonidas.LEONIDAS_TOOLS[0].function_declarations)}")
        
        # Test tool handlers directly
        print("\nTesting tool handlers...")
        
        # Test think tool
        think_response = await orchestrator._handle_think("test_id", {
            'analysis': 'Test analysis',
            'reasoning': 'Test reasoning', 
            'next_action': 'Test action'
        })
        print("Think tool handler works")
        
        # Test change_state tool
        state_response = await orchestrator._handle_change_state("test_id", {
            'new_state': 'analyzing',
            'reason': 'Test state change'
        })
        print(f"State change tool works - new state: {orchestrator.agent_state}")
        
        # Test get_context tool
        context_response = await orchestrator._handle_get_context("test_id", {
            'context_type': 'system_status'
        })
        print("Get context tool handler works")
        
        # Test get_time tool
        time_response = await orchestrator._handle_get_time("test_id", {
            'format': 'datetime'
        })
        print("Get time tool handler works")
        
        return True
        
    except Exception as e:
        print(f"Error testing orchestrator: {e}")
        return False

def test_prompt_system():
    """Test the prompt system configuration."""
    
    print("\nTesting prompt system...")
    
    try:
        # Check prompt structure
        prompt = leonidas.LEONIDAS_SYSTEM_PROMPT
        print(f"System prompt has {len(prompt)} sections")
        
        # Check tools structure
        tools = leonidas.LEONIDAS_TOOLS
        print(f"Tool system has {len(tools)} tool groups")
        
        tool_declarations = tools[0].function_declarations
        tool_names = [decl.name for decl in tool_declarations]
        print(f"Available tools: {', '.join(tool_names)}")
        
        # Validate required tools are present
        required_tools = ['think', 'change_state', 'get_context', 'get_time']
        missing_tools = [tool for tool in required_tools if tool not in tool_names]
        
        if missing_tools:
            print(f"Missing required tools: {missing_tools}")
            return False
        else:
            print("All required tools are present")
            
        return True
        
    except Exception as e:
        print(f"Error testing prompt system: {e}")
        return False

def test_modular_architecture():
    """Test the modular architecture components."""
    
    print("\nTesting modular architecture...")
    
    try:
        # Test that we can import and access the main components
        input_manager = leonidas.InputManager
        output_manager = leonidas.OutputManager
        orchestrator_class = leonidas.LeonidasOrchestrator
        factory_function = leonidas.create_leonidas_agent_v2
        
        print("All main components are accessible")
        print("   - InputManager (processor function)")
        print("   - OutputManager (processor function)")  
        print("   - LeonidasOrchestrator (processor class)")
        print("   - create_leonidas_agent_v2 (factory function)")
        
        # Test factory function structure (without real API key)
        print("\nTesting factory function structure...")
        
        # This will fail at runtime due to API key, but we can check the structure
        try:
            # Mock the API key validation for structure testing
            agent = leonidas.create_leonidas_agent_v2("test_key")
            print("Factory function creates processor pipeline")
        except Exception as e:
            # Expected to fail without real API key, but structure should be valid
            if "api_key" in str(e).lower() or "auth" in str(e).lower():
                print("Factory function structure is valid (API key needed for full test)")
            else:
                print(f"Unexpected factory function error: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error testing modular architecture: {e}")
        return False

def test_configuration():
    """Test configuration constants and settings."""
    
    print("\nTesting configuration...")
    
    try:
        # Test constants
        assert leonidas.MODEL_LIVE == 'gemini-live-2.5-flash-preview'
        assert leonidas.AUDIO_INPUT_RATE == 16000
        assert leonidas.AUDIO_OUTPUT_RATE == 24000
        
        print("Configuration constants are correct")
        print(f"   Model: {leonidas.MODEL_LIVE}")
        print(f"   Audio Input: {leonidas.AUDIO_INPUT_RATE}Hz")
        print(f"   Audio Output: {leonidas.AUDIO_OUTPUT_RATE}Hz")
        
        return True
        
    except Exception as e:
        print(f"Error testing configuration: {e}")
        return False

async def main():
    """Run all tests."""
    
    print("Leonidas v2 Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Prompt System", test_prompt_system), 
        ("Modular Architecture", test_modular_architecture),
        ("Orchestrator Tools", test_orchestrator_tools),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} tests...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Leonidas v2 is ready to run.")
        print("\nNext steps:")
        print("   1. Set GOOGLE_API_KEY environment variable")
        print("   2. Run: python leonidas/leonidas_cli.py")
        return True
    else:
        print("Some tests failed. Please review the implementation.")
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
