"""
train_pretrained_gnn.py
=======================
Pre-trains the CodeForge GNN encoder across all collected CPG graphs
and saves the encoder weights as gnn_encoder_pretrained.pt.

This script replaces per-job training in gnn_model.py. Once weights are
produced here, generate_gnn_embeddings() loads them at startup and skips
training entirely — reducing embedding time from ~2s to ~50ms per job.

Improvements over per-job training in gnn_model.py:
  1. Multi-graph training  — model sees 28 diverse graphs per epoch
                             instead of one, eliminating the 0.75 plateau
  2. L2-normalised decoder — prevents magnitude cheating in inner product
  3. ReduceLROnPlateau     — halves LR after 30 epochs of no improvement
  4. Early stopping        — stops when val loss plateaus (saves time)
  5. Gradient clipping     — prevents exploding gradients on large graphs
  6. Checkpoint saving     — best weights are always preserved

Run locally (sanity check — 30 epochs, ~30 seconds):
    cd backend
    python train_pretrained_gnn.py --local --epochs 30

Run full training locally (500 epochs, ~10–20 minutes on CPU):
    python train_pretrained_gnn.py --local

Submit to Azure ML GPU cluster (via azure_job_submit.py):
    python azure_job_submit.py
    (this script runs automatically on the cluster)

Flags:
    --data DIR      Path to training data directory (default: ./training_data)
    --dataset FILE  Path to dataset.pt directly (overrides --data)
    --epochs N      Maximum training epochs (default: 500)
    --lr FLOAT      Initial learning rate (default: 0.005)
    --hidden N      GCN hidden layer width (default: 256)
    --embed N       Embedding output dimension (default: 128)
    --dropout F     Dropout rate (default: 0.3)
    --local         Skip Azure upload after training
    --out FILE      Output weights path (default: ./gnn_encoder_pretrained.pt)
    --seed N        Random seed for reproducibility (default: 42)
"""

import os
import sys
import time
import json
import random
import argparse
import traceback
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Hyperparameters (all overridable via CLI flags)
# ---------------------------------------------------------------------------

DEFAULTS = {
    "epochs":       500,
    "lr":           0.005,
    "weight_decay": 1e-4,
    "hidden_dim":   256,
    "embed_dim":    128,
    "dropout":      0.3,
    "train_split":  0.85,
    "early_stop":   50,     # epochs of no improvement before stopping
    "lr_patience":  30,     # epochs before LR is halved
    "min_lr":       1e-5,
    "grad_clip":    1.0,
    "in_features":  77,     # must match feature_engineering.prepare_initial_features()
}

WEIGHTS_FILENAME = "gnn_encoder_pretrained.pt"
TRAINING_LOG     = "training_log.json"

# Terminal colours
BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
DIM   = "\033[2m"
RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Model Definition
# ---------------------------------------------------------------------------
# Defined here independently so this script has no import dependency on
# gnn_model.py. The architecture is identical — GCNEncoder weights saved
# here are directly loadable by gnn_model.GCNEncoder.load_state_dict().

