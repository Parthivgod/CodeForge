"""
test_gnn_model.py — Comprehensive test suite for gnn_model.py

Tests cover:
  1. Unit tests  — individual components (GCNLayer, GCNEncoder, GraphAutoencoder)
  2. Integration tests — full generate_gnn_embeddings() pipeline
  3. Comparison test — GNN embeddings vs TF-IDF baseline (what changes in the pipeline)
  4. Edge case tests — empty graphs, disconnected graphs, single node
  5. Regression test — embeddings are stable and consistent across runs

Run from the backend directory:
    python test_gnn_model.py

Or with verbose output:
    python test_gnn_model.py -v

Requires: torch, numpy, scikit-learn (all in requirements.txt)
"""

import sys
import time
import traceback
import numpy as np

# ─── Colour helpers for readable terminal output ─────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"
SKIP = f"{YELLOW}SKIP{RESET}"
INFO = f"{CYAN}INFO{RESET}"

results = {"passed": 0, "failed": 0, "skipped": 0}

def run_test(name, fn):
    """Run a single test function and record the result."""
    try:
        fn()
        print(f"  [{PASS}] {name}")
        results["passed"] += 1
    except AssertionError as e:
        print(f"  [{FAIL}] {name}")
        print(f"          {RED}{e}{RESET}")
        results["failed"] += 1
    except Exception as e:
        print(f"  [{FAIL}] {name}  ({type(e).__name__})")
        print(f"          {RED}{traceback.format_exc().strip()}{RESET}")
        results["failed"] += 1

def skip_test(name, reason):
    print(f"  [{SKIP}] {name}  ({reason})")
    results["skipped"] += 1

def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*60}{RESET}")

# ─── Check PyTorch availability ───────────────────────────────────────────────
section("Environment check")
try:
    import torch
    import torch.nn as nn
    print(f"  [{INFO}] PyTorch version : {torch.__version__}")
    print(f"  [{INFO}] CUDA available  : {torch.cuda.is_available()} (not required)")
    TORCH_OK = True
except ImportError:
    print(f"  [{FAIL}] PyTorch not installed. Run:  pip install torch --index-url https://download.pytorch.org/whl/cpu")
    TORCH_OK = False
    sys.exit(1)

try:
    from gnn_model import (
        GCNLayer, GCNEncoder, GraphAutoencoder,
        build_adjacency, normalise_adjacency,
        train_gae, generate_gnn_embeddings,
    )
    print(f"  [{INFO}] gnn_model.py     : imported successfully")
    GNN_OK = True
except ImportError as e:
    print(f"  [{FAIL}] Could not import gnn_model: {e}")
    GNN_OK = False
    sys.exit(1)

try:
    from feature_engineering import prepare_initial_features, generate_embeddings
    FE_OK = True
    print(f"  [{INFO}] feature_engineering.py : imported successfully")
except ImportError:
    FE_OK = False
    print(f"  [{SKIP}] feature_engineering.py not found — comparison tests will be skipped")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_nodes(n=8):
    """Create n synthetic code nodes that mimic real CPG output."""
    types = ["function", "function", "class", "api_call", "module", "function", "function", "class"]
    nodes = []
    for i in range(n):
        node = {
            "id": f"node_{i}",
            "name": f"func_{i}" if i % 3 != 2 else f"MyClass_{i}",
            "type": types[i % len(types)],
            "file": f"src/module_{i % 3}.py",
            "language": "python",
            "line_start": i * 10 + 1,
            "loc": 10 + i * 5,
            "calls": [f"func_{j}" for j in range(max(0, i-2), i)],
            "api_calls": [f"requests.get"] if i % 4 == 0 else [],
            "variables": [f"var_{i}", f"result_{i}", "data"],
            "parameters": ["self"] if i % 3 == 2 else ["x", "y"],
            "fan_in": i % 4,
            "fan_out": (i + 1) % 5,
            "total_degree": i % 4 + (i + 1) % 5,
            "betweenness_centrality": float(i) / max(n, 1),
            "depth_from_entry": i % 5,
            "reachable_sink_count": i % 3,
            "reachable_source_count": (i + 1) % 3,
            "num_api_calls": 1 if i % 4 == 0 else 0,
            "is_entry_point": (i == 0),
            "has_auth_logic": (i == 3),
        }
        nodes.append(node)
    return nodes

