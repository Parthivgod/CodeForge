"""
risk_ast.py - Risk AST Builder for Security Analysis
Generates per-function abstract Risk AST profiles derived from the graph + features.
"""

from typing import List, Dict


def build_risk_ast(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Dict]:
    """Generate per-function abstract Risk AST profiles derived from the graph + features."""
    risk_profiles = {}
    
    # Pre-compute edge lookups
    node_out_edges = {}
    node_in_edges = {}
    for edge in edges:
        src = edge['source']
        tgt = edge['target']
        etype = edge['type']
        node_out_edges.setdefault(src, []).append({'target': tgt, 'type': etype})
        node_in_edges.setdefault(tgt, []).append({'source': src, 'type': etype})
        
    for node in nodes:
        if node.get('type') != 'function':
            continue
            
        nid = node['id']
        
        # Sources / Sinks (from features)
        sources = ['env'] if node.get('has_env_access') else []
        sources += ['file'] if node.get('has_file_access') else []
        sinks = ['eval'] if node.get('has_eval') else []
        sinks += ['shell'] if node.get('has_shell_call') else []
        
        # External interactions (APIs)
        external = [n for n in node.get('api_calls', [])]
        
        # Call neighbors
        call_neighbors = [e['target'] for e in node_out_edges.get(nid, []) if e['type'] == 'calls']
        
        # Control flags
        control_flags = {
            'has_conditional': node.get('has_conditional', False),
            'has_loop': node.get('has_loop', False),
            'has_try_catch': node.get('has_try_catch', False),
            'has_async_await': node.get('has_async_await', False)
        }
        
        # Data flow (intra-function mappings from CPG)
        data_flow_neighbors = []
        for df in node.get('data_flows', []):
            data_flow_neighbors.append(df)
            
        risk_profiles[nid] = {
            "node_id": nid,
            "risk_profile": {
                "sources": sources,
                "sinks": sinks,
                "entry": node.get('is_entry_point', False),
                "external_interactions": external,
                "control_flags": control_flags,
                "data_flow_neighbors": data_flow_neighbors,
                "call_neighbors": call_neighbors
            }
        }
    
    return risk_profiles
