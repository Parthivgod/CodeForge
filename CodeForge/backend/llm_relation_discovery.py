import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable
from langsmith.wrappers import wrap_openai

load_dotenv()

@traceable(run_type="llm", project_name="CodeForge")
def discover_relations_llm(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses an LLM to discover logical and dependency relations between code nodes,
    and performs a failure risk assessment for each function.
    """
    api_key = os.getenv("GROQ_API_KEY")
    endpoint = os.getenv("GROQ_BASE_URL")
    
    if not api_key:
        print("Warning: No LLM API key found. Skipping LLM relation discovery.")
        return {"edges": [], "node_updates": {}}
        
    # Wrap the client to automatically capture token usage in LangSmith
    client = wrap_openai(OpenAI(
        base_url=endpoint,
        api_key=api_key
    ))
    
    # Prepare comprehensive node summaries for the LLM
    node_summaries = []
    for node in nodes:
        summary = {
            "id": node['id'],
            "name": node['name'],
            "type": node['type'],
            "file": node['file'],
            "line": node.get('line_start')
        }
        if node['type'] == 'function':
            summary['calls'] = node.get('calls', [])
            summary['api_calls'] = node.get('api_calls', [])
            summary['variables'] = node.get('variables', [])
            summary['parameters'] = node.get('parameters', [])
        elif node['type'] == 'class':
            summary['methods'] = [n['name'] for n in nodes if n.get('parent_class') == node['name']]
            summary['inherits'] = node.get('inherits', [])
        node_summaries.append(summary)
    
    # Process in larger, overlapping batches to catch cross-batch relationships
    batch_size = 30  # Increased batch size
    overlap = 10     # Overlap between batches
    all_edges = []
    node_updates = {}
    
    # First pass: Process all nodes in overlapping batches
    for i in range(0, len(node_summaries), batch_size - overlap):
        batch = node_summaries[i:i+batch_size]
        
        prompt = f"""
        Analyze the following code components as a system architect. Focus on finding ALL possible relationships.
        
        Tasks:
        1. Identify EVERY relationship type:
           - Direct Calls (function A calls function B)
           - Structural (Inheritance, Composition, one class contains another)
           - Dependency (Logical coupling, same file, imports, configurations)
           - Flow (Data flow, temporal dependency, execution order)
           
        2. Look for indirect relationships:
           - Functions that work on same data structures
           - Classes that implement similar patterns
           - Functions called in sequence
           - Shared utility functions
           
        3. Risk Assessment for each function:
           - 'risk_level': low/medium/high
           - 'failure_reason': specific technical reason

        Nodes to analyze:
        {json.dumps(batch, indent=2)}
        
        IMPORTANT: Be aggressive in finding relationships. If two components seem related in ANY way, include them.
        
        Return JSON format ONLY:
        {{
          "relationships": [
            {{"source": "id1", "target": "id2", "type": "calls|structural|dependency|flow", "description": "detailed reason", "confidence": 0.8}}
          ],
          "risk_analysis": [
            {{"id": "node_id", "risk_level": "low|medium|high", "failure_reason": "specific explanation"}}
          ]
        }}
        """
        
        model_name = os.getenv("LLM_MODEL") or os.getenv("MODEL_NAME") or "gpt-4-turbo"
        
        try:
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "You are a senior system architect. Find ALL possible relationships between code components. Be thorough and aggressive in identifying connections. ALWAYS RETURN VALID JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # Lower temperature for more consistent results
            }
            
            # Enable JSON mode for supported models
            if any(m in model_name.lower() for m in ["gpt-4", "gpt-3.5"]):
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(
                **kwargs,
                timeout=60  # Increase timeout to 60 seconds
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                if "relationships" in result:
                    # Filter out low-confidence relationships
                    high_conf_edges = [
                        edge for edge in result["relationships"] 
                        if edge.get("confidence", 1.0) >= 0.6
                    ]
                    all_edges.extend(high_conf_edges)
                if "risk_analysis" in result:
                    for risk in result["risk_analysis"]:
                        node_updates[risk["id"]] = {
                            "risk_level": risk.get("risk_level", "low"),
                            "failure_reason": risk.get("failure_reason", "No risk detected")
                        }
            except json.JSONDecodeError as je:
                print(f"Failed to parse LLM response as JSON: {content[:200]}...")
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        if "relationships" in result:
                            all_edges.extend(result["relationships"])
                    except:
                        pass
                
        except Exception as e:
            print(f"Error calling LLM for relation discovery (batch {i//batch_size + 1}): {e}")
            # Continue with next batch instead of failing completely
            continue
    
    # Second pass: Global analysis for high-level patterns
    if len(nodes) > 10:
        try:
            # Create a summary of all components for global pattern analysis
            global_summary = {
                "total_nodes": len(nodes),
                "files": list(set(n['file'] for n in nodes)),
                "classes": [n['name'] for n in nodes if n['type'] == 'class'],
                "functions": [n['name'] for n in nodes if n['type'] == 'function'][:20],  # Limit for token usage
                "api_calls": list(set(call for n in nodes for call in n.get('api_calls', [])))[:10]
            }
            
            global_prompt = f"""
            Analyze this codebase for high-level architectural patterns and missing relationships:
            
            {json.dumps(global_summary, indent=2)}
            
            Find:
            1. Architectural patterns (MVC, Repository, Factory, etc.)
            2. Cross-cutting concerns (logging, auth, validation)
            3. Data flow patterns
            4. Missing relationships between components
            
            Return additional relationships in JSON:
            {{
              "relationships": [
                {{"source": "component1", "target": "component2", "type": "pattern", "description": "architectural relationship"}}
              ]
            }}
            """
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a software architect. Identify high-level patterns and relationships."},
                    {"role": "user", "content": global_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                if "relationships" in result:
                    all_edges.extend(result["relationships"])
            except:
                pass
                
        except Exception as e:
            print(f"Error in global analysis: {e}")
    
    # Remove duplicate edges
    seen_edges = set()
    unique_edges = []
    for edge in all_edges:
        edge_key = (edge.get('source'), edge.get('target'), edge.get('type'))
        if edge_key not in seen_edges and edge.get('source') and edge.get('target'):
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    print(f"LLM discovered {len(unique_edges)} relationships")
    
    # If LLM failed to find many relationships, add some basic heuristic ones
    if len(unique_edges) < len(nodes) * 0.1:  # Less than 10% connectivity
        print("Low LLM connectivity detected, adding heuristic relationships...")
        heuristic_edges = create_heuristic_relationships(nodes)
        unique_edges.extend(heuristic_edges)
        print(f"Added {len(heuristic_edges)} heuristic relationships")
    
    return {"edges": unique_edges, "node_updates": node_updates}

def create_heuristic_relationships(nodes):
    """Create basic relationships when LLM fails or returns few results."""
    heuristic_edges = []
    
    # Group nodes by file
    file_groups = {}
    for node in nodes:
        file_path = node.get('file', '')
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(node)
    
    # Create relationships based on simple heuristics
    for node in nodes:
        # 1. Functions that call each other (from calls list)
        for call_name in node.get('calls', []):
            for other_node in nodes:
                if (other_node['name'] == call_name and 
                    other_node['id'] != node['id']):
                    heuristic_edges.append({
                        "source": node['id'],
                        "target": other_node['id'],
                        "type": "calls",
                        "description": f"Function {node['name']} calls {other_node['name']}",
                        "confidence": 0.9
                    })
        
        # 2. Same-file relationships (high coupling)
        file_path = node.get('file', '')
        if file_path in file_groups:
            for sibling in file_groups[file_path]:
                if sibling['id'] != node['id']:
                    heuristic_edges.append({
                        "source": node['id'],
                        "target": sibling['id'],
                        "type": "dependency",
                        "description": f"Same file coupling: {file_path}",
                        "confidence": 0.7
                    })
        
        # 3. Shared variables (data flow)
        node_vars = set(node.get('variables', []))
        if node_vars:
            for other_node in nodes:
                if other_node['id'] != node['id']:
                    other_vars = set(other_node.get('variables', []))
                    shared_vars = node_vars.intersection(other_vars)
                    if shared_vars and len(shared_vars) >= 2:  # At least 2 shared variables
                        heuristic_edges.append({
                            "source": node['id'],
                            "target": other_node['id'],
                            "type": "flow",
                            "description": f"Shared variables: {', '.join(list(shared_vars)[:3])}",
                            "confidence": 0.8
                        })
    
    # Remove duplicates
    seen_edges = set()
    unique_heuristic_edges = []
    for edge in heuristic_edges:
        edge_key = (edge['source'], edge['target'], edge['type'])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_heuristic_edges.append(edge)
    
    return unique_heuristic_edges
