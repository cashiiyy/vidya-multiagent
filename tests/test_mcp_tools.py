"""
Test MCP tools (local).
"""
from mcp_server.tools import career_lookup, college_lookup

def test_career_lookup():
    result = career_lookup(query="software", limit=1)
    assert result["success"] is True
    assert len(result["careers"]) <= 1

def test_college_lookup():
    result = college_lookup(state="Kerala", limit=1)
    assert result["success"] is True
    if len(result["colleges"]) > 0:
        assert result["colleges"][0]["state"] == "Kerala"
