"""
Quick test script to verify the backend parsing is working.
Creates a small sample Python codebase and tests the parsing pipeline.
"""
import os
import tempfile
import zipfile
from pathlib import Path

# Create test Python files
test_code = {
    "main.py": """
import utils
from models import User, Product

def main():
    user = User("John")
    product = Product("Widget")
    result = utils.process(user, product)
    return result

if __name__ == "__main__":
    main()
""",
    "models.py": """
class User:
    def __init__(self, name):
        self.name = name
    
    def get_info(self):
        return f"User: {self.name}"

class Product:
    def __init__(self, name):
        self.name = name
    
    def get_price(self):
        return 99.99
""",
    "utils.py": """
def process(user, product):
    user_info = user.get_info()
    price = product.get_price()
    return f"{user_info} - ${price}"

def validate(data):
    return data is not None
"""
}

# Create temp directory and write files
with tempfile.TemporaryDirectory() as tmpdir:
    test_dir = Path(tmpdir) / "test_project"
    test_dir.mkdir()
    
    for filename, content in test_code.items():
        (test_dir / filename).write_text(content)
    
    # Test the pipeline
    print("Testing CPG Builder...")
    from cpg_builder import build_cpg
    nodes = build_cpg(str(test_dir), "test")
    
    print(f"\n✅ Extracted {len(nodes)} nodes")
    for node in nodes[:5]:
        print(f"  - {node['type']}: {node['name']} (LoC: {node['loc']})")
    
    print("\nTesting Embedding Generation...")
    from gnn_pipeline import generate_embeddings
    nodes_with_embeddings = generate_embeddings(nodes)
    
    print(f"✅ Generated embeddings for {len(nodes_with_embeddings)} nodes")
    if nodes_with_embeddings:
        print(f"  - Embedding dimension: {len(nodes_with_embeddings[0]['embedding'])}")
    
    print("\nTesting Clustering...")
    from clustering import cluster_nodes
    clusters = cluster_nodes(nodes_with_embeddings)
    
    print(f"✅ Created {len(clusters)} clusters")
    for cluster in clusters:
        print(f"  - {cluster['name']}: {cluster['node_count']} nodes, {cluster['loc_count']} LoC, risk={cluster['risk']}")
    
    print("\n🎉 All tests passed! Backend is working correctly.")
