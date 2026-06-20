# Deployment Guide

## Running Locally

1. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
2. Add your Google Gemini API Key (`GEMINI_API_KEY`).
3. (Optional) Add Google Custom Search keys (`GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_ID`).

**Using Docker Compose (Recommended)**
```bash
docker-compose up --build
```
This starts both the MCP Server (Port 8000) and the Streamlit App (Port 8501).

**Using Python Directly**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Terminal 1: MCP Server
python -m mcp_server.server

# Terminal 2: Streamlit App
streamlit run frontend/app.py
```

## Streamlit Community Cloud Deployment

Vidya AI is designed to run seamlessly on Streamlit Community Cloud:

1. Push your repository to GitHub (ensure `.env` and `memory/*.json` are in `.gitignore`).
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create a new app pointing to your repository and select `frontend/app.py` as the main file.
4. In the Advanced Settings, add your Secrets:
   ```toml
   GEMINI_API_KEY="your-api-key"
   ```
5. Deploy!

*Note on Memory: Streamlit Community Cloud has ephemeral storage. The JSON memory manager will work perfectly during a session and for the lifetime of the container, but will reset upon container restart.*
