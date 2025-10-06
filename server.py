# server.py
# -----------------------------------------------------------
# MCP Server bootstrap with auto-discovered @mcp.tool modules
# -----------------------------------------------------------

import os
import sys
import logging
import importlib.util

try:
    from dotenv import load_dotenv
except Exception:  # dotenv is optional in prod
    def load_dotenv():
        return None

from mcp_core import MCP

# Load environment (.env is optional)
load_dotenv()

# ---------- Logging ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("mcp-server")

# ---------- Create MCP server ----------
mcp = MCP(name=os.getenv("SERVER_NAME", "MCP Country Server"))

# Allow /tools/list and /tools/call to work with or without trailing slash
# (avoid accidental 404s on '/tools/list/' etc.)
mcp.app.url_map.strict_slashes = False

# ---------- Optional: CORS for browser UIs ----------
# Allows calling from React/Vite dev servers, etc.
try:
    from flask_cors import CORS

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    CORS(
        mcp.app,
        resources={r"/*": {"origins": [o.strip() for o in cors_origins.split(",")]}},
        supports_credentials=False,
    )
    logger.info("CORS enabled for origins: %s", cors_origins)
except Exception:
    logger.info("flask-cors not installed; skipping CORS setup")

# ---------- Health & root routes (handy for 404 debugging) ----------
from flask import jsonify  # noqa: E402

@mcp.app.get("/")
def root():
    return jsonify({
        "status": "ok",
        "name": mcp.name,
        "tools": sorted(t for t in mcp._tools.keys()),
    })

@mcp.app.get("/health")
def health():
    return jsonify({"status": "healthy", "name": mcp.name})


# ---------- Auto-discover tools in tools/ ----------
def _register_tools_from_folder(folder_path: str):
    if not os.path.isdir(folder_path):
        logger.warning("Tools directory not found: %s", folder_path)
        return

    # Ensure folder is importable if modules do relative imports
    if folder_path not in sys.path:
        sys.path.insert(0, folder_path)

    for fname in sorted(os.listdir(folder_path)):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue

        path = os.path.join(folder_path, fname)
        module_name = f"tools_{fname[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]

            if hasattr(module, "register") and callable(module.register):
                module.register(mcp)
                logger.info("Registered tools from %s", fname)
            else:
                logger.info("No register(mcp) found in %s", fname)

        except Exception as e:
            logger.exception("Failed to load tool module %s: %s", fname, e)


# Resolve tools directory (works when executed from anywhere)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(PROJECT_DIR, "tools")
_register_tools_from_folder(TOOLS_DIR)

# Debug output of registered tools
logger.info("Available tools: %s", sorted(list(mcp._tools.keys())))
print("Registered tools:", sorted(list(mcp._tools.keys())))

# ---------- Entrypoint ----------
if __name__ == "__main__":
    # Ensure working dir is project root (important for relative paths)
    os.chdir(PROJECT_DIR)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    debug = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

    logger.info("Starting %s on http://%s:%s (debug=%s)", mcp.name, host, port, debug)
    logger.info(
        'Try: curl -H "x-api-key: %s" http://localhost:%s/tools/list',
        os.getenv("MCP_API_KEY", "dev-key-123"),
        port,
    )

    # --- Wait-for-health logging in background (retry) ---
    # This thread pings /health until the server is ready, then logs ✅
    import threading
    import time
    import requests

    def _wait_for_health():
        # If bound to 0.0.0.0, use localhost for the probe
        probe_host = "localhost" if host == "0.0.0.0" else host
        url = f"http://{probe_host}:{port}/health"
        deadline = time.time() + 10.0  # total 10 seconds
        backoff = 0.25
        while time.time() < deadline:
            try:
                r = requests.get(url, timeout=1.5)
                if r.ok:
                    logger.info("✅ MCP server is healthy: %s", url)
                    return
            except Exception:
                pass
            time.sleep(backoff)
            # mild backoff up to ~1s
            backoff = min(backoff * 1.5, 1.0)
        logger.warning("⚠️ MCP server did not report healthy within timeout: %s", url)

    threading.Thread(target=_wait_for_health, daemon=True).start()

    # Run Flask server
    mcp.run(host=host, port=port, debug=debug)
