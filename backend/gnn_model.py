"""
gnn_model.py — Lightweight Graph Convolutional Network for CodeForge

Architecture: 2-layer GCN (Graph Autoencoder style)
  - Input  : N x F  node feature matrix (F = 77 from feature_engineering.py)
  - Layer 1: GCN conv  F  -> 256  (ReLU + Dropout)
  - Layer 2: GCN conv 256 -> 128  (final node embeddings)
  - Decoder: inner-product reconstruction of adjacency (unsupervised)

Training objective: reconstruct which nodes are connected (link prediction).
No labelled data required — the graph structure itself is the supervision signal.

Why GCN over Transformer for this task:
  - Data is a graph (CPG) — GCN processes edges natively; Transformer ignores them.
  - O(N * avg_degree) message passing vs O(N^2) attention — scales to large codebases.
  - Node embeddings encode neighbourhood context (caller/callee patterns, risk propagation).
  - 128-dim output slots directly into the existing cluster_nodes() pipeline.

Usage:
    from gnn_model import generate_gnn_embeddings
    nodes = generate_gnn_embeddings(nodes, edges)   # nodes get 'embedding' set in-place
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Tuple


# ---------------------------------------------------------------------------
# GCN Layer
# ---------------------------------------------------------------------------

class GCNLayer(nn.Module):
    """
    Single Graph Convolutional layer.

    Implements:  H' = σ( D^{-1/2} A_hat D^{-1/2} H W )

    Where A_hat = A + I  (self-loops added so each node attends to itself too).
    D is the degree matrix of A_hat.

    Using the symmetric normalisation keeps gradients stable and prevents
    high-degree nodes from dominating the aggregation.
    """

    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(in_features, out_features))
        self.bias   = nn.Parameter(torch.zeros(out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        # Linear transform: X W
        support = x @ self.weight + self.bias          # (N, out)
        # Graph aggregation: A_hat_norm * support
        return adj_norm @ support                       # (N, out)


# ---------------------------------------------------------------------------
# 2-Layer GCN Encoder
# ---------------------------------------------------------------------------

class GCNEncoder(nn.Module):
    """
    Two-layer GCN that maps node features to 128-dim embeddings.

    Layer 1: in_features -> hidden_dim  (ReLU + Dropout)
    Layer 2: hidden_dim  -> embed_dim   (linear — no activation on final layer)
    """

    def __init__(self, in_features: int, hidden_dim: int = 256, embed_dim: int = 128,
                 dropout: float = 0.3):
        super().__init__()
        self.conv1   = GCNLayer(in_features, hidden_dim)
        self.conv2   = GCNLayer(hidden_dim, embed_dim)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.conv1(x, adj_norm))
        h = self.dropout(h)
        z = self.conv2(h, adj_norm)          # Raw embeddings — no activation
        return z                             # (N, embed_dim)


# ---------------------------------------------------------------------------
# Graph Autoencoder (Decoder = inner-product)
# ---------------------------------------------------------------------------

class GraphAutoencoder(nn.Module):
    """
    Unsupervised Graph Autoencoder.

    Encoder : GCNEncoder  →  Z  (N x embed_dim)
    Decoder : Z Z^T       →  A_reconstructed  (N x N logits)

    Loss: Binary cross-entropy between A_reconstructed and the true adjacency A.
    This trains the encoder to produce embeddings where connected nodes end up
    close together in embedding space (dot product ≈ 1) and disconnected nodes
    end up far apart (dot product ≈ 0).
    """

    def __init__(self, in_features: int, hidden_dim: int = 256, embed_dim: int = 128,
                 dropout: float = 0.3):
        super().__init__()
        self.encoder = GCNEncoder(in_features, hidden_dim, embed_dim, dropout)

    def encode(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        return self.encoder(x, adj_norm)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Inner-product decoder: logits[i,j] = z_i · z_j"""
        return z @ z.t()                     # (N, N) logits

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        z = self.encode(x, adj_norm)
        return z, self.decode(z)


