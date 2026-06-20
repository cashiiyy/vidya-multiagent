"""
MCP Server configuration for Vidya AI.
"""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings


class ServerConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    cors_origins: list[str] = ["*"]  # Restrict in production
    api_title: str = "Vidya AI MCP Server"
    api_version: str = "1.0.0"
    api_description: str = (
        "MCP-compatible server exposing career, college, scholarship, "
        "skill, and roadmap tools for Vidya AI agents."
    )

    model_config = {"env_prefix": "MCP_", "env_file": ".env", "extra": "ignore"}


config = ServerConfig()
