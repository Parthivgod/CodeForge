"""
Multi-Model Orchestrator for CodeForge.

Routes AST nodes through a 3-model analysis pipeline:
  Mapper — Node Mapper (fast triage & tier assignment)
  Linker — Relation Linker (semantic topology mapping)
  Sentinel — Security Sentinel (security & stability reasoning)

Every LLM call logs token usage to token_usage.txt.
"""

import os
import json
import hashlib
import asyncio
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import boto3
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# ---------------------------------------------------------------------------
# RATE LIMITING CONFIGURATION
# ---------------------------------------------------------------------------
class RateLimiter:
    """Simple rate limiter to prevent API throttling"""
    def __init__(self, calls_per_second=10):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()

# Global rate limiter (10 requests per second for AWS Bedrock)
rate_limiter = RateLimiter(calls_per_second=10)

# ---------------------------------------------------------------------------
# MODEL CONFIGURATION — Replace placeholder values with real model IDs
# ---------------------------------------------------------------------------
MODEL_ROLES: Dict[str, Dict[str, Any]] = {
    "mapper": {
        "name": "Node Mapper",
        "model_id": os.getenv("MODEL_MAPPER", "PLACEHOLDER_CLASSIFIER_MODEL"),
        "temperature": 0.0,
        "max_retries": 2,
        "timeout_seconds": 30,
        "description": "Fast, lightweight model for triage and tier assignment.",
    },
    "linker": {
        "name": "Relation Linker",
        "model_id": os.getenv("MODEL_LINKER", "PLACEHOLDER_EXTRACTOR_MODEL"),
        "temperature": 0.1,
        "max_retries": 2,
        "timeout_seconds": 60,
        "description": "Mid-range model for semantic relation extraction.",
    },
    "sentinel": {
        "name": "Security Sentinel",
        "model_id": os.getenv("MODEL_SENTINEL", "PLACEHOLDER_RISK_MODEL"),
        "temperature": 0.1,
        "max_retries": 3,
        "timeout_seconds": 120,
        "description": "Frontier reasoning model for deep security analysis.",
    },
}


TOKEN_LOG_FILE = os.path.join(os.path.dirname(__file__), "token_usage.txt")

# ---------------------------------------------------------------------------
# SYSTEM PROMPTS
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_MAPPER = """You are a High-Speed Code Triage Engine.
Classify each AST node and determine the required depth of analysis.

TIER DEFINITIONS:
- Tier 0: Trivial. Imports, logging calls, constants, boilerplate. No risk.
- Tier 1: Low-Risk. Pure functions, simple data transforms, formatting helpers.
- Tier 2: Moderate-Risk. Business logic, API endpoints, DB queries, complex branching.
- Tier 3: High-Risk. Auth, crypto, concurrency primitives, PII handling, file I/O with user input.

For EACH node return STRICT JSON (no markdown, no explanation):
{
  "classifications": [
    {
      "id": "node_id",
      "classification": "structural_unit|control_flow|data_flow|external_call|security_sensitive|utility",
      "risk_tier": 0,
      "deep_reasoning_required": false,
      "external_interaction_likelihood": "none|low|high",
      "confidence": 0.95
    }
  ]
}"""

SYSTEM_PROMPT_LINKER = """You are a Code Topology Specialist.
Extract semantic relationships between the provided nodes and the system context.

CONSTRAINTS:
- Identify calls, implementations, dependencies, and data flow.
- DO NOT perform risk analysis or security reasoning.
- DO NOT create redundant edges between the same source-target pair.
  Pick the MOST SPECIFIC applicable edge type.
- Return structured relations only.

For the given nodes return STRICT JSON (no markdown, no explanation):
{
  "results": [
    {
      "id": "node_id",
      "node_summary": "...",
      "classification": "structural_unit|control_flow|data_flow|external_call|security_sensitive|utility",
      "architectural_role": "controller|service|repository|utility|middleware|model|config|infrastructure|test|unknown",
      "entry_point": {"is_entry_point": false, "entry_type": "unknown"},
      "sensitive_behaviors": {"handles_user_input": false, "accesses_filesystem": false, "network_calls": false},
      "impact_analysis": {"blast_radius_score": 1, "critical_path_likelihood": 1, "change_sensitivity": "low"},
      "confidence_score": 0.9
    }
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "calls|structural|dependency|flow", "description": "short reason"}
  ]
}"""

