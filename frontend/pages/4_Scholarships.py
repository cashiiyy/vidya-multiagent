"""
Scholarships Page for Vidya AI.
UI for finding scholarships using the ScholarshipAgent.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Scholarships – Vidya AI", page_icon="🎓", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    import uuid; st.session_state.session_id = str(uuid.uuid4())
if "language" not in st.session_state:
    st.session_state.language = "en"

with st.sidebar:
    st.markdown("## 🎓 Scholarships")

st.markdown("<h1 class='gradient-text'>🎓 Scholarships</h1>", unsafe_allow_html=True)

with st.form("scholarship_form"):
    c1, c2 = st.columns(2)
    with c1:
        category = st.selectbox("Category", ["Merit", "SC", "ST", "OBC", "Girl", "Research", "Need-based"])
    with c2:
        state = st.text_input("State", placeholder="e.g. Kerala, Tamil Nadu (Optional)")
    submit = st.form_submit_button("Find Scholarships 🔍", use_container_width=True)

if submit:
    with st.spinner("Searching for scholarships..."):
        from agents.scholarship_agent import ScholarshipAgent
        agent = ScholarshipAgent()
        
        entities = {"category": category, "state": state if state else None}
        result = agent.run(
            query=f"Find {category} scholarships",
            session_id=st.session_state.session_id,
            language=st.session_state.language,
            entities=entities
        )
        
        st.markdown(f"### 💡 Counselor's Advice\n{result.get('response_text')}")
        
        data = result.get("structured_data", {})
        scholarships = data.get("scholarships", [])
        urgent_list = data.get("urgent", [])
        
        if scholarships:
            st.markdown("### 📋 Matching Scholarships")
            for s in scholarships:
                is_urgent = s.get('scholarship_name') in urgent_list
                urgency_class = "badge-urgent" if is_urgent else ""
                tag = f"<span class='{urgency_class}'>⚠️ URGENT DEADLINE</span>" if is_urgent else ""
                
                with st.expander(f"**{s.get('scholarship_name')}**"):
                    st.markdown(f"{tag}", unsafe_allow_html=True)
                    st.markdown(f"**Amount:** {s.get('amount')}")
                    st.markdown(f"**Deadline:** {s.get('deadline')}")
                    st.markdown(f"**Eligibility:** {s.get('eligibility')}")
                    
            st.info("💡 Pro Tip: Apply through [scholarships.gov.in](https://scholarships.gov.in) for Central Government scholarships.")
