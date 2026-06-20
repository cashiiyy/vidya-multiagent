from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from pathlib import Path

# ── Page configuration (must be first Streamlit call) ────────────────────────
st.set_page_config(
    page_title="Vidya AI – Career & Education Mentor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/vidya-ai",
        "About": "Vidya AI – Multi-Agent Career Mentor for Indian Students",
    },
)

# ── Load custom CSS ───────────────────────────────────────────────────────────
_CSS_PATH = Path(__file__).parent / "styles" / "theme.css"
if _CSS_PATH.exists():
    st.markdown(f"<style>{_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

# ── Session state initialisation ──────────────────────────────────────────────
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "language" not in st.session_state:
    st.session_state.language = "en"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding: 1rem 0 0.5rem;'>
          <span style='font-size:2.5rem;'>🎓</span>
          <h2 style='margin:0; color:#f5c842; font-family:Space Grotesk,sans-serif;'>Vidya AI</h2>
          <p style='color:#8892b0; font-size:0.82rem; margin:0;'>
            Career & Education Mentor
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # Language toggle
    lang_choice = st.radio(
        "🌐 Language / ഭാഷ",
        options=["English", "Malayalam / മലയാളം"],
        index=0 if st.session_state.language == "en" else 1,
        key="lang_toggle",
    )
    st.session_state.language = "en" if lang_choice == "English" else "ml"

    st.divider()
    st.markdown(
        """
        <div style='color:#8892b0; font-size:0.78rem; padding:0.5rem 0;'>
        <b style='color:#f5c842'>🤖 Active Agents</b><br>
        • 🔀 Router Agent<br>
        • 📋 Planner Agent<br>
        • 🎯 Career Agent<br>
        • 🏫 College Agent<br>
        • 🎓 Scholarship Agent<br>
        • 📊 Skill Gap Agent<br>
        • 🗺️ Roadmap Agent
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        "<div style='color:#8892b0; font-size:0.75rem; text-align:center;'>"
        "Powered by Google Gemini + ADK<br>"
        "Built for Kaggle AI Agents Capstone"
        "</div>",
        unsafe_allow_html=True,
    )


# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align:center; padding: 3rem 1rem 1.5rem;'>
      <div style='font-size:4rem; margin-bottom:0.5rem;'>🎓</div>
      <h1 class='gradient-text' style='font-size:3rem; margin:0;'>Vidya AI</h1>
      <p style='color:#8892b0; font-size:1.15rem; margin:0.5rem 0 2rem;'>
        Helping Indian students discover careers, colleges, scholarships,<br>
        and skills through an AI-powered multilingual mentor.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Feature cards ──────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
features1 = [
    ("💬", "Chat Assistant", "Talk with Vidya AI to get answers to your queries and general guidance.", "pages/1_💬_Chat_Assistant.py"),
    ("🎯", "Career Explorer", "Discover the perfect career matching your interests and skills with AI.", "pages/2_🎯_Career_Explorer.py"),
    ("🏫", "College Finder", "Discover top colleges across India matching your criteria and budget.", "pages/3_🏫_College_Finder.py"),
]
for col, (icon, title, desc, target) in zip([c1, c2, c3], features1):
    with col:
        st.markdown(
            f"""<div class='glass-card' style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 180px; margin-bottom: 0.5rem;'>
              <div style='font-size:2.2rem; margin-bottom:0.5rem;'>{icon}</div>
              <h3 style='color:#f5c842; margin:0 0 0.5rem 0; font-size:1.3rem;'>{title}</h3>
              <p style='color:#8892b0; font-size:0.85rem; margin:0; line-height: 1.4;'>{desc}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(f"Open {title}", key=f"btn_{title.replace(' ', '_').lower()}", use_container_width=True):
            st.switch_page(target)

st.markdown("<br>", unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)
features2 = [
    ("🎓", "Scholarships", "Find government and private scholarships you're eligible for.", "pages/4_🎓_Scholarships.py"),
    ("📊", "Skill Gap Analyzer", "Compare your skills against dream careers and get a learning path.", "pages/5_📊_Skill_Gap_Analyzer.py"),
    ("ℹ️", "About", "Learn more about Vidya AI and how this platform helps students.", "pages/6_ℹ️_About.py"),
]
for col, (icon, title, desc, target) in zip([c4, c5, c6], features2):
    with col:
        st.markdown(
            f"""<div class='glass-card' style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 180px; margin-bottom: 0.5rem;'>
              <div style='font-size:2.2rem; margin-bottom:0.5rem;'>{icon}</div>
              <h3 style='color:#f5c842; margin:0 0 0.5rem 0; font-size:1.3rem;'>{title}</h3>
              <p style='color:#8892b0; font-size:0.85rem; margin:0; line-height: 1.4;'>{desc}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(f"Open {title}", key=f"btn_{title.replace(' ', '_').lower()}", use_container_width=True):
            st.switch_page(target)

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick-start CTA ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<h2 style='text-align:center; color:#f5c842'>🚀 Get Started</h2>"
    "<p style='text-align:center; color:#8892b0'>Navigate to any page using the sidebar, or start chatting below</p>",
    unsafe_allow_html=True,
)

col_a, col_b, col_c = st.columns([1, 2, 1])
with col_b:
    quick_q = st.text_input(
        "Ask Vidya AI anything",
        placeholder='e.g. "I love maths and AI — what career suits me?" / "AI Engineer ആകാൻ എന്ത് ചെയ്യണം?"',
        key="home_quick_q",
        label_visibility="collapsed",
    )
    if st.button("✨ Ask Vidya AI", use_container_width=True, key="home_ask_btn"):
        if quick_q.strip():
            st.session_state["pending_query"] = quick_q
            st.switch_page("pages/1_💬_Chat_Assistant.py")
        else:
            st.warning("Please type a question first.")

# ── Stats bar ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
s1, s2, s3, s4, s5 = st.columns(5)
stats = [
    ("30+", "Careers"), ("50+", "Colleges"), ("30+", "Scholarships"),
    ("7", "AI Agents"), ("2", "Languages"),
]
for col, (val, label) in zip([s1, s2, s3, s4, s5], stats):
    col.metric(label, val)