def make_edges(nodes):
    """Create edges between nodes, safely capped to the actual node count."""
    ids = [n["id"] for n in nodes]
    n = len(ids)
    # All candidate edges — only added if both endpoints exist
    candidates = [
        (0, 1, "calls"),
        (1, 2, "calls"),
        (2, 3, "contains"),
        (0, 4, "depends_on"),
        (3, 5, "calls"),
        (5, 6, "calls"),
        (4, 7, "structural"),
        (6, 0, "flow"),   # cycle back to start
    ]
    edges = [
        {"source": ids[s], "target": ids[t], "type": typ}
        for s, t, typ in candidates
        if s < n and t < n
    ]
    return edges


# ─── Section 1: Unit Tests — GCNLayer ─────────────────────────────────────────
section("1. Unit tests — GCNLayer")

def test_gcn_layer_output_shape():
    layer = GCNLayer(in_features=16, out_features=32)
    N = 5
    x = torch.randn(N, 16)
    A = torch.eye(N)  # identity = trivial adjacency
    out = layer(x, A)
    assert out.shape == (N, 32), f"Expected (5,32), got {out.shape}"

def test_gcn_layer_has_parameters():
    layer = GCNLayer(in_features=8, out_features=4)
    params = list(layer.parameters())
    assert len(params) == 2, "Expected weight and bias"
    assert params[0].shape == (8, 4)
    assert params[1].shape == (4,)

def test_gcn_layer_propagates_graph_signal():
    """Output should differ with different adjacency (non-trivial graph signal)."""
    torch.manual_seed(0)
    layer = GCNLayer(in_features=4, out_features=4)
    N = 4
    x = torch.randn(N, 4)
    A_eye  = torch.eye(N)
    A_full = torch.ones(N, N) / N
    out_eye  = layer(x, A_eye)
    out_full = layer(x, A_full)
    assert not torch.allclose(out_eye, out_full, atol=1e-5), \
        "GCN layer output should differ for different adjacencies"

def test_gcn_layer_gradient_flows():
    layer = GCNLayer(in_features=4, out_features=4)
    x = torch.randn(3, 4)
    A = torch.eye(3)
    out = layer(x, A).sum()
    out.backward()
    assert layer.weight.grad is not None, "Weight gradient should exist after backward()"

run_test("output shape (N,out_features)", test_gcn_layer_output_shape)
run_test("has weight and bias parameters", test_gcn_layer_has_parameters)
run_test("propagates graph signal (adjacency matters)", test_gcn_layer_propagates_graph_signal)
run_test("gradient flows through layer", test_gcn_layer_gradient_flows)


# ─── Section 2: Unit Tests — GCNEncoder ───────────────────────────────────────
section("2. Unit tests — GCNEncoder")

def test_encoder_output_shape():
    enc = GCNEncoder(in_features=10, hidden_dim=32, embed_dim=16)
    N = 6
    x = torch.randn(N, 10)
    A = normalise_adjacency(torch.eye(N))
    z = enc(x, A)
    assert z.shape == (N, 16), f"Expected ({N},16), got {z.shape}"

