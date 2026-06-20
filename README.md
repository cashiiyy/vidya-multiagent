<div align="center">
  <h1>🎓 Vidya AI</h1>
  <p><b>Multi-Agent Career & Education Mentor for Indian Students</b></p>
  <p><i>Helping students discover careers, colleges, scholarships, and skills through an AI-powered bilingual mentor.</i></p>
  
  [![Built with Google ADK](https://img.shields.io/badge/Google-ADK-blue?logo=google)](https://github.com/google/agent-development-kit)
  [![Powered by Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-orange)](https://deepmind.google/technologies/gemini/)
  [![MCP Server](https://img.shields.io/badge/MCP-FastAPI-green)](https://modelcontextprotocol.io/)
  [![Kaggle AI Agents Intensive](https://img.shields.io/badge/Kaggle-Capstone-blue?logo=kaggle)](https://www.kaggle.com/)
</div>

<br>

## 🌟 Overview

**Vidya AI** is a production-ready, multi-agent AI system designed for the Kaggle AI Agents Intensive "Agents for Good" track. It addresses a critical gap in the Indian education system by providing personalized, accurate, and accessible career counseling in both English and Malayalam.

Vidya AI orchestrates 7 specialized agents using Google ADK to analyze student interests, recommend high-demand careers, find eligible colleges, rank scholarships by urgency, and generate step-by-step learning roadmaps.

## 🏗️ Architecture

The system uses a decoupled, robust architecture built on modern AI standards:

1. **Google ADK Multi-Agent System**: 7 agents orchestrating complex reasoning.
2. **Model Context Protocol (MCP)**: A FastAPI server exposing 9 standardized tools (5 local data tools, 4 Gemini-powered grounding tools).
3. **ADK Skills Layer**: Decouples business logic from agent definitions.
4. **Stateful Memory**: Thread-safe JSON persistence for student profiles and conversation history.
5. **Streamlit Frontend**: A glassmorphic, highly interactive bilingual web app.

[View full architecture diagram here](docs/architecture.md)

## 🚀 The Agents

- **🔀 Router Agent**: The gateway. Handles security, translates Malayalam to English, extracts entities, and routes queries.
- **📋 Planner Agent**: Orchestrates complex, multi-intent queries (e.g., "Find colleges and scholarships") by running multiple sub-agents sequentially.
- **🎯 Career Agent**: Maps student interests to careers using salary and demand data.
- **🏫 College Agent**: Recommends colleges based on state, course, marks, and fee constraints.
- **🎓 Scholarship Agent**: Finds government and private scholarships, sorting them by deadline urgency.
- **📊 Skill Gap Agent**: Analyzes current skills vs target career requirements.
- **🗺️ Roadmap Agent**: Generates personalized month-by-month learning plans.

## 🛠️ Installation & Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API Key

### Setup
1. Clone the repository
2. Create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```
3. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Running the System
You need to run both the MCP Server and the Streamlit Frontend.

**Terminal 1 (MCP Server):**
```bash
python -m mcp_server.server
# Server starts on http://localhost:8000
```

**Terminal 2 (Streamlit App):**
```bash
streamlit run frontend/🧠Vidya.py
# App opens at http://localhost:8501
```

*(Alternatively, use `docker-compose up --build` to run everything automatically).*

## 📚 Documentation

- [Deployment Guide](docs/deployment.md) - Instructions for local, Docker, and Streamlit Cloud deployment.
- [Architecture Details](docs/architecture.md) - Deep dive into the ADK and MCP implementation.
- [Antigravity Evidence](docs/antigravity_prompts.md) - Details on how this project was built using Prompt-Driven Development.

## 🔒 Security & Safety
Vidya AI implements strict security middleware (`utils/security.py`) to prevent prompt injections, validate MCP payloads, and enforce Gemini safety settings to ensure an appropriate environment for students.

---
*Built for the Kaggle AI Agents Intensive Vibe Coding Capstone.*
