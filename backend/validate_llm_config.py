#!/usr/bin/env python3
"""
Validate LLM configuration without making API calls
"""

import os
from dotenv import load_dotenv

def validate_config():
    load_dotenv()
    
    print("=== LLM Configuration Validation ===")
    
    # Check environment variables
    api_key = os.getenv("LLM_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    model_name = os.getenv("LLM_MODEL") or os.getenv("MODEL_NAME") or "gpt-4-turbo"
    
    print(f"✓ API Key: {'Found (' + api_key[-4:] + ')' if api_key else '❌ Missing'}")
    print(f"✓ Endpoint: {endpoint if endpoint else '❌ Missing'}")
    print(f"✓ Model: {model_name}")
    
    # Check if all required variables are present
    if api_key and endpoint:
        print("\n✅ Configuration looks good!")
        
        # Check endpoint format
        if not endpoint.startswith('http'):
            print("⚠️  Warning: Endpoint should start with http:// or https://")
        
        # Check model compatibility
        if 'kimi' in model_name.lower():
            print("ℹ️  Using Kimi model - ensure it's available on your endpoint")
        
        return True
    else:
        print("\n❌ Configuration incomplete!")
        print("Required: AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        return False

def test_heuristic_fallback():
    """Test the heuristic relationship creation"""
    print("\n=== Testing Heuristic Fallback ===")
    
    # Import the function
    try:
        from llm_relation_discovery import create_heuristic_relationships
        
        # Sample nodes
        test_nodes = [
            {
                "id": "func1",
                "name": "authenticate",
                "type": "function",
                "file": "auth.py",
                "calls": ["validate_password"],
                "variables": ["user", "token"]
            },
            {
                "id": "func2", 
                "name": "validate_password",
                "type": "function",
                "file": "auth.py",
                "calls": [],
                "variables": ["user", "hash"]
            }
        ]
        
        edges = create_heuristic_relationships(test_nodes)
        print(f"✓ Heuristic fallback created {len(edges)} relationships")
        
        for edge in edges:
            print(f"  {edge['source']} --[{edge['type']}]--> {edge['target']}")
        
        return len(edges) > 0
        
    except Exception as e:
        print(f"❌ Heuristic fallback failed: {e}")
        return False

if __name__ == "__main__":
    config_ok = validate_config()
    heuristic_ok = test_heuristic_fallback()
    
    print(f"\n=== Summary ===")
    print(f"Configuration: {'✅' if config_ok else '❌'}")
    print(f"Heuristic Fallback: {'✅' if heuristic_ok else '❌'}")
    
    if not config_ok:
        print("\nTo fix configuration:")
        print("1. Check your .env file has AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        print("2. Verify the API key is valid")
        print("3. Ensure the endpoint URL is correct")
        print("4. Check if the model 'kimi-k2-thinking' is available on your endpoint")