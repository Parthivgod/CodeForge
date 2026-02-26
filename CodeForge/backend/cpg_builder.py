"""
Multi-Language AST Parser and Code Property Graph Builder

Supports: Python, JavaScript, TypeScript, Java, Go
"""

import ast
import os
import zipfile
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

# Language extension mapping
LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.rb': 'ruby',
    '.php': 'php',
}

def detect_language(filepath: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(filepath).suffix.lower()
    return LANGUAGE_MAP.get(ext)

def extract_archive(zip_path: str, extract_to: str) -> str:
    """Extract zip archive to target directory."""
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
        return extract_to
    # If it's already a directory (from git clone), return as-is
    if os.path.isdir(zip_path):
        return zip_path
    return zip_path

def find_code_files(directory: str) -> List[str]:
    """Find all supported code files in directory."""
    code_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common non-code directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', '.venv', 'dist', 'build']]
        for file in files:
            filepath = os.path.join(root, file)
            if detect_language(filepath):
                code_files.append(filepath)
    return code_files


# ============ PYTHON PARSER ============

class PythonASTVisitor(ast.NodeVisitor):
    """Extract functions, classes, imports and calls from Python AST."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.module_name = Path(filepath).stem
        self.nodes = []
        self.current_class = None
        self.current_function = None
        self.imports = []
        self.calls = []
        # Common API libraries
        self.api_libs = {'requests', 'httpx', 'urllib', 'flask', 'fastapi', 'django', 'aiohttp'}
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        class_id = f"{self.module_name}.{node.name}"
        bases = [self._get_name(base) for base in node.bases]
        
        self.nodes.append({
            "id": class_id,
            "type": "class",
            "name": node.name,
            "file": self.filepath,
            "language": "python",
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "loc": (node.end_lineno or node.lineno) - node.lineno + 1,
            "inherits": bases,
            "imports": [],
            "calls": []
        })
        
        old_class = self.current_class
        self.current_class = class_id
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node):
        self._process_function(node)
    
    def visit_AsyncFunctionDef(self, node):
        self._process_function(node)
    
    def _process_function(self, node):
        if self.current_class:
            func_id = f"{self.current_class}.{node.name}"
            parent_class = self.current_class
        elif self.current_function:
            func_id = f"{self.current_function}.{node.name}"
            parent_class = None
        else:
            func_id = f"{self.module_name}.{node.name}"
            parent_class = None
        
        # Collect calls and search for API calls
        local_calls = []
        api_calls = []
        variables = []
        parameters = []
        
        # Extract function parameters
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        # Extract variables and calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child)
                if call_name:
                    local_calls.append(call_name)
                    # Heuristic for API calls: common library names or common patterns
                    if any(lib in call_name.lower() for lib in self.api_libs) or \
                       call_name.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                        api_id = f"api_{func_id}_{call_name}_{child.lineno}"
                        api_calls.append({
                            "id": api_id,
                            "type": "api_call",
                            "name": call_name,
                            "file": self.filepath,
                            "language": "python",
                            "line_start": child.lineno,
                            "parent": func_id
                        })
            
            # Extract variable names (assignments)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
            
            # Extract variable names (name references)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id not in parameters and child.id not in ['self', 'cls']:
                    variables.append(child.id)
        
        # Remove duplicates
        variables = list(set(variables))
        local_calls = list(set(local_calls))
        
        self.nodes.append({
            "id": func_id,
            "type": "function",
            "name": node.name,
            "file": self.filepath,
            "language": "python",
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "loc": (node.end_lineno or node.lineno) - node.lineno + 1,
            "imports": [],
            "calls": local_calls,
            "api_calls": [a['id'] for a in api_calls],
            "variables": variables,
            "parameters": parameters,
            "parent_class": parent_class
        })
        
        self.nodes.extend(api_calls)
        
        old_func = self.current_function
        self.current_function = func_id
        self.generic_visit(node)
        self.current_function = old_func
    
    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return ""
    
    def _get_call_name(self, node) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            base = self._get_name(node.func.value)
            return f"{base}.{node.func.attr}" if base else node.func.attr
        return ""


def parse_python(filepath: str) -> Dict[str, Any]:
    """Parse Python file and extract nodes."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        tree = ast.parse(source, filename=filepath)
        visitor = PythonASTVisitor(filepath)
        visitor.visit(tree)
        
        return {
            "file": filepath,
            "language": "python",
            "nodes": visitor.nodes,
            "imports": visitor.imports
        }
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return {"file": filepath, "language": "python", "nodes": [], "imports": []}
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {"file": filepath, "language": "python", "nodes": [], "imports": []}


# ============ JAVASCRIPT/TYPESCRIPT PARSER ============

def parse_javascript(filepath: str) -> Dict[str, Any]:
    """
    Parse JavaScript/TypeScript file using regex-based extraction.
    For production, use tree-sitter or esprima.
    """
    import re
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        nodes = []
        imports = []
        module_name = Path(filepath).stem
        language = "typescript" if filepath.endswith(('.ts', '.tsx')) else "javascript"
        
        # Extract imports
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        for pattern in import_patterns:
            imports.extend(re.findall(pattern, source))
        
        # Extract functions (including arrow functions)
        func_patterns = [
            (r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(', "function"),
            (r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>', "function"),
            (r'(?:export\s+)?class\s+(\w+)', "class")
        ]
        
        for pattern, node_type in func_patterns:
            for match in re.finditer(pattern, source):
                name = match.group(1)
                line_num = source[:match.start()].count('\n') + 1
                nodes.append({
                    "id": f"{module_name}.{name}",
                    "type": node_type,
                    "name": name,
                    "file": filepath,
                    "language": language,
                    "line_start": line_num,
                    "line_end": line_num,
                    "loc": 10 if node_type == "function" else 20,
                    "imports": [],
                    "calls": []
                })
        
        # Extract API calls (axios, fetch)
        api_patterns = [
            (r'axios\.(get|post|put|delete|patch)\s*\(', "axios"),
            (r'fetch\s*\(', "fetch")
        ]
        for pattern, api_lib in api_patterns:
            for match in re.finditer(pattern, source):
                line_num = source[:match.start()].count('\n') + 1
                name = match.group(1) if api_lib == "axios" else "fetch"
                api_id = f"api_{module_name}_{api_lib}_{line_num}"
                nodes.append({
                    "id": api_id,
                    "type": "api_call",
                    "name": f"{api_lib}.{name}" if api_lib == "axios" else name,
                    "file": filepath,
                    "language": language,
                    "line_start": line_num,
                    "parent": None # Hard to determine parent with regex
                })
        
        return {
            "file": filepath,
            "language": language,
            "nodes": nodes,
            "imports": imports
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {"file": filepath, "language": language, "nodes": [], "imports": []}


# ============ JAVA PARSER ============

def parse_java(filepath: str) -> Dict[str, Any]:
    """Parse Java file using regex-based extraction."""
    import re
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        nodes = []
        imports = []
        module_name = Path(filepath).stem
        
        # Extract imports
        import_pattern = r'import\s+([\w.]+);'
        imports = re.findall(import_pattern, source)
        
        # Extract classes
        class_pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            nodes.append({
                "id": f"{module_name}.{name}",
                "type": "class",
                "name": name,
                "file": filepath,
                "language": "java",
                "line_start": line_num,
                "line_end": line_num,
                "loc": 50,
                "imports": [],
                "calls": []
            })
        
        # Extract methods
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+)\s+(\w+)\s*\([^)]*\)\s*{'
        for match in re.finditer(method_pattern, source):
            name = match.group(1)
            if name not in ['if', 'while', 'for', 'switch']:  # Skip keywords
                line_num = source[:match.start()].count('\n') + 1
                nodes.append({
                    "id": f"{module_name}.{name}",
                    "type": "function",
                    "name": name,
                    "file": filepath,
                    "language": "java",
                    "line_start": line_num,
                    "line_end": line_num,
                    "loc": 15,
                    "imports": [],
                    "calls": []
                })
        
        return {
            "file": filepath,
            "language": "java",
            "nodes": nodes,
            "imports": imports
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {"file": filepath, "language": "java", "nodes": [], "imports": []}


# ============ GO PARSER ============

def parse_go(filepath: str) -> Dict[str, Any]:
    """Parse Go file using regex-based extraction."""
    import re
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        
        nodes = []
        imports = []
        module_name = Path(filepath).stem
        
        # Extract imports
        import_pattern = r'import\s+(?:\(\s*([^)]+)\)|"([^"]+)")'
        for match in re.finditer(import_pattern, source):
            if match.group(1):
                imports.extend(re.findall(r'"([^"]+)"', match.group(1)))
            elif match.group(2):
                imports.append(match.group(2))
        
        # Extract functions
        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)\s*\('
        for match in re.finditer(func_pattern, source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            nodes.append({
                "id": f"{module_name}.{name}",
                "type": "function",
                "name": name,
                "file": filepath,
                "language": "go",
                "line_start": line_num,
                "line_end": line_num,
                "loc": 15,
                "imports": [],
                "calls": []
            })
        
        # Extract structs (like classes)
        struct_pattern = r'type\s+(\w+)\s+struct'
        for match in re.finditer(struct_pattern, source):
            name = match.group(1)
            line_num = source[:match.start()].count('\n') + 1
            nodes.append({
                "id": f"{module_name}.{name}",
                "type": "class",
                "name": name,
                "file": filepath,
                "language": "go",
                "line_start": line_num,
                "line_end": line_num,
                "loc": 20,
                "imports": [],
                "calls": []
            })
        
        return {
            "file": filepath,
            "language": "go",
            "nodes": nodes,
            "imports": imports
        }
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return {"file": filepath, "language": "go", "nodes": [], "imports": []}


# ============ GENERIC FALLBACK ============

def parse_generic(filepath: str) -> Dict[str, Any]:
    """Fallback parser - just count lines."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        module_name = Path(filepath).stem
        language = detect_language(filepath) or "unknown"
        
        return {
            "file": filepath,
            "language": language,
            "nodes": [{
                "id": f"{module_name}",
                "type": "module",
                "name": module_name,
                "file": filepath,
                "language": language,
                "line_start": 1,
                "line_end": len(lines),
                "loc": len(lines),
                "imports": [],
                "calls": []
            }],
            "imports": []
        }
    except Exception as e:
        return {"file": filepath, "language": "unknown", "nodes": [], "imports": []}


# ============ MAIN PARSER ROUTER ============

def parse_file(filepath: str) -> Dict[str, Any]:
    """Route to appropriate parser based on language."""
    language = detect_language(filepath)
    
    if language == 'python':
        return parse_python(filepath)
    elif language in ['javascript', 'typescript']:
        return parse_javascript(filepath)
    elif language == 'java':
        return parse_java(filepath)
    elif language == 'go':
        return parse_go(filepath)
    else:
        return parse_generic(filepath)


# ============ GRAPH BUILDER ============

import networkx as nx
from langsmith import traceable

@traceable(project_name="CodeForge")
def build_cpg(path: str, job_id: str) -> Dict[str, Any]:
    """
    Build Code Property Graph from uploaded codebase.
    """
    print(f"Building CPG for {path}")
    
    # Extract if zip
    if path.endswith('.zip') and zipfile.is_zipfile(path):
        extract_dir = tempfile.mkdtemp(prefix=f"cpg_{job_id}_")
        working_dir = extract_archive(path, extract_dir)
    else:
        working_dir = path
    
    # Find all code files
    code_files = find_code_files(working_dir)
    print(f"Found {len(code_files)} code files")
    
    # Parse all files
    all_nodes = []
    all_imports = {}
    
    for filepath in code_files:
        result = parse_file(filepath)
        all_nodes.extend(result['nodes'])
        all_imports[filepath] = result['imports']
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    for node in all_nodes:
        # Avoid duplicates and ensure all required fields exist
        if node['id'] not in G:
            G.add_node(node['id'], **node)
    
    # Build edges based on imports, calls, and parent relations
    edges = build_edges(all_nodes, all_imports)
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], type=edge['type'])
    
    print(f"Extracted {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Convert to JSON serializable format for the frontend
    result_nodes = []
    for node_id, data in G.nodes(data=True):
        result_nodes.append(data)
        
    result_edges = []
    for u, v, data in G.edges(data=True):
        result_edges.append({
            "id": f"e_{u}_{v}",
            "source": u,
            "target": v,
            "type": data.get('type', 'calls')
        })
        
    return {
        "nodes": result_nodes,
        "edges": result_edges,
        "nx_graph": G # Keep the object for further processing if needed
    }


def build_edges(nodes: List[Dict], imports: Dict[str, List[str]]) -> List[Dict]:
    """Build comprehensive edges from various relationships."""
    edges = []
    node_ids = {n['id'] for n in nodes}
    
    # Create multiple lookup maps for better name resolution
    node_names = {n['name']: n['id'] for n in nodes}
    file_nodes = {}  # file -> [node_ids]
    class_methods = {}  # class_name -> [method_ids]
    
    # Build lookup maps
    for node in nodes:
        file_path = node.get('file', '')
        if file_path not in file_nodes:
            file_nodes[file_path] = []
        file_nodes[file_path].append(node['id'])
        
        if node['type'] == 'function' and node.get('parent_class'):
            class_name = node['parent_class']
            if class_name not in class_methods:
                class_methods[class_name] = []
            class_methods[class_name].append(node['id'])
    
    for node in nodes:
        # 1. Enhanced function call edges
        for call in node.get('calls', []):
            targets = []
            
            # Direct name match
            if call in node_names and node_names[call] != node['id']:
                targets.append(node_names[call])
            
            # Method call pattern (e.g., "obj.method" -> "method")
            if '.' in call:
                method_name = call.split('.')[-1]
                if method_name in node_names:
                    targets.append(node_names[method_name])
            
            # Partial name matching for similar functions
            for node_name, node_id in node_names.items():
                if node_id != node['id'] and (
                    call.lower() in node_name.lower() or 
                    node_name.lower() in call.lower()
                ):
                    targets.append(node_id)
            
            for target in targets:
                edges.append({
                    "source": node['id'],
                    "target": target,
                    "type": "calls"
                })
        
        # 2. Inheritance edges
        for base in node.get('inherits', []):
            if base in node_names:
                edges.append({
                    "source": node['id'],
                    "target": node_names[base],
                    "type": "structural"
                })
        
        # 3. File-level dependencies (import edges)
        node_file = node.get('file', '')
        if node_file in imports:
            for imported_module in imports[node_file]:
                # Find nodes in imported files
                for other_file, other_nodes in file_nodes.items():
                    if imported_module in other_file or any(imported_module in part for part in other_file.split('/')):
                        for target_id in other_nodes:
                            if target_id != node['id']:
                                edges.append({
                                    "source": node['id'],
                                    "target": target_id,
                                    "type": "dependency"
                                })
        
        # 4. Same-file relationships (high coupling)
        node_file = node.get('file', '')
        if node_file in file_nodes:
            for sibling_id in file_nodes[node_file]:
                if sibling_id != node['id']:
                    edges.append({
                        "source": node['id'],
                        "target": sibling_id,
                        "type": "dependency"
                    })
        
        # 5. Class-method relationships
        if node['type'] == 'class':
            class_name = node['name']
            if class_name in class_methods:
                for method_id in class_methods[class_name]:
                    edges.append({
                        "source": node['id'],
                        "target": method_id,
                        "type": "structural"
                    })
        
        # 6. API call containment
        if node['type'] == 'api_call' and node.get('parent'):
            edges.append({
                "source": node['parent'],
                "target": node['id'],
                "type": "contains"
            })
        
        # 7. Data flow edges (shared variables/parameters)
        node_vars = set(node.get('variables', []))
        if node_vars:
            for other_node in nodes:
                if other_node['id'] != node['id']:
                    other_vars = set(other_node.get('variables', []))
                    shared_vars = node_vars.intersection(other_vars)
                    if shared_vars:
                        edges.append({
                            "source": node['id'],
                            "target": other_node['id'],
                            "type": "flow",
                            "shared_vars": list(shared_vars)
                        })
    
    # Remove duplicate edges
    seen_edges = set()
    unique_edges = []
    for edge in edges:
        edge_key = (edge['source'], edge['target'], edge['type'])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    print(f"Built {len(unique_edges)} edges from static analysis")
    return unique_edges
