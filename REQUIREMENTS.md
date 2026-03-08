# CodeForge - Requirements

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git (for repository cloning)
- 8GB RAM minimum

### Python Dependencies

Install via pip:
```bash
pip install -r backend/requirements.txt
```

Core libraries:
- **fastapi** - Web API framework
- **uvicorn** - ASGI server
- **networkx** - Graph analysis and algorithms
- **scikit-learn** - TF-IDF vectorization, clustering
- **numpy** - Numerical operations
- **boto3** - AWS Bedrock client for LLM integration
- **GitPython** - Git repository cloning
- **python-dotenv** - Environment variable management
- **langsmith** - LLM tracing and monitoring
- **aiofiles** - Async file operations
- **python-multipart** - File upload handling

### GNN Support (Optional - Not Currently Used)

The system previously used PyTorch and PyTorch Geometric for GNN-based embeddings, but has been refactored to use TF-IDF + structural features instead. If you want to add back GNN capabilities:

```bash
# CPU version
pip install torch torchvision torchaudio

# GPU version (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# PyTorch Geometric
pip install torch-geometric
```

### Database 
- **PostgreSQL 14+** with **pgvector** extension
- **sqlalchemy** - Database ORM
- **psycopg2-binary** - PostgreSQL adapter

### LLM Models

Supported provider:
- **AWS Bedrock** (Claude models via boto3)

Used models:
- Claude 3 Haiku (Mapper - fast classification)
- Claude 3 Sonnet (Linker - relation extraction)
- Claude 3 Opus (Sentinel - deep risk analysis)

### Environment Variables

Create `.env` file:
```bash
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Model IDs for Multi-Model Orchestrator
MODEL_MAPPER=anthropic.claude-3-haiku-20240307-v1:0
MODEL_LINKER=anthropic.claude-3-sonnet-20240229-v1:0
MODEL_SENTINEL=anthropic.claude-3-opus-20240229-v1:0

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/monolith

# LangSmith Tracing (optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=CodeForge
```

### Running the Application

Backend:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:
```bash
cd frontend
npm install
npm start
```

## Core Features

### 1. Code Analysis
- Multi-language AST parsing (Python, JavaScript, TypeScript, Java, Go)
- Code Property Graph (CPG) construction
- Input: ZIP upload, Git URL, or local directory

### 2. Relationship Discovery
- Static analysis (function calls, imports, inheritance)
- Multi-model LLM orchestration (Mapper, Linker, Sentinel) with AWS Bedrock
- Heuristic fallback for reliability

### 3. Feature Engineering & Embeddings
- 128-dimensional node embeddings (64 text + 64 structural)
- TF-IDF vectorization for semantic features
- Structural graph metrics (centrality, depth, fan-in/out)

### 4. Risk Assessment
- Component-level risk analysis
- Failure prediction using LLM
- Risk levels: low, medium, high

### 5. Visualization
- Interactive graph with Sigma.js (force-directed layout)
- File tree view with React Flow (hierarchical layout)
- Color-coded nodes by type and risk level
- Risk indicators (borders, glow effects)

### 6. Reports
- Markdown analysis reports
- Service recommendations
- Migration roadmap