# ---------------------------------------------------------------------------
# Graph Construction Helpers
# ---------------------------------------------------------------------------

def build_adjacency(nodes: List[Dict], edges: List[Dict]) -> Tuple[torch.Tensor, Dict[str, int]]:
    """
    Build a sparse-friendly adjacency matrix from node/edge dicts.

    Returns:
        adj  : (N, N) float32 tensor (binary, NOT normalised yet)
        idx  : {node_id: row_index}  mapping
    """
    idx = {n["id"]: i for i, n in enumerate(nodes)}
    N   = len(nodes)
    adj = torch.zeros(N, N, dtype=torch.float32)

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src in idx and tgt in idx:
            i, j = idx[src], idx[tgt]
            adj[i, j] = 1.0
            adj[j, i] = 1.0   # Treat as undirected for message passing

    return adj, idx


def normalise_adjacency(adj: torch.Tensor) -> torch.Tensor:
    """
    Compute the symmetric normalised adjacency with self-loops:

        A_hat     = A + I
        D_hat     = diag(row_sums of A_hat)
        A_hat_norm = D_hat^{-1/2}  A_hat  D_hat^{-1/2}

    This is the standard GCN normalisation from Kipf & Welling (2017).
    """
    N     = adj.shape[0]
    A_hat = adj + torch.eye(N, dtype=torch.float32)
    deg   = A_hat.sum(dim=1)                        # (N,)
    d_inv_sqrt = torch.pow(deg.clamp(min=1e-8), -0.5)
    D_inv_sqrt = torch.diag(d_inv_sqrt)             # (N, N)
    return D_inv_sqrt @ A_hat @ D_inv_sqrt           # (N, N)


# ---------------------------------------------------------------------------
# Unsupervised Training Loop
# ---------------------------------------------------------------------------

def train_gae(model: GraphAutoencoder, x: torch.Tensor, adj_norm: torch.Tensor,
              adj_target: torch.Tensor, epochs: int = 200, lr: float = 0.01,
              weight_decay: float = 5e-4) -> GraphAutoencoder:
    """
    Train the Graph Autoencoder using link-prediction loss.

    Since the CPG tends to be sparse (most node pairs are NOT connected),
    we apply positive-class weighting so the loss doesn't collapse to "predict
    no edges" — a common failure mode on sparse graphs.

    Args:
        model      : GraphAutoencoder instance
        x          : (N, F) node feature tensor
        adj_norm   : (N, N) normalised adjacency (used by GCN layers)
        adj_target : (N, N) binary adjacency (supervision signal)
        epochs     : training iterations
        lr         : Adam learning rate
        weight_decay: L2 regularisation

    Returns:
        Trained model.
    """
    optimiser = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    # Positive-class weight = ratio of negatives to positives (handles sparsity)
    n_pos = adj_target.sum().item()
    n_neg = adj_target.numel() - n_pos
    pos_weight = torch.tensor(n_neg / max(n_pos, 1), dtype=torch.float32)

    model.train()
    for epoch in range(epochs):
        optimiser.zero_grad()
        z, logits = model(x, adj_norm)
        loss = F.binary_cross_entropy_with_logits(logits, adj_target,
                                                   pos_weight=pos_weight)
        loss.backward()
        optimiser.step()

        if (epoch + 1) % 50 == 0:
            print(f"[GNN] Epoch {epoch+1:03d}/{epochs}  loss={loss.item():.4f}")

    return model


# ---------------------------------------------------------------------------
# Public Entry Point
# ---------------------------------------------------------------------------

