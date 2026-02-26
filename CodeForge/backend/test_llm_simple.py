#!/usr/bin/env python3
"""
Simple test for LLM connection
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_llm_connection():
    api_key = os.getenv("GROQ_API_KEY")
    endpoint = os.getenv("GROQ_BASE_URL")
    model_name = os.getenv("LLM_MODEL") or "openai/gpt-oss-120b"
    
    print(f"API Key: {'***' + api_key[-4:] if api_key else 'None'}")
    print(f"Endpoint: {endpoint}")
    print(f"Model: {model_name}")
    
    if not api_key:
        print("ERROR: No API key found")
        return
    
    try:
        client = OpenAI(
            base_url=endpoint,
            api_key=api_key
        )
        
        print("\nTesting simple completion...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "Hello, respond with just 'OK' if you can hear me."}
            ],
            timeout=30  # 30 second timeout
        )
        
        print(f"Response: {response.choices[0].message.content}")
        print("✅ LLM connection successful!")
        
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_connection()