SYSTEM_PROMPT_SENTINEL = """You are a Principal Security Reasoning Engine.
Analyze the provided code node and its extracted relations for deep architectural risks.

ANALYSIS VECTORS:
1. Injection: SQL, Command, NoSQL, LDAP, XSS.
2. Authorization: Broken access control, privilege escalation, IDOR.
3. Concurrency: Race conditions, deadlocks, shared state mutation.
4. Data Exposure: PII leaks, sensitive logging, secret exposure.

CONSTRAINTS:
- Be conservative: flag potential risks even if partially obscured.
- Lower confidence if context is missing. Never assume safety.
- NO HALLUCINATION: Only reference symbols present in the input.

Return STRICT JSON (no markdown, no explanation):
{
  "risk_breakdown": {
    "injection": {"level": "none|low|moderate|high|critical", "reason": "..."},
    "authorization": {"level": "none|low|moderate|high|critical", "reason": "..."},
    "concurrency": {"level": "none|low|moderate|high|critical", "reason": "..."},
    "exposure": {"level": "none|low|moderate|high|critical", "reason": "..."}
  },
  "overall_risk": "none|low|moderate|high|critical",
  "blast_radius": 1,
  "confidence_score": 0.0,
  "risk_summary": "..."
}"""




# ---------------------------------------------------------------------------
# TOKEN LOGGING (shared across all roles)
# ---------------------------------------------------------------------------

def _log_tokens(role: str, model_id: str, input_tokens: int, output_tokens: int):
    """Append token usage to token_usage.txt for every LLM call."""
    total = input_tokens + output_tokens
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{timestamp}] role={role} | model={model_id} "
        f"| input={input_tokens} | output={output_tokens} | total={total}\n"
    )
    with open(TOKEN_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[Token] {role}: in={input_tokens} out={output_tokens} total={total}")


# ---------------------------------------------------------------------------
# BEDROCK CLIENT
# ---------------------------------------------------------------------------

def _get_bedrock_client():
    """Create a boto3 bedrock-runtime client."""
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


@traceable(run_type="llm", project_name="CodeForge")
def _call_model(client, role: str, model_id: str, system_prompt: str,
                user_prompt: str, temperature: float = 0.1) -> str:
    """Call AWS Bedrock Converse API with rate limiting, log tokens, and return text."""
    
    # Apply rate limiting to prevent throttling
    rate_limiter.wait_if_needed()
    
    messages = [{"role": "user", "content": [{"text": user_prompt}]}]
    system = [{"text": system_prompt}]

    response = client.converse(
        modelId=model_id,
        messages=messages,
        system=system,
        inferenceConfig={
            "temperature": temperature,
            "maxTokens": 4096
        },
    )

    # Extract and log tokens
    usage = response.get("usage", {})
    input_tokens = usage.get("inputTokens", 0)
    output_tokens = usage.get("outputTokens", 0)
    _log_tokens(role, model_id, input_tokens, output_tokens)

    # Attach to LangSmith
    rt = get_current_run_tree()
    if rt:
        rt.extra = rt.extra or {}
        rt.extra["usage"] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }
        rt.extra["metadata"] = rt.extra.get("metadata", {})
        rt.extra["metadata"]["model"] = model_id
        rt.extra["metadata"]["role"] = role
        rt.extra["metadata"]["provider"] = "aws_bedrock"

    # Extract text
    output_message = response.get("output", {}).get("message", {})
    content_blocks = output_message.get("content", [])
    return "".join(block.get("text", "") for block in content_blocks)


def _parse_json_response(raw: str) -> Optional[Dict]:
    """Robustly extract JSON from an LLM response (handles markdown fences)."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try finding JSON block
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            try:
                content = match.group(1)
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[Orchestrator] JSON Parse Error (Regex Match): {e}\nRaw start: {raw[:200]}...")
        else:
            print(f"[Orchestrator] JSON Parse Error (No Match): Raw start: {raw[:200]}...")
    return None


# ---------------------------------------------------------------------------
# NODE HASHING / CACHING
# ---------------------------------------------------------------------------

_result_cache: Dict[str, Any] = {}


def _node_hash(node: Dict) -> str:
    """Content-addressable hash for a node to enable caching."""
    key_parts = json.dumps({
        "name": node.get("name"),
        "type": node.get("type"),
        "file": node.get("file"),
        "line": node.get("line_start"),
        "calls": sorted(node.get("calls", [])),
        "params": sorted(node.get("parameters", [])),
    }, sort_keys=True)
    return hashlib.sha256(key_parts.encode()).hexdigest()


# ---------------------------------------------------------------------------
# ROLE A — NODE CLASSIFIER
# ---------------------------------------------------------------------------

def _prepare_node_summary(node: Dict, all_nodes: List[Dict]) -> Dict:
    """Create a compact summary of a node for LLM consumption."""
    summary: Dict[str, Any] = {
        "id": node["id"],
        "name": node["name"],
        "type": node["type"],
        "file": node["file"],
        "line": node.get("line_start"),
    }
    if node["type"] == "function":
        summary["calls"] = node.get("calls", [])
        summary["api_calls"] = node.get("api_calls", [])
        summary["variables"] = node.get("variables", [])
        summary["parameters"] = node.get("parameters", [])
    elif node["type"] == "class":
        summary["methods"] = [
            n["name"] for n in all_nodes if n.get("parent_class") == node["name"]
        ]
        summary["inherits"] = node.get("inherits", [])
    return summary


@traceable(project_name="CodeForge")
def classify_nodes(client, nodes: List[Dict], all_nodes: List[Dict]) -> Dict[str, Dict]:
    """
    Mapper: Classify a batch of nodes and assign risk tiers.
    Returns {node_id: classification_dict}.
    """
    cfg = MODEL_ROLES["mapper"]
    summaries = [_prepare_node_summary(n, all_nodes) for n in nodes]

    prompt = f"""Classify the following {len(summaries)} AST nodes.