def generate_gnn_embeddings(nodes: List[Dict], edges: List[Dict],
                            hidden_dim: int = 256, embed_dim: int = 128,
                            epochs: int = 200) -> List[Dict]:
    """
    Generate GNN-based 128-dim embeddings for each node and attach them
    as node['embedding'].  Falls back to the TF-IDF baseline silently on error.

    This function is a drop-in replacement for generate_embeddings() in
    feature_engineering.py, but produces richer embeddings because the GCN
    aggregates information from each node's 1- and 2-hop neighbourhood in the
    Code Property Graph.

    Pipeline:
        1. Build initial 77-dim features  (TF-IDF + structural metrics)
        2. Build adjacency matrix A from edges
        3. Normalise A  →  A_hat_norm
        4. Train 2-layer GCN Autoencoder (unsupervised, link-prediction loss)
        5. Extract Z = encoder(X, A_hat_norm)  — final 128-dim embeddings
        6. Write embedding back into each node dict

    Args:
        nodes      : List of node dicts (output of build_cpg)
        edges      : List of edge dicts  {source, target, type, ...}
        hidden_dim : GCN hidden layer width (default 256)
        embed_dim  : Output embedding dimension (default 128, matches clustering.py)
        epochs     : Unsupervised training epochs (200 is fast; raise to 400 for quality)

    Returns:
        nodes with 'embedding' key set (in-place modification + return).
    """
    if not nodes:
        return nodes

    try:
        # ------------------------------------------------------------------
        # Step 1: Node feature matrix X using existing feature pipeline
        # ------------------------------------------------------------------
        from feature_engineering import prepare_initial_features
        feats_np = prepare_initial_features(nodes)          # (N, F)
        x = torch.tensor(feats_np, dtype=torch.float32)
        in_features = x.shape[1]
        N = x.shape[0]

        print(f"[GNN] Building graph: {N} nodes, {len(edges)} edges")

        # ------------------------------------------------------------------
        # Step 2 & 3: Adjacency + normalisation
        # ------------------------------------------------------------------
        adj_raw, node_idx = build_adjacency(nodes, edges)   # (N, N) binary
        adj_norm = normalise_adjacency(adj_raw)              # (N, N) normalised

        # ------------------------------------------------------------------
        # Step 4: Initialise and train the Graph Autoencoder
        # ------------------------------------------------------------------
        model = GraphAutoencoder(
            in_features=in_features,
            hidden_dim=hidden_dim,
            embed_dim=embed_dim,
            dropout=0.3 if N > 20 else 0.0   # No dropout on tiny graphs
        )

        print(f"[GNN] Training Graph Autoencoder  "
              f"(in={in_features} → hidden={hidden_dim} → embed={embed_dim}, "
              f"epochs={epochs})")

        model = train_gae(model, x, adj_norm, adj_raw, epochs=epochs)

        # ------------------------------------------------------------------
        # Step 5: Extract embeddings (inference mode, no gradient)
        # ------------------------------------------------------------------
        model.eval()
        with torch.no_grad():
            z = model.encode(x, adj_norm)           # (N, embed_dim)
        z_np = z.numpy()                            # (N, 128)

        # ------------------------------------------------------------------
        # Step 6: Write embeddings back into node dicts
        # ------------------------------------------------------------------
        id_to_row = {n["id"]: i for i, n in enumerate(nodes)}
        for node in nodes:
            row = id_to_row.get(node["id"])
            if row is not None:
                node["embedding"] = z_np[row].tolist()
            else:
                node["embedding"] = [0.0] * embed_dim

        print(f"[GNN] Done. Generated {embed_dim}-dim GNN embeddings for {N} nodes.")
        return nodes

    except ImportError as e:
        print(f"[GNN] PyTorch not available ({e}). Falling back to TF-IDF embeddings.")
        from feature_engineering import generate_embeddings
        return generate_embeddings(nodes)

    except Exception as e:
        import traceback
        print(f"[GNN] Embedding generation failed: {e}\n{traceback.format_exc()}")
        print("[GNN] Falling back to TF-IDF embeddings.")
        from feature_engineering import generate_embeddings
        return generate_embeddings(nodes)
