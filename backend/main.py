from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uuid
import os
import shutil
from typing import List
import time
from cpg_builder import build_cpg
from orchestrator import discover_relations_orchestrated
from risk_ast import build_risk_ast
from feature_engineering import generate_embeddings
from clustering import cluster_nodes, label_clusters_with_llm

# GNN import with graceful fallback
try:
    from gnn_model import generate_gnn_embeddings
    GNN_AVAILABLE = True
    print("[Startup] GNN model loaded (PyTorch available).")
except ImportError:
    GNN_AVAILABLE = False
    print("[Startup] PyTorch not found — GNN disabled, using TF-IDF embeddings.")
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

    import tempfile as _tempfile
    job_id = str(uuid.uuid4())
    upload_dir = os.path.join(_tempfile.gettempdir(), "codeforge", job_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    if file:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        target_path = file_path
        update_status(job_id, 0, 7, "Parsing ZIP file...")
    elif repo_url:
        target_path = os.path.join(upload_dir, "repo")
        update_status(job_id, 0, 7, f"Cloning repository: {repo_url}...")
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

@app.get("/node/{job_id}/{node_id}")
def get_node_details(job_id: str, node_id: str):
    """Get detailed information for a specific node (lazy loading)"""
    if job_id not in JOB_RESULTS:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    
    nodes = JOB_RESULTS[job_id]['nodes']
    node = next((n for n in nodes if n['id'] == node_id), None)
    
    if not node:
        return JSONResponse(status_code=404, content={"error": "Node not found"})
    
    return {
        "id": node['id'],
        "name": node['name'],
        "type": node['type'],
        "file": node.get('file'),
        "line_start": node.get('line_start'),
        "loc": node.get('loc'),
        "language": node.get('language'),
        "risk_level": node.get('risk_level'),
        "risk_analysis": node.get('risk_analysis'),
        "failure_reason": node.get('failure_reason'),
        "calls": node.get('calls', []),
        "api_calls": node.get('api_calls', []),
        "variables": node.get('variables', []),
        "parameters": node.get('parameters', []),
        "risk_ast": node.get('risk_ast'),
        "confidence_score": node.get('confidence_score'),
        "architectural_role": node.get('architectural_role'),
        "node_summary": node.get('node_summary')
    }

@app.get("/report/{job_id}")
def get_report(job_id: str):
    if job_id not in JOB_RESULTS:
        return {"content": "Not ready."}
    return {"content": JOB_RESULTS[job_id]["report"]}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Serve frontend static files (for Railway deployment)
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True, reload_excludes=["temp/*"])

