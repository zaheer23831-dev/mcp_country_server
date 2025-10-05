from __future__ import annotations
from flask import Flask, request, jsonify
from functools import wraps
import jsonschema
import os

class MCP:
    def __init__(self, name: str = "MCP Server"):
        self.name = name
        self._tools = {}
        self.app = Flask(self.name)
        self._configure_routes()
        self.api_key = os.getenv("MCP_API_KEY", "dev-key-123")

    def tool(self, id: str = None, name: str = None, description: str = None, input_schema: dict | None = None, version: str = "1.0.0"):
        def decorator(func):
            tool_id = id or func.__name__
            tool_name = name or func.__name__.replace("_", " ").title()
            tool_desc = description or (func.__doc__ or "").strip() or tool_name
            entry = {
                "id": tool_id,
                "name": tool_name,
                "description": tool_desc,
                "version": version,
                "func": func,
                "input_schema": input_schema or {"type": "object"}
            }
            self._tools[tool_id] = entry
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def _auth(self) -> bool:
        key = request.headers.get("x-api-key") or request.args.get("key")
        return key == self.api_key

    def _configure_routes(self):
        @self.app.get("/tools/list")
        def list_tools():
            if not self._auth():
                return jsonify({"error": "unauthorized"}), 401
            payload = [{k: v for k, v in t.items() if k != "func"} for t in self._tools.values()]
            return jsonify({"tools": payload})

        @self.app.post("/tools/call")
        def call_tool():
            if not self._auth():
                return jsonify({"error": "unauthorized"}), 401
            body = request.get_json(silent=True) or {}
            tool_id = body.get("tool_id")
            input_ = body.get("input", {})
            tool = self._tools.get(tool_id)
            if not tool:
                return jsonify({"error": "tool_not_found"}), 404
            try:
                jsonschema.validate(instance=input_, schema=tool["input_schema"])
            except jsonschema.ValidationError as e:
                return jsonify({"error": "invalid_input", "details": str(e)}), 400
            try:
                result = tool["func"](input_)
                return jsonify({"tool_id": tool_id, "result": result})
            except Exception as e:
                return jsonify({"error": "execution_failed", "details": str(e)}), 500

    def run(self, host: str = "0.0.0.0", port: int | None = None, debug: bool = True):
        port = port or int(os.getenv("PORT", "3000"))
        self.app.run(host=host, port=port, debug=debug)
