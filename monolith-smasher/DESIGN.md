# Monolith Smasher - Design Document

## System Overview

Monolith Smasher analyzes codebases to identify microservice boundaries using AI and graph analysis.

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Frontend (React)                      │
│  Upload → Visualization → Reports               │
└──────────────────┬──────────────────────────────┘
                   │ REST API
┌──────────────────┴──────────────────────────────┐
│           Backend (FastAPI)                     │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  1. CPG Builder (AST Parsing)            │  │
│  │  2. LLM Relation Discovery               │  │
│  │  3. GNN Embeddings (Optional)            │  │
│  │  4. Risk Assessment                      │  │
│  │  5. Report Generation                    │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│  External: Azure OpenAI, LangSmith, PostgreSQL  │
└─────────────────────────────────────────────────┘
```

## Pipeline Flow

1. **Code Parsing** → Parse AST, extract nodes (functions, classes) and edges (calls, imports)
2. **LLM Analysis** → Discover semantic relationships and assess risk using GPT-4
3. **GNN Embeddings** → Generate 128-dim vectors (optional, requires PyTorch)
4. **Graph Analysis** → Merge edges, validate, calculate statistics
5. **Report Generation** → Create markdown report with recommendations

## Key Components

**cpg_builder.py** - Parse code (Python, JS, TS, Java, Go) and build graph  
**llm_relation_discovery.py** - Find relationships using LLM (batch size: 30 nodes)  
**gnn_pipeline.py** - Generate embeddings with 3-layer GCN  
**main.py** - FastAPI endpoints and pipeline orchestration

## API Endpoints

- `POST /analyze` - Start analysis (file or repo_url)
- `GET /status/{job_id}` - Check progress
- `GET /tree/{job_id}` - Get React Flow graph
- `GET /results/{job_id}` - Get full results
- `GET /report/{job_id}` - Get markdown report              