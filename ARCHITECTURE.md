# CodeForge Architecture & Connectivity

## System Overview

CodeForge is a full-stack application for analyzing monolithic codebases using AI-powered graph analysis. The system consists of a FastAPI backend and a React frontend.

---

## Backend Architecture

### Core Pipeline Flow

```
User Upload → main.py → Pipeline Orchestration
                ↓
    1. CPG Builder (cpg_builder.py)
                ↓
    2. Graph Features (graph_features.py)
                ↓
    3. Risk AST Builder (risk_ast.py)
                ↓
    4. Multi-Model Orchestrator (orchestrator.py)
                ↓
    5. Feature Engineering (feature_engineering.py)
                ↓
    6. Results Formatting → Frontend
```

---

## Component Details

### 1. **main.py** - API Gateway & Pipeline Orchestrator
**Role**: FastAPI application that exposes REST endpoints and orchestrates the analysis pipeline

**Key Endpoints**:
- `POST /analyze` - Upload code (ZIP or Git URL) and start analysis
- `GET /status/{job_id}` - Poll analysis progress
- `GET /results/{job_id}` - Retrieve complete analysis results
- `GET /tree/{job_id}` - Get React Flow formatted graph data
- `GET /report/{job_id}` - Get markdown report

**Pipeline Steps**:
1. Build CPG (Code Property Graph)
2. Build Risk AST Profiles
3. Multi-Model AI Analysis
4. Generate Embeddings
5. Compute Statistics
6. Generate Report
7. Format for Frontend

**Dependencies**:
```python
from cpg_builder import build_cpg
from orchestrator import discover_relations_orchestrated
from risk_ast import build_risk_ast
from feature_engineering import generate_embeddings
```

---

### 2. **cpg_builder.py** - Code Property Graph Builder
**Role**: Parses source code files and builds an initial graph representation

**Key Functions**:
- `build_cpg(path, job_id)` - Main entry point
- `parse_file(filepath)` - Parse individual files using Tree-sitter
- `build_edges(nodes, symbols)` - Create relationships between nodes
- `detect_language(filepath)` - Auto-detect programming language

**Output**:
```python
{
    "nodes": [...],      # List of code entities (functions, classes, etc.)
    "edges": [...],      # Initial relationships (calls, contains, etc.)
    "nx_graph": G        # NetworkX DiGraph object
}
```

**Integration with graph_features.py**:
```python
from graph_features import compute_graph_features
G = compute_graph_features(G)  # Enriches nodes with topological metrics
```

---

### 3. **graph_features.py** - Graph Feature Engineering
**Role**: Computes topological and structural features for each node in the graph

**Key Function**:
- `compute_graph_features(G: nx.DiGraph) -> nx.DiGraph`

**Features Computed**:
- **Degree Metrics**: fan_in, fan_out, total_degree
- **Centrality**: betweenness_centrality (approximated for large graphs)
- **Entry Points**: Identifies main functions, API endpoints
- **Security Heuristics**: Sources (env access, file I/O) and sinks (eval, shell calls)
- **Depth Analysis**: Distance from entry points
- **Reachability**: Counts of reachable sources/sinks

**Node Attributes Added**:
```python
{
    'fan_in': int,
    'fan_out': int,
    'total_degree': int,
    'betweenness_centrality': float,
    'depth_from_entry': int,
    'reachable_sink_count': int,
    'reachable_source_count': int,
    'num_api_calls': int
}
```

---

### 4. **risk_ast.py** - Risk AST Profile Builder
**Role**: Generates security-focused abstract syntax tree profiles for functions

**Key Function**:
- `build_risk_ast(nodes, edges) -> Dict[str, Dict]`

**Risk Profile Structure**:
```python
{
    "node_id": "func_123",
    "risk_profile": {
        "sources": ["env", "file"],           # Data sources
        "sinks": ["eval", "shell"],           # Dangerous operations
        "entry": bool,                        # Is entry point?
        "external_interactions": [...],       # API calls
        "control_flags": {
            "has_conditional": bool,
            "has_loop": bool,
            "has_try_catch": bool,
            "has_async_await": bool
        },
        "data_flow_neighbors": [...],         # Intra-function data flow
        "call_neighbors": [...]               # Functions called
    }
}
```

**Integration**: Risk profiles are merged into nodes in main.py:
```python
if node['id'] in risk_profiles:
    node['risk_ast'] = risk_profiles[node['id']]['risk_profile']
```