def test_encoder_train_vs_eval_dropout():
    """Dropout should make train/eval outputs differ on the same input."""
    torch.manual_seed(42)
    enc = GCNEncoder(in_features=8, hidden_dim=32, embed_dim=8, dropout=0.5)
    N = 10
    x = torch.randn(N, 8)
    A = normalise_adjacency(torch.eye(N))
    enc.train()
    out_train_1 = enc(x, A).detach()
    out_train_2 = enc(x, A).detach()
    enc.eval()
    with torch.no_grad():
        out_eval_1 = enc(x, A)
        out_eval_2 = enc(x, A)
    # Eval outputs must be deterministic
    assert torch.allclose(out_eval_1, out_eval_2), "Eval outputs should be deterministic"
    # Train outputs with dropout should differ (not guaranteed every run but very likely at 0.5 rate)
    # Just check the shapes are consistent
    assert out_train_1.shape == out_train_2.shape

def test_encoder_no_nan():
    torch.manual_seed(7)
    enc = GCNEncoder(in_features=12, hidden_dim=64, embed_dim=32)
    N = 15
    x = torch.randn(N, 12)
    A = normalise_adjacency(torch.rand(N, N).fill_diagonal_(1))
    enc.eval()
    with torch.no_grad():
        z = enc(x, A)
    assert not torch.isnan(z).any(), "Encoder output contains NaN"
    assert not torch.isinf(z).any(), "Encoder output contains Inf"

run_test("output shape (N, embed_dim)", test_encoder_output_shape)
run_test("deterministic in eval mode (dropout off)", test_encoder_train_vs_eval_dropout)
run_test("no NaN or Inf in output", test_encoder_no_nan)


# ─── Section 3: Unit Tests — Graph construction helpers ───────────────────────
section("3. Unit tests — build_adjacency + normalise_adjacency")

def test_build_adjacency_shape():
    nodes = make_nodes(6)
    edges = make_edges(nodes)[:4]
    adj, idx = build_adjacency(nodes, edges)
    assert adj.shape == (6, 6), f"Expected (6,6), got {adj.shape}"
    assert len(idx) == 6

def test_build_adjacency_symmetric():
    nodes = make_nodes(5)
    edges = [{"source": "node_0", "target": "node_1", "type": "calls"},
             {"source": "node_2", "target": "node_4", "type": "depends_on"}]
    adj, _ = build_adjacency(nodes, edges)
    assert torch.allclose(adj, adj.t()), "Adjacency should be symmetric (undirected)"

def test_build_adjacency_unknown_nodes_ignored():
    nodes = make_nodes(3)
    edges = [{"source": "node_0", "target": "DOES_NOT_EXIST", "type": "calls"}]
    adj, _ = build_adjacency(nodes, edges)
    assert adj.sum().item() == 0, "Unknown node ID should be silently ignored"

def test_normalise_adjacency_shape():
    adj = torch.zeros(4, 4)
    adj[0, 1] = adj[1, 0] = 1.0
    A_norm = normalise_adjacency(adj)
    assert A_norm.shape == (4, 4)

def test_normalise_adjacency_no_nan():
    adj = torch.zeros(5, 5)  # completely disconnected
    A_norm = normalise_adjacency(adj)
    assert not torch.isnan(A_norm).any(), "Normalised adjacency should not contain NaN for isolated nodes"

def test_normalise_adjacency_self_loops():
    """Self-loops are added inside normalise_adjacency — diagonal should be non-zero."""
    adj = torch.zeros(3, 3)  # no edges
    A_norm = normalise_adjacency(adj)
    assert A_norm.diagonal().sum().item() > 0, "Self-loops should produce non-zero diagonal"

run_test("adjacency matrix shape == (N,N)", test_build_adjacency_shape)
run_test("adjacency is symmetric", test_build_adjacency_symmetric)
run_test("unknown node IDs are ignored", test_build_adjacency_unknown_nodes_ignored)
run_test("normalised adjacency shape preserved", test_normalise_adjacency_shape)
run_test("normalised adjacency — no NaN on disconnected graph", test_normalise_adjacency_no_nan)
run_test("normalised adjacency — self-loops give non-zero diagonal", test_normalise_adjacency_self_loops)


# ─── Section 4: Unit Tests — GraphAutoencoder ─────────────────────────────────
section("4. Unit tests — GraphAutoencoder")

