# Future Plans for CodeForge

This document outlines the roadmap for enhancing the CodeForge application with advanced AI, graph analytics, and DevOps practices.

## 1. Advanced AI & Machine Learning

### Graph Neural Networks (GNNs)
- **Link Prediction**: Implement link prediction to identify "hidden" dependencies (e.g., shared database tables, event-driven triggers) that static analysis might miss.
- **Graph Attention Networks (GATs)**: Transition from simple GCNs to GATs to allow the model to learn weighted importance of neighboring nodes.

### Transformers
- **Feature Extraction**: Replace TF-IDF vectorization with Transformer-based models like **CodeBERT** or **GraphCodeBERT** for deeper semantic understanding of code logic.
- **Automated Summarization**: Use Transformers to generate descriptive names and summaries for identified clusters/microservices.

## 2. Graph Analytics with NetworkX

- **Community Detection**: Implement Louvain or Girvan-Newman algorithms as a baseline for service boundary identification.
- **Impact Analysis (Blast Radius)**: Use graph traversal algorithms (`nx.shortest_path`, `nx.descendants`) to show the ripple effects of code changes across the monolith.
- **Metric Extraction**: Calculate centrality measures to identify "God Objects" or critical bottlenecks in the codebase.

## 4. Robust Parsing & Multilingual Support

- **Tree-Sitter Migration**: Replace standard AST/Regex parsers with **Tree-Sitter** to provide industrial-strength parsing for all supported languages.
- **Cross-Language Resolution**: Implement logic to resolve calls between different languages (e.g., a React frontend calling a Go microservice).

## 5. Data Layer Analysis

- **Schema Decomposition**: Parse SQL/DDL files to map table dependencies. Identify "Shared Database" anti-patterns where multiple services write to the same table.
- **Transaction Boundaries**: Use static analysis to identify long-running transactions that might be difficult to split across distributed services.

## 6. Developer Experience & UX

- **Interactive Refinement**: Allow architects to manually adjust clusters in the UI, with the GNN learning from these manual corrections (Human-in-the-loop).
- **Refactoring Recipes**: For every identified microservice, generate a step-by-step "Refactoring Recipe" (e.g., "1. Extract these classes, 2. Mock this interface, 3. Create this REST endpoint").

## 7. Pipeline Integration

- **End-to-End Automation**: Fully integrate `gnn_pipeline.py` and `clustering.py` into the main FastAPI `run_pipeline` to ensure every analysis benefit from AI-driven clustering.

---
*Note: This roadmap follows enterprise best practices for scalable code analysis and microservices decomposition.*