---

### 5. **orchestrator.py** - Multi-Model AI Orchestrator
**Role**: Routes nodes through a 3-role LLM analysis pipeline using AWS Bedrock

**Architecture**:
```
Mapper: Node Classifier (Fast Triage)
    ↓
Linker: Relation Extractor (Semantic Topology)
    ↓
Sentinel: Deep Risk Analyzer (Security Reasoning)
```

**Key Function**:
- `discover_relations_orchestrated(nodes) -> Dict`

**Output**:
```python
{
    "edges": [...],           # Semantic relationships discovered by LLMs
    "node_updates": {         # Enriched metadata for each node
        "node_id": {
            "risk_level": "low|medium|high|critical",
            "risk_tier": 0-3,
            "classification": "...",
            "architectural_role": "...",
            "risk_analysis": {...},
            "confidence_score": float
        }
    }
}
```

**Risk Tiers**:
- **Tier 0**: Trivial (imports, constants) - Skip deep analysis
- **Tier 1**: Low-risk (pure functions) - Lightweight analysis
- **Tier 2**: Moderate-risk (business logic, APIs) - Full analysis
- **Tier 3**: High-risk (auth, crypto, PII) - Deep security analysis

**Models Used** (configured via .env):
- `MODEL_MAPPER`: Fast classifier
- `MODEL_LINKER`: Relation extractor
- `MODEL_SENTINEL`: Deep risk analyzer

---

### 6. **feature_engineering.py** - Embedding Generation
**Role**: Generates numerical embeddings for nodes using TF-IDF and structural features

**Key Functions**:
- `prepare_initial_features(nodes) -> np.ndarray`
- `generate_embeddings(nodes) -> List[Dict]`

**Feature Components**:
1. **Text Features (TF-IDF)**: 64-dimensional vectors from node names and variables
2. **Structural Features**: 13-dimensional vectors including:
   - Topology metrics (fan_in, fan_out, centrality)
   - Node type flags (is_function, is_class, is_api)
   - Security flags (has_auth_logic)

**Output**: Each node gets a 128-dimensional embedding vector:
```python
node['embedding'] = [0.1, 0.2, ..., 0.5]  # 128 floats
```

**Note**: This replaces the old GNN-based approach with a simpler, dependency-free solution.

---

### 7. **models.py** - Database Models
**Role**: SQLAlchemy models for persistent storage (currently unused in main pipeline)

**Models**:
- `CodeGraph`: Stores code graph metadata
- `NodeEmbeddings`: Stores node embeddings with pgvector
- `Clusters`: Stores clustering results

---

## Frontend Architecture

### Component Hierarchy

```
App.jsx (Main Container)
    ├── HeroSection.jsx (Landing Page)
    ├── HowItWorks.jsx (How It Works Section)
    ├── Footer.jsx (Footer)
    ├── UploadZone.jsx (File/Git Upload)
    ├── AnalysisStepper.jsx (Progress Indicator)
    └── ResultsDashboard.jsx (Results Display)
        ├── MetricsCards.jsx (Statistics)
        ├── ActionBar.jsx (Controls)
        ├── TreeExplorer.jsx (File Tree with React Flow)
        └── GraphExplorer/ (Graph Visualization with Sigma.js)
            ├── GraphExplorer.jsx (Container)
            ├── SigmaRenderer.jsx (Sigma.js Rendering)
            ├── FilterToolbar.jsx (Filters)
            └── NodeDetailPanel.jsx (Node Details)
```

---

## Frontend-Backend Connectivity

### API Client (api.js)

```javascript
// Base URL
const API_Base = 'http://localhost:8000';

// API Functions
analyzeMonolith(fileOrUrl)  → POST /analyze
getStatus(jobId)            → GET /status/{jobId}
getTree(jobId)              → GET /tree/{jobId}
getReport(jobId)            → GET /report/{jobId}
getResults(jobId)           → GET /results/{jobId}
```

### Data Flow

1. **User uploads code** → `analyzeMonolith()` → Backend starts pipeline
2. **Frontend polls status** → `getStatus()` every 2 seconds
3. **Pipeline completes** → Status = "Done"
4. **Frontend fetches results** → `getResults()` → Display dashboard

### Results Structure

