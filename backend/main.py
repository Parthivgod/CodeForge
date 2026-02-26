from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
from typing import List
import time
from cpg_builder import build_cpg
from llm_relation_discovery import discover_relations_llm
from docs_gen import generate_report
from langsmith import traceable

app = FastAPI(title="CodeForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock in-memory status
JOB_STATUS = {}
JOB_RESULTS = {}

import shutil
from typing import List, Optional
import time
import json
from git import Repo
from fastapi import Form

# ... imports ...

def update_status(job_id: str, step: int, total_steps: int, message: str):
    """Helper to update job status with structured data."""
    status_data = {
        "step": step,
        "total": total_steps,
        "message": message,
        "timestamp": time.time()
    }
    JOB_STATUS[job_id] = json.dumps(status_data)
    print(f"Job {job_id} [{step}/{total_steps}]: {message}")

def check_git_installed():
    try:
        # Check if git is in PATH
        if shutil.which("git") is None:
            return False
        return True
    except Exception:
        return False

@app.post("/analyze")
async def analyze_monolith(
    file: Optional[UploadFile] = None, 
    repo_url: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Pre-flight check
    if repo_url and not check_git_installed():
        return JSONResponse(
            status_code=400, 
            content={"error": "System Error: Git is not installed or not found in PATH on the server. Please install Git and restart the backend."}
        )

    job_id = str(uuid.uuid4())
    upload_dir = f"temp/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    if file:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        target_path = file_path
        JOB_STATUS[job_id] = "Processing: Parsing ZIP..."
    elif repo_url:
        target_path = os.path.join(upload_dir, "repo")
        JOB_STATUS[job_id] = f"Processing: Cloning {repo_url}..."
        background_tasks.add_task(run_pipeline_with_clone, job_id, repo_url, target_path)
        return {"job_id": job_id, "message": "Cloning & Analysis started"}
    else:
        return JSONResponse(status_code=400, content={"error": "No file or repo_url provided"})
    
    background_tasks.add_task(run_pipeline, job_id, target_path)
    
    return {"job_id": job_id, "message": "Analysis started"}

@traceable(project_name="CodeForge")
def run_pipeline_with_clone(job_id: str, repo_url: str, target_path: str):
    try:
        Repo.clone_from(repo_url, target_path)
        run_pipeline(job_id, target_path)
    except Exception as e:
        import traceback
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        JOB_STATUS[job_id] = f"Failed: {str(e)}"
        print(error_msg)

# ... existing run_pipeline ...

@app.get("/status/{job_id}")
def get_status(job_id: str):
    return {"status": JOB_STATUS.get(job_id, "Unknown")}

@app.get("/tree/{job_id}")
def get_tree(job_id: str):
    # Returns React Flow compatible nodes/edges
    if job_id not in JOB_RESULTS:
        return {"nodes": [], "edges": []}
    return JOB_RESULTS[job_id]["tree_data"]

@app.get("/results/{job_id}")
def get_results(job_id: str):
    if job_id not in JOB_RESULTS:
        return JSONResponse(status_code=404, content={"error": "Results not found or not ready."})
    return JOB_RESULTS[job_id]

@app.get("/report/{job_id}")
def get_report(job_id: str):
    if job_id not in JOB_RESULTS:
        return {"content": "Not ready."}
    return {"content": JOB_RESULTS[job_id]["report"]}

@traceable(project_name="CodeForge")
def run_pipeline(job_id: str, zip_path: str):
    try:
        # 1. Build CPG
        JOB_STATUS[job_id] = "Processing: Building CPG..."
        cpg_data = build_cpg(zip_path, job_id)
        nodes = cpg_data['nodes']
        initial_edges = cpg_data['edges']
        
        # 2. LLM Relation Discovery & Risk Analysis
        JOB_STATUS[job_id] = "Processing: AI Analysis (Relations & Risk)..."
        llm_result = discover_relations_llm(nodes)
        llm_edges = llm_result.get('edges', [])
        node_updates = llm_result.get('node_updates', {})
        
        # Merge LLM metadata (risk) into nodes
        for node in nodes:
            if node['id'] in node_updates:
                node.update(node_updates[node['id']])
            else:
                node['risk_level'] = 'low'
                node['failure_reason'] = 'No specific risk identified'
        
        # Combine and validate edges
        all_edges = initial_edges + llm_edges
        
        # Validate and enhance edges
        JOB_STATUS[job_id] = "Processing: Validating Relationships..."
        all_edges = validate_and_enhance_edges(all_edges, nodes)
        
        # 3. Graph Analysis & Stats
        JOB_STATUS[job_id] = "Processing: Analyzing Graph..."
        total_loc = sum(n.get('loc', 10) for n in nodes)
        num_nodes = len(nodes)
        num_edges = len(all_edges)
        
        # Mock stats for the UI
        stats = {
            "services": "N/A", 
            "loc": f"{total_loc // 1000}k" if total_loc >= 1000 else str(total_loc),
            "nodes": num_nodes,
            "edges": num_edges,
            "reduction": "1.0x",
            "confidence": "94%"
        }
        
        # 4. Generate Report
        JOB_STATUS[job_id] = "Processing: Generating Report..."
        report = f"# Codebase Analysis Report\n\nExtracted {num_nodes} nodes and {num_edges} edges.\nTotal LoC: {total_loc}"
        
        # Format for Frontend (React Flow)
        tree_data = format_for_react_flow(nodes, all_edges)
        
        JOB_RESULTS[job_id] = {
            "nodes": nodes,
            "edges": all_edges,
            "report": report,
            "stats": stats,
            "tree_data": tree_data
        }
        JOB_STATUS[job_id] = "Done"

    except Exception as e:
        import traceback
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        JOB_STATUS[job_id] = f"Failed: {str(e)}"
        print(error_msg)

def format_for_react_flow(nodes, edges):
    """
    Convert nodes and edges to React Flow format with Risk visualization.
    """
    import math
    
    rf_nodes = []
    rf_edges = []
    
    if not nodes:
        return {"nodes": [], "edges": []}
    
    # Simple grid layout
    num_nodes = len(nodes)
    cols = math.ceil(math.sqrt(num_nodes))
    spacing = 280
    
    for idx, node in enumerate(nodes):
        row = idx // cols
        col = idx % cols
        
        # Styling based on type
        node_type = node.get('type', 'function')
        risk = node.get('risk_level', 'low')
        
        bg_gradient = "linear-gradient(135deg, #10b981 0%, #059669 100%)" # Green
        if node_type == 'class':
            bg_gradient = "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)" # Indigo
        elif node_type == 'api_call':
            bg_gradient = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" # Amber

        # Risk Indicator (Border/Glow)
        border_color = "transparent"
        box_shadow = "0 4px 6px rgba(0,0,0,0.1)"
        
        if risk == 'high':
            border_color = "#ef4444"
            box_shadow = "0 0 15px rgba(239, 68, 68, 0.4)"
        elif risk == 'medium':
            border_color = "#eab308"
            box_shadow = "0 0 10px rgba(234, 179, 8, 0.3)"
            
        rf_nodes.append({
            "id": node['id'],
            "type": "default",
            "data": {
                "label": f"{node['name']}\n({node_type})",
                "risk": risk
            },
            "position": {"x": col * spacing, "y": row * spacing},
            "style": {
                "background": bg_gradient,
                "color": "white",
                "border": f"3px solid {border_color}",
                "borderRadius": "12px",
                "padding": "12px",
                "fontSize": "11px",
                "fontWeight": "600",
                "textAlign": "center",
                "width": 200,
                "boxShadow": box_shadow,
                "whiteSpace": "pre-line"
            }
        })
        
    for edge in edges:
        edge_type = edge.get('type', 'calls')
        animated = edge_type in ['calls', 'flow']
        
        # Color mapping for different relation types
        color_map = {
            'calls': '#94a3b8',      # Slate-400
            'structural': '#6366f1', # Indigo-500
            'dependency': '#475569', # Slate-600
            'flow': '#a855f7'        # Purple-500
        }
        edge_color = color_map.get(edge_type, '#94a3b8')
        
        rf_edges.append({
            "id": edge.get('id', f"e_{edge['source']}_{edge['target']}"),
            "source": edge['source'],
            "target": edge['target'],
            "label": edge_type,
            "type": "smoothstep",
            "animated": animated,
            "style": {
                "stroke": edge_color, 
                "strokeWidth": 2 if edge_type == 'calls' else 3
            },
            "markerEnd": {"type": "arrowclosed", "color": edge_color}
        })
        
    return {"nodes": rf_nodes, "edges": rf_edges}


def validate_and_enhance_edges(edges, nodes):
    """Validate edges and remove invalid ones, enhance with additional metadata."""
    valid_node_ids = {node['id'] for node in nodes}
    node_lookup = {node['id']: node for node in nodes}
    
    validated_edges = []
    edge_counts = {}
    
    for edge in edges:
        source_id = edge.get('source')
        target_id = edge.get('target')
        edge_type = edge.get('type', 'unknown')
        
        # Skip invalid edges
        if not source_id or not target_id:
            continue
        if source_id not in valid_node_ids or target_id not in valid_node_ids:
            continue
        if source_id == target_id:  # No self-loops
            continue
            
        # Normalize relation types
        type_map = {
            'composition': 'structural',
            'contains': 'structural',
            'inheritance': 'structural',
            'inherits': 'structural',
            'import': 'dependency',
            'imports': 'dependency',
            'same_file': 'dependency',
            'coupling': 'dependency',
            'temporal': 'flow',
            'flow': 'flow',
            'data_flow': 'flow'
        }
        
        # Count original edge types for statistics
        edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1
        
        # Merge types
        edge_type = type_map.get(edge_type, edge_type)
        
        # Enhance edge with metadata
        source_node = node_lookup[source_id]
        target_node = node_lookup[target_id]
        
        enhanced_edge = {
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "description": edge.get('description', ''),
            "source_file": source_node.get('file', ''),
            "target_file": target_node.get('file', ''),
            "cross_file": source_node.get('file') != target_node.get('file'),
            "confidence": edge.get('confidence', 1.0)
        }
        
        validated_edges.append(enhanced_edge)
    
    # Remove duplicate edges (same source, target, type)
    seen_edges = set()
    unique_edges = []
    for edge in validated_edges:
        edge_key = (edge['source'], edge['target'], edge['type'])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    print(f"Edge validation: {len(edges)} -> {len(unique_edges)} edges")
    print(f"Edge types: {edge_counts}")
    
    return unique_edges