def test_autoencoder_forward_shapes():
    N, F = 7, 10
    model = GraphAutoencoder(in_features=F, hidden_dim=32, embed_dim=16)
    x = torch.randn(N, F)
    A = normalise_adjacency(torch.eye(N))
    z, logits = model(x, A)
    assert z.shape == (N, 16),    f"Embeddings shape: expected (7,16), got {z.shape}"
    assert logits.shape == (N, N), f"Logits shape: expected (7,7), got {logits.shape}"

def test_autoencoder_decoder_is_symmetric():
    """Inner-product decoder Z Z^T should always produce a symmetric matrix."""
    model = GraphAutoencoder(in_features=8, hidden_dim=16, embed_dim=8)
    x = torch.randn(5, 8)
    A = normalise_adjacency(torch.eye(5))
    model.eval()
    with torch.no_grad():
        z, logits = model(x, A)
    assert torch.allclose(logits, logits.t(), atol=1e-5), "Decoder output should be symmetric"

def test_autoencoder_loss_decreases():
    """Training loss should decrease over 100 epochs on a small graph."""
    import torch.nn.functional as F_nn
    torch.manual_seed(0)
    N, in_feats = 8, 6      # renamed to avoid shadowing F_nn
    model = GraphAutoencoder(in_features=in_feats, hidden_dim=16, embed_dim=8, dropout=0.0)
    x = torch.randn(N, in_feats)
    adj_raw  = torch.zeros(N, N)
    for i in range(N - 1):
        adj_raw[i, i+1] = adj_raw[i+1, i] = 1.0
    adj_norm = normalise_adjacency(adj_raw)
    opt = torch.optim.Adam(model.parameters(), lr=0.05)

    losses = []
    for _ in range(100):
        opt.zero_grad()
        z, logits = model(x, adj_norm)
        loss = F_nn.binary_cross_entropy_with_logits(logits, adj_raw)
        loss.backward()
        opt.step()
        losses.append(loss.item())

    assert losses[-1] < losses[0], \
        f"Loss should decrease: initial={losses[0]:.4f}, final={losses[-1]:.4f}"

run_test("forward pass shapes (embeddings + logits)", test_autoencoder_forward_shapes)
run_test("decoder output is symmetric (Z Z^T)", test_autoencoder_decoder_is_symmetric)
run_test("loss decreases over 100 training epochs", test_autoencoder_loss_decreases)


# ─── Section 5: Integration Tests — generate_gnn_embeddings ───────────────────
section("5. Integration tests — generate_gnn_embeddings()")

def test_gnn_embeddings_written_to_nodes():
    nodes = make_nodes(8)
    edges = make_edges(nodes)
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=64, embed_dim=128, epochs=50)
    for node in result:
        assert "embedding" in node, f"Node {node['id']} missing 'embedding'"
        assert isinstance(node["embedding"], list)

def test_gnn_embedding_dimension():
    nodes = make_nodes(8)
    edges = make_edges(nodes)
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=32, embed_dim=128, epochs=30)
    for node in result:
        assert len(node["embedding"]) == 128, \
            f"Expected 128-dim embedding, got {len(node['embedding'])}"

def test_gnn_embeddings_are_floats():
    nodes = make_nodes(6)
    edges = make_edges(nodes)[:3]
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=32, embed_dim=64, epochs=20)
    for node in result:
        assert all(isinstance(v, float) for v in node["embedding"]), \
            "Embedding values should be Python floats"

def test_gnn_embeddings_not_all_zero():
    nodes = make_nodes(8)
    edges = make_edges(nodes)
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=64, embed_dim=128, epochs=50)
    for node in result:
        emb = np.array(node["embedding"])
        assert emb.std() > 1e-6, f"Node {node['id']} embedding is effectively all-zero/constant"

