"""
inspect_dataset.py
==================
Lightweight preview of dataset.pt and individual .pt graph files
without loading the full tensors into memory.

Uses torch.load with weights_only=False but immediately discards
tensor data — only reads metadata and tensor shapes.

Run from backend/ directory:

    # Preview the combined dataset
    python inspect_dataset.py

    # Preview a specific repo file
    python inspect_dataset.py --file training_data/fastapi.pt

    # Preview all individual files (no combined dataset)
    python inspect_dataset.py --all

    # Export a CSV summary of all files
    python inspect_dataset.py --csv
"""

import os
import sys
import argparse
import glob
from pathlib import Path

import torch
import numpy as np


TRAINING_DATA_DIR = os.path.join(os.path.dirname(__file__), "training_data")
DATASET_PT        = os.path.join(TRAINING_DATA_DIR, "dataset.pt")

# ── Terminal colours ─────────────────────────────────────────────────────────
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def hr(char="─", width=65):
    print(char * width)

def mb(path):
    return os.path.getsize(path) / (1024 * 1024)


# ---------------------------------------------------------------------------
# Inspect combined dataset.pt
# ---------------------------------------------------------------------------

def inspect_dataset(path: str):
    if not os.path.exists(path):
        print(f"{RED}dataset.pt not found at {path}{RESET}")
        return

    size = mb(path)
    print(f"\n{BOLD}{CYAN}  dataset.pt  —  {size:.1f} MB{RESET}")
    hr()

    print(f"  Loading metadata only (this may take ~10–30s for large files)...")

    # torch.load reads the full file but we only inspect shapes immediately
    data = torch.load(path, map_location="cpu")

    graphs     = data.get("graphs", [])
    num_graphs = data.get("num_graphs", len(graphs))
    feat_dim   = data.get("feat_dim", "?")
    total_n    = data.get("total_nodes", sum(g["num_nodes"] for g in graphs))
    total_e    = data.get("total_edges", sum(g.get("num_edges", 0) for g in graphs))
    built      = data.get("built", "unknown")

    print(f"\n  {'Graphs':<22} {num_graphs}")
    print(f"  {'Feature dimension':<22} {feat_dim}")
    print(f"  {'Total nodes':<22} {total_n:,}")
    print(f"  {'Total edges':<22} {total_e:,}")
    print(f"  {'Built':<22} {built}")
    print(f"  {'File size':<22} {size:.1f} MB")

    if graphs:
        node_counts = [g["num_nodes"] for g in graphs]
        edge_counts = [g.get("num_edges", 0) for g in graphs]
        avg_n = sum(node_counts) / len(node_counts)
        avg_e = sum(edge_counts) / len(edge_counts)

        print(f"\n  {'Nodes per graph':<22} "
              f"min={min(node_counts)}  max={max(node_counts)}  avg={avg_n:.0f}")
        print(f"  {'Edges per graph':<22} "
              f"min={min(edge_counts)}  max={max(edge_counts)}  avg={avg_e:.0f}")

        # Tensor shape table
        hr()
        print(f"  {BOLD}{'#':<4} {'Repo':<30} {'Nodes':>7} {'Edges':>7} "
              f"{'x shape':<16} {'adj shape':<16}{RESET}")
        hr()
        for i, g in enumerate(graphs):
            x_shape   = tuple(g["x"].shape)
            adj_shape = tuple(g["adj"].shape)
            repo_name = g.get("repo", "").split("/")[-1] or f"graph_{i}"
            n = g["num_nodes"]
            e = g.get("num_edges", 0)

            # Colour-code by size
            col = GREEN if n < 200 else (YELLOW if n < 1000 else RED)
            print(f"  {i+1:<4} {col}{repo_name:<30}{RESET} "
                  f"{n:>7,} {e:>7,} "
                  f"{str(x_shape):<16} {str(adj_shape):<16}")

        hr()

        # Distribution histogram (ASCII)
        print(f"\n  {BOLD}Node count distribution{RESET}")
        _ascii_histogram(node_counts, bins=8, label="nodes")

    print()


