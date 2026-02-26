import networkx as nx
from sklearn.cluster import KMeans
import numpy as np
from collections import defaultdict

def cluster_nodes(embeddings):
    """
    Cluster code nodes using KMeans on their embeddings.
    Returns clusters with metadata: files, LoC, complexity, risk levels.
    """
    print(f"Clustering {len(embeddings)} nodes...")
    
    if not embeddings:
        return []
    
    # Extract embeddings matrix
    embedding_matrix = np.array([node['embedding'] for node in embeddings])
    
    # Determine optimal number of clusters (between 3-8 based on data size)
    n_nodes = len(embeddings)
    n_clusters = min(max(3, n_nodes // 10), 8)
    n_clusters = min(n_clusters, n_nodes)  # Can't have more clusters than nodes
    
    print(f"Creating {n_clusters} clusters...")
    
    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embedding_matrix)
    
    # Group nodes by cluster
    cluster_groups = defaultdict(list)
    for i, label in enumerate(labels):
        cluster_groups[label].append(embeddings[i])
    
    # Build cluster metadata
    clusters = []
    for cluster_id, nodes in cluster_groups.items():
        # Calculate cluster metrics
        total_loc = sum(node.get('loc', 10) for node in nodes)
        files = list(set(node.get('file', '') for node in nodes))
        
        # Count node types
        class_count = sum(1 for n in nodes if n['type'] == 'class')
        function_count = sum(1 for n in nodes if n['type'] == 'function')
        
        # Calculate complexity score
        total_calls = sum(len(node.get('calls', [])) for node in nodes)
        total_edges = sum(len(node.get('edges', [])) for node in nodes)
        complexity = total_calls + total_edges + len(nodes)
        
        # Determine risk level based on cluster size and complexity
        if total_loc > 5000 or len(nodes) > 50:
            risk = 'high'
        elif total_loc > 2000 or len(nodes) > 20:
            risk = 'medium'
        else:
            risk = 'low'
        
        # Extract primary language
        languages = [node.get('language', 'unknown') for node in nodes]
        primary_language = max(set(languages), key=languages.count) if languages else 'unknown'
        
        # Generate cluster name based on content
        node_names = [n['name'] for n in nodes[:5]]  # Top 5 node names
        common_prefix = os.path.commonprefix([os.path.dirname(f) for f in files]) if files else ""
        
        # Simple name generation (can be enhanced with AI labeling)
        if common_prefix and os.path.basename(common_prefix):
            cluster_name = os.path.basename(common_prefix).replace('_', ' ').title()
        elif node_names:
            cluster_name = f"Component {cluster_id + 1}"
        else:
            cluster_name = f"Cluster {cluster_id + 1}"
        
        clusters.append({
            'id': int(cluster_id + 1),
            'name': cluster_name,
            'node_ids': [n['id'] for n in nodes],
            'nodes': nodes,
            'files': files,
            'loc_count': int(total_loc),
            'node_count': int(len(nodes)),
            'class_count': int(class_count),
            'function_count': int(function_count),
            'complexity': int(complexity),
            'risk': risk,
            'language': primary_language,
            'description': f"{len(nodes)} nodes, {total_loc} LoC, {len(files)} files"
        })

    
    print(f"Created {len(clusters)} clusters")
    return clusters

import os

