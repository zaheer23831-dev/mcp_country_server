#!/usr/bin/env python3
"""
DeepSeek-powered MCP Agent as a Web Service.

- Exposes POST /report (JSON: {"country":"france"}) and GET /report?country=france
- DeepSeek (OpenAI-compatible) model orchestrates which MCP tools to call
- We expose two function-calling "tools" to the model:
    1) list_tools()  -> calls MCP /tools/list
    2) call_tool(...) -> calls MCP /tools/call
- The model must produce final Markdown strictly from tool outputs.
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

# ==== Config via environment variables ====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:3001")  # run your MCP server here
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-key-123")

SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5050"))

# ==== Init DeepSeek client ====
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# ==== HTTP helpers to reach MCP server ====
def mcp_list_tools():
    r = requests.get(f"{MCP_BASE_URL}/tools/list", headers={"x-api-key": MCP_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()

def mcp_call_tool(tool_id: str, input_dict: dict):
    r = requests.post(
        f"{MCP_BASE_URL}/tools/call",
        headers={"x-api-key": MCP_API_KEY, "Content-Type": "application/json"},
        json={"tool_id": tool_id, "input": input_dict},
        timeout=60,
    )
    # surface error payloads
    if r.status_code >= 400:
        try:
            errj = r.json()
        except Exception:
            errj = {"error": r.text}
        raise RuntimeError(f"MCP tool call failed {r.status_code}: {errj}")
    return r.json()

# ==== Tools (function-calling) schema we present to DeepSeek ====
# The model will decide when to call these; we will execute & feed back the results.
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_tools",
            "description": "Discover available MCP tools and their schemas.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_tool",
            "description": "Invoke an MCP tool by id with a JSON input object.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_id": {"type": "string"},
                    "input": {"type": "object"},
                },
                "required": ["tool_id", "input"],
                "additionalProperties": False,
            },
        },
    },
]

# ==== System prompt that enforces “tools only” + Markdown output ====
SYSTEM_PROMPT = """You are an AI agent connected to an MCP server.
Your job: produce a Markdown report strictly from MCP tool outputs.

Rules:
- Use tools only: first call list_tools(), then call_tool() as needed.
- Do NOT use external knowledge or assumptions.
- Follow this Markdown layout; omit sections with no data and use '—' for missing fields:

# Report: <Country Name or User Query>

## Country Information
- **Official Name:** <…>
- **Capital:** <…>
- **Region:** <…>
- **Subregion:** <…>
- **Population:** <…>
- **Area (km²):** <…>
- **Languages:** <…>
- **Currency:** <…>
- **Symbol:** <…>
- **Flag:** <…>
- **Borders:** <…>
- **Maps:** <…>

## Weather Location Info
- **Country:** <…>
- **Capital:** <…>
- **Latitude:** <…>
- **Longitude:** <…>
- **Timezone:** <…>
- **Population (country):** <…>

If a section has no tool data, write: "No data available from tools."
Return ONLY the final Markdown, no extra commentary.
"""

# ==== Agent loop: handle function calls until model returns final content ====
def run_deepseek_agent(country_query: str) -> str:
    """
    Drive DeepSeek with function-calling. The model decides which tool to call.
    We execute tools and feed results back until it returns Markdown.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Generate a Markdown report for the country: {country_query}. "
                       "Use only MCP tools you discover via list_tools() and call_tool(). "
                       "Return the final Markdown only."
        },
    ]

    while True:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0,  # deterministic-ish
            max_tokens=1500,
        )

        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        # If the model responded with final content (no tool calls), return it
        if not tool_calls:
            # DeepSeek (OpenAI-compatible) content accessor:
            content = msg.get("content") if isinstance(msg, dict) else msg.content
            return content or ""

        # Otherwise, execute requested tool calls
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

        for tc in tool_calls:
            fn_name = tc.function.name
            args_json = tc.function.arguments or "{}"
            try:
                args = json.loads(args_json)
            except Exception:
                args = {}

            if fn_name == "list_tools":
                try:
                    result = mcp_list_tools()
                    tool_result = json.dumps(result)
                except Exception as e:
                    tool_result = json.dumps({"error": str(e)})
            elif fn_name == "call_tool":
                try:
                    tool_id = args.get("tool_id")
                    input_obj = args.get("input") or {}
                    result = mcp_call_tool(tool_id, input_obj)
                    tool_result = json.dumps(result)
                except Exception as e:
                    tool_result = json.dumps({"error": str(e)})
            else:
                tool_result = json.dumps({"error": f"Unknown function {fn_name}"})

            # push tool result back to model
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": fn_name,
                "content": tool_result,
            })

# ==== Flask service ====
app = Flask(__name__)

@app.route("/report", methods=["GET", "POST"])
def report():
    """
    GET /report?country=france
    POST /report  { "country": "france" }
    Returns: { "markdown": "..." }
    """
    if request.method == "GET":
        country = request.args.get("country", "").strip() or "france"
    else:
        data = request.get_json(silent=True) or {}
        country = (data.get("country") or "").strip() or "france"

    try:
        markdown = run_deepseek_agent(country)
        return jsonify({"markdown": markdown})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": DEEPSEEK_MODEL})

if __name__ == "__main__":
    print(f"DeepSeek Agent service listening on http://{SERVICE_HOST}:{SERVICE_PORT}")
    print("Try: curl 'http://localhost:%d/report?country=france'" % SERVICE_PORT)
    app.run(host=SERVICE_HOST, port=SERVICE_PORT)
