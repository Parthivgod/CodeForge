"""
Multi-Language AST Parser and Code Property Graph Builder
"""

import ast
import os
import zipfile
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import networkx as nx
from langsmith import traceable

# ─── Language Mapping ───
LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', 
    '.tsx': 'typescript', '.java': 'java', '.go': 'go', '.c': 'c', '.cpp': 'cpp', 
    '.h': 'c', '.hpp': 'cpp', '.cs': 'csharp', '.rb': 'ruby', '.php': 'php',
}

def detect_language(filepath: str) -> Optional[str]:
    return LANGUAGE_MAP.get(Path(filepath).suffix.lower())

def extract_archive(zip_path: str, extract_to: str) -> str:
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf: zf.extractall(extract_to)
        return extract_to
    return zip_path if os.path.isdir(zip_path) else zip_path

def find_code_files(directory: str) -> List[str]:
    code_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build']]
        for file in files:
            filepath = os.path.join(root, file)
            if detect_language(filepath): code_files.append(filepath)
    return code_files

# ─── Tree-sitter Setup ───
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_java
import tree_sitter_go

TS_LANGUAGES = {
    'python': tree_sitter.Language(tree_sitter_python.language()),
    'javascript': tree_sitter.Language(tree_sitter_javascript.language()),
    'typescript': tree_sitter.Language(tree_sitter_typescript.language_typescript()),
    'java': tree_sitter.Language(tree_sitter_java.language()),
    'go': tree_sitter.Language(tree_sitter_go.language())
}