# ---------------------------------------------------------------------------
# Inspect a single .pt file
# ---------------------------------------------------------------------------

def inspect_single(path: str):
    if not os.path.exists(path):
        print(f"{RED}File not found: {path}{RESET}")
        return

    name = Path(path).stem
    size = mb(path)

    print(f"\n{BOLD}{CYAN}  {name}.pt  —  {size:.1f} MB{RESET}")
    hr()

    data = torch.load(path, map_location="cpu")

    x        = data.get("x")
    adj      = data.get("adj")
    adj_norm = data.get("adj_norm")
    repo     = data.get("repo", "unknown")
    n_nodes  = data.get("num_nodes", x.shape[0] if x is not None else "?")
    n_edges  = data.get("num_edges", "?")
    feat_dim = data.get("feat_dim", x.shape[1] if x is not None else "?")

    print(f"  {'Repo':<22} {repo}")
    print(f"  {'Nodes':<22} {n_nodes:,}" if isinstance(n_nodes, int) else f"  {'Nodes':<22} {n_nodes}")
    print(f"  {'Edges':<22} {n_edges:,}" if isinstance(n_edges, int) else f"  {'Edges':<22} {n_edges}")
    print(f"  {'Feature dim':<22} {feat_dim}")
    print(f"  {'File size':<22} {size:.1f} MB")

    if x is not None:
        print(f"\n  {BOLD}Tensors{RESET}")
        hr("·")
        print(f"  {'x (features)':<22} shape={tuple(x.shape)}  "
              f"dtype={x.dtype}  "
              f"mem={x.element_size() * x.nelement() / 1e6:.2f} MB")

        if adj is not None:
            density = adj.sum().item() / adj.numel()
            print(f"  {'adj (binary)':<22} shape={tuple(adj.shape)}  "
                  f"dtype={adj.dtype}  "
                  f"density={density:.4f}  "
                  f"edges={int(adj.sum().item() / 2)}")

        if adj_norm is not None:
            print(f"  {'adj_norm':<22} shape={tuple(adj_norm.shape)}  "
                  f"dtype={adj_norm.dtype}")

        # Feature stats (sample first 5 columns)
        print(f"\n  {BOLD}Feature matrix stats  (x){RESET}")
        hr("·")
        x_np = x.numpy()
        print(f"  {'Column':<8} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
        hr("·")
        for col in range(min(10, x_np.shape[1])):
            col_data = x_np[:, col]
            print(f"  {col:<8} {col_data.mean():>10.4f} {col_data.std():>10.4f} "
                  f"{col_data.min():>10.4f} {col_data.max():>10.4f}")
        if x_np.shape[1] > 10:
            print(f"  {DIM}  ... ({x_np.shape[1] - 10} more columns){RESET}")

        # Degree distribution from adjacency
        if adj is not None:
            degrees = adj.sum(dim=1).numpy().astype(int)
            print(f"\n  {BOLD}Node degree distribution{RESET}")
            hr("·")
            print(f"  mean={degrees.mean():.2f}  "
                  f"median={int(np.median(degrees))}  "
                  f"max={degrees.max()}  "
                  f"isolated (deg=0): {(degrees == 0).sum()}")
            _ascii_histogram(degrees.tolist(), bins=8, label="degree")

    print()


# ---------------------------------------------------------------------------
# Inspect all individual .pt files
# ---------------------------------------------------------------------------

def inspect_all(data_dir: str):
    files = sorted([
        f for f in glob.glob(os.path.join(data_dir, "*.pt"))
        if Path(f).name != "dataset.pt"
    ])

    if not files:
        print(f"{RED}No .pt files found in {data_dir}{RESET}")
        return

    print(f"\n{BOLD}{CYAN}  All graphs in {data_dir}{RESET}")
    hr()
    print(f"  {BOLD}{'#':<4} {'File':<28} {'Size MB':>8} {'Nodes':>8} "
          f"{'Edges':>8} {'Density':>10}{RESET}")
    hr()

    total_size  = 0
    total_nodes = 0
    total_edges = 0

    for i, fpath in enumerate(files):
        name = Path(fpath).stem
        size = mb(fpath)
        total_size += size

        try:
            d        = torch.load(fpath, map_location="cpu")
            n_nodes  = d.get("num_nodes", 0)
            n_edges  = d.get("num_edges", 0)
            adj      = d.get("adj")
            density  = (adj.sum().item() / adj.numel()) if adj is not None else 0.0
            total_nodes += n_nodes
            total_edges += n_edges

            col = GREEN if n_nodes < 200 else (YELLOW if n_nodes < 1000 else RED)
            print(f"  {i+1:<4} {col}{name:<28}{RESET} "
                  f"{size:>8.1f} {n_nodes:>8,} {n_edges:>8,} {density:>10.5f}")

        except Exception as e:
            print(f"  {i+1:<4} {RED}{name:<28}  ERROR: {e}{RESET}")

    hr()
    print(f"  {'TOTAL':<32} {total_size:>8.1f} MB  "
          f"{total_nodes:>7,} nodes  {total_edges:>7,} edges")
    print()


# ---------------------------------------------------------------------------
# Export CSV summary
# ---------------------------------------------------------------------------

def export_csv(data_dir: str):
    import csv

    files = sorted([
        f for f in glob.glob(os.path.join(data_dir, "*.pt"))
        if Path(f).name != "dataset.pt"
    ])

    csv_path = os.path.join(data_dir, "dataset_summary.csv")
    rows = []

    for fpath in files:
        name = Path(fpath).stem
        size = mb(fpath)
        try:
            d       = torch.load(fpath, map_location="cpu")
            n_nodes = d.get("num_nodes", 0)
            n_edges = d.get("num_edges", 0)
            adj     = d.get("adj")
            density = (adj.sum().item() / adj.numel()) if adj is not None else 0.0
            feat_dim = d.get("feat_dim", d["x"].shape[1] if "x" in d else "?")
            rows.append({
                "repo":       name,
                "num_nodes":  n_nodes,
                "num_edges":  n_edges,
                "feat_dim":   feat_dim,
                "adj_density": round(density, 6),
                "file_size_mb": round(size, 2),
            })
        except Exception as e:
            rows.append({"repo": name, "error": str(e)})

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "repo", "num_nodes", "num_edges", "feat_dim",
            "adj_density", "file_size_mb"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{GREEN}CSV saved to: {csv_path}{RESET}")
    print(f"Open with Excel or any spreadsheet tool.\n")


# ---------------------------------------------------------------------------
# ASCII histogram helper
# ---------------------------------------------------------------------------

def _ascii_histogram(values: list, bins: int = 8, label: str = ""):
    if not values:
        return

    min_v  = min(values)
    max_v  = max(values)
    if min_v == max_v:
        print(f"  All values are {min_v}")
        return

    width  = (max_v - min_v) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - min_v) / width), bins - 1)
        counts[idx] += 1

    max_count = max(counts)
    bar_width = 30

    for i, count in enumerate(counts):
        low  = int(min_v + i * width)
        high = int(min_v + (i + 1) * width)
        bar  = "█" * int(count / max_count * bar_width)
        print(f"  {low:>6}–{high:<6} │{GREEN}{bar:<30}{RESET} {count}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Preview CodeForge training dataset without loading full tensors"
    )
    parser.add_argument("--file",  type=str, default="",
                        help="Inspect a specific .pt file")
    parser.add_argument("--all",   action="store_true",
                        help="Show summary table of all individual .pt files")
    parser.add_argument("--csv",   action="store_true",
                        help="Export CSV summary to training_data/dataset_summary.csv")
    parser.add_argument("--data",  type=str, default=TRAINING_DATA_DIR,
                        help="Training data directory (default: ./training_data)")
    args = parser.parse_args()

    dataset_path = os.path.join(args.data, "dataset.pt")

    if args.file:
        inspect_single(args.file)

    elif args.all:
        inspect_all(args.data)

    elif args.csv:
        export_csv(args.data)

    else:
        # Default: inspect combined dataset.pt + show all-files table
        inspect_dataset(dataset_path)
        print()
        inspect_all(args.data)


if __name__ == "__main__":
    main()
