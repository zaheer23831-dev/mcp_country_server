# ...existing code...
import os
import logging
import importlib.util

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None

from mcp_core import MCP

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = MCP(name="MCP Country Server")

# Auto-discover and register tool modules in the tools/ folder
tools_dir = os.path.join(os.path.dirname(__file__), "tools")
if os.path.isdir(tools_dir):
    for fname in sorted(os.listdir(tools_dir)):
        if not fname.endswith(".py") or fname.startswith("__"):
            continue
        path = os.path.join(tools_dir, fname)
        module_name = f"tools_{fname[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(mcp)
                logger.info("Registered tools from %s", fname)
            else:
                logger.info("No register(mcp) in %s", fname)
        except Exception as e:
            logger.exception("Failed to load tool module %s: %s", fname, e)

# Debug output of registered tools
logger.info("Available tools: %s", list(mcp._tools.keys()))
print("Registered tools:", list(mcp._tools.keys()))

if __name__ == "__main__":
    # ensure working directory is project root when running
    os.chdir(os.path.dirname(__file__))
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    debug = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
    mcp.run(host=host, port=port, debug=debug)
# ...existing code...