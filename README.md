# CodeForge

**CodeForge** is an AI-powered code analysis tool that helps developers break down monolithic applications into microservices.

## What It Does

CodeForge analyzes your codebase and provides intelligent recommendations for decomposing monoliths into microservices by:

- **Multi-Language Code Parsing** - Supports Python, JavaScript, TypeScript, Java, Go
- **AI-Powered Analysis** - Uses AWS Bedrock Claude models to understand code relationships
- **Interactive Visualization** - Shows code dependencies and suggested service boundaries
- **Risk Assessment** - Identifies potential failure points and complexity hotspots
- **Comprehensive Reports** - Provides actionable migration recommendations

## Quick Start

### 1. Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Deploy Frontend
See [DEPLOY.md](./DEPLOY.md) for deployment options (Render, Vercel, Netlify).

## Tech Stack

**Frontend:**
- React 18 + Vite
- Sigma.js (Graph visualization)
- Tailwind CSS
- Zustand (State management)

**Backend:**
- Python + FastAPI
- AWS Bedrock (Claude models)
- NetworkX (Graph analysis)
- Tree-sitter (Code parsing)

## Project Structure

```
├── frontend/          # React frontend
├── backend/           # Python FastAPI backend
├── ARCHITECTURE.md    # System architecture
├── COST_ANALYSIS.md   # AWS cost breakdown
├── QUICK_START.md     # Getting started guide
└── DEPLOY.md          # Deployment instructions
```

## License

MIT License
