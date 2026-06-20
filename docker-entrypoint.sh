#!/bin/bash
# docker-entrypoint.sh – starts MCP server then Streamlit frontend
set -e

echo "🚀 Starting Vidya AI MCP Server on port 8000..."
uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000 &

echo "🎨 Starting Vidya AI Streamlit Frontend on port 8501..."
streamlit run frontend/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true

# Keep container alive if streamlit exits
wait