# ─── Universal Parser ───
class UniversalTreeSitterParser:
    def __init__(self, filepath: str, language_name: str, root_dir: str = ""):
        self.filepath = filepath
        if root_dir:
            rel = os.path.relpath(filepath, root_dir)
            self.module_name = Path(rel).with_suffix('').as_posix().replace('/', '.')
        else:
            self.module_name = Path(filepath).stem
            
        self.language_name = language_name
        self.imports = []
        self.local_symbols = {} # name -> resolved mapping
        
        self.nodes = [{
            "id": self.module_name,
            "type": "module",
            "name": Path(filepath).stem,
            "file": self.filepath,
            "language": self.language_name,
            "line_start": 1,
            "imports": [],
            "calls": []
        }]
        
        self.api_libs = {
            # HTTP/Web frameworks
            'requests', 'httpx', 'flask', 'fastapi', 'django', 'axios', 'fetch',
            # AI/ML libraries
            'langchain', 'openai', 'anthropic', 'boto3', 'groq', 'huggingface',
            # Common AI class names
            'chatgroq', 'chatopenai', 'chatanthropic', 'huggingfaceembeddings',
            'faiss', 'vectorstore', 'embeddings', 'llm',
            # Document loaders
            'pdfloader', 'unstructuredpdfloader', 'documentloader',
            # Agents
            'agent', 'create_react_agent', 'create_agent',
            # Streamlit
            'streamlit', 'st.',
            # Database
            'sqlalchemy', 'pymongo', 'redis', 'postgres'
        }

    def _get_text(self, node, source: bytes) -> str:
        if not node: return ""
        return source[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')

    def walk(self, node, source: bytes, parent_class=None, parent_function=None):
        if not node: return
        
        # 1. IMPORTS & ALIASES
        if node.type in ['import_statement', 'import_from_statement', 'import_declaration']:
            imp_val = self._get_text(node, source).strip()
            self.imports.append(imp_val)

        # 2. CLASSES
        is_class = node.type in ['class_definition', 'class_declaration']
        if is_class:
            name_node = node.child_by_field_name('name')
            name = self._get_text(name_node, source) if name_node else f"AnonClass_{node.start_point[0]}"
            class_id = f"{self.module_name}.{name}"
            self.local_symbols[name] = class_id # Symbol table
            
            self.nodes.append({
                "id": class_id, "type": "class", "name": name, "file": self.filepath,
                "language": self.language_name, "line_start": node.start_point[0] + 1,
                "loc": node.end_point[0] - node.start_point[0] + 1,
            })
            parent_class = class_id

        # 3. FUNCTIONS
        is_func = node.type in ['function_definition', 'function_declaration', 'method_definition']
        if is_func:
            name_node = node.child_by_field_name('name')
            name = self._get_text(name_node, source) if name_node else f"AnonFunc_{node.start_point[0]}"
            func_id = f"{parent_class}.{name}" if parent_class else f"{self.module_name}.{name}"
            self.local_symbols[name] = func_id
            
            # Entry points & Logic
            is_entry = name in ['main', 'handler']
            entry_type = 'unknown'
            if is_entry: entry_type = 'main'
            
            # Look for decorators for routes
            if node.prev_sibling and 'decorator' in node.prev_sibling.type:
                dec_txt = self._get_text(node.prev_sibling, source).lower()
                if any(verb in dec_txt for verb in ['@app', '@route', '@get', '@post', '@router', '@celery']):
                    is_entry = True
                    entry_type = 'http' if '@route' in dec_txt or '@get' in dec_txt or '@post' in dec_txt or '@app' in dec_txt else 'job'
            
            local_calls, api_calls, variables, params, data_flows, flags = self._extract_function_body(node, source, func_id)
            
            self.nodes.append({
                "id": func_id, "type": "function", "name": name, "file": self.filepath,
                "language": self.language_name, "line_start": node.start_point[0] + 1,
                "loc": node.end_point[0] - node.start_point[0] + 1,
                "calls": local_calls, "api_calls": [a['id'] for a in api_calls],
                "variables": variables, "parameters": params,
                "data_flows": data_flows, # [ {type: 'assigns_to', src: 'a', dst: 'b'} ]
                "parent_class": parent_class,
                "is_entry_point": is_entry, "entry_type": entry_type,
                **flags # has_loop, has_conditional, etc.
            })
            self.nodes.extend(api_calls)
            # Don't return here - continue walking to find more functions
            parent_function = func_id

        # 4. Top-level API Calls
        if node.type in ['call', 'call_expression']:
            fn = node.child_by_field_name('function')
            c_name = self._get_text(fn, source)
            if c_name and any(lib in c_name.lower() for lib in self.api_libs):
                # Global API ID (no line number, no module-specific prefix)
                api_id = f"api_global_{c_name.replace('.', '_')}"
                self.nodes.append({
                    "id": api_id,
                    "type": "api_call", "name": c_name, "file": self.filepath,
                    "language": self.language_name, "parent": self.module_name,
                    "line": node.start_point[0] + 1
                })

        for child in node.children:
            self.walk(child, source, parent_class, parent_function)

    def _extract_function_body(self, func_node, source: bytes, func_id: str):
        local_calls = []
        api_nodes = []
        variables = set()
        params = []
        data_flows = []
        
        flags = {
            'has_conditional': False, 'has_loop': False, 'has_try_catch': False,
            'has_throw': False, 'has_async_await': False, 'has_lock_usage': False,
            'has_eval': False, 'has_shell_call': False, 'has_file_access': False, 'has_env_access': False
        }
        
        queue = [func_node]
        while queue:
            curr = queue.pop(0)
            
            # Flags
            if curr.type in ['if_statement', 'switch_statement']: flags['has_conditional'] = True
            elif curr.type in ['for_statement', 'while_statement']: flags['has_loop'] = True
            elif curr.type in ['try_statement']: flags['has_try_catch'] = True
            elif curr.type in ['raise_statement', 'throw_statement']: flags['has_throw'] = True
            elif curr.type in ['await_expression']: flags['has_async_await'] = True
            
            # Params
            if curr.type in ['formal_parameters', 'parameters']:
                for p in curr.children:
                    if p.type == 'identifier':
                        params.append(self._get_text(p, source))
            
            # Assignments (Data Flow: RHS -> LHS)
            if curr.type == 'assignment':
                lhs = curr.child_by_field_name('left')
                rhs = curr.child_by_field_name('right')
                if lhs and rhs:
                    lhs_txt = self._get_text(lhs, source)
                    if rhs.type in ['call', 'call_expression']:
                        data_flows.append({"type": "returns_to", "src": self._get_text(rhs.child_by_field_name('function'), source), "dst": lhs_txt})
                    else:
                        data_flows.append({"type": "assigns_to", "src": "expr", "dst": lhs_txt})
            
            # Calls
            if curr.type in ['call', 'call_expression']:
                func_name_node = curr.child_by_field_name('function')
                call_name = self._get_text(func_name_node, source)
                if call_name:
                    local_calls.append({"name": call_name, "qualified": '.' in call_name})
                    
                    nl = call_name.lower()
                    if 'eval' in nl: flags['has_eval'] = True
                    if 'subprocess' in nl or 'exec' in nl: flags['has_shell_call'] = True
                    if 'open' in nl or 'fs.' in nl: flags['has_file_access'] = True
                    if 'environ' in nl or 'process.env' in nl: flags['has_env_access'] = True
                    if 'lock' in nl or 'mutex' in nl: flags['has_lock_usage'] = True

                    if any(lib in nl for lib in self.api_libs):
                        # Global API ID (no line number, no function-specific prefix)
                        api_id = f"api_global_{call_name.replace('.', '_')}"
                        api_nodes.append({
                            "id": api_id,
                            "type": "api_call", "name": call_name, "file": self.filepath,
                            "language": self.language_name, "parent": func_id,
                            "line": curr.start_point[0] + 1  # Track line for reference
                        })
            
            if curr.type == 'identifier':
                vname = self._get_text(curr, source)
                if vname not in ['self', 'cls', 'this']: variables.add(vname)
            
            for ch in curr.children: queue.append(ch)
                
        return local_calls, api_nodes, list(variables - set(params)), params, data_flows, flags

def parse_file(filepath: str, **kwargs) -> Dict[str, Any]:
    language_name = detect_language(filepath)
    if language_name not in TS_LANGUAGES:
        return {"file": filepath, "language": "unknown", "nodes": [], "imports": [], "symbols": {}}

    try:
        with open(filepath, 'rb') as f: source = f.read()
        visitor = UniversalTreeSitterParser(filepath, language_name, root_dir=kwargs.get('root_dir', ''))
        visitor.walk(tree_sitter.Parser(TS_LANGUAGES[language_name]).parse(source).root_node, source)
        return {"file": filepath, "language": language_name, "nodes": visitor.nodes, "imports": visitor.imports, "symbols": visitor.local_symbols}
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {"file": filepath, "language": language_name, "nodes": [], "imports": [], "symbols": {}}

# ─── Import Resolution ───

def build_import_edges(module_imports: Dict[str, List[str]], module_ids: set) -> List[Dict]:
    """Resolve import statements to module IDs and create depends_on edges.
    
    Args:
        module_imports: {module_id: [raw_import_strings]}
        module_ids: set of all known module node IDs in the graph
    Returns:
        List of edges with type 'depends_on'
    """
    import re
    edges = []
    seen = set()

    for src_module, imports in module_imports.items():
        for imp_str in imports:
            # Extract the base module name from various import forms:
            #   'import foo'           -> 'foo'
            #   'from foo import bar'  -> 'foo'
            #   'from foo.bar import X'-> 'foo.bar', then 'foo'
            #   'import foo.bar'       -> 'foo.bar', then 'foo'
            target_module = None

            m = re.match(r'^from\s+([\w.]+)\s+import', imp_str)
            if m:
                target_module = m.group(1)
            else:
                m = re.match(r'^import\s+([\w.]+)', imp_str)
                if m:
                    target_module = m.group(1)

            if not target_module:
                continue

            # Try exact match first, then progressively shorten dotted path
            candidates = []
            parts = target_module.split('.')
            for i in range(len(parts), 0, -1):
                candidates.append('.'.join(parts[:i]))

            for candidate in candidates:
                if candidate in module_ids and candidate != src_module:
                    key = (src_module, candidate)
                    if key not in seen:
                        seen.add(key)
                        edges.append({
                            "source": src_module,
                            "target": candidate,
                            "type": "depends_on",
                            "confidence": 1.0,
                        })
                    break  # first (most specific) match wins

    return edges


# ─── Symbol Resolution & Edge Building ───

def build_edges(nodes: List[Dict], all_symbols: Dict[str, str]) -> List[Dict]:
    edges = []
    node_by_id = {n['id']: n for n in nodes}
    class_methods = {}
    
    for n in nodes:
        if n['type'] == 'function' and n.get('parent_class'):
            class_methods.setdefault(n['parent_class'], []).append(n['id'])

    for node in nodes:
        # Calls (with confidence)
        for call_info in node.get('calls', []):
            if isinstance(call_info, str): call_name = call_info # Fallback
            else: call_name = call_info.get('name', '')
            
            targets = []
            confidence = 0.0

            # 1. Exact local match mapping
            if call_name in all_symbols:
                targets.append(all_symbols[call_name])
                confidence = 1.0
            # 2. Heuristic: Dotted resolution (e.g. obj.method -> find method)
            elif '.' in call_name:
                method = call_name.split('.')[-1]
                for n_id in node_by_id:
                    if n_id.endswith(f".{method}"):
                        targets.append(n_id)
                        confidence = 0.6
                        break # First match heuristic

            # Add Edge if confident enough
            for t in targets:
                if confidence >= 0.5:
                    edges.append({"source": node['id'], "target": t, "type": "calls", "confidence": confidence})

        # Inheritance (structural)
        for base in node.get('inherits', []):
            if base in all_symbols:
                edges.append({"source": node['id'], "target": all_symbols[base], "type": "structural", "confidence": 1.0})

        # Class Containment (use 'contains' type instead of 'structural')
        if node['type'] == 'class':
            for mid in class_methods.get(node['id'], []):
                edges.append({"source": node['id'], "target": mid, "type": "contains", "confidence": 1.0})

        # API Usage - function uses API call
        # For deduplicated API nodes, create edges from all functions that use it
        if node['type'] == 'api_call':
            # New: Handle deduplicated API nodes with 'used_by' list
            if 'used_by' in node:
                for parent_id in node['used_by']:
                    if parent_id and parent_id in node_by_id:
                        edges.append({"source": parent_id, "target": node['id'], "type": "uses_api", "confidence": 1.0})
            # Fallback: Old single-parent format
            elif node.get('parent'):
                edges.append({"source": node['parent'], "target": node['id'], "type": "uses_api", "confidence": 1.0})

    # Deduplicate edges while preserving different edge types between same nodes
    seen = set()
    unique_edges = []
    for edge in edges:
        # Create a key that includes source, target, AND type
        key = (edge['source'], edge['target'], edge['type'])
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)
    
    return unique_edges

