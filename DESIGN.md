# CodeForge - Design Document

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Upload UI    │  │ Visualization│  │ Report View  │          │
│  │              │  │ (Sigma.js +  │  │              │          │
│  │              │  │  React Flow) │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   API Layer (main.py)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────┬───────────┴───────────┬──────────────────┐  │
│  │              │                       │                   │  │
│  │  CPG Builder │  Multi-Model         │  Feature Eng.     │  │
│  │              │  Orchestrator        │  (Embeddings)     │  │
│  └──────────────┘  └───────────────────┘  └───────────────┘  │
│                             │                                    │
│  ┌──────────────┬───────────┴───────────┬──────────────────┐  │
│  │              │                       │                   │  │
│  │  Clustering  │  Risk Assessment     │  Report Gen       │  │
│  │  (Louvain)   │                      │                   │  │
│  └──────────────┘  └───────────────────┘  └───────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ AWS Bedrock  │  │ PostgreSQL   │  │ LangSmith    │          │
│  │ (Claude)     │  │ + pgvector   │  │ (Tracing)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Overview

#### Frontend Components
- **Upload Interface**: File/URL input, validation
- **Progress Tracker**: Real-time analysis status with stepper
- **Graph Visualization**: Interactive Sigma.js force-directed graph
- **Tree Visualization**: React Flow hierarchical file tree
- **Service Dashboard**: Metrics and statistics
- **Report Viewer**: Markdown report display

#### Backend Components
- **API Layer**: FastAPI endpoints, request handling
- **CPG Builder**: Multi-language AST parsing with Tree-sitter
- **Graph Features**: Topological metrics (centrality, depth, fan-in/out)
- **Risk AST**: Security-focused AST profile generation
- **Multi-Model Orchestrator**: Three-role LLM pipeline (Mapper, Linker, Sentinel)
- **Feature Engineering**: TF-IDF + structural embeddings (128-dimensional)
