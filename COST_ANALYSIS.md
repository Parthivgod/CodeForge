# CodeForge Cost Analysis

## AWS Bedrock Pricing (Per 1M Tokens)

| Model | Role | Input Cost | Output Cost |
|-------|------|------------|-------------|
| GPT-OSS-120B | Mapper | $0.15 | $0.60 |
| Amazon Nova Pro | Linker | $0.80 | $3.20 |
| DeepSeek R1 | Sentinel | $1.35 | $5.40 |

## Cost Breakdown by Role

### Mapper (Fast Classification)
- **Purpose**: Quick triage and tier assignment
- **Model**: GPT-OSS-120B (fastest, cheapest)
- **Batch Size**: 30 nodes
- **Average Tokens**: ~2,000 input, ~500 output per batch
- **Cost per 1K nodes**: ~$0.02

### Linker (Relation Extraction)
- **Purpose**: Semantic relationship discovery
- **Model**: Amazon Nova Pro (balanced)
- **Batch Size**: 8 nodes (reduced to avoid truncation)
- **Average Tokens**: ~3,000 input, ~800 output per batch
- **Cost per 1K nodes**: ~$0.16

### Sentinel (Deep Risk Analysis)
- **Purpose**: Security and stability reasoning
- **Model**: DeepSeek R1 (most capable for reasoning)
- **Selective**: Only analyzes Tier 2-3 nodes (~10% of codebase)
- **Average Tokens**: ~4,000 input, ~1,200 output per node
- **Cost per 1K nodes**: ~$1.19

## Estimated Costs by Codebase Size

| Nodes | Mapper | Linker | Sentinel | **Total** |
|-------|--------|--------|----------|-----------|
| 50 | $0.0006 | $0.0050 | $0.0594 | **$0.07** |
| 100 | $0.0018 | $0.0149 | $0.1188 | **$0.14** |
| 200 | $0.0036 | $0.0298 | $0.2376 | **$0.27** |
| 500 | $0.0096 | $0.0794 | $0.5940 | **$0.68** |
| 1000 | $0.0198 | $0.1637 | $1.1880 | **$1.37** |

## Cost Optimization Strategies

### 1. Tier-Based Processing
- **Tier 0** (Trivial): Skip LLM analysis entirely
- **Tier 1** (Low-risk): Mapper only
- **Tier 2** (Moderate): Mapper + Linker
- **Tier 3** (High-risk): Full pipeline (Mapper + Linker + Sentinel)

This reduces costs by ~60% compared to analyzing all nodes with all models.

### 2. Batch Processing
- Mapper and Linker process nodes in batches
- Reduces API calls and overhead
- Batch sizes optimized for model context windows

### 3. Caching
- Results cached by job ID
- Re-analysis of same codebase uses cached results
- Reduces redundant API calls

### 4. Heuristic Fallback
- If LLM analysis fails, use static analysis
- Ensures reliability without additional cost
- Fallback edges marked with lower confidence

## Real-World Example

**Recent Analysis Run:**
- **Nodes Analyzed**: ~150 nodes
- **Total Calls**: 40 LLM calls
- **Total Tokens**: 154,027 tokens (108K input + 46K output)
- **Total Cost**: $0.18
- **Average per Call**: $0.0046

**Breakdown:**
- Mapper: 5 calls, $0.01
- Linker: 11 calls, $0.09
- Sentinel: 24 calls, $0.08

## Cost Monitoring

Run the cost analysis script to see your actual usage:

```bash
cd backend
python analyze_costs.py
```

This will:
- Parse `token_usage.txt` log file
- Calculate costs based on current pricing
- Show breakdown by role
- Provide estimates for different codebase sizes

## Tips for Reducing Costs

1. **Filter before analysis**: Remove test files, generated code, and vendor dependencies
2. **Use smaller batches**: For very large codebases, analyze incrementally
3. **Adjust tier thresholds**: Tune the risk tier assignment to reduce Sentinel usage
4. **Cache aggressively**: Reuse results when possible
5. **Monitor token usage**: Check `token_usage.txt` regularly

## Comparison with Alternatives

| Approach | Cost per 1K Nodes | Accuracy | Speed |
|----------|-------------------|----------|-------|
| **CodeForge (Multi-Model)** | $1.37 | High | Fast |
| Single Model (GPT-4) | $2.50 | Medium | Medium |
| Static Analysis Only | $0 | Low | Very Fast |
| Manual Review | $500+ | High | Very Slow |

CodeForge provides the best balance of cost, accuracy, and speed for automated code analysis.
