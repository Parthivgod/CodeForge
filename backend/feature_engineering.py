"""
feature_engineering.py - Feature preparation for code analysis
Handles initial feature extraction from code nodes using TF-IDF and structural metrics.
"""

import numpy as np
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


def prepare_initial_features(nodes: List[Dict]) -> np.ndarray:
    """
    Prepare enhanced initial features for code nodes.
    Combines text-based TF-IDF features with structural/topological metrics.
    """
    print(f"Preparing enhanced initial features for {len(nodes)} nodes...")
    
    # 1. Text TF-IDF
    text_features = []
    for node in nodes:
        name = node.get('name', '')
        vars_st = ' '.join(node.get('variables', []))
        text_features.append(f"{name} {vars_st}")
        
    try:
        tfidf = TfidfVectorizer(max_features=64, stop_words='english').fit_transform(text_features).toarray()
    except:
        tfidf = np.zeros((len(nodes), 64))
        
    # 2. Structural & Topological Features
    structural = []
    for n in nodes:
        # Topology metrics from graph_features.py
        fan_in = n.get('fan_in', 0)
        fan_out = n.get('fan_out', 0)
        total_deg = n.get('total_degree', 0)
        bc = n.get('betweenness_centrality', 0.0)
        depth = n.get('depth_from_entry', -1)
        r_sinks = n.get('reachable_sink_count', 0)
        r_srcs = n.get('reachable_source_count', 0)
        loc = n.get('loc', 1) / 100.0
        
        # Boolean flags encoded
        is_func = 1 if n.get('type') == 'function' else 0
        is_class = 1 if n.get('type') == 'class' else 0
        is_api = 1 if n.get('type') == 'api_call' else 0
        is_entry = 1 if n.get('is_entry_point', False) else 0
        has_auth = 1 if n.get('has_auth_logic', False) else 0
        
        vec = [fan_in, fan_out, total_deg, bc, depth, r_sinks, r_srcs, 
               loc, is_func, is_class, is_api, is_entry, has_auth]
        structural.append(vec)
        
    structural = np.array(structural)
    structural_scaled = StandardScaler().fit_transform(structural)
    
    # 3. Combine
    combined = np.hstack((tfidf, structural_scaled))
    print(f"Initial feature dimension: {combined.shape[1]}")
    return combined


def generate_embeddings(nodes: List[Dict]) -> List[Dict]:
    """
    Generate embeddings for nodes using feature engineering.
    Fallback implementation without GNN dependencies.
    """
    if not nodes:
        return nodes
        
    try:
        feats = prepare_initial_features(nodes)
        dim = min(feats.shape[1], 128)
        
        for i, node in enumerate(nodes):
            emb = feats[i, :dim].tolist()
            if dim < 128:
                emb += [0.0] * (128 - dim)
            node['embedding'] = emb
            
        return nodes
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Return nodes with zero embeddings as fallback
        for node in nodes:
            node['embedding'] = [0.0] * 128
        return nodes