Assign each node a risk_tier (0-3), classification, and whether deep reasoning is required.

Nodes:
{json.dumps(summaries, indent=2)}"""

    raw = _call_model(
        client, "Mapper", cfg["model_id"],
        SYSTEM_PROMPT_MAPPER, prompt, cfg["temperature"]
    )
    parsed = _parse_json_response(raw)
    if not parsed or "classifications" not in parsed:
        print(f"[Role A] Failed to parse response, defaulting to Tier 1.")
        return {
            n["id"]: {
                "classification": "unknown",
                "risk_tier": 1,
                "deep_reasoning_required": False,
                "external_interaction_likelihood": "low",
                "confidence": 0.5,
            }
            for n in nodes
        }

    return {
        c["id"]: c for c in parsed["classifications"] if "id" in c
    }


# ---------------------------------------------------------------------------
# LINKER — RELATION EXTRACTOR
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def extract_relations(client, nodes: List[Dict], all_nodes: List[Dict]) -> Dict[str, Any]:
    """
    Linker: Extract semantic relationships without deep risk reasoning.
    Returns {"results": [...], "relationships": [...]}.
    """
    cfg = MODEL_ROLES["linker"]
    summaries = [_prepare_node_summary(n, all_nodes) for n in nodes]

    prompt = f"""Analyze the following {len(summaries)} AST nodes.
Extract semantic relations and assign architectural roles.

IMPORTANT: NO REDUNDANT EDGES between the same source and target.
Pick the MOST SPECIFIC edge type.

Nodes:
{json.dumps(summaries, indent=2)}"""

    raw = _call_model(
        client, "linker", cfg["model_id"],
        SYSTEM_PROMPT_LINKER, prompt, cfg["temperature"]
    )
    parsed = _parse_json_response(raw)
    if not parsed:
        print("[Linker] Failed to parse response.")
        return {"results": [], "relationships": []}
    return parsed


# ---------------------------------------------------------------------------
# SENTINEL — DEEP RISK ANALYZER
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def analyze_risk_deep(client, node: Dict, relations: List[Dict]) -> Optional[Dict]:
    """
    Sentinel: Perform deep security/stability reasoning on a single node.
    Returns a risk_breakdown dict or None on failure.
    """
    cfg = MODEL_ROLES["sentinel"]

    prompt = f"""Analyze the following node for security and stability risks.

Node:
{json.dumps(node, indent=2)}

