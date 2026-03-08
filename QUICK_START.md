# CodeForge Quick Start Guide

## 🎯 What Changed?

### Before Refactoring
```
gnn_pipeline.py (REMOVED)
├─ GNN model training (PyTorch)
├─ build_risk_ast()
├─ generate_embeddings()
└─ prepare_initial_features()
```

### After Refactoring
```
risk_ast.py (NEW)
└─ build_risk_ast()

feature_engineering.py (NEW)
├─ generate_embeddings()
└─ prepare_initial_features()
```

**Result**: Cleaner, modular, no heavy GNN dependencies!

---

## 🚀 Quick Start

### 1. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `backend/.env`:
```bash
# AWS Bedrock (for LLM analysis)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1

# Model IDs
MODEL_MAPPER=anthropic.claude-3-haiku-20240307-v1:0
MODEL_LINKER=anthropic.claude-3-sonnet-20240229-v1:0
MODEL_SENTINEL=anthropic.claude-3-opus-20240229-v1:0
```

### 3. Test Connectivity

```bash
cd backend
python test_connectivity.py
```

Expected output:
```
✓ cpg_builder imported
✓ graph_features imported
✓ risk_ast imported
✓ orchestrator imported
✓ feature_engineering imported
✓ main imported
✓ ALL TESTS PASSED
```

### 4. Start Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`

### 5. Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────┐
│           FRONTEND (React)                   │
│  Upload → Poll Status → Display Results     │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│           BACKEND (FastAPI)                  │
│              main.py                         │
└─┬──────┬──────┬──────┬──────┬──────────────┘
  │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼
┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐
│CPG│→│GF │→│RA │→│OR │→│FE │
└───┘  └───┘  └───┘  └───┘  └───┘
  1      2      3      4      5

1. CPG Builder - Parse code
2. Graph Features - Add metrics
3. Risk AST - Security profiles
4. Orchestrator - LLM analysis
5. Feature Engineering - Embeddings
```

---

## 🔍 Pipeline Flow

### Step-by-Step

1. **User uploads code** (ZIP or Git URL)
   ```
   POST /analyze
   ```

2. **CPG Builder** parses files
   ```python
   cpg_data = build_cpg(path, job_id)
   # Output: nodes, edges, nx_graph
   ```

3. **Graph Features** enriches nodes
   ```python
   G = compute_graph_features(G)
   # Adds: fan_in, fan_out, centrality, depth
   ```

4. **Risk AST** generates security profiles
   ```python
   risk_profiles = build_risk_ast(nodes, edges)
   # Output: sources, sinks, control_flags
   ```

5. **Orchestrator** performs AI analysis
   ```python
   llm_result = discover_relations_orchestrated(nodes)
   # Output: risk_level, relationships
   ```

6. **Feature Engineering** creates embeddings
   ```python
   nodes = generate_embeddings(nodes)
   # Output: 128-dim vectors
   ```

7. **Results** sent to frontend
   ```
   GET /results/{job_id}
   ```

---

## 🧪 Testing

### Manual Test

1. Start backend: `uvicorn main:app --reload`
2. Start frontend: `npm run dev`
3. Upload a small codebase
4. Watch the progress stepper
5. View results in dashboard

### Automated Test

```bash
cd backend
python test_connectivity.py
```

---

## 📁 Key Files

### Backend
- `main.py` - FastAPI app, pipeline orchestration
- `cpg_builder.py` - Code parsing with Tree-sitter
- `graph_features.py` - Topology metrics
- `risk_ast.py` - Security profile generation ⭐ NEW
- `orchestrator.py` - Multi-model LLM analysis
- `feature_engineering.py` - Embedding generation ⭐ NEW

### Frontend
- `src/App.jsx` - Main component
- `src/api.js` - Backend API client
- `src/components/ResultsDashboard.jsx` - Results display
- `src/components/GraphExplorer/` - Graph visualization

---

## 🔧 Troubleshooting

### Import Errors
```bash
cd backend
python -c "import main"
```
If fails, check `requirements.txt` installation.

### Frontend Not Connecting
Check `frontend/src/api.js`:
```javascript
const API_Base = 'http://localhost:8000';
```
Ensure backend is running on port 8000.

### AWS Credentials
If LLM analysis fails, check `.env`:
```bash
echo $AWS_ACCESS_KEY_ID
```

---

## 📚 Documentation

- **ARCHITECTURE.md** - Complete system architecture
- **CONNECTIVITY_DIAGRAM.md** - Visual diagrams
- **REFACTORING_SUMMARY.md** - Detailed changes
- **QUICK_START.md** - This file

---

## ✅ Verification Checklist

- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] `.env` file configured
- [ ] Connectivity test passes
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can upload and analyze code
- [ ] Results display correctly

---

## 🎉 Success Indicators

When everything works:

1. **Backend logs**:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

2. **Frontend logs**:
   ```
   VITE v5.x.x  ready in xxx ms
   ➜  Local:   http://localhost:5173/
   ```

3. **Connectivity test**:
   ```
   ✓ ALL TESTS PASSED - System connectivity verified!
   ```

4. **Analysis completes**:
   ```
   Status: Done
   Results: 150 nodes, 200 edges
   ```

---

## 🚨 Common Issues

### Issue: "Module not found: cpg_builder"
**Solution**: Run from backend directory
```bash
cd backend
python main.py
```

### Issue: "AWS credentials not found"
**Solution**: Create `.env` file in backend directory

### Issue: "Frontend can't connect to backend"
**Solution**: Check CORS settings in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should allow localhost:5173
)
```

---

## 📞 Need Help?

1. Check logs in terminal
2. Run connectivity test: `python test_connectivity.py`
3. Review documentation in `ARCHITECTURE.md`
4. Check diagnostics: No errors should appear

---

## 🎯 Next Steps

After successful setup:

1. **Try sample analysis**: Upload a small Python/JavaScript project
2. **Explore results**: Check graph visualization, risk analysis
3. **Review documentation**: Understand the architecture
4. **Customize**: Modify prompts in `orchestrator.py`
5. **Extend**: Add new features or languages

---

## 📊 Expected Performance

- **Small codebase** (<100 files): 1-2 minutes
- **Medium codebase** (100-500 files): 3-5 minutes
- **Large codebase** (500+ files): 5-10 minutes

Time depends on:
- Number of files
- Code complexity
- LLM response time
- Network speed

---

## 🔐 Security Notes

- AWS credentials stored in `.env` (not committed to git)
- LLM analysis uses AWS Bedrock (secure)
- No code uploaded to external services
- All processing happens locally/in your AWS account

---

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **React Flow**: https://reactflow.dev/
- **Tree-sitter**: https://tree-sitter.github.io/
- **AWS Bedrock**: https://aws.amazon.com/bedrock/

---

Happy coding! 🚀
