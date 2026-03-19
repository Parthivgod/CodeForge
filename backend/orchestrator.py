"""
Multi-Model Orchestrator for CodeForge.

Routes AST nodes through a 3-model analysis pipeline:
  Mapper   — Node Mapper    (fast triage & tier assignment)
  Linker   — Relation Linker (semantic topology mapping)
  Sentinel — Security Sentinel (security & stability reasoning)

Every LLM call logs token usage to token_usage.txt.

Performance optimisations (v2):
  1. Heuristic pre-filter  — obvious Tier-0 nodes bypass the Mapper entirely.
  2. Result cache          — content-addressable hash skips nodes seen in a
                             previous run within the same process lifetime.
  3. Parallel Mapper       — all Mapper batches run concurrently.
  4. Parallel Linker       — all Linker batches run concurrently (no overlap).
  5. Higher Sentinel pool  — MAX_PARALLEL_RISK raised from 3 → 6.
  6. RateLimiter is thread-safe — uses a Lock so parallel callers don't race.
"""

import os
import json
import hashlib
import re
import time
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import boto3
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# ---------------------------------------------------------------------------
# RATE LIMITING — thread-safe
# ---------------------------------------------------------------------------
class RateLimiter:
    """Token-bucket rate limiter safe for use across multiple threads."""
    def __init__(self, calls_per_second: int = 10):
        self.min_interval   = 1.0 / calls_per_second
        self.last_call_time = 0.0
        self._lock          = threading.Lock()

    def wait_if_needed(self):
        with self._lock:
            now   = time.time()
            delta = now - self.last_call_time
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
            self.last_call_time = time.time()

# 10 req/s ceiling — shared across all parallel workers
rate_limiter = RateLimiter(calls_per_second=10)

# ---------------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------------
MODEL_ROLES: Dict[str, Dict[str, Any]] = {
    "mapper": {
        "name":            "Node Mapper",
        "model_id":        os.getenv("MODEL_MAPPER", "PLACEHOLDER_CLASSIFIER_MODEL"),
        "temperature":     0.0,
        "max_retries":     2,
        "timeout_seconds": 30,
        "description":     "Fast, lightweight model for triage and tier assignment.",
    },
    "linker": {
        "name":            "Relation Linker",
        "model_id":        os.getenv("MODEL_LINKER", "PLACEHOLDER_EXTRACTOR_MODEL"),
        "temperature":     0.1,
        "max_retries":     2,
        "timeout_seconds": 60,
        "description":     "Mid-range model for semantic relation extraction.",
    },
    "sentinel": {
        "name":            "Security Sentinel",
        "model_id":        os.getenv("MODEL_SENTINEL", "PLACEHOLDER_RISK_MODEL"),
        "temperature":     0.1,
        "max_retries":     3,
        "timeout_seconds": 120,
        "description":     "Frontier reasoning model for deep security analysis.",
    },
}

TOKEN_LOG_FILE = os.path.join(os.path.dirname(__file__), "token_usage.txt")
_token_log_lock = threading.Lock()   # prevent garbled log lines from parallel writes

