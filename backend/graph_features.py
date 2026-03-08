import networkx as nx

def compute_graph_features(G: nx.DiGraph) -> nx.DiGraph:
    """Compute and attach feature engineering attributes to nodes for the GNN."""
    
    # 1. Degree Metrics
    for node_id in G.nodes():
        G.nodes[node_id]['fan_in'] = G.in_degree(node_id)
        G.nodes[node_id]['fan_out'] = G.out_degree(node_id)
        G.nodes[node_id]['total_degree'] = G.degree(node_id)
        
    # 2. Betweenness Centrality (Appx for speed on >10k nodes)
    k = min(len(G), 100) if len(G) > 0 else None
    betweenness = nx.betweenness_centrality(G, k=k)
    for node_id, bc in betweenness.items():
        G.nodes[node_id]['betweenness_centrality'] = bc

    # 3. Identify Sources, Sinks, and Entry Points
    entry_nodes = []
    sources = []
    sinks = []
    
    for node_id, data in G.nodes(data=True):
        if data.get('is_entry_point', False):
            entry_nodes.append(node_id)
            
        # Security source/sink heuristics
        if data.get('has_env_access') or data.get('has_file_access') or data.get('type') == 'api_call':
            sources.append(node_id)
            sinks.append(node_id) # Network/APIs can be both
            
        if data.get('has_eval') or data.get('has_shell_call'):
            sinks.append(node_id)

    # 4. Depth from Entry Point
    depths = {}
    if entry_nodes:
        for entry in entry_nodes:
            if G.has_node(entry):
                lengths = nx.single_source_shortest_path_length(G, entry)
                for node_id, dist in lengths.items():
                    if node_id not in depths or dist < depths[node_id]:
                        depths[node_id] = dist
                    
    for node_id in G.nodes():
        G.nodes[node_id]['depth_from_entry'] = depths.get(node_id, -1) # -1 means unreachable

    # 5. Reachable sinks/sources
    for node_id in G.nodes():
        if G.out_degree(node_id) > 0:
            desc = nx.descendants(G, node_id)
            G.nodes[node_id]['reachable_sink_count'] = sum(1 for d in desc if d in sinks)
        else:
            G.nodes[node_id]['reachable_sink_count'] = 1 if node_id in sinks else 0
            
        if G.in_degree(node_id) > 0:
            anc = nx.ancestors(G, node_id)
            G.nodes[node_id]['reachable_source_count'] = sum(1 for a in anc if a in sources)
        else:
            G.nodes[node_id]['reachable_source_count'] = 1 if node_id in sources else 0

        # Fill defaults
        api_calls = G.nodes[node_id].get('api_calls')
        G.nodes[node_id]['num_api_calls'] = len(api_calls) if isinstance(api_calls, list) else 0

    return G
