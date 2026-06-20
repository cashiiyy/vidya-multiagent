"""
College Finder Page for Vidya AI.
Provides a UI directly interfacing with the CollegeAgent.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
st.set_page_config(page_title="College Finder – Vidya AI", page_icon="🏫", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    import uuid; st.session_state.session_id = str(uuid.uuid4())
if "language" not in st.session_state:
    st.session_state.language = "en"

with st.sidebar:
    st.markdown("## 🏫 College Finder")

st.markdown("<h1 class='gradient-text'>🏫 College Finder</h1>", unsafe_allow_html=True)

with st.form("college_form"):
    c1, c2, c3 = st.columns(3)
    with c1:
        course = st.text_input("Course", placeholder="e.g. B.Tech, MBBS")
    with c2:
        state = st.text_input("State", placeholder="e.g. Kerala, Tamil Nadu")
    with c3:
        marks = st.number_input("12th Marks (%)", min_value=35.0, max_value=100.0, value=80.0)
    submit = st.form_submit_button("Find Colleges 🔍")

if submit and course:
    with st.spinner("Searching for top colleges..."):
        from agents.college_agent import CollegeAgent
        agent = CollegeAgent()
        
        entities = {"state": state if state else None, "marks": marks}
        result = agent.run(
            query=f"Find {course} colleges",
            session_id=st.session_state.session_id,
            language=st.session_state.language,
            entities=entities
        )
        
        st.markdown(f"### 💡 Counselor's Advice\n{result.get('response_text')}")
        
        colleges = result.get("structured_data", {}).get("colleges", [])
        if colleges:
            st.markdown("### 🏫 Recommended Colleges")
            for c in colleges:
                fee = c.get('fees', {}).get('per_year', 0)
                eligible = c.get('marks_eligible')
                eligibility_tag = "✅ Eligible" if eligible is True else "⚠️ Competitive"
                with st.expander(f"**{c.get('college_name')}** - {c.get('city')}, {c.get('state')} ({c.get('type')})"):
                    col_a, col_b = st.columns(2)
                    col_a.markdown(f"**Ranking:** {c.get('ranking')}")
                    col_a.markdown(f"**Fees:** ₹{fee:,} / year")
                    col_b.markdown(f"**Your Eligibility:** {eligibility_tag} based on {marks}%")
                    col_b.markdown(f"**Accreditation:** {', '.join(c.get('accreditation', []))}")