# ---------------------------------------------------------------------------
# SYSTEM PROMPTS
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_MAPPER = """You are a High-Speed Code Triage Engine.
Classify each AST node and determine the required depth of analysis.
Nodes may be from Python, JavaScript, TypeScript, Java, or Go — apply
language-appropriate heuristics for what constitutes boilerplate vs. risk.

TIER DEFINITIONS:
- Tier 0: Trivial. Imports, logging calls, constants, boilerplate, empty
  modules. No risk. EXCEPTION: a module whose imports include subprocess,
  os, exec, shell, or crypto is NOT Tier 0 — treat as at least Tier 2.
- Tier 1: Low-Risk. Pure functions, simple data transforms, formatting helpers.
- Tier 2: Moderate-Risk. Business logic, API endpoints, DB queries, complex branching.
- Tier 3: High-Risk. Auth, crypto, concurrency primitives, PII handling,
  file I/O with user input, shell/eval calls.

PRE-COMPUTED SIGNALS (use these to inform tier assignment):
- "security_flags": concrete behavioral flags already extracted from the AST
  (has_eval, has_shell_call, has_file_access, has_env_access, etc.).
  Any node with has_eval=true or has_shell_call=true is at minimum Tier 3.
- "risk_ast.sinks": dangerous operation targets already identified.
  Non-empty sinks push tier up by at least 1.
- "risk_ast.sources": data source signals (env, file, user input).
- "graph.reachable_sinks": number of dangerous sinks reachable from this node.
  A value >= 3 indicates high blast radius — treat as Tier 2 minimum.

CONFIDENCE SCORE GUIDANCE:
- 0.90–0.99: security_flags and risk_ast provide direct, clear evidence.
- 0.70–0.89: Risk inferred from call names, parameters, or graph position.
- 0.50–0.69: Node is ambiguous — limited signal.
- 0.20–0.49: Node is too minimal to classify reliably.

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
Nodes may be from Python, JavaScript, TypeScript, Java, or Go.

CONSTRAINTS:
- Identify calls, implementations, dependencies, and data flow.
- DO NOT perform risk analysis or security reasoning — that is Sentinel's job.
- DO NOT re-classify nodes; the Mapper has already assigned classification.
  Echo the Mapper's classification in your output unchanged.
- DO NOT create redundant edges between the same source-target pair.
  Pick the MOST SPECIFIC applicable edge type.

EDGE TYPES (use exactly these values):
  calls        — function/method invocation
  contains     — parent/child structural containment (class→method, module→function)
  depends_on   — import or module-level dependency
  uses_api     — external HTTP/RPC/SDK call
  structural   — inheritance, interface implementation
  flow         — data flow / shared state

ARCHITECTURAL ROLE GUIDANCE:
- Use the "graph" field (fan_in, fan_out, betweenness, depth_from_entry) to
  inform role assignment: high fan_in + low depth = likely controller/middleware;
  high fan_out + many reachable sinks = likely service/infrastructure.
- Use "risk_ast.external_interactions" to identify repository/infrastructure roles.

IMPACT ANALYSIS SCALE (blast_radius_score and change_sensitivity):
- blast_radius_score: integer 1–10. Use graph.reachable_sink_count and fan_out
  as primary signals. A node with fan_out > 10 or reachable_sinks > 5 scores >= 7.
- change_sensitivity: "low" (isolated), "medium" (affects 1–3 modules),
  "high" (cross-cutting or entry point).

For the given nodes return STRICT JSON (no markdown, no explanation):
{
  "results": [
    {
      "id": "node_id",
      "node_summary": "...",
      "classification": "<echo Mapper value>",
      "architectural_role": "controller|service|repository|utility|middleware|model|config|infrastructure|test|unknown",
      "entry_point": {"is_entry_point": false, "entry_type": "unknown"},
      "sensitive_behaviors": {"handles_user_input": false, "accesses_filesystem": false, "network_calls": false},
      "impact_analysis": {"blast_radius_score": 1, "critical_path_likelihood": 1, "change_sensitivity": "low"},
      "confidence_score": 0.9
    }
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "calls|contains|depends_on|uses_api|structural|flow", "description": "short reason"}
  ]
}"""

