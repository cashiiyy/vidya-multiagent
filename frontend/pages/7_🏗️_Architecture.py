"""
Architecture Page for Vidya AI.
Kaggle project information, architecture overview, and evidence.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Architecture – Vidya AI", page_icon="🏗️", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🏗️ Architecture")

st.markdown("<h1 class='gradient-text'>🏗️ Vidya AI Architecture</h1>", unsafe_allow_html=True)

st.markdown("""

**Vidya AI** is a Multi-Agent system designed for the "Agents for Good" track. It provides career, college, and scholarship guidance to Indian students, acting as an AI-powered educational mentor.

#### 🏗️ Architecture

- **Google ADK**: Used to orchestrate 6 specialized agents and a Router.
- **MCP Server**: A FastAPI-based Model Context Protocol server exposing data via local JSON stores and Gemini grounding tools.
- **Gemini 2.0 Flash**: Powers reasoning, intent routing, and Malayalam translation.
- **Streamlit**: The glassmorphic, bilingual user interface.

#### 🤖 The Agents
1. **Router Agent**: Detects user intent, language, and extracts entities securely.
2. **Planner Agent**: Orchestrates multi-step queries (e.g., "Find colleges and scholarships").
3. **Career Agent**: Maps student interests to high-demand careers.
4. **College Agent**: Filters Indian colleges by marks, course, and fee.
5. **Scholarship Agent**: Ranks scholarships by deadline urgency.
6. **Skill Gap Agent**: Analyzes current vs required skills.
7. **Roadmap Agent**: Generates month-by-month learning plans.

#### 🔐 Security & Memory
- Features prompt injection and safety filtering using `utils/security.py`.
- Maintains thread-safe, local JSON memory for session context and profile persistence.

---
*Built entirely using Prompt-Driven Development via Google Antigravity.*
""")