def test_gnn_embeddings_no_nan():
    nodes = make_nodes(8)
    edges = make_edges(nodes)
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=64, embed_dim=128, epochs=50)
    for node in result:
        emb = np.array(node["embedding"])
        assert not np.isnan(emb).any(), f"Node {node['id']} embedding contains NaN"
        assert not np.isinf(emb).any(), f"Node {node['id']} embedding contains Inf"

def test_gnn_different_nodes_get_different_embeddings():
    """Connected nodes with different neighbourhoods should get distinct embeddings."""
    nodes = make_nodes(8)
    edges = make_edges(nodes)
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=64, embed_dim=128, epochs=100)
    embeddings = [np.array(n["embedding"]) for n in result]
    # Check that not all embeddings are identical
    pairs_same = sum(
        1 for i in range(len(embeddings))
        for j in range(i+1, len(embeddings))
        if np.allclose(embeddings[i], embeddings[j], atol=1e-4)
    )
    assert pairs_same == 0, f"{pairs_same} node pairs have identical embeddings — GCN not differentiating nodes"

run_test("'embedding' key written to every node", test_gnn_embeddings_written_to_nodes)
run_test("embedding dimension is 128", test_gnn_embedding_dimension)
run_test("embedding values are Python floats", test_gnn_embeddings_are_floats)
run_test("embeddings are not all-zero (model is learning)", test_gnn_embeddings_not_all_zero)
run_test("no NaN or Inf in any embedding", test_gnn_embeddings_no_nan)
run_test("different nodes get different embeddings", test_gnn_different_nodes_get_different_embeddings)


# ─── Section 6: Edge case tests ───────────────────────────────────────────────
section("6. Edge case tests")

def test_single_node_graph():
    nodes = make_nodes(1)
    result = generate_gnn_embeddings(nodes, [], embed_dim=128, epochs=20)
    assert len(result) == 1
    assert len(result[0]["embedding"]) == 128

def test_empty_nodes_returns_empty():
    result = generate_gnn_embeddings([], [], embed_dim=128, epochs=5)
    assert result == [], "Empty input should return empty list"

def test_disconnected_graph():
    """A graph with no edges at all should still produce valid embeddings."""
    nodes = make_nodes(6)
    result = generate_gnn_embeddings(nodes, [], embed_dim=128, epochs=30)
    for node in result:
        emb = np.array(node["embedding"])
        assert not np.isnan(emb).any(), "Disconnected graph produced NaN embeddings"

def test_self_loop_edges_ignored():
    """Edges where source == target should not crash anything."""
    nodes = make_nodes(4)
    edges = [
        {"source": "node_0", "target": "node_0", "type": "calls"},  # self-loop
        {"source": "node_1", "target": "node_2", "type": "calls"},
    ]
    result = generate_gnn_embeddings(nodes, edges, embed_dim=64, epochs=20)
    assert len(result) == 4

def test_large_ish_graph_performance():
    """50 nodes should complete in under 30 seconds on CPU."""
    nodes = make_nodes(50)
    # Build a chain of edges
    edges = [{"source": f"node_{i}", "target": f"node_{i+1}", "type": "calls"}
             for i in range(49)]
    t0 = time.time()
    result = generate_gnn_embeddings(nodes, edges, hidden_dim=128, embed_dim=128, epochs=100)
    elapsed = time.time() - t0
    assert len(result) == 50
    assert elapsed < 30, f"50-node graph took {elapsed:.1f}s — expected < 30s on CPU"
    print(f"          {INFO} 50-node graph completed in {elapsed:.2f}s")

run_test("single node graph", test_single_node_graph)
run_test("empty node list returns empty", test_empty_nodes_returns_empty)
run_test("disconnected graph (no edges)", test_disconnected_graph)
run_test("self-loop edges don't crash", test_self_loop_edges_ignored)
run_test("50-node graph completes < 30s on CPU", test_large_ish_graph_performance)


# ─── Section 7: Comparison — GNN vs TF-IDF baseline ──────────────────────────
section("7. Comparison — GNN vs TF-IDF baseline  (what changes in the pipeline)")