SYSTEM_PROMPT_SENTINEL = """You are a Principal Security Reasoning Engine.
Analyze the provided code node and its extracted relations for deep architectural risks.
This is a backend code analysis tool; focus on server-side vulnerabilities only.

ANALYSIS VECTORS:
1. Injection: SQL, Command, NoSQL, LDAP. (Exclude XSS — frontend concern only.)
2. Authorization: Broken access control, privilege escalation, IDOR.
3. Concurrency: Race conditions, deadlocks, shared state mutation.
4. Exposure: PII leaks, sensitive logging, secret/credential exposure.

USING INPUT SIGNALS:
- "security_flags": pre-extracted behavioral flags. has_eval=true or
  has_shell_call=true should immediately raise injection to at least "high".
  has_env_access=true is a strong exposure signal.
- "risk_ast.sources/sinks": already-identified data sources and dangerous sinks.
  A node with both a source and a sink in its profile warrants critical scrutiny.
- "relations": use these to assess blast radius — how many other nodes are
  reachable from this one and what are their roles?

OVERALL RISK AGGREGATION:
- If ANY vector is "critical" → overall_risk = "critical"
- If ANY vector is "high" and none are "critical" → overall_risk = "high"
- If the highest is "moderate" → overall_risk = "moderate"
- Otherwise → overall_risk = "low" or "none"

BLAST RADIUS SCALE: integer 1–10.
- 1–3: Isolated node, few callers, no sensitive sinks reachable.
- 4–6: Moderate reach, touches 1–2 sensitive subsystems.
- 7–9: Cross-cutting node or entry point with many downstream dependencies.
- 10: System-wide impact (e.g., auth middleware, global request handler).

CONSTRAINTS:
- Be conservative: flag potential risks even if partially obscured.
- NO HALLUCINATION: Only reference symbols present in the input.

CONFIDENCE SCORE GUIDANCE (confidence_score reflects certainty in your conclusion):
- 0.85–0.95: Evidence is clear and directly observable in the provided code.
- 0.65–0.84: Risk is strongly inferred from patterns, flags, or call signatures.
- 0.40–0.64: Risk is possible but ambiguous — limited direct evidence.
- 0.20–0.39: Node is structurally unclear or too minimal to reason about.
Do NOT lower confidence because full codebase context is absent.
You are reasoning about what IS present in the node, not what is missing.

Return STRICT JSON (no markdown, no explanation):
{
  "risk_breakdown": {
    "injection":      {"level": "none|low|moderate|high|critical", "reason": "..."},
    "authorization":  {"level": "none|low|moderate|high|critical", "reason": "..."},
    "concurrency":    {"level": "none|low|moderate|high|critical", "reason": "..."},
    "exposure":       {"level": "none|low|moderate|high|critical", "reason": "..."}
  },
  "overall_risk":     "none|low|moderate|high|critical",
  "blast_radius":     1,
  "confidence_score": 0.0,
  "risk_summary":     "..."
}"""

# ---------------------------------------------------------------------------
# TOKEN LOGGING
# ---------------------------------------------------------------------------