```javascript
{
    nodes: [...],           // Code entities with risk analysis
    edges: [...],           // Relationships
    report: "...",          // Markdown report
    stats: {                // Summary statistics
        services: "N/A",
        loc: "10k",
        nodes: 150,
        edges: 200,
        reduction: "1.0x",
        confidence: "94%"
    },
    tree_data: {            // React Flow formatted data
        nodes: [...],       // Styled nodes with positions
        edges: [...]        // Styled edges with animations
    }
}
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  (React + Vite + TailwindCSS + React Flow + Sigma.js)       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST API
                     │ (JSON)
┌────────────────────▼────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                        main.py                               │
└─┬──────────┬──────────┬──────────┬──────────┬──────────────┘
  │          │          │          │          │
  │          │          │          │          │
┌─▼──────┐ ┌▼────────┐ ┌▼────────┐ ┌▼────────┐ ┌▼─────────────┐
│ CPG    │ │ Graph   │ │ Risk    │ │Orchestr.│ │ Feature      │
│Builder │→│Features │→│AST      │→│(LLMs)   │→│Engineering   │
└────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────────┘
    │           │           │           │              │
    └───────────┴───────────┴───────────┴──────────────┘
                            │
                    ┌───────▼────────┐
                    │  Results JSON  │
                    │  (nodes+edges) │
                    └────────────────┘
```

---

## Key Integration Points

### 1. CPG Builder → Graph Features
```python
# In cpg_builder.py
from graph_features import compute_graph_features
G = compute_graph_features(G)
```
**Purpose**: Enrich nodes with topological metrics before LLM analysis

### 2. Main Pipeline → Risk AST
```python
# In main.py
from risk_ast import build_risk_ast
risk_profiles = build_risk_ast(nodes, initial_edges)
```
**Purpose**: Generate security profiles for each function

### 3. Main Pipeline → Orchestrator
```python
# In main.py
from orchestrator import discover_relations_orchestrated
llm_result = discover_relations_orchestrated(nodes)
```
**Purpose**: Perform multi-model AI analysis for risk and relationships

### 4. Main Pipeline → Feature Engineering
```python
# In main.py
from feature_engineering import generate_embeddings
nodes = generate_embeddings(nodes)
```
**Purpose**: Generate embeddings for future ML features

### 5. Backend → Frontend
```python
# In main.py
tree_data = format_for_react_flow(nodes, all_edges)
JOB_RESULTS[job_id] = {
    "nodes": nodes,
    "edges": all_edges,
    "tree_data": tree_data,
    ...
}
```
**Purpose**: Format data for React Flow visualization

---

## Configuration

### Environment Variables (.env)

```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Model IDs for Multi-Model Orchestrator
MODEL_MAPPER=anthropic.claude-3-haiku-20240307-v1:0
MODEL_LINKER=anthropic.claude-3-sonnet-20240229-v1:0
MODEL_SENTINEL=anthropic.claude-3-opus-20240229-v1:0

# LangSmith (Optional)
LANGCHAIN_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=CodeForge
```

---

## Removed Components

### gnn_pipeline.py (REMOVED)
**Reason**: GNN dependencies (PyTorch, PyTorch Geometric) were heavy and optional

**Functionality Split Into**:
1. **risk_ast.py**: Risk AST profile generation
2. **feature_engineering.py**: Embedding generation without GNN

**Migration**:
- `build_risk_ast()` → Moved to `risk_ast.py`
- `generate_embeddings()` → Simplified version in `feature_engineering.py`
- `prepare_initial_features()` → Moved to `feature_engineering.py`
- GNN model training → Removed (can be added back as optional feature)

---

## Testing the System

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full Stack
```bash
docker-compose up
```

---

## Future Enhancements

1. **Database Integration**: Use models.py for persistent storage
2. **Clustering**: Implement clustering.py for microservice boundary detection
3. **Advanced GNN**: Optional GNN module for enhanced embeddings
4. **Real-time Updates**: WebSocket support for live progress updates
5. **Multi-language Support**: Expand Tree-sitter parsers

---

## Summary

The system follows a clear pipeline:
1. **Parse** code into CPG (cpg_builder.py)
2. **Enrich** with graph features (graph_features.py)
3. **Analyze** security risks (risk_ast.py)
4. **Reason** with LLMs (orchestrator.py)
5. **Embed** for ML (feature_engineering.py)
6. **Visualize** in frontend (React Flow + Sigma.js)

All components are loosely coupled through well-defined interfaces, making the system maintainable and extensible.