@traceable(project_name="CodeForge")
def run_pipeline(job_id: str, zip_path: str):
    try:
        total_steps = 7
        
        # 1. Build CPG
        update_status(job_id, 1, total_steps, "Building Code Property Graph...")
        cpg_data = build_cpg(zip_path, job_id)
        nodes = cpg_data['nodes']
        initial_edges = cpg_data['edges']
        
        # 2. Build Risk AST Profiles
        update_status(job_id, 2, total_steps, "Building Risk AST Profiles...")
        risk_profiles = build_risk_ast(nodes, initial_edges)
        print(f"Generated {len(risk_profiles)} risk profiles")
        
        # Merge Risk AST into nodes BEFORE orchestrator (so Sentinel can use it)
        for node in nodes:
            if node['id'] in risk_profiles:
                node['risk_ast'] = risk_profiles[node['id']]['risk_profile']
        
        # 3. Multi-Model Orchestrated Analysis (Relations, Risk & Refactoring)
        update_status(job_id, 3, total_steps, "AI Analysis: Mapper, Linker & Sentinel...")
        
        # Defensive fix: Ensure all nodes have valid IDs before LLM processing
        valid_nodes = [n for n in nodes if 'id' in n and n['id']]
        if len(valid_nodes) < len(nodes):
            print(f"Warning: Removed {len(nodes) - len(valid_nodes)} nodes missing 'id' key.")
            nodes = valid_nodes
            
        llm_result = discover_relations_orchestrated(nodes)
        llm_edges = llm_result.get('edges', [])
        node_updates = llm_result.get('node_updates', {})
        
        # Merge LLM metadata (risk analysis results) into nodes
        for node in nodes:
            # Add LLM analysis results
            if node['id'] in node_updates:
                node.update(node_updates[node['id']])
            else:
                node['risk_level'] = 'low'
                node['failure_reason'] = 'No specific risk identified'
            # Note: risk_ast was already merged above before orchestrator call
        
        # Final deduplication guard — ensure unique node IDs
        seen_ids = set()
        unique_nodes = []
        for node in nodes:
            if node['id'] not in seen_ids:
                seen_ids.add(node['id'])
                unique_nodes.append(node)
        if len(unique_nodes) < len(nodes):
            print(f"[Pipeline] Deduplicated {len(nodes) - len(unique_nodes)} duplicate nodes before output.")
        nodes = unique_nodes
        
        # Combine and validate edges
        all_edges = initial_edges + llm_edges
        
        # Validate and enhance edges
        update_status(job_id, 4, total_steps, "Validating Relationships...")
        all_edges = validate_and_enhance_edges(all_edges, nodes)
        
        # 4. Generate Embeddings — GNN if available, TF-IDF fallback
        update_status(job_id, 5, total_steps, "Generating Node Embeddings (GNN)...")
        try:
            if GNN_AVAILABLE:
                nodes = generate_gnn_embeddings(nodes, all_edges)
                print(f"[GNN] Generated GNN embeddings for {len(nodes)} nodes")
            else:
                nodes = generate_embeddings(nodes)
                print(f"Generated TF-IDF embeddings for {len(nodes)} nodes")
        except Exception as e:
            print(f"Warning: Embedding generation failed: {e}")
            nodes = generate_embeddings(nodes)
        
        # 5. Graph Analysis & Stats
        update_status(job_id, 6, total_steps, "Computing Graph Statistics...")
        total_loc = sum(n.get('loc', 10) for n in nodes)
        num_nodes = len(nodes)
        num_edges = len(all_edges)
        
        # Calculate confidence using tier-weighted average.
        # Higher-risk tiers received more analysis so their scores carry more weight.
        # All scored nodes are included (threshold >= 0, not > 0) so Tier 1 nodes
        # with confidence_score=0.75 and Sentinel fallbacks at 0.4 are not dropped.
        _tier_weights = {'none': 0.5, 'low': 0.75, 'moderate': 1.0,
                         'medium': 1.0, 'high': 1.2, 'critical': 1.5, 'unknown': 0.6}
        weighted_sum, weight_total = 0.0, 0.0
        for n in nodes:
            score = n.get('confidence_score', 0.0)
            if isinstance(score, (int, float)) and score >= 0:
                w = _tier_weights.get(n.get('risk_level', 'none'), 1.0)
                weighted_sum += score * w
                weight_total += w
        avg_confidence = (weighted_sum / weight_total) if weight_total > 0 else 0.85
        confidence_pct = f"{int(avg_confidence * 100)}%"
        
        # Cluster nodes into microservice boundaries using GNN embeddings
        clusters = []
        num_services = "N/A"
        try:
            embeddable = [n for n in nodes if isinstance(n.get('embedding'), list) and len(n['embedding']) > 0]
            if embeddable:
                clusters = cluster_nodes(embeddable)
                num_services = len(clusters)
                print(f"[Clustering] Identified {num_services} microservice boundary candidates")

                # LLM cluster labelling — runs after clustering, uses Mapper model
                try:
                    from clustering import label_clusters_with_llm
                    from orchestrator import _get_bedrock_client, MODEL_ROLES
                    bedrock_client = _get_bedrock_client()
                    mapper_model_id = MODEL_ROLES["mapper"]["model_id"]
                    clusters = label_clusters_with_llm(clusters, bedrock_client, mapper_model_id)
                    print(f"[Clustering] LLM labelling complete")
                except Exception as llm_err:
                    print(f"[Clustering] LLM labelling skipped: {llm_err}")

                # Attach cluster ID and LLM-assigned name back to each node
                for cluster in clusters:
                    for nid in cluster.get('node_ids', []):
                        for node in nodes:
                            if node['id'] == nid:
                                node['cluster_id'] = cluster['id']
                                node['cluster_name'] = cluster['name']
        except Exception as e:
            print(f"Warning: Clustering failed: {e}")

        stats = {
            "services": num_services,
            "loc": f"{total_loc // 1000}k" if total_loc >= 1000 else str(total_loc),
            "nodes": num_nodes,
            "edges": num_edges,
            "reduction": "1.0x",
            "confidence": confidence_pct
        }
        
        # 6. Generate Report with Architect Insight
        update_status(job_id, 7, total_steps, "Generating Final Report...")
        
        # Find hottest risk node for an actionable insight
        risk_priority = {'critical': 4, 'high': 3, 'medium': 2, 'moderate': 2, 'low': 1, 'none': 0}
        hottest = max(nodes, key=lambda n: risk_priority.get(n.get('risk_level', 'none'), 0), default=None)
        if hottest and risk_priority.get(hottest.get('risk_level', 'none'), 0) >= 2:
            insight = (
                f"Highest risk detected in `{hottest.get('name', 'unknown')}` "
                f"({hottest.get('risk_level', 'unknown')} risk"
                f"{', ' + hottest.get('architectural_role', '') if hottest.get('architectural_role') else ''}). "
                f"Confidence: {confidence_pct} across {len(confidence_scores)} analyzed nodes."
            )
        else:
            insight = f"Codebase Analysis Report — {num_nodes} nodes, {num_edges} edges, {confidence_pct} confidence."
        
        report = f"# {insight}\n\nExtracted {num_nodes} nodes and {num_edges} edges.\nTotal LoC: {total_loc}"
        
        # Format for Frontend (React Flow)
        tree_data = format_for_react_flow(nodes, all_edges)
        
        JOB_RESULTS[job_id] = {
            "nodes": nodes,
            "edges": all_edges,
            "report": report,
            "stats": stats,
            "tree_data": tree_data,
            "clusters": clusters
        }
        JOB_STATUS[job_id] = "Done"

    except Exception as e:
        import traceback
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        JOB_STATUS[job_id] = f"Failed: {str(e)}"
        print(error_msg)