Known relations:
{json.dumps(relations, indent=2)}"""

    for attempt in range(cfg["max_retries"]):
        try:
            raw = _call_model(
                client, "sentinel", cfg["model_id"],
                SYSTEM_PROMPT_SENTINEL, prompt, cfg["temperature"]
            )
            parsed = _parse_json_response(raw)
            if parsed and "risk_breakdown" in parsed:
                return parsed
        except Exception as e:
            print(f"[Sentinel] Attempt {attempt + 1} failed: {e}")
            import time
            time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
    
    # Fallback: Mark as unverified
    return {
        "risk_breakdown": {
            "injection": {"level": "unknown", "reason": "Analysis failed"},
            "authorization": {"level": "unknown", "reason": "Analysis failed"},
            "concurrency": {"level": "unknown", "reason": "Analysis failed"},
            "exposure": {"level": "unknown", "reason": "Analysis failed"},
        },
        "overall_risk": "unknown",
        "blast_radius": 0,
        "confidence_score": 0.0,
        "risk_summary": "Deep risk analysis failed. Manual review recommended.",
    }



# ---------------------------------------------------------------------------
# HEURISTIC FALLBACK
# ---------------------------------------------------------------------------

def _create_heuristic_relationships(nodes: List[Dict]) -> List[Dict]:
    """Create basic relationships when LLM fails or returns few results."""
    edges = []
    for node in nodes:
        for call_name in node.get("calls", []):
            for other in nodes:
                if other["name"] == call_name and other["id"] != node["id"]:
                    edges.append({
                        "source": node["id"],
                        "target": other["id"],
                        "type": "calls",
                        "description": f"{node['name']} calls {other['name']}",
                        "confidence": 0.9,
                    })

        node_vars = set(node.get("variables", []))
        if len(node_vars) >= 3:
            for other in nodes:
                if other["id"] != node["id"]:
                    shared = node_vars & set(other.get("variables", []))
                    if len(shared) >= 3:
                        edges.append({
                            "source": node["id"],
                            "target": other["id"],
                            "type": "flow",
                            "description": f"Shared data: {', '.join(list(shared)[:2])}...",
                            "confidence": 0.8,
                        })

    seen = set()
    unique = []
    for e in edges:
        key = (e["source"], e["target"], e["type"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


# ---------------------------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def discover_relations_orchestrated(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Multi-model orchestrated relation discovery.

    Pipeline:
      1. Cache check (skip already-analyzed nodes)
      2. Mapper  — Classify all nodes, assign tiers
      3. Linker  — Extract relations (Tier 1-3)
      4. Sentinel  — Deep risk analysis (Tier 2-3)
      5. Heuristic fallback if connectivity is low

    Returns: {"edges": [...], "node_updates": {...}}
    """
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not aws_key or not aws_secret:
        print("Warning: No AWS credentials. Skipping orchestrated analysis.")
        return {"edges": [], "node_updates": {}}

    try:
        client = _get_bedrock_client()
    except Exception as e:
        print(f"Warning: Failed to create Bedrock client: {e}")
        return {"edges": [], "node_updates": {}}

    valid_nodes = [n for n in nodes if n.get("id")]
    if not valid_nodes:
        return {"edges": [], "node_updates": {}}

    all_edges: List[Dict] = []
    node_updates: Dict[str, Dict] = {}

    # ── Phase 1: Classification (Mapper) ──────────────────────────────
    print(f"[Orchestrator] Phase 1: Classifying {len(valid_nodes)} nodes...")
    batch_size_a = 20  # Reduced from 50 to avoid output truncation
    tier_map: Dict[str, Dict] = {}

    for i in range(0, len(valid_nodes), batch_size_a):
        batch = valid_nodes[i : i + batch_size_a]
        classifications = classify_nodes(client, batch, valid_nodes)
        tier_map.update(classifications)

    # Partition by tier
    tier_buckets: Dict[int, List[Dict]] = {0: [], 1: [], 2: [], 3: []}
    for node in valid_nodes:
        tier_info = tier_map.get(node["id"], {})
        tier = tier_info.get("risk_tier", 1)
        tier = max(0, min(3, tier))  # clamp
        tier_buckets[tier].append(node)
        # Store classification in node_updates
        node_updates[node["id"]] = {
            "risk_tier": tier,
            "classification": tier_info.get("classification", "unknown"),
            "deep_reasoning_required": tier_info.get("deep_reasoning_required", False),
            "external_interaction_likelihood": tier_info.get(
                "external_interaction_likelihood", "none"
            ),
        }

    t0, t1, t2, t3 = (
        len(tier_buckets[0]),
        len(tier_buckets[1]),
        len(tier_buckets[2]),
        len(tier_buckets[3]),
    )
    print(f"[Orchestrator] Tiers: T0={t0} skip, T1={t1} light, T2={t2} moderate, T3={t3} deep")

    if (t2 + t3) == 0 and len(valid_nodes) > 10:
        print("[Orchestrator] WARNING: Zero nodes classified as Tier 2 or 3. Sentinel (Deep Analysis) will be skipped.")

    # Tier 0 nodes: minimal metadata, skip further LLM calls
    for node in tier_buckets[0]:
        node_updates[node["id"]].update({
            "risk_level": "none",
            "failure_reason": "Trivial node — skipped deep analysis",
            "architectural_role": "utility",
            "confidence_score": 0.95,
            "node_summary": f"Trivial: {node['name']}",
        })

    # ── Phase 2: Relation Extraction (Linker) — Tiers 1, 2, 3 ────────
    nodes_for_extraction = tier_buckets[1] + tier_buckets[2] + tier_buckets[3]
    if nodes_for_extraction:
        print(f"[Orchestrator] Phase 2: Extracting relations for {len(nodes_for_extraction)} nodes...")
        # Reduced batch size to avoid output truncation (2000 token limit)
        batch_size_b = 8   # Reduced from 20 to fit within model output limit
        overlap_b = 2      # Reduced from 5 proportionally

        for i in range(0, len(nodes_for_extraction), batch_size_b - overlap_b):
            batch = nodes_for_extraction[i : i + batch_size_b]
            result = extract_relations(client, batch, valid_nodes)

            if "relationships" in result:
                all_edges.extend(result["relationships"])

            if "results" in result:
                for nd in result["results"]:
                    nid = nd.get("id")
                    if nid and nid in node_updates:
                        node_updates[nid].update({
                            "architectural_role": nd.get("architectural_role", "unknown"),
                            "node_summary": nd.get("node_summary", ""),
                            "entry_point": nd.get("entry_point", {}),
                            "sensitive_behaviors": nd.get("sensitive_behaviors", {}),
                            "impact_analysis": nd.get("impact_analysis", {}),
                            "confidence_score": nd.get("confidence_score", 0.0),
                        })

    # ── Phase 3: Deep Risk Analysis (Sentinel) — Tiers 2, 3 ────────────
    # Parallelized: up to MAX_PARALLEL_RISK concurrent LLM calls
    MAX_PARALLEL_RISK = 3  # Reduced from 5 to avoid AWS Bedrock throttling
    nodes_for_deep_risk = tier_buckets[2] + tier_buckets[3]
    if nodes_for_deep_risk:
        print(f"[Orchestrator] Phase 3: Deep risk analysis for {len(nodes_for_deep_risk)} nodes (parallel, workers={MAX_PARALLEL_RISK})...")

        # Pre-compute per-node relations so threads don't mutate shared state
        node_relation_map = {}
        for node in nodes_for_deep_risk:
            nid = node["id"]
            node_relation_map[nid] = [
                e for e in all_edges
                if e.get("source") == nid or e.get("target") == nid
            ]

        def _analyze_single_node(node):
            """Thread worker: call Sentinel for a single node."""
            nid = node["id"]
            return nid, analyze_risk_deep(client, node, node_relation_map[nid])

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_RISK) as executor:
            futures = {
                executor.submit(_analyze_single_node, node): node
                for node in nodes_for_deep_risk
            }
            for future in futures:
                try:
                    nid, risk_report = future.result()
                    if risk_report:
                        overall = risk_report.get("overall_risk", "low")
                        risk_breakdown = risk_report.get("risk_breakdown", {})
                        node_updates[nid].update({
                            "risk_level": overall,
                            "risk_analysis": {
                                "overall_risk": overall,
                                "risk_factors": {
                                    k + "_risk": v for k, v in risk_breakdown.items()
                                },
                            },
                            "failure_reason": risk_report.get("risk_summary", ""),
                            "confidence_score": risk_report.get("confidence_score", 0.0),
                        })
                except Exception as e:
                    node = futures[future]
                    print(f"[Sentinel] Parallel analysis failed for {node['id']}: {e}")

    # Fill defaults for Tier 1 nodes that didn't get deep risk analysis
    for node in tier_buckets[1]:
        nid = node["id"]
        if "risk_level" not in node_updates.get(nid, {}):
            node_updates[nid].update({
                "risk_level": "low",
                "failure_reason": "Low-risk node — lightweight analysis only",
            })

    # ── Deduplication ─────────────────────────────────────────────────
    seen_edges = set()
    unique_edges = []
    for edge in all_edges:
        key = (edge.get("source"), edge.get("target"), edge.get("type"))
        if key not in seen_edges and edge.get("source") and edge.get("target"):
            seen_edges.add(key)
            unique_edges.append(edge)

    # ── Heuristic fallback ────────────────────────────────────────────
    if len(unique_edges) < len(valid_nodes) * 0.1:
        print("[Orchestrator] Low connectivity. Adding heuristic relationships...")
        heuristic = _create_heuristic_relationships(valid_nodes)
        for e in heuristic:
            key = (e["source"], e["target"], e["type"])
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(e)
        print(f"[Orchestrator] Added {len(heuristic)} heuristic edges.")

    print(f"[Orchestrator] Done. {len(unique_edges)} edges.")

    return {
        "edges": unique_edges,
        "node_updates": node_updates,
    }
