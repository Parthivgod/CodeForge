# CodeForge - Design Document

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Upload UI    │  │ Visualization│  │ Report View  │          │
│  │              │  │ (React Flow) │  │              │          │
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
│  │  CPG Builder │  LLM Relation        │  GNN Pipeline     │  │
│  │              │  Discovery           │                   │  │
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
│  │ Azure OpenAI │  │ PostgreSQL   │  │ LangSmith    │          │
│  │ / OpenAI     │  │ + pgvector   │  │ (Tracing)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Overview

#### Frontend Components
- **Upload Interface**: File/URL input, validation
- **Progress Tracker**: Real-time analysis status
- **Graph Visualization**: Interactive React Flow diagram
- **Service Dashboard**: Metrics and statistics
- **Report Viewer**: Markdown/HTML report display

#### Backend Components
- **API Layer**: FastAPI endpoints, request handling
- **CPG Builder**: Multi-language AST parsing
- **Relationship Discovery**: Static + LLM analysis
- **GNN Pipeline**: Embedding generation and training.
    - **Feature Engineering**: Combines TF-IDF node semantics with structural metrics (LoC, Fan-in/out).
    - **GCN model**: A 3-layer Graph Convolutional Network that learns latent architectural representations.
    - **Self-Supervised Learning**: Model trains on graph reconstruction to capture structural context.
