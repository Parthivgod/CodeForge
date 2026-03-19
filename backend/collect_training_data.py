"""
collect_training_data.py
========================
Collects training data for the CodeForge pre-trained GNN by cloning
30 open-source GitHub repositories, running each through the full
CodeForge CPG pipeline, and saving the resulting graph tensors as
individual .pt files in backend/training_data/.

At the end it also builds a single combined dataset.pt file that
train_pretrained_gnn.py can load directly without iterating files.

Optionally uploads everything to Azure Blob Storage if
AZURE_STORAGE_CONNECTION_STRING is set in .env.

Run from the backend/ directory:
    python collect_training_data.py

Optional flags:
    --workers N     Number of parallel clone workers (default: 3)
    --min-nodes N   Skip graphs with fewer than N nodes (default: 10)
    --no-upload     Skip Azure upload even if credentials are present
    --output DIR    Override output directory (default: ./training_data)

Dependencies already in requirements.txt:
    GitPython, torch, scikit-learn, tree-sitter, networkx, python-dotenv

New dependency (add to requirements.txt):
    azure-storage-blob>=12.19.0
"""

import os
import sys
import uuid
import json
import time
import shutil
import argparse
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Load .env before any other imports that might need env vars ──────────────
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import torch
import numpy as np

# ── Make sure we can import project modules when run from backend/ ───────────
sys.path.insert(0, os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRAINING_REPOS = [
    # Python — web frameworks / APIs
    "https://github.com/tiangolo/fastapi",
    "https://github.com/pallets/flask",
    "https://github.com/encode/httpx",
    "https://github.com/psf/requests",
    "https://github.com/encode/starlette",
    # Python — project utilities
    "https://github.com/samuelcolvin/pydantic",
    "https://github.com/pallets/click",
    "https://github.com/Textualize/rich",
    "https://github.com/tqdm/tqdm",
    "https://github.com/pytest-dev/pytest",
    # Python — async / networking
    "https://github.com/aio-libs/aiohttp",
    "https://github.com/celery/celery",
    "https://github.com/redis/redis-py",
    "https://github.com/psutil/psutil",
    # Python — AI / ML adjacent
    "https://github.com/openai/openai-python",
    "https://github.com/pydantic/logfire",
    "https://github.com/tiangolo/sqlmodel",
    "https://github.com/nicegui/nicegui",
    "https://github.com/streamlit/streamlit",
    # Python — miscellaneous
    "https://github.com/python-poetry/poetry",
    # JavaScript / TypeScript
    "https://github.com/expressjs/express",
    "https://github.com/axios/axios",
    "https://github.com/vitejs/vite",
    "https://github.com/fastify/fastify",
    "https://github.com/nestjs/nest",
    "https://github.com/colinhacks/zod",
    "https://github.com/sindresorhus/got",
    "https://github.com/motdotla/dotenv",
    "https://github.com/chalk/chalk",
    "https://github.com/debug-js/debug",
]

AZURE_CONTAINER_TRAINING = "training-data"
AZURE_CONTAINER_WEIGHTS  = "model-weights"
EXPECTED_FEAT_DIM        = 77   # 64 TF-IDF + 13 structural — must match feature_engineering.py


# ---------------------------------------------------------------------------
# Single-repo collection
# ---------------------------------------------------------------------------

def collect_single_repo(repo_url: str, output_dir: str, min_nodes: int) -> dict:
    """
    Clone one repo, parse it through the full CodeForge CPG pipeline,
    build feature matrix and adjacency tensors, save as a .pt file.

    Returns a result dict:
        success=True  → {success, repo, name, nodes, edges, feat_dim, path, duration}
        success=False → {success, repo, name, reason}
        skipped=True  → {skipped, repo, name, reason}
    """
    repo_name = repo_url.rstrip("/").split("/")[-1]
    out_path  = os.path.join(output_dir, f"{repo_name}.pt")

    # Already collected — skip without re-cloning
    if os.path.exists(out_path):
        return {"skipped": True, "repo": repo_url, "name": repo_name,
                "reason": "already exists"}

    clone_dir = tempfile.mkdtemp(prefix=f"codeforge_collect_{repo_name}_")
    t0 = time.time()

    try:
        # ── 1. Shallow clone ──────────────────────────────────────────────
        from git import Repo as GitRepo, GitCommandError
        try:
            GitRepo.clone_from(repo_url, clone_dir, depth=1)
        except GitCommandError as e:
            return {"success": False, "repo": repo_url, "name": repo_name,
                    "reason": f"git clone failed: {e}"}

        # ── 2. Build Code Property Graph ──────────────────────────────────
        # build_cpg internally calls:
        #   find_code_files → parse_file (Tree-sitter) → build_edges
        #   → compute_graph_features (fan_in, betweenness, depth, etc.)
        from cpg_builder import build_cpg
        job_id = str(uuid.uuid4())[:8]
        cpg    = build_cpg(clone_dir, job_id)

        nodes = cpg["nodes"]
        edges = cpg["edges"]

        if len(nodes) < min_nodes:
            return {"success": False, "repo": repo_url, "name": repo_name,
                    "reason": f"only {len(nodes)} nodes (min={min_nodes})"}

        # ── 3. Build N×77 feature matrix ──────────────────────────────────
        # prepare_initial_features uses TF-IDF on node names/variables (64 dims)
        # plus 13 structural metrics already written to nodes by build_cpg.
        from feature_engineering import prepare_initial_features
        feats_np = prepare_initial_features(nodes)   # (N, F) numpy array

        feat_dim = feats_np.shape[1]
        if feat_dim != EXPECTED_FEAT_DIM:
            # Pad with zeros to reach EXPECTED_FEAT_DIM so all graphs have
            # identical input width when loaded by the training script.
            if feat_dim < EXPECTED_FEAT_DIM:
                pad = np.zeros((feats_np.shape[0], EXPECTED_FEAT_DIM - feat_dim),
                               dtype=feats_np.dtype)
                feats_np = np.hstack([feats_np, pad])
                print(f"[Collect] {repo_name} — padded feat_dim {feat_dim} → {EXPECTED_FEAT_DIM}")
            else:
                feats_np = feats_np[:, :EXPECTED_FEAT_DIM]
                print(f"[Collect] {repo_name} — truncated feat_dim {feat_dim} → {EXPECTED_FEAT_DIM}")

        x = torch.tensor(feats_np, dtype=torch.float32)

        # ── 4. Build adjacency tensors ────────────────────────────────────
        from gnn_model import build_adjacency, normalise_adjacency
        adj_raw, _  = build_adjacency(nodes, edges)   # (N, N) binary float32
        adj_norm    = normalise_adjacency(adj_raw)     # (N, N) D^{-1/2} A_hat D^{-1/2}

        # ── 5. Save .pt file ──────────────────────────────────────────────
        # Saves only tensors + lightweight metadata — not the full node dicts
        # (which contain file paths and would bloat the file).
        torch.save({
            "x":         x,           # (N, 77) float32  — node feature matrix
            "adj":       adj_raw,     # (N, N)  float32  — binary adjacency
            "adj_norm":  adj_norm,    # (N, N)  float32  — normalised adjacency
            "repo":      repo_url,
            "num_nodes": len(nodes),
            "num_edges": len(edges),
            "feat_dim":  EXPECTED_FEAT_DIM,
            "collected": datetime.utcnow().isoformat(),
        }, out_path)

        duration = round(time.time() - t0, 1)
        print(f"[Collect] ✓ {repo_name:<30} "
              f"{len(nodes):>5} nodes  {len(edges):>5} edges  "
              f"feat={EXPECTED_FEAT_DIM}  ({duration}s)")

        return {
            "success":  True,
            "repo":     repo_url,
            "name":     repo_name,
            "nodes":    len(nodes),
            "edges":    len(edges),
            "feat_dim": EXPECTED_FEAT_DIM,
            "path":     out_path,
            "duration": duration,
        }

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[Collect] ✗ {repo_name:<30} FAILED: {e}")
        print(f"          {tb.strip()}")
        return {"success": False, "repo": repo_url, "name": repo_name,
                "reason": str(e)}

    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Parallel collection across all repos
# ---------------------------------------------------------------------------

def collect_all(repos: list, output_dir: str, workers: int,
                min_nodes: int) -> tuple[list, list, list]:
    """
    Run collect_single_repo in parallel.

    Returns:
        successes : list of successful result dicts
        failures  : list of failed result dicts
        skipped   : list of skipped result dicts
    """
    os.makedirs(output_dir, exist_ok=True)
    successes, failures, skipped = [], [], []

    print(f"\n[Collect] Starting collection of {len(repos)} repos "
          f"({workers} parallel workers, min_nodes={min_nodes})")
    print(f"[Collect] Output directory: {output_dir}\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {
            executor.submit(collect_single_repo, url, output_dir, min_nodes): url
            for url in repos
        }
        for future in as_completed(future_to_url):
            result = future.result()
            if result.get("skipped"):
                skipped.append(result)
                print(f"[Collect] — {result['name']:<30} skipped ({result['reason']})")
            elif result.get("success"):
                successes.append(result)
            else:
                failures.append(result)

    return successes, failures, skipped


# ---------------------------------------------------------------------------
# Build combined dataset.pt
# ---------------------------------------------------------------------------

def build_combined_dataset(output_dir: str) -> str:
    """
    Load all individual .pt graph files from output_dir (excluding
    dataset.pt itself) and merge them into a single dataset.pt file.

    dataset.pt structure:
        {
            "graphs": [
                {
                    "x":         Tensor (N_i, 77),
                    "adj":       Tensor (N_i, N_i),
                    "adj_norm":  Tensor (N_i, N_i),
                    "repo":      str,
                    "num_nodes": int,
                    "num_edges": int,
                    "feat_dim":  int,
                },
                ...
            ],
            "num_graphs":   int,
            "feat_dim":     int,
            "total_nodes":  int,
            "total_edges":  int,
            "built":        str  (ISO timestamp),
        }

    train_pretrained_gnn.py loads this single file instead of
    iterating over individual files.
    """
    pt_files = sorted([
        f for f in Path(output_dir).glob("*.pt")
        if f.name != "dataset.pt"
    ])

    if not pt_files:
        print("[Dataset] No .pt files found — cannot build dataset.pt")
        return ""

    graphs     = []
    total_n    = 0
    total_e    = 0
    bad_dim    = 0

    print(f"\n[Dataset] Building combined dataset.pt from {len(pt_files)} files...")

    for pt_file in pt_files:
        try:
            d = torch.load(pt_file, map_location="cpu")

            # Validate required keys
            if not all(k in d for k in ("x", "adj", "adj_norm", "num_nodes")):
                print(f"[Dataset]   Skipping {pt_file.name} — missing required keys")
                continue

            # Validate feature dimension
            actual_dim = d["x"].shape[1]
            if actual_dim != EXPECTED_FEAT_DIM:
                print(f"[Dataset]   Skipping {pt_file.name} — "
                      f"feat_dim={actual_dim} expected {EXPECTED_FEAT_DIM}")
                bad_dim += 1
                continue

            graphs.append({
                "x":         d["x"],
                "adj":       d["adj"],
                "adj_norm":  d["adj_norm"],
                "repo":      d.get("repo", pt_file.stem),
                "num_nodes": d["num_nodes"],
                "num_edges": d.get("num_edges", 0),
                "feat_dim":  EXPECTED_FEAT_DIM,
            })
            total_n += d["num_nodes"]
            total_e += d.get("num_edges", 0)

        except Exception as e:
            print(f"[Dataset]   Error loading {pt_file.name}: {e}")

    if not graphs:
        print("[Dataset] No valid graphs — dataset.pt not created.")
        return ""

    dataset_path = os.path.join(output_dir, "dataset.pt")
    torch.save({
        "graphs":      graphs,
        "num_graphs":  len(graphs),
        "feat_dim":    EXPECTED_FEAT_DIM,
        "total_nodes": total_n,
        "total_edges": total_e,
        "built":       datetime.utcnow().isoformat(),
    }, dataset_path)

    size_mb = os.path.getsize(dataset_path) / (1024 * 1024)

    print(f"[Dataset] ✓ dataset.pt created")
    print(f"[Dataset]   graphs      : {len(graphs)}")
    print(f"[Dataset]   total nodes : {total_n:,}")
    print(f"[Dataset]   total edges : {total_e:,}")
    print(f"[Dataset]   feat_dim    : {EXPECTED_FEAT_DIM}")
    print(f"[Dataset]   file size   : {size_mb:.1f} MB")
    if bad_dim:
        print(f"[Dataset]   skipped (wrong dim): {bad_dim}")

    return dataset_path


# ---------------------------------------------------------------------------
# Azure upload
# ---------------------------------------------------------------------------

def upload_to_azure(output_dir: str, skip_upload: bool):
    """
    Upload all .pt files (including dataset.pt) to Azure Blob Storage.
    Only runs if AZURE_STORAGE_CONNECTION_STRING is in the environment.
    """
    if skip_upload:
        print("\n[Azure] Upload skipped (--no-upload flag).")
        return

    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    if not conn_str:
        print("\n[Azure] AZURE_STORAGE_CONNECTION_STRING not set — skipping upload.")
        print("[Azure] To upload later, run with the env var set.")
        return

    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("\n[Azure] azure-storage-blob not installed.")
        print("[Azure] Run: pip install azure-storage-blob")
        return

    try:
        client    = BlobServiceClient.from_connection_string(conn_str)
        pt_files  = list(Path(output_dir).glob("*.pt"))
        uploaded  = 0

        print(f"\n[Azure] Uploading {len(pt_files)} .pt files to "
              f"container '{AZURE_CONTAINER_TRAINING}'...")

        for pt_file in pt_files:
            blob = client.get_blob_client(
                container=AZURE_CONTAINER_TRAINING,
                blob=pt_file.name
            )
            with open(pt_file, "rb") as f:
                blob.upload_blob(f, overwrite=True)
            uploaded += 1
            print(f"[Azure]   ✓ {pt_file.name}")

        print(f"[Azure] Upload complete — {uploaded} files uploaded.")

    except Exception as e:
        print(f"[Azure] Upload failed: {e}")
        print("[Azure] Individual .pt files are still saved locally in training_data/")


# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------

def print_summary(successes: list, failures: list, skipped: list,
                  dataset_path: str, total_time: float):
    """Print a final summary table to the terminal."""
    total = len(successes) + len(failures) + len(skipped)

    print("\n" + "=" * 65)
    print("  COLLECTION SUMMARY")
    print("=" * 65)
    print(f"  Total repos attempted : {total}")
    print(f"  Successful            : {len(successes)}")
    print(f"  Failed                : {len(failures)}")
    print(f"  Skipped (cached)      : {len(skipped)}")
    print(f"  Total time            : {total_time:.0f}s")

    if successes:
        node_counts = [r["nodes"] for r in successes]
        edge_counts = [r["edges"] for r in successes]
        print(f"\n  Node count  — min={min(node_counts)}  "
              f"max={max(node_counts)}  "
              f"avg={sum(node_counts)//len(node_counts)}")
        print(f"  Edge count  — min={min(edge_counts)}  "
              f"max={max(edge_counts)}  "
              f"avg={sum(edge_counts)//len(edge_counts)}")
        print(f"  Total nodes in dataset : {sum(node_counts):,}")

    if failures:
        print(f"\n  Failed repos:")
        for r in failures:
            print(f"    ✗ {r['name']:<30} {r['reason']}")

    if dataset_path and os.path.exists(dataset_path):
        size_mb = os.path.getsize(dataset_path) / (1024 * 1024)
        print(f"\n  Combined dataset: {dataset_path}  ({size_mb:.1f} MB)")
        print(f"  → Pass this path to train_pretrained_gnn.py with --data flag")

    print("=" * 65)
    print("\n  Next step:")
    print("  python train_pretrained_gnn.py --local --epochs 30")
    print("  (sanity check before submitting to Azure)\n")


# ---------------------------------------------------------------------------
# Save collection log as JSON
# ---------------------------------------------------------------------------

def save_collection_log(output_dir: str, successes: list, failures: list,
                         skipped: list):
    """Save a JSON log of the collection run for debugging and reproducibility."""
    log = {
        "timestamp":  datetime.utcnow().isoformat(),
        "successes":  successes,
        "failures":   failures,
        "skipped":    skipped,
        "total":      len(successes) + len(failures) + len(skipped),
    }
    log_path = os.path.join(output_dir, "collection_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"[Collect] Collection log saved to {log_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Collect training data for CodeForge GNN pre-training"
    )
    parser.add_argument(
        "--workers",  type=int, default=3,
        help="Number of parallel git clone workers (default: 3)"
    )
    parser.add_argument(
        "--min-nodes", type=int, default=10,
        help="Skip repos with fewer than N parsed nodes (default: 10)"
    )
    parser.add_argument(
        "--no-upload", action="store_true",
        help="Skip Azure Blob Storage upload"
    )
    parser.add_argument(
        "--output", type=str,
        default=os.path.join(os.path.dirname(__file__), "training_data"),
        help="Output directory for .pt files (default: ./training_data)"
    )
    args = parser.parse_args()

    t_start = time.time()

    # ── Collect all repos ────────────────────────────────────────────────────
    successes, failures, skipped = collect_all(
        repos     = TRAINING_REPOS,
        output_dir = args.output,
        workers   = args.workers,
        min_nodes = args.min_nodes,
    )

    # ── Build combined dataset.pt ─────────────────────────────────────────────
    # This is the main file that train_pretrained_gnn.py loads.
    # It merges all individual .pt graph files into one tensor collection.
    dataset_path = build_combined_dataset(args.output)

    # ── Upload to Azure Blob Storage ─────────────────────────────────────────
    upload_to_azure(args.output, args.no_upload)

    # ── Save collection log ──────────────────────────────────────────────────
    save_collection_log(args.output, successes, failures, skipped)

    # ── Final summary ────────────────────────────────────────────────────────
    print_summary(successes, failures, skipped, dataset_path,
                  time.time() - t_start)


if __name__ == "__main__":
    main()
