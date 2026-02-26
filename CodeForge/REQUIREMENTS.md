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
- **openai** - LLM API client
- **GitPython** - Git repository cloning
- **python-dotenv** - Environment variable management
- **langsmith** - LLM tracing and monitoring
- **aiofiles** - Async file operations
- **python-multipart** - File upload handling

### GNN Support
- **torch** - PyTorch deep learning framework
- **torch-geometric** - Graph neural network library

Install PyTorch:
```bash
# CPU version
pip install torch torchvision torchaudio

# GPU version (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Install PyTorch Geometric:
```bash
pip install torch-geometric
```

### Database 
- **PostgreSQL 14+** with **pgvector** extension
- **sqlalchemy** - Database ORM
- **psycopg2-binary** - PostgreSQL adapter

### LLM Models

Supported providers:
- **Azure OpenAI** (recommended)
- **OpenAI API**
- **Compatible APIs** (OpenRouter, local models)

Used models:

kimi-k2-thinking

### Environment Variables

Create `.env` file:
```bash
# LLM Configuration
LLM_MODEL=kimi-k2-thinking
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your-api-key

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
- LLM-enhanced semantic analysis (logical coupling, patterns)
- Heuristic fallback for reliability

### 3. GNN Embeddings 
- 128-dimensional node embeddings
- Graph Convolutional Networks (GCN)
- Self-supervised training

### 4. Risk Assessment
- Component-level risk analysis
- Failure prediction using LLM
- Risk levels: low, medium, high

### 5. Visualization
- Interactive graph with React Flow
- Color-coded nodes by type
- Risk indicators (borders, glow effects)

### 6. Reports
- Markdown analysis reports
- Service recommendations
- Migration roadmap