def _log_tokens(role: str, model_id: str, input_tokens: int, output_tokens: int):
    """Append token usage to token_usage.txt — thread-safe."""
    total     = input_tokens + output_tokens
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{timestamp}] role={role} | model={model_id} "
        f"| input={input_tokens} | output={output_tokens} | total={total}\n"
    )
    with _token_log_lock:
        with open(TOKEN_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    print(f"[Token] {role}: in={input_tokens} out={output_tokens} total={total}")

# ---------------------------------------------------------------------------
# BEDROCK CLIENT
# ---------------------------------------------------------------------------

def _get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

@traceable(run_type="llm", project_name="CodeForge")
def _call_model(client, role: str, model_id: str, system_prompt: str,
                user_prompt: str, temperature: float = 0.1) -> str:
    """Call AWS Bedrock Converse API with rate limiting, log tokens, return text."""
    rate_limiter.wait_if_needed()

    messages = [{"role": "user", "content": [{"text": user_prompt}]}]
    system   = [{"text": system_prompt}]

    response = client.converse(
        modelId=model_id,
        messages=messages,
        system=system,
        inferenceConfig={"temperature": temperature, "maxTokens": 4096},
    )

    usage        = response.get("usage", {})
    input_tokens = usage.get("inputTokens", 0)
    output_tokens= usage.get("outputTokens", 0)
    _log_tokens(role, model_id, input_tokens, output_tokens)

    rt = get_current_run_tree()
    if rt:
        rt.extra = rt.extra or {}
        rt.extra["usage"] = {
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "total_tokens":  input_tokens + output_tokens,
        }
        rt.extra.setdefault("metadata", {}).update(
            {"model": model_id, "role": role, "provider": "aws_bedrock"}
        )

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
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                print(f"[Orchestrator] JSON Parse Error (Regex): {e}\nRaw: {raw[:200]}...")
        else:
            print(f"[Orchestrator] JSON Parse Error (No Match): {raw[:200]}...")
    return None

# ---------------------------------------------------------------------------
# NODE HASHING / RESULT CACHE
# ---------------------------------------------------------------------------

# Persists for the lifetime of the process — repeated uploads of the same
# codebase skip re-analysis of unchanged nodes entirely.
_result_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()


def _node_hash(node: Dict) -> str:
    """Content-addressable hash for a node."""
    calls = node.get("calls", [])
    call_names = sorted([c if isinstance(c, str) else c.get("name", "") for c in calls])
    key_parts = json.dumps({
        "name":   node.get("name"),
        "type":   node.get("type"),
        "file":   node.get("file"),
        "line":   node.get("line_start"),
        "calls":  call_names,
        "params": sorted(node.get("parameters", [])),
    }, sort_keys=True)
    return hashlib.sha256(key_parts.encode()).hexdigest()


def _cache_get(node: Dict) -> Optional[Dict]:
    h = _node_hash(node)
    with _cache_lock:
        return _result_cache.get(h)


def _cache_set(node: Dict, value: Dict):
    h = _node_hash(node)
    with _cache_lock:
        _result_cache[h] = value

# ---------------------------------------------------------------------------
# HEURISTIC TIER-0 PRE-FILTER
# ---------------------------------------------------------------------------

_DANGEROUS_IMPORTS = {
    "subprocess", "os", "exec", "shell", "crypto", "eval",
    "ctypes", "pickle", "socket", "pty",
}

def _is_heuristic_tier0(node: Dict) -> bool:
    """
    Return True if a node is obviously Tier-0 without asking the Mapper.
    Criteria (ALL must hold):
      - loc ≤ 3  (tiny node — almost certainly a stub or constant)
      - no calls
      - no security_flags set
      - no risk_ast sinks
      - type is module/import BUT imports list is empty or contains no dangerous names
    A node that passes this check gets auto-assigned Tier 0 and never hits the LLM.
    """
    if node.get("loc", 99) > 3:
        return False
    if node.get("calls"):
        return False
    # Any security flag set → not trivial
    for flag in ("has_eval", "has_shell_call", "has_file_access",
                 "has_env_access", "has_lock_usage"):
        if node.get(flag):
            return False
    # Non-empty sinks → not trivial
    risk_ast = node.get("risk_ast") or {}
    if risk_ast.get("sinks"):
        return False
    # Module with dangerous import → not trivial
    imports = [str(i).lower() for i in node.get("imports", [])]
    if any(d in imp for imp in imports for d in _DANGEROUS_IMPORTS):
        return False
    return True

# ---------------------------------------------------------------------------
# NODE SUMMARY BUILDER
# ---------------------------------------------------------------------------

def _prepare_node_summary(node: Dict, all_nodes: List[Dict]) -> Dict:
    """Enriched summary of a node for LLM consumption."""
    summary: Dict[str, Any] = {
        "id":       node["id"],
        "name":     node["name"],
        "type":     node["type"],
        "file":     node["file"],
        "line":     node.get("line_start"),
        "loc":      node.get("loc", 0),
        "language": node.get("language", "unknown"),
    }

    fan_in  = node.get("fan_in", 0)
    fan_out = node.get("fan_out", 0)
    if fan_in or fan_out:
        summary["graph"] = {
            "fan_in":           fan_in,
            "fan_out":          fan_out,
            "betweenness":      round(node.get("betweenness_centrality", 0.0), 4),
            "depth_from_entry": node.get("depth_from_entry", -1),
            "reachable_sinks":  node.get("reachable_sink_count", 0),
        }

    sec_flags = {
        k: node[k] for k in (
            "has_eval", "has_shell_call", "has_file_access",
            "has_env_access", "has_lock_usage", "has_async_await",
            "has_try_catch", "has_loop", "has_conditional",
        ) if node.get(k)
    }
    if sec_flags:
        summary["security_flags"] = sec_flags

    risk_ast = node.get("risk_ast")
    if risk_ast:
        summary["risk_ast"] = {
            "sources":              risk_ast.get("sources", []),
            "sinks":                risk_ast.get("sinks", []),
            "entry":                risk_ast.get("entry", False),
            "external_interactions":risk_ast.get("external_interactions", [])[:5],
        }

    if node["type"] == "function":
        calls = node.get("calls", [])
        call_names = [c if isinstance(c, str) else c.get("name", "") for c in calls][:12]
        summary["calls"]      = call_names
        summary["api_calls"]  = node.get("api_calls", [])[:8]
        summary["parameters"] = node.get("parameters", [])[:8]
        summary["variables"]  = node.get("variables", [])[:10]
        if node.get("is_entry_point"):
            summary["entry_point"] = node.get("entry_type", "unknown")
    elif node["type"] == "class":
        summary["methods"]  = [n["name"] for n in all_nodes if n.get("parent_class") == node["name"]][:10]
        summary["inherits"] = node.get("inherits", [])
    elif node["type"] == "module":
        summary["imports"]  = node.get("imports", [])[:10]

    return summary

# ---------------------------------------------------------------------------
# MAPPER — parallel batch classification
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def classify_nodes(client, nodes: List[Dict], all_nodes: List[Dict]) -> Dict[str, Dict]:
    """Classify a single batch. Called by parallel workers."""
    cfg       = MODEL_ROLES["mapper"]
    summaries = [_prepare_node_summary(n, all_nodes) for n in nodes]
    prompt    = (
        f"Classify the following {len(summaries)} AST nodes.\n"
        "Assign each node a risk_tier (0-3), classification, and whether "
        "deep reasoning is required.\n\n"
        f"Nodes:\n{json.dumps(summaries, indent=2)}"
    )
    raw    = _call_model(client, "Mapper", cfg["model_id"], SYSTEM_PROMPT_MAPPER, prompt, cfg["temperature"])
    parsed = _parse_json_response(raw)
    if not parsed or "classifications" not in parsed:
        print("[Mapper] Failed to parse response — defaulting to Tier 1.")
        return {
            n["id"]: {
                "classification": "unknown", "risk_tier": 1,
                "deep_reasoning_required": False,
                "external_interaction_likelihood": "low", "confidence": 0.5,
            }
            for n in nodes
        }
    return {c["id"]: c for c in parsed["classifications"] if "id" in c}


def _run_mapper_parallel(client, nodes_to_classify: List[Dict],
                          all_nodes: List[Dict],
                          batch_size: int = 20) -> Dict[str, Dict]:
    """
    Split nodes into batches and classify them all concurrently.
    Workers=5 keeps us well within the 10 req/s ceiling even at max batch rate.
    """
    batches = [nodes_to_classify[i:i + batch_size]
               for i in range(0, len(nodes_to_classify), batch_size)]
    tier_map: Dict[str, Dict] = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(classify_nodes, client, batch, all_nodes): batch
            for batch in batches
        }
        for future in as_completed(futures):
            try:
                tier_map.update(future.result())
            except Exception as e:
                batch = futures[future]
                print(f"[Mapper] Batch failed ({[n['id'] for n in batch[:3]]}…): {e}")
                # Fallback: assign Tier 1 to every node in the failed batch
                for n in batch:
                    tier_map[n["id"]] = {
                        "classification": "unknown", "risk_tier": 1,
                        "deep_reasoning_required": False,
                        "external_interaction_likelihood": "low", "confidence": 0.5,
                    }
    return tier_map