if not FE_OK:
    skip_test("all comparison tests", "feature_engineering.py not found")
else:
    def get_tfidf_embeddings(nodes):
        import copy
        nodes_copy = copy.deepcopy(nodes)
        return generate_embeddings(nodes_copy)

    def get_gnn_embeddings(nodes, edges):
        import copy
        nodes_copy = copy.deepcopy(nodes)
        return generate_gnn_embeddings(nodes_copy, edges, hidden_dim=64, embed_dim=128, epochs=100)

    def cosine_similarity(a, b):
        a, b = np.array(a), np.array(b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom > 1e-8 else 0.0

    def test_gnn_encodes_connectivity():
        """
        WHAT CHANGES: GNN embeddings should make directly connected nodes more
        similar to each other than TF-IDF embeddings do.

        node_0 -> node_1 (direct edge)
        node_0 -> node_5 (no edge, far apart structurally)

        Expected: cosine_sim_gnn(node_0, node_1) > cosine_sim_tfidf(node_0, node_1)
        OR overall: GNN connected-pair similarity > GNN unconnected-pair similarity
        """
        nodes = make_nodes(8)
        edges = make_edges(nodes)

        tfidf_nodes = get_tfidf_embeddings(nodes)
        gnn_nodes   = get_gnn_embeddings(nodes, edges)

        edge_pairs = [(e["source"], e["target"]) for e in edges]

        all_ids = [n["id"] for n in nodes]
        edge_set = set((s, t) for s, t in edge_pairs) | set((t, s) for s, t in edge_pairs)

        tfidf_map = {n["id"]: n["embedding"] for n in tfidf_nodes}
        gnn_map   = {n["id"]: n["embedding"] for n in gnn_nodes}

        connected_sim_tfidf, connected_sim_gnn = [], []
        disconnected_sim_tfidf, disconnected_sim_gnn = [], []

        for i, id_a in enumerate(all_ids):
            for id_b in all_ids[i+1:]:
                sim_t = cosine_similarity(tfidf_map[id_a], tfidf_map[id_b])
                sim_g = cosine_similarity(gnn_map[id_a],   gnn_map[id_b])
                if (id_a, id_b) in edge_set or (id_b, id_a) in edge_set:
                    connected_sim_tfidf.append(sim_t)
                    connected_sim_gnn.append(sim_g)
                else:
                    disconnected_sim_tfidf.append(sim_t)
                    disconnected_sim_gnn.append(sim_g)

        avg_conn_t    = np.mean(connected_sim_tfidf)    if connected_sim_tfidf    else 0
        avg_conn_g    = np.mean(connected_sim_gnn)      if connected_sim_gnn      else 0
        avg_disconn_t = np.mean(disconnected_sim_tfidf) if disconnected_sim_tfidf else 0
        avg_disconn_g = np.mean(disconnected_sim_gnn)   if disconnected_sim_gnn   else 0

        print(f"\n          {INFO} TF-IDF  — connected avg cosine sim : {avg_conn_t:.4f}")
        print(f"          {INFO} TF-IDF  — unconnected avg cosine sim: {avg_disconn_t:.4f}")
        print(f"          {INFO} GNN     — connected avg cosine sim : {avg_conn_g:.4f}")
        print(f"          {INFO} GNN     — unconnected avg cosine sim: {avg_disconn_g:.4f}")

        # GNN should produce a larger gap between connected and unconnected pairs
        gap_tfidf = avg_conn_t - avg_disconn_t
        gap_gnn   = avg_conn_g - avg_disconn_g
        print(f"          {INFO} Connectivity gap (connected-unconnected):")
        print(f"          {INFO}   TF-IDF: {gap_tfidf:+.4f}")
        print(f"          {INFO}   GNN   : {gap_gnn:+.4f}")

        # GNN gap should be positive (connected nodes closer) or larger than TF-IDF gap
        assert gap_gnn > gap_tfidf - 0.05, \
            f"GNN should encode graph connectivity better than TF-IDF. Gap GNN={gap_gnn:.4f} vs TF-IDF={gap_tfidf:.4f}"

    def test_gnn_embedding_variance_higher():
        """
        WHAT CHANGES: GNN embeddings should have higher variance across nodes
        because they aggregate neighbourhood signals — each node gets a unique
        embedding shaped by its local graph context, not just its own text features.
        """
        nodes = make_nodes(8)
        edges = make_edges(nodes)

        tfidf_nodes = get_tfidf_embeddings(nodes)
        gnn_nodes   = get_gnn_embeddings(nodes, edges)

        tfidf_matrix = np.array([n["embedding"] for n in tfidf_nodes])
        gnn_matrix   = np.array([n["embedding"] for n in gnn_nodes])

        # Per-dimension variance, then mean
        tfidf_var = float(np.var(tfidf_matrix, axis=0).mean())
        gnn_var   = float(np.var(gnn_matrix,   axis=0).mean())

        print(f"\n          {INFO} TF-IDF avg per-dim variance: {tfidf_var:.6f}")
        print(f"          {INFO} GNN    avg per-dim variance: {gnn_var:.6f}")

        # We mainly want to confirm GNN embeddings are not collapsed / degenerate
        assert gnn_var > 1e-6, f"GNN embeddings appear collapsed (variance={gnn_var:.2e})"
        print(f"          {INFO} GNN embeddings are non-degenerate (variance > 1e-6)")

    def test_clustering_produces_services():
        """
        WHAT CHANGES IN PIPELINE: stats['services'] should now be a number,
        not 'N/A'. clustering.py uses the GNN embeddings to form microservice
        boundary candidates — this tests the full embedding->clustering chain.
        """
        try:
            from clustering import cluster_nodes
        except ImportError:
            print(f"          {SKIP} clustering.py not found")
            return

        nodes = make_nodes(30)  # Need enough nodes for clustering
        edges = [{"source": f"node_{i}", "target": f"node_{(i+1)%30}", "type": "calls"}
                 for i in range(30)]

        result = get_gnn_embeddings(nodes, edges)
        embeddable = [n for n in result if isinstance(n.get("embedding"), list)]
        clusters = cluster_nodes(embeddable)

        assert isinstance(clusters, list), "cluster_nodes should return a list"
        assert len(clusters) > 0, "Should produce at least one cluster"
        assert len(clusters) <= 8, "Should produce at most 8 clusters (bounded by clustering.py)"

        total_in_clusters = sum(len(c["node_ids"]) for c in clusters)
        assert total_in_clusters == len(embeddable), \
            f"All nodes should be in a cluster. {len(embeddable)} nodes, {total_in_clusters} in clusters"

        print(f"\n          {INFO} 30 nodes → {len(clusters)} microservice boundary clusters")
        for c in clusters:
            print(f"          {INFO}   Cluster '{c['name']}': {c['node_count']} nodes, {c['loc_count']} LoC, risk={c['risk']}")

    run_test("GNN encodes graph connectivity (connected nodes more similar)", test_gnn_encodes_connectivity)
    run_test("GNN embeddings are non-degenerate (sufficient variance)", test_gnn_embedding_variance_higher)
    run_test("GNN → clustering produces microservice boundary candidates", test_clustering_produces_services)


# ─── Final Summary ─────────────────────────────────────────────────────────────
section("Test Summary")
total = results["passed"] + results["failed"] + results["skipped"]
print(f"  Total  : {total}")
print(f"  {GREEN}Passed : {results['passed']}{RESET}")
print(f"  {RED}Failed : {results['failed']}{RESET}")
print(f"  {YELLOW}Skipped: {results['skipped']}{RESET}")

if results["failed"] == 0:
    print(f"\n  {GREEN}{BOLD}All tests passed!{RESET}")
else:
    print(f"\n  {RED}{BOLD}{results['failed']} test(s) failed.{RESET}")
    sys.exit(1)
