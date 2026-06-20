"""
Chat Assistant Page – main conversation interface for Vidya AI.
All user queries are processed through RouterAgent → Planner/Sub-agents.
"""
import streamlit as st
from pathlib import Path
import sys, os

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Chat – Vidya AI", page_icon="💬", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    import uuid; st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "en"

AGENT_ICONS = {
    "router_agent": "🔀", "planner_agent": "📋",
    "career_agent": "🎯", "college_agent": "🏫",
    "scholarship_agent": "🎓", "skill_gap_agent": "📊",
    "roadmap_agent": "🗺️",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💬 Chat Assistant")
    lang = st.radio("Language", ["English", "Malayalam / മലയാളം"],
                    index=0 if st.session_state.language == "en" else 1)
    st.session_state.language = "en" if lang == "English" else "ml"
    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        from memory.memory_manager import MemoryManager
        MemoryManager.clear_session(st.session_state.session_id)
        st.rerun()

    st.divider()
    st.markdown(
        """**💡 Try asking:**
- "I love maths and AI, what careers suit me?"
- "Best engineering colleges in Kerala under 50k fees"
- "SC scholarships for Tamil Nadu students"
- "I scored 82% and need an AI roadmap"
- "എനിക്ക് AI Engineer ആകണം"
"""
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    "<h1 class='gradient-text'>💬 Chat with Vidya AI</h1>"
    "<p style='color:#8892b0'>Ask anything about careers, colleges, scholarships or learning paths</p>",
    unsafe_allow_html=True,
)

# ── Display chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
        st.markdown(msg["content"])
        if msg.get("agent"):
            icon = AGENT_ICONS.get(msg["agent"], "🤖")
            st.markdown(
                f"<span class='agent-pill'>{icon} {msg['agent'].replace('_', ' ').title()}</span>",
                unsafe_allow_html=True,
            )
        if msg.get("follow_ups"):
            st.markdown("**Suggested follow-ups:**")
            cols = st.columns(min(len(msg["follow_ups"]), 2))
            for i, fq in enumerate(msg["follow_ups"][:4]):
                if cols[i % 2].button(fq[:50], key=f"fq_{id(msg)}_{i}"):
                    st.session_state["_pending"] = fq
                    st.rerun()

# ── Handle pending follow-up click ───────────────────────────────────────────
if "_pending" in st.session_state:
    pending = st.session_state.pop("_pending")
    st.session_state.messages.append({"role": "user", "content": pending})
    st.rerun()

# ── Check for query from home page ────────────────────────────────────────────
if "pending_query" in st.session_state:
    pending = st.session_state.pop("pending_query")
    st.session_state.messages.append({"role": "user", "content": pending})
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    placeholder="Type your question in English or Malayalam... / ഇവിടെ ടൈപ്പ് ചെയ്യൂ...",
    key="chat_input",
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# ── Process last message if it's from the user ─────────────────────────────────
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_query = st.session_state.messages[-1]["content"]

    with st.chat_message("assistant", avatar="🎓"):
        loading_placeholder = st.empty()
        loading_placeholder.markdown(
            "<div style='display:flex; align-items:center; gap:12px; padding:0.5rem 0;'>"
            "<div class='vidya-loading'>"
            "<span></span><span></span><span></span>"
            "</div>"
            "<span style='color:var(--accent); font-weight:600; font-size:0.95rem; letter-spacing:0.02em;'>Vidya is thinking...</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        try:
            from agents.router_agent import RouterAgent
            router = RouterAgent()
            result = router.route(
                query=last_query,
                session_id=st.session_state.session_id,
            )

            loading_placeholder.empty()
            response_text = result.get("response_text", "I couldn't process that. Please try again.")
            agent_used = result.get("agent_used", "")
            follow_ups = result.get("follow_up_suggestions", [])

            st.markdown(response_text)

            # Agent badge
            if agent_used:
                icon = AGENT_ICONS.get(agent_used, "🤖")
                plan = result.get("plan_executed", [])
                plan_str = f" → Plan: {', '.join(plan)}" if plan else ""
                st.markdown(
                    f"<span class='agent-pill'>{icon} {agent_used.replace('_',' ').title()}{plan_str}</span>",
                    unsafe_allow_html=True,
                )

            # Structured data expanders
            data = result.get("structured_data", {})
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list) and val:
                        with st.expander(f"📄 View {key.replace('_', ' ').title()} ({len(val)} results)"):
                            for item in val[:5]:
                                if isinstance(item, dict):
                                    st.json(item, expanded=False)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "agent": agent_used,
                "follow_ups": follow_ups,
            })

        except Exception as exc:
            loading_placeholder.empty()
            error_msg = (
                "⚠️ Vidya AI is not fully configured yet. "
                "Please set your `GEMINI_API_KEY` in the `.env` file and restart.\n\n"
                f"*Technical detail: {str(exc)[:120]}*"
            )
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    st.rerun()
