#  PrismAI
## AI-Powered UI/UX, Accessibility & Intelligent Code Analysis Platform

Prism AI is an advanced AI-driven developer platform built to modernize the way developers analyze, maintain, and improve frontend applications. It combines Large Language Models (LLMs), static code analysis, accessibility auditing, and intelligent automation into a single integrated ecosystem.

The platform acts as a bridge between **design quality**, **accessibility standards**, and **development workflows** by providing deep real-time insights directly inside the IDE and through a centralized analytics dashboard.

Unlike traditional linters or static analyzers, Code-Analyzer not only detects issues but also understands project context and generates intelligent code fixes, architectural recommendations, and UI/UX improvements.  
  
---             
#  Vision           
  
Modern applications often suffer from:    
  
- Poor accessibility compliance
- Inconsistent UI/UX implementations
- Hard-to-maintain frontend code
- Weak project documentation
- Lack of architectural visibility
- Fragmented development tooling

Code-Analyzer solves these problems by creating a unified AI-assisted analysis environment capable of understanding both the **code structure** and the **user experience layer** of an application.

The platform is designed for:

- Frontend Developers
- Full Stack Engineers
- UI/UX Teams
- Accessibility Auditors
- Engineering Managers
- Open Source Contributors
- AI-assisted Development Workflows

---

#  Core Features

---

##  Real-Time UI/UX & Accessibility Analysis

Code-Analyzer continuously scans frontend codebases and detects:

- WCAG accessibility violations
- Improper semantic HTML usage
- Missing ARIA attributes
- Color contrast issues
- Responsive layout inconsistencies
- Poor component hierarchy
- UI spacing and alignment problems
- Navigation accessibility issues
- Mobile usability problems

Supported frameworks include:

- React
- Vue.js
- Standard HTML/CSS

The analysis engine works in real time and provides immediate feedback during development.

### Example Checks

| Analysis Type | Description |
|---|---|
| Accessibility Audit | Detects WCAG compliance issues |
| Semantic Validation | Ensures proper HTML structure |
| Responsive Design Check | Identifies layout issues on multiple screen sizes |
| UX Consistency Audit | Detects inconsistent spacing, typography, and hierarchy |
| Component Quality Analysis | Evaluates reusable component structure |

---

#  AI-Powered Automated Code Fixes

Traditional tools stop at reporting errors.

Code-Analyzer goes further by generating intelligent fixes using LLM-powered transformations.

The AI engine can:

- Rewrite inaccessible UI components
- Improve semantic structure
- Refactor repetitive frontend logic
- Suggest optimized component structures
- Improve maintainability
- Generate cleaner UI patterns
- Provide accessibility-compliant alternatives

Developers can review and apply fixes directly from the IDE with a single click.

---

#  AI Architect Assistant

One of the most powerful components of Code-Analyzer is the AI Architect Assistant.

This assistant has contextual awareness of the entire workspace and can answer project-specific questions such as:

- "Where is authentication implemented?"
- "Which components depend on this service?"
- "Explain the routing architecture"
- "Why is this component re-rendering frequently?"
- "Find accessibility issues in the navbar"
- "Generate documentation for this module"

The assistant works using:

- Workspace indexing
- AST-based code understanding
- MCP-based context sharing
- LLM-powered reasoning

This transforms the codebase into an interactive, searchable knowledge system.

---

#  Interactive Project Health Dashboard

The web dashboard provides a visual overview of the entire project.

It helps teams monitor:

- Code quality metrics
- Accessibility scores
- Dependency relationships
- File complexity
- Project structure
- Technical debt indicators
- Component usage graphs
- Performance bottlenecks

### Dashboard Modules

| Module | Purpose |
|---|---|
| Dependency Graph | Visualizes project architecture |
| Health Metrics | Tracks overall project quality |
| Accessibility Reports | Displays WCAG audit summaries |
| File Insights | Shows complexity and maintainability scores |
| AI Recommendations | Provides optimization suggestions |

The dashboard enables both developers and managers to better understand project health at scale.

---

#  Multi-Engine Distributed Architecture

Code-Analyzer uses a modular distributed architecture designed for scalability, performance, and flexibility.

The platform is divided into multiple specialized services.

---

#  Backend Architecture

---

##  Go Backend Service (Port 8081)

The Go backend acts as the central orchestration layer.

### Responsibilities

- API management
- Job scheduling
- Analysis coordination
- Dashboard data serving
- File management
- Service communication
- Report aggregation

### Why Go?

Go was selected because of:

- High concurrency support
- Low memory usage
- Fast execution speed
- Excellent API performance
- Scalability for large projects

The backend is built using the Gin framework.

---

#  Python Analyzer Engine

The Python layer powers intelligent analysis and AI operations.

This layer handles:

- AST parsing
- UI analysis
- Accessibility scanning
- AI inference integration
- Deep code inspection
- LLM communication

