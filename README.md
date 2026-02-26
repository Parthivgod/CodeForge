# CodeForge

**CodeForge** is an AI-powered code analysis tool that helps developers break down monolithic applications into microservices.

## What It Does

CodeForge analyzes your codebase and provides intelligent recommendations for decomposing monoliths into microservices by:

1. **Multi-Language Code Parsing** - Parsing codebases in multiple languages (Python, JavaScript, TypeScript, Java, Go) using AST (Abstract Syntax Tree) analysis to extract code structure

2. **Code Property Graph Construction** - Building a comprehensive Code Property Graph (CPG) that maps all functions, classes, methods, and their relationships including calls, imports, inheritance, and data flow

3. **AI-Powered Relationship Discovery** - Using LLM models (GPT-4, GPT-3.5, or compatible APIs) hosted on cloud infrastructure to discover semantic relationships between code components that static analysis might miss, including logical coupling, architectural patterns, and cross-cutting concerns

4. **Graph Neural Network Embeddings** - Applying Graph Neural Networks (GNN) with 3-layer Graph Convolutional Networks to generate 128-dimensional embeddings that capture both structural and semantic code patterns

5. **AI Risk Assessment** - Performing risk assessment on each component using AI to identify potential failure points, analyzing code complexity, dependencies, state mutation patterns, and error handling

6. **Interactive Visualization** - Generating interactive React Flow visualizations showing code dependencies, suggested service boundaries, and risk indicators with color-coded nodes and animated edges

7. **Comprehensive Reports** - Producing detailed markdown reports with service recommendations, dependency analysis, migration roadmaps, and actionable next steps

The system combines traditional static analysis with cloud-hosted AI models to understand not just how code is connected, but why it's connected - identifying logical coupling, architectural patterns, and cross-cutting concerns. This hybrid approach provides more accurate microservice recommendations than purely rule-based tools, helping teams modernize legacy applications with confidence.

## Current Features

### ✅ Implemented
- Multi-language AST parsing (Python, JavaScript, TypeScript, Java, Go)
- Code Property Graph (CPG) construction with nodes and edges
- Static relationship discovery (function calls, imports, inheritance)
- LLM-enhanced semantic relationship discovery with batch processing
- Heuristic fallback for reliability when LLM unavailable
- Risk assessment using AI (low/medium/high risk levels)
- GNN pipeline with PyTorch Geometric (3-layer GCN)
- 128-dimensional node embeddings
- Interactive React Flow visualization
- Real-time progress tracking
- REST API with FastAPI
- Git repository cloning support
- ZIP file upload support
- LangSmith integration for LLM tracing
- Edge validation and deduplication

### 🚧 Refactoring Needed
- **Code Organization** - Consolidate duplicate code in temp folders
- **Error Handling** - Improve error messages and recovery mechanisms
- **Configuration Management** - Centralize environment variable handling
- **Test Coverage** - Add comprehensive unit and integration tests
- **Documentation** - Add inline code documentation and API docs
- **Performance Optimization** - Optimize batch processing for large codebases
- **Database Integration** - Complete PostgreSQL + pgvector implementation
- **Frontend Polish** - Improve UI/UX and add loading states

### 🔮 Yet to Be Done

#### Core Features
- **Louvain Clustering** - Implement community detection algorithm for automatic service boundary identification
- **Modularity Scoring** - Calculate and display modularity metrics for cluster quality
- **Service Naming** - Use LLM to generate meaningful service names based on cluster content
- **Migration Roadmap** - Generate step-by-step migration plans with dependency ordering
- **API Contract Generation** - Auto-generate OpenAPI specs for identified services
- **Database Schema Analysis** - Analyze and recommend database decomposition strategies

#### Advanced AI Features
- **Fine-tuned GNN Models** - Train domain-specific models for better accuracy
- **Multi-objective Optimization** - Balance performance, cost, and maintainability
- **Active Learning** - Incorporate user feedback to improve recommendations
- **Confidence Scoring** - Provide confidence levels for all recommendations
- **Pattern Recognition** - Identify common architectural patterns (MVC, Repository, Factory)

#### Visualization & UX
- **Service Dependency Graph** - Show high-level service-to-service dependencies
- **Risk Heatmap** - Visual heatmap of risk distribution across codebase
- **Diff Visualization** - Show before/after comparison of proposed changes
- **Export Options** - Export visualizations as PNG, SVG, or PDF
- **Collaborative Features** - Multi-user annotation and commenting

#### DevOps Integration
- **CI/CD Pipeline Integration** - Run analysis automatically on commits
- **GitHub/GitLab Integration** - Direct repository access and PR comments
- **Incremental Analysis** - Analyze only changed files for faster feedback
- **Automated Refactoring** - Generate pull requests with suggested changes
- **Monitoring Integration** - Connect with runtime metrics for better recommendations

#### Enterprise Features
- **Multi-tenant Support** - Support multiple organizations and projects
- **Role-based Access Control** - User permissions and team management
- **Audit Logging** - Track all analysis runs and decisions
- **Custom Rules Engine** - Allow teams to define custom analysis rules
- **Batch Processing** - Analyze multiple repositories simultaneously
- **Cost Estimation** - Estimate migration effort and cloud costs

#### Language Support
- **Additional Languages** - Add support for Rust, Kotlin, Swift, C#, Ruby, PHP
- **Framework Detection** - Identify and handle framework-specific patterns
- **Legacy Code Support** - Better handling of older language versions

#### Reporting & Analytics
- **PDF Report Generation** - Professional reports with charts and diagrams
- **Trend Analysis** - Track codebase evolution over time
- **Comparison Reports** - Compare different analysis runs
- **Custom Metrics** - Allow teams to define and track custom metrics
- **Executive Dashboards** - High-level summaries for stakeholders

## Tech Stack

**Backend:**
- Python 3.9+
- FastAPI (REST API)
- PyTorch + PyTorch Geometric (GNN)
- NetworkX (Graph analysis)
- scikit-learn (ML utilities)
- OpenAI SDK (LLM integration)
- LangSmith (LLM tracing)
- GitPython (Repository cloning)

**Frontend:**
- React 18
- React Flow (Graph visualization)
- Tailwind CSS (Styling)
- Vite (Build tool)

**Infrastructure:**
- Cloud-hosted LLM APIs (provider-agnostic)
- PostgreSQL + pgvector (Optional)
- Docker + Docker Compose

## Getting Started

See [REQUIREMENTS.md](./REQUIREMENTS.md) for installation instructions and [DESIGN.md](./DESIGN.md) for architecture details.

## Project Status

CodeForge is currently in active development. The core analysis pipeline is functional, but many advanced features are still being implemented. Contributions and feedback are welcome!

## License

[Add your license here]
