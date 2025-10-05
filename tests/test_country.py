import os
import pytest
from mcp_core import MCP
from tools.country import register as register_country

@pytest.fixture(scope="module")
def client():
    os.environ["MCP_API_KEY"] = "test-key"
    mcp = MCP("Test Server")
    register_country(mcp)
    return mcp.app.test_client()

def auth_headers():
    return {"x-api-key": "test-key"}

def test_list_tools(client):
    res = client.get("/tools/list", headers=auth_headers())
    assert res.status_code == 200
    data = res.get_json()
    assert any(t["id"] == "country/info" for t in data["tools"])
