"""
Test security module.
"""
from utils.security import validate_mcp_request, sanitize_input

def test_validate_mcp_request():
    valid, msg = validate_mcp_request("career_lookup", {"query": "AI"})
    assert valid is True
    
    valid, msg = validate_mcp_request("career_lookup", {})
    assert valid is False
    assert "Missing required field" in msg

def test_sanitize_input():
    safe = sanitize_input("  Hello <script>alert(1)</script> ")
    assert "script" not in safe
