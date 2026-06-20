# ── Vidya AI – Dockerfile ────────────────────────────────────
# Multi-stage: installs deps once, then copies app code.
# Build & run:
#   docker build -t vidya-ai .
#   docker run -p 8000:8000 -p 8501:8501 --env-file .env vidya-ai
# ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose ports: MCP server + Streamlit
EXPOSE 8000 8501

# Default: launch both services via a tiny shell script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