def format_for_react_flow(nodes, edges):
    """
    Convert nodes and edges to React Flow format with hierarchical layout.
    Groups nodes by file and positions them to minimize overlap.
    """
    import math
    from collections import defaultdict
    
    rf_nodes = []
    rf_edges = []
    
    if not nodes:
        return {"nodes": [], "edges": []}
    
    # Group nodes by file and type
    files = defaultdict(lambda: {
        'functions': [], 
        'api_calls': [], 
        'modules': [], 
        'classes': [],
        'databases': [],
        'external': []
    })
    
    for node in nodes:
        file_path = node.get('file', 'unknown')
        node_type = node.get('type', 'unknown')
        
        if node_type == 'function':
            files[file_path]['functions'].append(node)
        elif node_type == 'api_call':
            files[file_path]['api_calls'].append(node)
        elif node_type == 'module':
            files[file_path]['modules'].append(node)
        elif node_type == 'class':
            files[file_path]['classes'].append(node)
        elif node_type == 'database':
            files[file_path]['databases'].append(node)
        elif node_type == 'external':
            files[file_path]['external'].append(node)
        else:
            # Unknown types go to external
            files[file_path]['external'].append(node)
    
    # Layout parameters for better spacing
    file_spacing_x = 900      # Horizontal space between file groups
    function_spacing_y = 200  # Vertical space between functions
    api_spacing_y = 50        # Vertical space between API calls
    api_offset_x = 350        # Horizontal offset for API calls
    module_offset_y = -100    # Modules above functions
    
    current_file_x = 0
    current_file_x = 0
    
    # Process each file group
    for file_path, file_nodes in sorted(files.items()):
        functions = file_nodes['functions']
        api_calls = file_nodes['api_calls']
        modules = file_nodes['modules']
        classes = file_nodes['classes']
        databases = file_nodes['databases']
        external = file_nodes['external']
        
        current_y = 0
        
        # Position module nodes (at top)
        for module in modules:
            rf_nodes.append({
                "id": module['id'],
                "type": "default",
                "data": {
                    "label": f"📦 {module['name']}",
                    "nodeType": "module",
                    "language": module.get('language', 'unknown'),  # Add language
                    "node_details": module
                },
                "position": {"x": current_file_x, "y": module_offset_y},
                "style": {
                    "background": "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
                    "color": "white",
                    "border": "2px solid #4f46e5",
                    "borderRadius": "8px",
                    "padding": "10px",
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "width": 180,
                    "height": 50,
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                }
            })
        
        # Position class nodes
        for cls_idx, cls in enumerate(classes):
            cls_y = current_y + (cls_idx * function_spacing_y) - 50
            rf_nodes.append({
                "id": cls['id'],
                "type": "default",
                "data": {
                    "label": f"🏛️ {cls['name']}",
                    "nodeType": "class",
                    "language": cls.get('language', 'unknown'),  # Add language
                    "node_details": cls
                },
                "position": {"x": current_file_x - 200, "y": cls_y},
                "style": {
                    "background": "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
                    "color": "white",
                    "border": "2px solid #7c3aed",
                    "borderRadius": "10px",
                    "padding": "12px",
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "width": 160,
                    "height": 60,
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                }
            })
        
        # Position database nodes
        for db_idx, db in enumerate(databases):
            db_y = current_y + (db_idx * 100)
            rf_nodes.append({
                "id": db['id'],
                "type": "default",
                "data": {
                    "label": f"🗄️ {db['name']}",
                    "nodeType": "database",
                    "language": db.get('language', 'unknown'),  # Add language
                    "node_details": db
                },
                "position": {"x": current_file_x + 600, "y": db_y},
                "style": {
                    "background": "linear-gradient(135deg, #ec4899 0%, #db2777 100%)",
                    "color": "white",
                    "border": "2px solid #db2777",
                    "borderRadius": "8px",
                    "padding": "10px",
                    "fontSize": "10px",
                    "fontWeight": "600",
                    "width": 140,
                    "height": 50,
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                }
            })
        
        # Position function nodes
        for func_idx, func in enumerate(functions):
            func_y = current_y + (func_idx * function_spacing_y)
            
            # Determine styling based on risk
            risk = func.get('risk_level', 'low')
            border_color = "transparent"
            box_shadow = "0 4px 6px rgba(0,0,0,0.1)"
            
            if risk == 'high':
                border_color = "#ef4444"
                box_shadow = "0 0 15px rgba(239, 68, 68, 0.4)"
            elif risk == 'medium':
                border_color = "#eab308"
                box_shadow = "0 0 10px rgba(234, 179, 8, 0.3)"
            
            # Function node (larger, prominent)
            rf_nodes.append({
                "id": func['id'],
                "type": "default",
                "data": {
                    "label": f"⚡ {func['name']}\n({func.get('loc', 0)} LoC)",
                    "risk": risk,
                    "nodeType": "function",
                    "language": func.get('language', 'unknown'),  # Add language
                    "node_details": func
                },
                "position": {"x": current_file_x, "y": func_y},
                "style": {
                    "background": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                    "color": "white",
                    "border": f"3px solid {border_color}",
                    "borderRadius": "12px",
                    "padding": "14px",
                    "fontSize": "12px",
                    "fontWeight": "700",
                    "textAlign": "center",
                    "width": 220,
                    "height": 90,
                    "boxShadow": box_shadow,
                    "whiteSpace": "pre-line"
                }
            })
            
            # Position API calls for this function (to the right, stacked)
            # Handle both old (parent) and new (used_by) formats
            func_api_calls = []
            for a in api_calls:
                # New format: deduplicated API with 'used_by' list
                if 'used_by' in a and func['id'] in a.get('used_by', []):
                    func_api_calls.append(a)
                # Old format: single parent
                elif a.get('parent') == func['id']:
                    func_api_calls.append(a)
            
            # Limit visible API calls to avoid clutter (show first 8)
            visible_api_count = min(len(func_api_calls), 8)
            for api_idx in range(visible_api_count):
                api = func_api_calls[api_idx]
                api_y = func_y + (api_idx * api_spacing_y) - 20
                
                # Show usage count if API is used multiple times
                usage_info = ""
                if api.get('usage_count', 1) > 1:
                    usage_info = f" (×{api['usage_count']})"
                
                rf_nodes.append({
                    "id": api['id'],
                    "type": "default",
                    "data": {
                        "label": f"🔌 {api['name'][:20]}{'...' if len(api['name']) > 20 else ''}{usage_info}",
                        "nodeType": "api_call",
                        "language": api.get('language', 'unknown'),  # Add language
                        "node_details": api
                    },
                    "position": {"x": current_file_x + api_offset_x, "y": api_y},
                    "style": {
                        "background": "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                        "color": "white",
                        "border": "1px dashed rgba(255,255,255,0.3)",
                        "borderRadius": "20px",
                        "padding": "6px 12px",
                        "fontSize": "9px",
                        "fontWeight": "500",
                        "width": 140,
                        "height": 35,
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis"
                    }
                })
            
            # Add indicator if there are more API calls
            if len(func_api_calls) > visible_api_count:
                remaining = len(func_api_calls) - visible_api_count
                indicator_y = func_y + (visible_api_count * api_spacing_y) - 20
                rf_nodes.append({
                    "id": f"{func['id']}_more_apis",
                    "type": "default",
                    "data": {
                        "label": f"+{remaining} more APIs",
                        "node_details": {"type": "indicator"}
                    },
                    "position": {"x": current_file_x + api_offset_x, "y": indicator_y},
                    "style": {
                        "background": "#64748b",
                        "color": "white",
                        "border": "1px solid #475569",
                        "borderRadius": "15px",
                        "padding": "4px 10px",
                        "fontSize": "8px",
                        "fontWeight": "500",
                        "width": 100,
                        "height": 25,
                        "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
                    }
                })
        
        # Move to next file column
        current_file_x += file_spacing_x
        # Move to next file column
        current_file_x += file_spacing_x
    
    # Create edges with distinct styling per type
    for edge in edges:
        edge_type = edge.get('type', 'calls')
        
        # Enhanced styling for each edge type
        edge_styles = {
            'calls': {
                'color': '#3b82f6',  # Blue
                'width': 3,
                'animated': True,
                'dasharray': None,
                'label': 'calls',
                'opacity': 1.0
            },
            'contains': {
                'color': '#8b5cf6',  # Purple
                'width': 2,
                'animated': False,
                'dasharray': None,
                'label': 'contains',
                'opacity': 0.8
            },
            'uses_api': {
                'color': '#f59e0b',  # Orange
                'width': 2,
                'animated': False,
                'dasharray': '5,5',
                'label': 'uses API',
                'opacity': 0.7
            },
            'structural': {
                'color': '#6366f1',  # Indigo
                'width': 2,
                'animated': False,
                'dasharray': None,
                'label': 'inherits',
                'opacity': 0.8
            },
            'dependency': {
                'color': '#64748b',  # Slate
                'width': 1.5,
                'animated': False,
                'dasharray': '3,3',
                'label': 'depends',
                'opacity': 0.6
            },
            'flow': {
                'color': '#ec4899',  # Pink
                'width': 2,
                'animated': True,
                'dasharray': '8,4',
                'label': 'flow',
                'opacity': 0.7
            }
        }
        
        style = edge_styles.get(edge_type, {
            'color': '#94a3b8',
            'width': 1,
            'animated': False,
            'dasharray': None,
            'label': edge_type,
            'opacity': 0.5
        })
        
        # Build edge style
        edge_style = {
            "stroke": style['color'],
            "strokeWidth": style['width'],
            "opacity": style['opacity']
        }
        
        if style['dasharray']:
            edge_style["strokeDasharray"] = style['dasharray']
        
        # Create edge with enhanced styling
        rf_edges.append({
            "id": edge.get('id', f"e_{edge['source']}_{edge['target']}"),
            "source": edge['source'],
            "target": edge['target'],
            "label": style['label'],
            "type": "smoothstep",
            "animated": style['animated'],
            "style": edge_style,
            "markerEnd": {
                "type": "arrowclosed" if edge_type == 'calls' else "arrow",
                "color": style['color']
            },
            "data": {
                "edgeType": edge_type,
                "visible": True,
                "description": edge.get('description', '')
            },
            "labelStyle": {
                "fill": style['color'],
                "fontWeight": 600,
                "fontSize": 10
            },
            "labelBgStyle": {
                "fill": "#1e293b",
                "fillOpacity": 0.8
            }
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
            
        # Normalize relation types (keep 'contains' as separate type)
        type_map = {
            'composition': 'structural',
            # 'contains': 'structural',  # REMOVED - keep as separate type for filters
            'inheritance': 'structural',
            'inherits': 'structural',
            'import': 'dependency',
            'imports': 'dependency',
            'same_file': 'dependency',
            'coupling': 'dependency',
            'temporal': 'flow',
            'flow': 'flow',
            'data_flow': 'flow'
            # Note: 'depends_on', 'calls', 'contains', 'uses_api' pass through unchanged
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
    
    # Remove redundant edges between same source-target pairs
    # Priority: calls > contains > depends_on > structural > dependency > flow
    type_priority = {
        'calls': 1,
        'contains': 2,
        'depends_on': 3,
        'structural': 4,
        'dependency': 5,
        'flow': 6,
        'unknown': 7
    }
    
    # Store best edge for each (source, target) pair
    best_edges = {}
    for edge in validated_edges:
        key = (edge['source'], edge['target'])
        current_priority = type_priority.get(edge['type'], 99)
        
        if key not in best_edges:
            best_edges[key] = edge
        else:
            existing_priority = type_priority.get(best_edges[key]['type'], 99)
            if current_priority < existing_priority:
                best_edges[key] = edge
                
    unique_edges = list(best_edges.values())
    
    print(f"Edge validation: {len(edges)} -> {len(unique_edges)} edges")
    print(f"Edge types: {edge_counts}")
    
    return unique_edges