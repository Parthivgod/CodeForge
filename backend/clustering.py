import networkx as nx
from sklearn.cluster import KMeans
import numpy as np
from collections import defaultdict
import os
import re
import json

def cluster_nodes(embeddings):
    print(f"Clustering {len(embeddings)} nodes...")
    if not embeddings:
        return []
    embedding_matrix = np.array([node['embedding'] for node in embeddings])
    n_nodes = len(embeddings)
    n_clusters = min(max(3, n_nodes // 10), 8)
    n_clusters = min(n_clusters, n_nodes)
    print(f"Creating {n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embedding_matrix)
    cluster_groups = defaultdict(list)
    for i, label in enumerate(labels):
        cluster_groups[label].append(embeddings[i])
    clusters = []
    for cluster_id, nodes in cluster_groups.items():
        total_loc = sum(node.get('loc', 10) for node in nodes)
        files = list(set(node.get('file', '') for node in nodes))
        class_count = sum(1 for n in nodes if n['type'] == 'class')
        function_count = sum(1 for n in nodes if n['type'] == 'function')
        total_calls = sum(len(node.get('calls', [])) for node in nodes)
        total_edges = sum(len(node.get('edges', [])) for node in nodes)
        complexity = total_calls + total_edges + len(nodes)
        if total_loc > 5000 or len(nodes) > 50:
            risk = 'high'
        elif total_loc > 2000 or len(nodes) > 20:
            risk = 'medium'
        else:
            risk = 'low'
        languages = [node.get('language', 'unknown') for node in nodes]
        primary_language = max(set(languages), key=languages.count) if languages else 'unknown'
        
        cleaned_files = [re.sub(r'^temp[/\\][^/\\]+[/\\](repo[/\\])?', '', f) for f in files]
        dirnames = [os.path.dirname(f) for f in cleaned_files if f]
        common_prefix = os.path.commonprefix(dirnames) if dirnames else ""
        
        first_token = ""
        if common_prefix:
            parts = [p for p in re.split(r'[/\\]', common_prefix) if p]
            if parts:
                first_token = parts[0]
                
        if first_token:
            cluster_name = first_token.replace('_', ' ').title()
        else:
            top_func_class = [n['name'] for n in nodes if n.get('type') not in ('api_call', 'module')]
            if top_func_class:
                cluster_name = " / ".join(top_func_class[:3])
            else:
                cluster_name = f"Component {cluster_id + 1}"
                
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
            'description': "",
            'responsibilities': []
        })
    print(f"Created {len(clusters)} clusters")
    return clusters

def label_clusters_with_llm(clusters, bedrock_client, model_id):
    try:
        summaries = []
        for i, cluster in enumerate(clusters):
            nodes = cluster.get('nodes', [])
            
            functions = [n['name'] for n in nodes if n.get('type') == 'function'][:8]
            classes = [n['name'] for n in nodes if n.get('type') == 'class'][:4]
            api_calls = [n['name'] for n in nodes if n.get('type') == 'api_call'][:6]
            
            roles = set(n.get('architectural_role') for n in nodes if n.get('architectural_role'))
            architectural_roles = list(roles)
            
            summaries.append({
                "index": i,
                "node_count": cluster.get('node_count', 0),
                "loc": cluster.get('loc_count', 0),
                "risk": cluster.get('risk', 'low'),
                "functions": functions,
                "classes": classes,
                "api_calls": api_calls,
                "architectural_roles": architectural_roles
            })
            
        system_prompt = (
            "You are a principal software architect. Given a list of code cluster summaries "
            "from static analysis, assign each cluster a concise microservice name, a "
            "one-sentence description of what it does, and a list of 2-4 responsibilities "
            "(what this service owns or manages).\n"
            "Return STRICT JSON array — no markdown, no explanation, no backticks.\n"
            "One object per cluster in the same order as input.\n"
            "Schema: [{\"service_name\": \"...\", \"description\": \"...\", "
            "\"responsibilities\": [\"...\", \"...\"]}]"
        )
        
        user_prompt = f"Label these {len(summaries)} code clusters:\n{json.dumps(summaries, indent=2)}"
        
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={"temperature": 0.2, "maxTokens": 4096}
        )
        
        response_text = response['output']['message']['content'][0]['text']
        response_json = json.loads(response_text)
        
        if isinstance(response_json, list) and len(response_json) == len(clusters):
            for i, data in enumerate(response_json):
                clusters[i]["name"] = data.get("service_name", clusters[i]["name"])
                clusters[i]["description"] = data.get("description", "")
                clusters[i]["responsibilities"] = data.get("responsibilities", [])
                
    except Exception as e:
        pass
        
    return clusters
