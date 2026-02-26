#!/usr/bin/env python3
"""
Test script for LLM relation discovery
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from llm_relation_discovery import discover_relations_llm

# Sample nodes for testing
test_nodes = [
    {
        "id": "user_service.authenticate",
        "name": "authenticate",
        "type": "function",
        "file": "services/user_service.py",
        "line_start": 15,
        "calls": ["validate_password", "generate_token"],
        "api_calls": ["api_user_service_authenticate_post_25"],
        "variables": ["user", "password", "token"],
        "parameters": ["username", "password"],
        "parent_class": None
    },
    {
        "id": "user_service.validate_password",
        "name": "validate_password",
        "type": "function",
        "file": "services/user_service.py",
        "line_start": 45,
        "calls": ["hash_password"],
        "api_calls": [],
        "variables": ["hashed", "salt"],
        "parameters": ["password", "stored_hash"],
        "parent_class": None
    },
    {
        "id": "auth_controller.login",
        "name": "login",
        "type": "function",
        "file": "controllers/auth_controller.py",
        "line_start": 20,
        "calls": ["authenticate", "create_session"],
        "api_calls": ["api_auth_controller_login_post_22"],
        "variables": ["user", "session"],
        "parameters": ["request"],
        "parent_class": None
    },
    {
        "id": "session_manager.create_session",
        "name": "create_session",
        "type": "function",
        "file": "utils/session_manager.py",
        "line_start": 10,
        "calls": ["generate_session_id"],
        "api_calls": [],
        "variables": ["session_id", "user_id"],
        "parameters": ["user_id"],
        "parent_class": None
    },
    {
        "id": "UserModel",
        "name": "UserModel",
        "type": "class",
        "file": "models/user.py",
        "line_start": 5,
        "calls": [],
        "api_calls": [],
        "variables": [],
        "parameters": [],
        "inherits": ["BaseModel"],
        "parent_class": None
    }
]

def main():
    print("Testing LLM Relation Discovery...")
    print(f"Testing with {len(test_nodes)} sample nodes")
    
    # Test environment variables first
    api_key = os.getenv("GROQ_API_KEY")
    endpoint = os.getenv("GROQ_BASE_URL")
    model_name = os.getenv("LLM_MODEL") or "openai/gpt-oss-120b"
    
    print(f"API Key: {'***' + api_key[-4:] if api_key else 'None'}")
    print(f"Endpoint: {endpoint}")
    print(f"Model: {model_name}")
    
    try:
        result = discover_relations_llm(test_nodes)
        
        print(f"\n=== RESULTS ===")
        print(f"Discovered {len(result.get('edges', []))} relationships:")
        
        for edge in result.get('edges', []):
            print(f"  {edge.get('source')} --[{edge.get('type')}]--> {edge.get('target')}")
            if edge.get('description'):
                print(f"    Description: {edge.get('description')}")
            if edge.get('confidence'):
                print(f"    Confidence: {edge.get('confidence')}")
        
        print(f"\nRisk Analysis for {len(result.get('node_updates', {}))} nodes:")
        for node_id, risk_info in result.get('node_updates', {}).items():
            print(f"  {node_id}: {risk_info.get('risk_level')} - {risk_info.get('failure_reason')}")
            
        # Test success
        if len(result.get('edges', [])) > 0:
            print("\n✅ LLM relation discovery working!")
        else:
            print("\n⚠️  No relationships found - check LLM connectivity")
            
    except Exception as e:
        print(f"❌ Error testing LLM: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()