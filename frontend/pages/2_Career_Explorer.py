"""
Career Explorer Page for Vidya AI.
Provides a UI directly interfacing with the CareerAgent for dedicated exploration.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Career Explorer – Vidya AI", page_icon="🎯", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    import uuid; st.session_state.session_id = str(uuid.uuid4())
if "language" not in st.session_state:
    st.session_state.language = "en"

with st.sidebar:
    st.markdown("## 🎯 Career Explorer")
    st.info("Find careers matching your interests, marks, and passion.")

st.markdown("<h1 class='gradient-text'>🎯 Career Explorer</h1>", unsafe_allow_html=True)
st.markdown("Tell me about yourself, and I'll find the best career paths for you.")

# Input Form
with st.form("career_form"):
    col1, col2 = st.columns(2)
    with col1:
        interests = st.text_input("What are your interests or favourite subjects?", placeholder="e.g. Mathematics, AI, Art, Biology")
    with col2:
        course = st.selectbox("Preferred field of study", ["Any", "STEM (Engineering/Tech)", "Medical/Health", "Commerce/Business", "Arts/Humanities", "Law"])
    
    submit = st.form_submit_button("Explore Careers ✨", use_container_width=True)

if submit and interests:
    with st.spinner("Analyzing careers..."):
        from agents.career_agent import CareerAgent
        agent = CareerAgent()
        
        entities = {}
        if course != "Any":
            entities["course_preference"] = course
            
        result = agent.run(
            query=f"I am interested in {interests}",
            session_id=st.session_state.session_id,
            language=st.session_state.language,
            entities=entities
        )
        
        st.markdown(f"### 💡 Counselor's Advice\n{result.get('response_text')}")
        
        data = result.get("structured_data", {}).get("careers", [])
        if data:
            st.markdown("### 📋 Top Matches")
            for c in data:
                with st.expander(f"**{c.get('career_name')}**"):
                    c1, c2, c3 = st.columns(3)
                    demand = c.get("future_demand", "Moderate")
                    demand_class = "vh" if "Very High" in demand else "h" if "High" in demand else "m"
                    
                    c1.metric("Demand", demand)
                    salary = c.get("salary_range", {})
                    c2.metric("Salary Range", f"₹{salary.get('min',0)//100000}L - ₹{salary.get('max',0)//100000}L")
                    c3.markdown("**Required Skills:**")
                    c3.markdown(", ".join(c.get("required_skills", [])[:4]))
