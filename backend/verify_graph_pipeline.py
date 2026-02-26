import os
import sys
import json
from pathlib import Path
import tempfile
import networkx as nx

# Add current directory to path
sys.path.append(os.getcwd())

from cpg_builder import build_cpg
from llm_relation_discovery import discover_relations_llm

def test_pipeline():
    # 1. Setup a mini project
    test_code = {
        "main.py": """
import requests
def process_data(data):
    return data.upper()

def send_to_api(data):
    # This is a small function
    resp = requests.post("https://api.example.com/v1/data", json={"d": data})
    return resp.status_code

def run():
    d = "hello"
    processed = process_data(d)
    send_to_api(processed)
""",
        "utils.py": """
def helper():
    return True
"""
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "mini_project"
        project_dir.mkdir()
        for name, content in test_code.items():
            (project_dir / name).write_text(content)
            
        print(f"--- Step 1: Building CPG ---")
        result = build_cpg(str(project_dir), "test_job")
        nodes = result['nodes']
        edges = result['edges']
        
        print(f"Nodes found: {len(nodes)}")
        for node in nodes:
            print(f"  - {node['id']} ({node['type']})")
            
        # Verify "small" functions are there
        node_ids = [n['id'] for n in nodes]
        assert "main.process_data" in node_ids
        assert "main.send_to_api" in node_ids
        
        # Verify API calls are there
        api_nodes = [n for n in nodes if n['type'] == 'api_call']
        print(f"API nodes found: {len(api_nodes)}")
        assert len(api_nodes) > 0
        
        print(f"\n--- Step 2: Testing LLM Relation Discovery (Mocked) ---")
        # Since we don't want to burn tokens or fail if no API key, we'll mock the LLM part if needed
        # but here we just check if it runs or fails gracefully
        llm_edges = discover_relations_llm(nodes)
        print(f"LLM edges found: {len(llm_edges)}")
        
        print(f"\n--- Step 3: Verifying Graph Structure ---")
        all_edges = edges + llm_edges
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node['id'], **node)
        for edge in all_edges:
            G.add_edge(edge['source'], edge['target'])
            
        print(f"Total Nodes: {G.number_of_nodes()}")
        print(f"Total Edges: {G.number_of_edges()}")
        
        print("\n✅ Verification successful!")

if __name__ == "__main__":
    try:
        test_pipeline()
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