# ---------------------------------------------------------------------------
# LINKER — parallel batch relation extraction (no overlap)
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def extract_relations(client, nodes: List[Dict], all_nodes: List[Dict]) -> Dict[str, Any]:
    """Extract semantic relationships for a single batch."""
    cfg       = MODEL_ROLES["linker"]
    summaries = [_prepare_node_summary(n, all_nodes) for n in nodes]
    prompt    = (
        f"Analyze the following {len(summaries)} AST nodes.\n"
        "Extract semantic relations and assign architectural roles.\n\n"
        "IMPORTANT: NO REDUNDANT EDGES between the same source and target. "
        "Pick the MOST SPECIFIC edge type.\n\n"
        f"Nodes:\n{json.dumps(summaries, indent=2)}"
    )
    raw    = _call_model(client, "linker", cfg["model_id"], SYSTEM_PROMPT_LINKER, prompt, cfg["temperature"])
    parsed = _parse_json_response(raw)
    if not parsed:
        print("[Linker] Failed to parse response.")
        return {"results": [], "relationships": []}
    return parsed


def _run_linker_parallel(client, nodes_for_extraction: List[Dict],
                          all_nodes: List[Dict],
                          batch_size: int = 8) -> tuple:
    """
    Split nodes into batches and extract relations concurrently.
    Overlap removed — each node appears in exactly one batch.
    Returns (all_edges, node_result_map).
    """
    batches = [nodes_for_extraction[i:i + batch_size]
               for i in range(0, len(nodes_for_extraction), batch_size)]

    all_edges: List[Dict]        = []
    node_result_map: Dict[str, Dict] = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(extract_relations, client, batch, all_nodes): batch
            for batch in batches
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                if "relationships" in result:
                    all_edges.extend(result["relationships"])
                if "results" in result:
                    for nd in result["results"]:
                        nid = nd.get("id")
                        if nid:
                            node_result_map[nid] = nd
            except Exception as e:
                batch = futures[future]
                print(f"[Linker] Batch failed ({[n['id'] for n in batch[:3]]}…): {e}")

    return all_edges, node_result_map

