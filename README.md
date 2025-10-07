flowchart LR
  subgraph FE[React App - Vite :5173]
    UI[Country input + Generate]
    MD[Markdown Preview]
  end

  subgraph AG[DeepSeek Agent Service - Flask :5050]
    DSP[DeepSeek LLM]
    LOOP[Function-calling loop: list_tools(), call_tool()]
    API[/GET/POST /report, GET /health/]
  end

  subgraph MCP[MCP Server - Flask :3001]
    ROUTES[/GET /tools/list, POST /tools/call, GET /health/]
    T1[[country/info @mcp.tool]]
    T2[[weather/info @mcp.tool]]
  end

  UI -->|GET /report?country=france| API
  API --> DSP
  DSP -->|tool_call| LOOP
  LOOP -->|HTTP| ROUTES
  ROUTES --> T1
  ROUTES --> T2
  T1 -->|JSON| ROUTES
  T2 -->|JSON| ROUTES
  ROUTES --> LOOP
  LOOP --> DSP
  DSP -->|Markdown| API
  API -->|{ markdown }| UI
  UI --> MD