class GCNLayer(nn.Module):
    """
    Single Graph Convolutional layer.
    H' = σ( D^{-1/2} A_hat D^{-1/2} H W )
    Xavier-uniform weight initialisation for stable training across graphs.
    """
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(in_features, out_features))
        self.bias   = nn.Parameter(torch.zeros(out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        return adj_norm @ (x @ self.weight + self.bias)


class GCNEncoder(nn.Module):
    """
    2-layer GCN encoder: in_features → hidden_dim → embed_dim
    Layer 1: ReLU + Dropout
    Layer 2: Linear  (no final activation — embedding space is unrestricted)
    """
    def __init__(self, in_features: int, hidden_dim: int = 256,
                 embed_dim: int = 128, dropout: float = 0.3):
        super().__init__()
        self.conv1   = GCNLayer(in_features, hidden_dim)
        self.conv2   = GCNLayer(hidden_dim, embed_dim)
        self.dropout = nn.Dropout(p=dropout)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.conv1(x, adj_norm))
        h = self.dropout(h)
        return self.conv2(h, adj_norm)


class GraphAutoencoder(nn.Module):
    """
    Graph Autoencoder with L2-normalised inner-product decoder.

    Standard decoder:     Z · Z^T   (unbounded — model can cheat with magnitudes)
    Improved decoder: norm(Z) · norm(Z)^T  (cosine similarity — bounded [-1,1])

    The L2 normalisation forces the model to encode graph structure in the
    *direction* of embeddings, not their magnitude. This directly addresses
    the 0.75 plateau seen in per-job training — the model can no longer
    trivially satisfy the loss by scaling embeddings.
    """
    def __init__(self, in_features: int, hidden_dim: int = 256,
                 embed_dim: int = 128, dropout: float = 0.3):
        super().__init__()
        self.encoder = GCNEncoder(in_features, hidden_dim, embed_dim, dropout)

    def encode(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        return self.encoder(x, adj_norm)

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        z_norm = F.normalize(z, p=2, dim=1)   # unit-norm rows
        return z_norm @ z_norm.t()             # (N, N) cosine similarity logits

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor):
        z = self.encode(x, adj_norm)
        return z, self.decode(z)


# ---------------------------------------------------------------------------
# Dataset Loading
# ---------------------------------------------------------------------------

def load_dataset(data_dir: str, dataset_file: str, in_features: int) -> list:
    """
    Load graphs from dataset.pt (preferred) or individual .pt files.

    Each graph dict contains:
        x        : (N, 77) float32  — node feature matrix
        adj      : (N, N)  float32  — binary adjacency
        adj_norm : (N, N)  float32  — normalised adjacency
        repo     : str
        num_nodes: int
        num_edges: int

    Skips graphs with wrong feature dimension or fewer than 5 nodes.
    """
    graphs   = []
    skipped  = 0

    # ── Try combined dataset.pt first ────────────────────────────────────────
    if dataset_file and os.path.exists(dataset_file):
        source = dataset_file
    else:
        default_ds = os.path.join(data_dir, "dataset.pt")
        source     = default_ds if os.path.exists(default_ds) else None

    if source:
        print(f"[Train] Loading combined dataset from {source} ...")
        raw  = torch.load(source, map_location="cpu")
        all_graphs = raw.get("graphs", [])
        print(f"[Train] Found {len(all_graphs)} graphs in dataset.pt")

        for g in all_graphs:
            if g["x"].shape[1] != in_features:
                print(f"[Train]   Skip {g.get('repo','?')} — "
                      f"feat_dim {g['x'].shape[1]} ≠ {in_features}")
                skipped += 1
                continue
            if g["num_nodes"] < 5:
                skipped += 1
                continue
            graphs.append(g)

    else:
        # ── Fallback: load individual .pt files ───────────────────────────
        import glob
        files = sorted([
            f for f in glob.glob(os.path.join(data_dir, "*.pt"))
            if Path(f).name != "dataset.pt"
        ])
        print(f"[Train] No dataset.pt found — loading {len(files)} individual files ...")

        for fpath in files:
            try:
                d = torch.load(fpath, map_location="cpu")
                if d["x"].shape[1] != in_features:
                    skipped += 1
                    continue
                if d.get("num_nodes", 0) < 5:
                    skipped += 1
                    continue
                graphs.append({
                    "x":         d["x"],
                    "adj":       d["adj"],
                    "adj_norm":  d["adj_norm"],
                    "repo":      d.get("repo", Path(fpath).stem),
                    "num_nodes": d["num_nodes"],
                    "num_edges": d.get("num_edges", 0),
                })
            except Exception as e:
                print(f"[Train]   Error loading {Path(fpath).name}: {e}")
                skipped += 1

    if not graphs:
        raise RuntimeError(
            "No valid graphs loaded. "
            "Run collect_training_data.py first, or check --data path."
        )

    print(f"[Train] Loaded {len(graphs)} graphs  ({skipped} skipped)")
    return graphs


def split_dataset(graphs: list, train_split: float, seed: int):
    """Shuffle and split into train/validation sets."""
    rng = random.Random(seed)
    shuffled = graphs[:]
    rng.shuffle(shuffled)
    n_train = max(1, int(len(shuffled) * train_split))
    return shuffled[:n_train], shuffled[n_train:]


# ---------------------------------------------------------------------------
# Loss Computation
# ---------------------------------------------------------------------------

def compute_graph_loss(model: GraphAutoencoder, graph: dict,
                       device: torch.device) -> torch.Tensor:
    """
    Binary cross-entropy loss with positive-class weighting for one graph.

    CPG graphs are very sparse — most node pairs are NOT connected.
    Without pos_weight the model would learn to predict "no edge" everywhere
    and achieve low loss trivially. The weight penalises false negatives
    proportionally to sparsity ratio.

    pos_weight = num_negative_pairs / num_positive_pairs
    e.g. 50 edges among 200 nodes → ~19,950 negatives, 100 positives
         → pos_weight ≈ 199.5  (each missed edge counts 200× as much)
    """
    x        = graph["x"].to(device)
    adj_norm = graph["adj_norm"].to(device)
    adj_raw  = graph["adj"].to(device)

    n_pos = adj_raw.sum().item()
    n_neg = adj_raw.numel() - n_pos
    pos_weight = torch.tensor(
        n_neg / max(n_pos, 1), dtype=torch.float32, device=device
    )

    _, logits = model(x, adj_norm)
    return F.binary_cross_entropy_with_logits(
        logits, adj_raw, pos_weight=pos_weight
    )


# ---------------------------------------------------------------------------
# Training Loop
# ---------------------------------------------------------------------------

def train(model: GraphAutoencoder, train_set: list, val_set: list,
          args, device: torch.device) -> dict:
    """
    Multi-graph training loop with:
      - Full dataset pass per epoch (each graph contributes one gradient update)
      - ReduceLROnPlateau scheduler
      - Early stopping on validation loss
      - Best-checkpoint tracking
      - Gradient clipping

    Returns a metrics dict for the training log.
    """
    optimiser = torch.optim.Adam(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimiser,
        mode     = "min",
        factor   = 0.5,
        patience = args.lr_patience,
        min_lr   = args.min_lr,
    )

    best_val_loss    = float("inf")
    best_state       = None
    patience_counter = 0
    history          = []
    t_start          = time.time()

    print(f"\n[Train] {BOLD}Starting training{RESET}")
    print(f"[Train]   graphs      : {len(train_set)} train  {len(val_set)} val")
    print(f"[Train]   device      : {device}")
    print(f"[Train]   epochs      : {args.epochs}")
    print(f"[Train]   lr          : {args.lr}  (min {args.min_lr})")
    print(f"[Train]   weight_decay: {args.weight_decay}")
    print(f"[Train]   early_stop  : {args.early_stop} patience epochs")
    print()

    for epoch in range(1, args.epochs + 1):

        # ── Train pass ────────────────────────────────────────────────────
        model.train()
        train_losses = []
        random.shuffle(train_set)          # different order each epoch

        for graph in train_set:
            optimiser.zero_grad()
            loss = compute_graph_loss(model, graph, device)
            loss.backward()
            # Gradient clipping — prevents spikes from large graphs
            nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimiser.step()
            train_losses.append(loss.item())

        train_loss = sum(train_losses) / len(train_losses)

        # ── Validation pass ───────────────────────────────────────────────
        model.eval()
        val_losses = []
        with torch.no_grad():
            for graph in val_set:
                val_losses.append(compute_graph_loss(model, graph, device).item())

        val_loss = (sum(val_losses) / len(val_losses)) if val_losses else train_loss
        lr_now   = optimiser.param_groups[0]["lr"]

        scheduler.step(val_loss)

        # ── Logging ───────────────────────────────────────────────────────
        history.append({
            "epoch":      epoch,
            "train_loss": round(train_loss, 6),
            "val_loss":   round(val_loss, 6),
            "lr":         round(lr_now, 8),
        })

        if epoch % 10 == 0 or epoch == 1:
            elapsed  = time.time() - t_start
            eta_secs = (elapsed / epoch) * (args.epochs - epoch)
            eta_str  = f"{int(eta_secs // 60)}m {int(eta_secs % 60)}s"

            # Colour val_loss by progress
            if val_loss < 0.4:
                v_col = GREEN
            elif val_loss < 0.6:
                v_col = YELLOW
            else:
                v_col = RED

            print(f"  Epoch {epoch:04d}/{args.epochs}  "
                  f"train={train_loss:.4f}  "
                  f"val={v_col}{val_loss:.4f}{RESET}  "
                  f"lr={lr_now:.6f}  "
                  f"eta={eta_str}")

        # ── Checkpoint — save best weights ────────────────────────────────
        if val_loss < best_val_loss - 1e-4:
            best_val_loss    = val_loss
            best_state       = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        # ── Early stopping ────────────────────────────────────────────────
        if patience_counter >= args.early_stop:
            print(f"\n[Train] {YELLOW}Early stopping at epoch {epoch} "
                  f"(no improvement for {args.early_stop} epochs){RESET}")
            print(f"[Train]   Best val loss : {best_val_loss:.4f}")
            break

    # Restore best weights
    if best_state is not None:
        model.load_state_dict(best_state)
        print(f"[Train] Restored best checkpoint  (val_loss={best_val_loss:.4f})")

    total_time = time.time() - t_start
    epochs_run = len(history)

    print(f"\n[Train] {GREEN}Training complete{RESET}")
    print(f"[Train]   Epochs run    : {epochs_run}")
    print(f"[Train]   Best val loss : {best_val_loss:.4f}")
    print(f"[Train]   Total time    : {total_time:.0f}s "
          f"({total_time / 60:.1f} min)")

    return {
        "best_val_loss": best_val_loss,
        "epochs_run":    epochs_run,
        "total_time_s":  round(total_time, 1),
        "history":       history,
    }


# ---------------------------------------------------------------------------
# Embedding Quality Evaluation
# ---------------------------------------------------------------------------

def evaluate_embedding_quality(model: GraphAutoencoder, val_set: list,
                                device: torch.device) -> dict:
    """
    Measure how well the trained embeddings encode graph connectivity.

    For each validation graph, compare cosine similarity between:
      - Connected node pairs   (should be HIGH — encoder learned to group them)
      - Unconnected node pairs (should be LOW  — encoder separates them)

    The gap (connected_sim - unconnected_sim) is the key metric.
    A gap > 0.3 indicates the embeddings are meaningfully encoding structure.
    Per-job training with the old code typically achieves ~0.1–0.2.
    Multi-graph pre-training should achieve 0.5+.
    """
    model.eval()
    all_connected    = []
    all_unconnected  = []

    with torch.no_grad():
        for graph in val_set[:5]:    # sample first 5 val graphs for speed
            x        = graph["x"].to(device)
            adj_norm = graph["adj_norm"].to(device)
            adj_raw  = graph["adj"].to(device)

            z      = model.encode(x, adj_norm)
            z_norm = F.normalize(z, p=2, dim=1)
            sim    = (z_norm @ z_norm.t()).cpu()

            # Sample connected pairs
            pos_mask = adj_raw.cpu() > 0
            if pos_mask.sum() > 0:
                all_connected.extend(sim[pos_mask].tolist())

            # Sample same number of unconnected pairs
            neg_mask = (adj_raw.cpu() == 0)
            neg_mask.fill_diagonal_(False)
            if neg_mask.sum() > 0:
                neg_sims = sim[neg_mask].tolist()
                # Cap sample size to avoid huge lists
                sample_n = min(len(all_connected), len(neg_sims), 5000)
                all_unconnected.extend(random.sample(neg_sims, sample_n))

    if not all_connected or not all_unconnected:
        return {"connected_sim": None, "unconnected_sim": None, "gap": None}

    conn_sim   = sum(all_connected)   / len(all_connected)
    unconn_sim = sum(all_unconnected) / len(all_unconnected)
    gap        = conn_sim - unconn_sim

    return {
        "connected_sim":   round(conn_sim,   4),
        "unconnected_sim": round(unconn_sim, 4),
        "gap":             round(gap,        4),
    }


# ---------------------------------------------------------------------------
# Save Weights
# ---------------------------------------------------------------------------

def save_weights(model: GraphAutoencoder, out_path: str, metrics: dict,
                 args) -> None:
    """
    Save only the encoder state_dict (not the decoder).
    The decoder is only needed during training — at inference time
    generate_gnn_embeddings() only calls model.encoder.

    Also saves a companion metadata .json file with training details.
    """
    # Encoder weights
    torch.save(model.encoder.state_dict(), out_path)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"\n[Train] Encoder weights saved → {out_path}  ({size_mb:.2f} MB)")

    # Metadata JSON
    meta = {
        "saved":          datetime.utcnow().isoformat(),
        "in_features":    args.in_features,
        "hidden_dim":     args.hidden_dim,
        "embed_dim":      args.embed_dim,
        "best_val_loss":  metrics.get("best_val_loss"),
        "epochs_run":     metrics.get("epochs_run"),
        "total_time_s":   metrics.get("total_time_s"),
        "quality":        metrics.get("quality"),
        "hyperparams": {
            "lr":           args.lr,
            "weight_decay": args.weight_decay,
            "dropout":      args.dropout,
            "train_split":  args.train_split,
            "early_stop":   args.early_stop,
        },
    }
    meta_path = out_path.replace(".pt", "_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"[Train] Metadata saved       → {meta_path}")


def save_training_log(log_path: str, metrics: dict, args) -> None:
    """Save full training history (loss per epoch) as JSON."""
    log = {
        "timestamp":  datetime.utcnow().isoformat(),
        "hyperparams": vars(args),
        "metrics":     metrics,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(f"[Train] Training log saved   → {log_path}")


# ---------------------------------------------------------------------------
# Azure Upload
# ---------------------------------------------------------------------------

def upload_weights_to_azure(weights_path: str) -> None:
    """
    Upload gnn_encoder_pretrained.pt to Azure Blob Storage model-weights container.
    Silent no-op if AZURE_STORAGE_CONNECTION_STRING is not set.
    """
    conn_str  = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    container = os.getenv("AZURE_STORAGE_CONTAINER_WEIGHTS", "model-weights")

    if not conn_str:
        print("\n[Azure] AZURE_STORAGE_CONNECTION_STRING not set — skipping upload.")
        print("[Azure] Weights are saved locally. Copy manually if needed.")
        return

    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("\n[Azure] azure-storage-blob not installed — skipping upload.")
        print("[Azure] Run: pip install azure-storage-blob")
        return

    try:
        print(f"\n[Azure] Uploading {Path(weights_path).name} "
              f"→ Azure Blob container '{container}' ...")

        client = BlobServiceClient.from_connection_string(conn_str)

        # Upload weights .pt
        blob = client.get_blob_client(
            container=container,
            blob=Path(weights_path).name
        )
        with open(weights_path, "rb") as f:
            blob.upload_blob(f, overwrite=True)
        print(f"[Azure] ✓ {Path(weights_path).name} uploaded")

        # Upload companion metadata .json
        meta_path = weights_path.replace(".pt", "_meta.json")
        if os.path.exists(meta_path):
            meta_blob = client.get_blob_client(
                container=container,
                blob=Path(meta_path).name
            )
            with open(meta_path, "rb") as f:
                meta_blob.upload_blob(f, overwrite=True)
            print(f"[Azure] ✓ {Path(meta_path).name} uploaded")

        print(f"\n[Azure] {GREEN}Upload complete.{RESET}")
        print(f"[Azure] Download with:")
        print(f"        python -c \"")
        print(f"        import os; from azure.storage.blob import BlobServiceClient")
        print(f"        c = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))")
        print(f"        b = c.get_blob_client('{container}', 'gnn_encoder_pretrained.pt')")
        print(f"        open('gnn_encoder_pretrained.pt','wb').write(b.download_blob().readall())\"")

    except Exception as e:
        print(f"\n[Azure] Upload failed: {e}")
        print(f"[Azure] Weights saved locally at {weights_path}")


# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Pre-train CodeForge GNN encoder across multiple CPG graphs"
    )
    p.add_argument("--data",     type=str,   default=os.path.join(os.path.dirname(__file__), "training_data"),
                   help="Directory containing .pt graph files (default: ./training_data)")
    p.add_argument("--dataset",  type=str,   default="",
                   help="Path to dataset.pt directly (overrides --data search)")
    p.add_argument("--out",      type=str,   default=os.path.join(os.path.dirname(__file__), WEIGHTS_FILENAME),
                   help=f"Output weights path (default: ./{WEIGHTS_FILENAME})")
    p.add_argument("--epochs",   type=int,   default=DEFAULTS["epochs"])
    p.add_argument("--lr",       type=float, default=DEFAULTS["lr"])
    p.add_argument("--hidden",   type=int,   default=DEFAULTS["hidden_dim"],  dest="hidden_dim")
    p.add_argument("--embed",    type=int,   default=DEFAULTS["embed_dim"],   dest="embed_dim")
    p.add_argument("--dropout",  type=float, default=DEFAULTS["dropout"])
    p.add_argument("--weight-decay", type=float, default=DEFAULTS["weight_decay"], dest="weight_decay")
    p.add_argument("--train-split",  type=float, default=DEFAULTS["train_split"],  dest="train_split")
    p.add_argument("--early-stop",   type=int,   default=DEFAULTS["early_stop"],   dest="early_stop")
    p.add_argument("--lr-patience",  type=int,   default=DEFAULTS["lr_patience"],  dest="lr_patience")
    p.add_argument("--min-lr",       type=float, default=DEFAULTS["min_lr"],       dest="min_lr")
    p.add_argument("--grad-clip",    type=float, default=DEFAULTS["grad_clip"],    dest="grad_clip")
    p.add_argument("--in-features",  type=int,   default=DEFAULTS["in_features"],  dest="in_features")
    p.add_argument("--seed",     type=int,   default=42)
    p.add_argument("--local",    action="store_true",
                   help="Skip Azure upload after training (local run only)")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # ── Reproducibility ───────────────────────────────────────────────────────
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)

    # ── Device ────────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        print(f"[Train] GPU detected: {torch.cuda.get_device_name(0)}")
        torch.backends.cudnn.benchmark = True
    else:
        print(f"[Train] No GPU — running on CPU  "
              f"(expected ~10–20 min for 500 epochs on this dataset)")

    # ── Load dataset ──────────────────────────────────────────────────────────
    print(f"\n[Train] Loading dataset ...")
    graphs = load_dataset(
        data_dir    = args.data,
        dataset_file = args.dataset,
        in_features = args.in_features,
    )

    train_set, val_set = split_dataset(graphs, args.train_split, args.seed)

    node_counts = [g["num_nodes"] for g in graphs]
    edge_counts = [g["num_edges"] for g in graphs]
    print(f"[Train] Dataset split   : {len(train_set)} train / {len(val_set)} val")
    print(f"[Train] Node count      : min={min(node_counts)}  "
          f"max={max(node_counts)}  "
          f"avg={sum(node_counts) // len(node_counts)}")
    print(f"[Train] Edge count      : min={min(edge_counts)}  "
          f"max={max(edge_counts)}  "
          f"avg={sum(edge_counts) // len(edge_counts)}")

    # ── Build model ───────────────────────────────────────────────────────────
    model = GraphAutoencoder(
        in_features = args.in_features,
        hidden_dim  = args.hidden_dim,
        embed_dim   = args.embed_dim,
        dropout     = args.dropout,
    ).to(device)

    total_params     = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n[Train] Model           : GCN Autoencoder "
          f"({args.in_features}→{args.hidden_dim}→{args.embed_dim})")
    print(f"[Train] Parameters      : {total_params:,} total  "
          f"({trainable_params:,} trainable)")

    # ── Train ─────────────────────────────────────────────────────────────────
    metrics = train(model, train_set, val_set, args, device)

    # ── Evaluate embedding quality ────────────────────────────────────────────
    print(f"\n[Train] Evaluating embedding quality on validation graphs ...")
    quality = evaluate_embedding_quality(model, val_set, device)
    metrics["quality"] = quality

    if quality["gap"] is not None:
        gap_col = GREEN if quality["gap"] > 0.3 else (YELLOW if quality["gap"] > 0.1 else RED)
        print(f"[Train]   Connected    avg cosine sim : {quality['connected_sim']:.4f}")
        print(f"[Train]   Unconnected  avg cosine sim : {quality['unconnected_sim']:.4f}")
        print(f"[Train]   Connectivity gap            : "
              f"{gap_col}{quality['gap']:.4f}{RESET}"
              f"  {'✓ Good — embeddings encode graph structure' if quality['gap'] > 0.3 else '⚠ Low — consider more epochs'}")
    else:
        print("[Train]   Quality evaluation skipped (no validation graphs).")

    # ── Save weights and logs ─────────────────────────────────────────────────
    save_weights(model, args.out, metrics, args)
    save_training_log(
        os.path.join(os.path.dirname(args.out), TRAINING_LOG),
        metrics, args
    )

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'=' * 65}")
    print(f"  {BOLD}TRAINING SUMMARY{RESET}")
    print(f"{'=' * 65}")
    print(f"  Best val loss        : {metrics['best_val_loss']:.4f}")
    print(f"  Epochs run           : {metrics['epochs_run']}")
    print(f"  Total time           : {metrics['total_time_s']}s "
          f"({metrics['total_time_s'] / 60:.1f} min)")
    if quality["gap"] is not None:
        print(f"  Connectivity gap     : {quality['gap']:.4f}")
    print(f"  Weights saved to     : {args.out}")
    print(f"{'=' * 65}")

    print(f"\n  {BOLD}Next steps:{RESET}")
    print(f"  1. Copy {WEIGHTS_FILENAME} to backend/")
    print(f"     (or set AZURE_STORAGE_CONNECTION_STRING for auto-download)")
    print(f"  2. Restart the backend — CodeForge will load these weights")
    print(f"     at startup and skip per-job training automatically.")
    print(f"  3. Verify with:  python test_gnn_model.py\n")

    # ── Azure upload ──────────────────────────────────────────────────────────
    if not args.local:
        upload_weights_to_azure(args.out)
    else:
        print(f"[Train] --local flag set — skipping Azure upload.")
        print(f"[Train] Weights are at: {args.out}")


if __name__ == "__main__":
    main()