# ---------------------------------------------------------------------------
# SENTINEL — deep risk analysis (parallel, higher worker count)
# ---------------------------------------------------------------------------

@traceable(project_name="CodeForge")
def analyze_risk_deep(client, node: Dict, relations: List[Dict]) -> Optional[Dict]:
    """Deep security reasoning on a single node."""
    cfg    = MODEL_ROLES["sentinel"]
    prompt = (
        "Analyze the following node for security and stability risks.\n\n"
        f"Node:\n{json.dumps(node, indent=2)}\n\n"
        f"Known relations:\n{json.dumps(relations, indent=2)}"
    )
    for attempt in range(cfg["max_retries"]):
        try:
            raw    = _call_model(client, "sentinel", cfg["model_id"],
                                 SYSTEM_PROMPT_SENTINEL, prompt, cfg["temperature"])
            parsed = _parse_json_response(raw)
            if parsed and "risk_breakdown" in parsed:
                return parsed
        except Exception as e:
            print(f"[Sentinel] Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)

    return {
        "risk_breakdown": {
            "injection":     {"level": "unknown", "reason": "Analysis failed"},
            "authorization": {"level": "unknown", "reason": "Analysis failed"},
            "concurrency":   {"level": "unknown", "reason": "Analysis failed"},
            "exposure":      {"level": "unknown", "reason": "Analysis failed"},
        },
        "overall_risk":     "unknown",
        "blast_radius":     0,
        "confidence_score": 0.4,
        "risk_summary":     "Deep risk analysis failed. Manual review recommended.",
    }

# ---------------------------------------------------------------------------
# HEURISTIC FALLBACK
# ---------------------------------------------------------------------------

def _create_heuristic_relationships(nodes: List[Dict]) -> List[Dict]:
    """Basic structural edges when LLM connectivity is low."""
    edges = []
    for node in nodes:
        for call_name in node.get("calls", []):
            for other in nodes:
                if other["name"] == call_name and other["id"] != node["id"]:
                    edges.append({
                        "source":      node["id"],
                        "target":      other["id"],
                        "type":        "calls",
                        "description": f"{node['name']} calls {other['name']}",
                        "confidence":  0.9,
                    })
        node_vars = set(node.get("variables", []))
        if len(node_vars) >= 3:
            for other in nodes:
                if other["id"] != node["id"]:
                    shared = node_vars & set(other.get("variables", []))
                    if len(shared) >= 3:
                        edges.append({
                            "source":      node["id"],
                            "target":      other["id"],
                            "type":        "flow",
                            "description": f"Shared data: {', '.join(list(shared)[:2])}...",
                            "confidence":  0.8,
                        })
    seen   = set()
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
      0. Result cache      — skip nodes seen in a previous run
      0b. Heuristic filter — auto-assign obvious Tier-0 nodes without LLM
      1. Mapper (parallel) — classify remaining nodes, assign tiers
      2. Linker (parallel) — extract relations, no overlap
      3. Sentinel (×6)     — deep risk analysis on Tier 2-3
      4. Heuristic fallback if connectivity is low

    Returns: {"edges": [...], "node_updates": {...}}
    """
    # ── Credentials check ─────────────────────────────────────────────
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
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

    all_edges:    List[Dict]      = []
    node_updates: Dict[str, Dict] = {}

    # ── Step 0: Result cache — skip unchanged nodes from prior runs ────
    cached_nodes   = []
    uncached_nodes = []
    for node in valid_nodes:
        cached = _cache_get(node)
        if cached:
            node_updates[node["id"]] = cached
            cached_nodes.append(node)
        else:
            uncached_nodes.append(node)

    if cached_nodes:
        print(f"[Orchestrator] Cache hit: {len(cached_nodes)} nodes skipped "
              f"({len(uncached_nodes)} to analyse).")

    nodes_to_process = uncached_nodes

    # ── Step 0b: Heuristic Tier-0 pre-filter ──────────────────────────
    heuristic_tier0 = []
    needs_mapper    = []
    for node in nodes_to_process:
        if _is_heuristic_tier0(node):
            heuristic_tier0.append(node)
        else:
            needs_mapper.append(node)

    if heuristic_tier0:
        print(f"[Orchestrator] Heuristic pre-filter: {len(heuristic_tier0)} nodes "
              f"auto-assigned Tier 0 (no LLM call).")

    tier0_update = {
        "risk_tier":      0,
        "classification": "utility",
        "deep_reasoning_required": False,
        "external_interaction_likelihood": "none",
        "risk_level":     "none",
        "failure_reason": "Trivial node — heuristic pre-filter",
        "architectural_role": "utility",
        "confidence_score": 0.95,
        "node_summary":   "",   # filled per-node below
    }
    for node in heuristic_tier0:
        update = {**tier0_update, "node_summary": f"Trivial: {node['name']}"}
        node_updates[node["id"]] = update
        _cache_set(node, update)

    # ── Phase 1: Mapper — parallel batch classification ────────────────
    tier_map: Dict[str, Dict] = {}
    if needs_mapper:
        print(f"[Orchestrator] Phase 1: Classifying {len(needs_mapper)} nodes "
              f"(parallel batches, batch_size=20)...")
        tier_map = _run_mapper_parallel(client, needs_mapper, valid_nodes, batch_size=20)

    # Partition by tier
    tier_buckets: Dict[int, List[Dict]] = {0: [], 1: [], 2: [], 3: []}
    for node in needs_mapper:
        tier_info = tier_map.get(node["id"], {})
        tier      = max(0, min(3, tier_info.get("risk_tier", 1)))
        tier_buckets[tier].append(node)
        node_updates[node["id"]] = {
            "risk_tier":      tier,
            "classification": tier_info.get("classification", "unknown"),
            "deep_reasoning_required": tier_info.get("deep_reasoning_required", False),
            "external_interaction_likelihood": tier_info.get("external_interaction_likelihood", "none"),
        }

    # Include heuristic Tier-0 in the bucket for reporting
    tier_buckets[0].extend(heuristic_tier0)

    t0 = len(tier_buckets[0])
    t1 = len(tier_buckets[1])
    t2 = len(tier_buckets[2])
    t3 = len(tier_buckets[3])
    print(f"[Orchestrator] Tiers: T0={t0} skip, T1={t1} light, T2={t2} moderate, T3={t3} deep")

    if (t2 + t3) == 0 and len(valid_nodes) > 10:
        print("[Orchestrator] WARNING: Zero nodes classified as Tier 2 or 3. "
              "Sentinel will be skipped.")

    # LLM-classified Tier 0 nodes
    for node in tier_buckets[0]:
        if node["id"] not in node_updates or "risk_level" not in node_updates[node["id"]]:
            update = {
                **node_updates.get(node["id"], {}),
                "risk_level":     "none",
                "failure_reason": "Trivial node — skipped deep analysis",
                "architectural_role": "utility",
                "confidence_score": 0.95,
                "node_summary":   f"Trivial: {node['name']}",
            }
            node_updates[node["id"]] = update
            _cache_set(node, update)

    # ── Phase 2: Linker — parallel, no overlap ────────────────────────
    nodes_for_extraction = tier_buckets[1] + tier_buckets[2] + tier_buckets[3]
    if nodes_for_extraction:
        print(f"[Orchestrator] Phase 2: Extracting relations for "
              f"{len(nodes_for_extraction)} nodes (parallel, batch_size=8, no overlap)...")
        linker_edges, linker_results = _run_linker_parallel(
            client, nodes_for_extraction, valid_nodes, batch_size=8
        )
        all_edges.extend(linker_edges)

        for nid, nd in linker_results.items():
            if nid in node_updates:
                node_updates[nid].update({
                    "architectural_role":  nd.get("architectural_role", "unknown"),
                    "node_summary":        nd.get("node_summary", ""),
                    "entry_point":         nd.get("entry_point", {}),
                    "sensitive_behaviors": nd.get("sensitive_behaviors", {}),
                    "impact_analysis":     nd.get("impact_analysis", {}),
                    "confidence_score":    nd.get("confidence_score", 0.0),
                })

    # ── Phase 3: Sentinel — parallel, 6 workers ───────────────────────
    MAX_PARALLEL_RISK  = 6   # raised from 3; rate limiter keeps us at ≤10 req/s
    nodes_for_deep_risk = tier_buckets[2] + tier_buckets[3]
    if nodes_for_deep_risk:
        print(f"[Orchestrator] Phase 3: Deep risk analysis for "
              f"{len(nodes_for_deep_risk)} nodes (parallel, workers={MAX_PARALLEL_RISK})...")

        node_relation_map = {
            node["id"]: [
                e for e in all_edges
                if e.get("source") == node["id"] or e.get("target") == node["id"]
            ]
            for node in nodes_for_deep_risk
        }

        def _analyze_single(node):
            nid = node["id"]
            return nid, analyze_risk_deep(client, node, node_relation_map[nid])

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_RISK) as executor:
            futures = {executor.submit(_analyze_single, node): node
                       for node in nodes_for_deep_risk}
            for future in as_completed(futures):
                node = futures[future]
                try:
                    nid, risk_report = future.result()
                    if risk_report:
                        overall        = risk_report.get("overall_risk", "low")
                        risk_breakdown = risk_report.get("risk_breakdown", {})
                        update = {
                            "risk_level":    overall,
                            "risk_analysis": {
                                "overall_risk": overall,
                                "risk_factors": {
                                    k + "_risk": v for k, v in risk_breakdown.items()
                                },
                            },
                            "failure_reason":  risk_report.get("risk_summary", ""),
                            "confidence_score":risk_report.get("confidence_score", 0.0),
                        }
                        node_updates[nid].update(update)
                        _cache_set(node, node_updates[nid])
                except Exception as e:
                    print(f"[Sentinel] Parallel analysis failed for {node['id']}: {e}")

    # Tier-1 defaults (no Sentinel)
    for node in tier_buckets[1]:
        nid = node["id"]
        if "risk_level" not in node_updates.get(nid, {}):
            update = {"risk_level": "low",
                      "failure_reason": "Low-risk node — lightweight analysis only",
                      "confidence_score": 0.75}
            node_updates[nid].update(update)
            _cache_set(node, node_updates[nid])

    # ── Deduplication ─────────────────────────────────────────────────
    seen_edges   = set()
    unique_edges = []
    for edge in all_edges:
        key = (edge.get("source"), edge.get("target"), edge.get("type"))
        if key not in seen_edges and edge.get("source") and edge.get("target"):
            seen_edges.add(key)
            unique_edges.append(edge)

    # ── Heuristic fallback ────────────────────────────────────────────
    if len(unique_edges) < len(valid_nodes) * 0.1:
        print("[Orchestrator] Low connectivity — adding heuristic relationships...")
        for e in _create_heuristic_relationships(valid_nodes):
            key = (e["source"], e["target"], e["type"])
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(e)

    print(f"[Orchestrator] Done. {len(unique_edges)} edges, "
          f"{len(cached_nodes)} cache hits, "
          f"{len(heuristic_tier0)} heuristic Tier-0 skips.")

    return {"edges": unique_edges, "node_updates": node_updates}