@traceable(project_name="CodeForge")
def build_cpg(path: str, job_id: str) -> Dict[str, Any]:
    print(f"Building Enhanced CPG for {path}")
    working_dir = extract_archive(path, tempfile.mkdtemp(prefix=f"cpg_{job_id}_")) if path.endswith('.zip') else path
    
    all_nodes = []
    global_symbols = {}
    module_imports = {}  # module_id -> [import_strings]
    
    for filepath in find_code_files(working_dir):
        res = parse_file(filepath, root_dir=working_dir)
        all_nodes.extend(res['nodes'])
        # Merge symbols for cross-file resolution (naive global namespace for prototype)
        global_symbols.update(res.get('symbols', {}))
        # Collect imports keyed by module node ID
        for n in res['nodes']:
            if n.get('type') == 'module':
                module_imports[n['id']] = res.get('imports', [])
    
    # Deduplicate API nodes globally
    api_nodes = {}  # api_id -> merged node
    non_api_nodes = []
    
    for node in all_nodes:
        if node.get('type') == 'api_call':
            api_id = node['id']
            if api_id not in api_nodes:
                # First occurrence - initialize with usage tracking
                api_nodes[api_id] = {
                    **node,
                    'usage_count': 1,
                    'used_by': [node.get('parent')],
                    'files': [node.get('file')],
                    'lines': [node.get('line')]
                }
            else:
                # Duplicate - merge usage data
                api_nodes[api_id]['usage_count'] += 1
                if node.get('parent') not in api_nodes[api_id]['used_by']:
                    api_nodes[api_id]['used_by'].append(node.get('parent'))
                if node.get('file') not in api_nodes[api_id]['files']:
                    api_nodes[api_id]['files'].append(node.get('file'))
                api_nodes[api_id]['lines'].append(node.get('line'))
        else:
            non_api_nodes.append(node)
    
    # Combine deduplicated API nodes with other nodes
    unique_nodes = non_api_nodes + list(api_nodes.values())
    
    print(f"[CPG] Deduplicated {len(all_nodes) - len(unique_nodes)} duplicate API nodes")
    print(f"[CPG] Total nodes: {len(unique_nodes)} ({len(non_api_nodes)} code entities + {len(api_nodes)} unique APIs)")
    
    unique_nodes = {n['id']: n for n in unique_nodes}.values()
    
    G = nx.DiGraph()
    for node in unique_nodes: G.add_node(node['id'], **node)
    
    edges = build_edges(list(unique_nodes), global_symbols)
    
    # Build inter-file dependency edges from import resolution
    module_ids = {n['id'] for n in unique_nodes if n.get('type') == 'module'}
    import_edges = build_import_edges(module_imports, module_ids)
    edges.extend(import_edges)
    print(f"[CPG] Resolved {len(import_edges)} inter-file dependency edges")
    
    for e in edges: G.add_edge(e['source'], e['target'], type=e['type'], confidence=e['confidence'])
    
    # Feature Engineering Injection
    from graph_features import compute_graph_features
    G = compute_graph_features(G)
    
    # Expose for frontend
    res_nodes = [data for _, data in G.nodes(data=True)]
    res_edges = [{"id": f"e_{u}_{v}", "source": u, "target": v, "type": data.get('type', 'calls')} for u, v, data in G.edges(data=True)]
    
    return {"nodes": res_nodes, "edges": res_edges, "nx_graph": G}
