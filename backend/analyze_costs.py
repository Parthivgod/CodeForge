"""
Cost Analysis Utility for AWS Bedrock Token Usage

This script analyzes token_usage.txt and calculates costs based on AWS Bedrock pricing.

AWS Bedrock Model Pricing (per 1M tokens):
- Mapper (GPT-OSS-120B):  $0.15 input, $0.60 output
- Linker (Nova Pro):      $0.80 input, $3.20 output  
- Sentinel (DeepSeek R1): $1.35 input, $5.40 output
"""

import os
from datetime import datetime
from collections import defaultdict

# Pricing per 1M tokens (USD) - Updated pricing
PRICING = {
    "gpt-oss": {"input": 0.15, "output": 0.60},
    "nova-pro": {"input": 0.80, "output": 3.20},
    "deepseek-r1": {"input": 1.35, "output": 5.40},
}

def get_model_type(model_id: str) -> str:
    """Extract model type from model ID."""
    model_lower = model_id.lower()
    if "gpt-oss" in model_lower or "openai" in model_lower:
        return "gpt-oss"
    elif "nova" in model_lower:
        return "nova-pro"
    elif "deepseek" in model_lower or "r1" in model_lower:
        return "deepseek-r1"
    return "unknown"

def analyze_token_usage(log_file: str = "token_usage.txt"):
    """Analyze token usage and calculate costs."""
    if not os.path.exists(log_file):
        print(f"❌ Token log file not found: {log_file}")
        return
    
    stats = defaultdict(lambda: {"input": 0, "output": 0, "calls": 0})
    total_input = 0
    total_output = 0
    total_calls = 0
    
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                # Parse: [timestamp] role=X | model=Y | input=A | output=B | total=C
                parts = line.split("|")
                if len(parts) < 3:
                    continue
                
                # Extract role
                role_part = parts[0].split("]")[1].strip()
                role = role_part.split("=")[1].strip()
                
                # Extract model
                model_part = parts[1].strip()
                model_id = model_part.split("=")[1].strip()
                
                # Extract tokens
                input_part = parts[2].strip()
                input_tokens = int(input_part.split("=")[1].strip())
                
                output_part = parts[3].strip()
                output_tokens = int(output_part.split("=")[1].strip())
                
                # Aggregate by role
                stats[role]["input"] += input_tokens
                stats[role]["output"] += output_tokens
                stats[role]["calls"] += 1
                
                total_input += input_tokens
                total_output += output_tokens
                total_calls += 1
                
            except Exception as e:
                print(f"⚠️  Skipping malformed line: {line[:50]}...")
                continue
    
    # Calculate costs
    print("\n" + "="*70)
    print("📊 AWS BEDROCK TOKEN USAGE & COST ANALYSIS")
    print("="*70)
    
    total_cost = 0.0
    
    for role, data in sorted(stats.items()):
        input_tokens = data["input"]
        output_tokens = data["output"]
        calls = data["calls"]
        
        # Determine model type (assume based on role)
        if "Mapper" in role:
            model_type = "gpt-oss"
        elif "Linker" in role or "linker" in role:
            model_type = "nova-pro"
        elif "Sentinel" in role or "sentinel" in role:
            model_type = "deepseek-r1"
        else:
            model_type = "nova-pro"  # default
        
        pricing = PRICING[model_type]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        role_cost = input_cost + output_cost
        total_cost += role_cost
        
        print(f"\n🤖 {role} ({model_type.upper()})")
        print(f"   Calls:        {calls:,}")
        print(f"   Input:        {input_tokens:,} tokens (${input_cost:.4f})")
        print(f"   Output:       {output_tokens:,} tokens (${output_cost:.4f})")
        print(f"   Subtotal:     ${role_cost:.4f}")
    
    print("\n" + "-"*70)
    print(f"📈 TOTAL")
    print(f"   Total Calls:  {total_calls:,}")
    print(f"   Total Input:  {total_input:,} tokens")
    print(f"   Total Output: {total_output:,} tokens")
    print(f"   Total Tokens: {total_input + total_output:,}")
    print(f"   💰 TOTAL COST: ${total_cost:.4f}")
    print("="*70 + "\n")
    
    # Cost per analysis (if we can estimate)
    if total_calls > 0:
        avg_cost_per_call = total_cost / total_calls
        print(f"📊 Average cost per LLM call: ${avg_cost_per_call:.4f}")
    
    return {
        "total_cost": total_cost,
        "total_input": total_input,
        "total_output": total_output,
        "total_calls": total_calls,
        "by_role": dict(stats)
    }

def estimate_analysis_cost(num_nodes: int) -> dict:
    """Estimate cost for analyzing a codebase with N nodes."""
    # Rough estimates based on typical usage
    mapper_calls = num_nodes // 30  # Batch size 30
    linker_calls = num_nodes // 30
    sentinel_calls = num_nodes // 10  # Only high-risk nodes
    
    # Average tokens per call (estimated)
    mapper_input_avg = 2000
    mapper_output_avg = 500
    linker_input_avg = 3000
    linker_output_avg = 800
    sentinel_input_avg = 4000
    sentinel_output_avg = 1200
    
    # Calculate costs with updated pricing
    mapper_cost = (
        (mapper_calls * mapper_input_avg / 1_000_000) * PRICING["gpt-oss"]["input"] +
        (mapper_calls * mapper_output_avg / 1_000_000) * PRICING["gpt-oss"]["output"]
    )
    
    linker_cost = (
        (linker_calls * linker_input_avg / 1_000_000) * PRICING["nova-pro"]["input"] +
        (linker_calls * linker_output_avg / 1_000_000) * PRICING["nova-pro"]["output"]
    )
    
    sentinel_cost = (
        (sentinel_calls * sentinel_input_avg / 1_000_000) * PRICING["deepseek-r1"]["input"] +
        (sentinel_calls * sentinel_output_avg / 1_000_000) * PRICING["deepseek-r1"]["output"]
    )
    
    total_cost = mapper_cost + linker_cost + sentinel_cost
    
    print(f"\n💡 ESTIMATED COST FOR {num_nodes} NODES")
    print(f"   Mapper (GPT-OSS):      ${mapper_cost:.4f}")
    print(f"   Linker (Nova Pro):     ${linker_cost:.4f}")
    print(f"   Sentinel (DeepSeek):   ${sentinel_cost:.4f}")
    print(f"   💰 TOTAL ESTIMATE:     ${total_cost:.4f}\n")
    
    return {
        "num_nodes": num_nodes,
        "mapper_cost": mapper_cost,
        "linker_cost": linker_cost,
        "sentinel_cost": sentinel_cost,
        "total_cost": total_cost
    }

if __name__ == "__main__":
    import sys
    
    # Analyze existing usage
    log_file = os.path.join(os.path.dirname(__file__), "token_usage.txt")
    
    if os.path.exists(log_file):
        print("📁 Analyzing existing token usage log...")
        analyze_token_usage(log_file)
    else:
        print("⚠️  No token usage log found. Showing cost estimates only.\n")
    
    # Show estimates for different codebase sizes
    print("\n" + "="*70)
    print("📊 COST ESTIMATES BY CODEBASE SIZE")
    print("="*70)
    
    for size in [50, 100, 200, 500, 1000]:
        estimate_analysis_cost(size)
