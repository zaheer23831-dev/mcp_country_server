# 🧠 Agentic AI Demo: MCP Tools + DeepSeek + React

This project demonstrates a **full agentic AI setup**:

- **MCP Server (Flask)** → hosts multiple tools (e.g. `country/info`, `weather/info`) registered with `@mcp.tool`.
- **DeepSeek Agent Service (Flask + DeepSeek LLM)** → orchestrates tool calls using LLM function-calling and generates structured Markdown reports.
- **React Frontend (Vite + React + ReactMarkdown)** → calls the agent service and renders the Markdown with live preview.

---

## ⚙️ Components

### 🔹 1. MCP Server
- Runs on `http://localhost:3001` by default.
- Endpoints:
  - `GET /health` → returns `{ "status": "healthy", "name": "..." }`
  - `GET /tools/list` → returns all registered tools
  - `POST /tools/call` → invoke a tool with JSON payload
- Tools are auto-discovered from the `tools/` folder.

Example tool:
```python
from mcp_core import mcp

@mcp.tool()
def country_info(name: str):
    """Fetch information about a country by name."""
    # Calls RestCountries API...
    return {...}