Python was chosen because of its strong ecosystem for:

- AI/ML integration
- Parsing libraries
- NLP tooling
- Static analysis frameworks

---

##  Flask Bridge (Port 7891)

The Flask Bridge enables communication between:

- VS Code Extension
- AI Services
- Backend APIs

It provides:

- Real-time messaging
- Analysis streaming
- AI response handling
- IDE synchronization

---

##  MCP Server (Port 8892)

The MCP (Model Context Protocol) Server provides structured project context to LLMs.

This enables the AI assistant to understand:

- File relationships
- Project architecture
- Component hierarchies
- Business logic flow
- Shared dependencies

The MCP layer is critical for building context-aware AI interactions.

---

#  Logic & Analysis Layer

The core analysis engine uses:

- Abstract Syntax Tree (AST) parsing
- DOM analysis
- Semantic inspection
- Custom rule engines
- BeautifulSoup-based HTML parsing

This enables deep understanding of both:

- Source code structure
- Rendered UI semantics

---

#  Frontend Dashboard (Vite + Vue.js)

The frontend dashboard is built using:

- Vue.js
- Vite
- Modern reactive UI architecture

### Features

- Fast performance
- Real-time updates
- Interactive visualizations
- Dependency graph rendering
- Report filtering
- AI insights panel
- Dark/light theme support

The frontend communicates with the Go backend through REST APIs.

---

#  VS Code Extension Integration

The VS Code extension integrates Code-Analyzer directly into the developer workflow.

### Features

- Inline issue detection
- AI-generated fixes
- Accessibility warnings
- Real-time analysis
- Context-aware suggestions
- Chat-based project assistance

This eliminates the need to constantly switch between tools.

---

#  Technology Stack

| Layer | Technology |
|---|---|
| Core Logic | Python 3.11+ |
| Backend APIs | Go + Gin |
| Frontend Dashboard | Vue.js + Vite |
| IDE Extension | TypeScript |
| AI Integration | OpenAI SDK / OpenWebUI / Ollama |
| HTML Parsing | BeautifulSoup4 |
| Code Analysis | Custom AST Parsers |
| Communication Layer | Flask |
| Context Engine | MCP Server |

---

#  Installation & Setup

---

#  Prerequisites

Ensure the following tools are installed:

- Go 1.20+
- Python 3.11+
- Node.js 18+
- npm
- PowerShell

---

#  Clone Repository

```bash
git clone https://github.com/your-username/code-analyzer.git
cd code-analyzer
```

---

#  Configure Environment Variables

Create a `.env` file in the root directory.

```env
OPENWEBUI_BASE_URL=http://your-ai-endpoint:8084
OPENWEBUI_API_KEY=your_api_key_here
LLM_MODEL=gemma3:latest
```

---

#  Install Python Dependencies

```bash
cd analyzer
pip install -r requirements.txt
```

---

#  Running the Platform

The project includes a unified launcher script that starts all services together.

## Run the Launcher

```powershell
.\start.ps1
```

---

#  Running Services

| Service | URL |
|---|---|
| Backend API | http://localhost:8081 |
| Frontend Dashboard | http://localhost:5173 |
| Flask Bridge | http://localhost:7891 |
| MCP Server | http://localhost:8892 |

---

#  VS Code Extension Setup

Navigate to the extension directory.

```bash
cd uiux-copilot-extension
```

Install dependencies.

```bash
npm install
```

Package the extension.

```bash
npx vsce package
```

Install the generated VSIX file.

```bash
code --install-extension uiux-copilot-0.0.1.vsix
```

---

#  Future Roadmap

The future roadmap includes:

## Planned Features

- AI-based full project refactoring
- Multi-framework support
- CI/CD integration
- GitHub Pull Request reviews
- Security vulnerability scanning
- Automated UI test generation
- Performance optimization engine
- Team collaboration workspace
- Cloud-hosted analysis engine
- Plugin marketplace

---

#  Potential Use Cases

---

## Enterprise Frontend Auditing

Large organizations can continuously monitor accessibility and UI quality across multiple projects.


## AI-Assisted Development

Developers can accelerate frontend development using intelligent AI-generated fixes.


## Educational Platforms

Students can learn better frontend practices with real-time guidance.


## Open Source Maintenance

Maintainers can improve code consistency and project health automatically.

---

#  Contributing

Contributions are welcome.

## Contribution Workflow

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push your branch
5. Open a Pull Request

---
# Demo Preview

<p align="center">
  <img src="./assets/Final_Internship_video.gif" alt="Code-Analyzer Demo"/>
</p>
---


#  Final Note

Code-Analyzer is more than a static analysis tool.

It is an AI-powered development ecosystem designed to help developers write:

- Cleaner code
- More accessible interfaces
- Better user experiences
- More maintainable applications

By combining AI, architecture analysis, and developer tooling into a unified platform, Code-Analyzer represents the next generation of intelligent software development systems.

```
