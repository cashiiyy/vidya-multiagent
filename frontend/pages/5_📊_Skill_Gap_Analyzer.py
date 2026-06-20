"""
Skill Gap Analyzer & Roadmap Page for Vidya AI.
UI interfacing with both SkillGapAgent and RoadmapAgent.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Skill Gap Analyzer – Vidya AI", page_icon="📊", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    import uuid; st.session_state.session_id = str(uuid.uuid4())
if "language" not in st.session_state:
    st.session_state.language = "en"

with st.sidebar:
    st.markdown("## 📊 Skill Gap Analyzer")

st.markdown("<h1 class='gradient-text'>📊 Skill Gap & Roadmap Planner</h1>", unsafe_allow_html=True)

with st.form("skill_form"):
    career = st.text_input("Target Career", placeholder="e.g. AI Engineer, Data Scientist")
    skills = st.text_input("Skills you already have (comma separated)", placeholder="e.g. Python, SQL, Communication")
    duration = st.slider("Roadmap Duration (Months)", min_value=3, max_value=24, value=12)
    
    col1, col2 = st.columns(2)
    with col1:
        analyze_btn = st.form_submit_button("Analyze Skill Gap", use_container_width=True)
    with col2:
        roadmap_btn = st.form_submit_button("Generate Roadmap", use_container_width=True)

skills_list = [s.strip() for s in skills.split(",")] if skills else []

if analyze_btn and career:
    with st.spinner("Analyzing skill gap..."):
        from agents.skill_gap_agent import SkillGapAgent
        agent = SkillGapAgent()
        result = agent.run(
            query=f"Skill gap for {career}",
            session_id=st.session_state.session_id,
            language=st.session_state.language,
            career_name=career,
            current_skills=skills_list
        )
        
        data = result.get("structured_data", {})
        readiness = data.get("readiness_percentage", 0)
        
        st.markdown(f"### 💡 Counselor's Advice\n{result.get('response_text')}")
        
        st.markdown("### 📊 Your Readiness")
        st.progress(int(readiness))
        st.write(f"You are **{readiness}%** ready for this career.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.success("**Skills you have:**\n- " + "\n- ".join(data.get("have_skills", ["None"])))
        with col_b:
            st.error("**Skills to learn:**\n- " + "\n- ".join(data.get("missing_skills", ["None"])))
            
        resources = data.get("top_resources", [])
        if resources:
            st.markdown("### 📚 Top Learning Resources")
            for r in resources:
                st.markdown(f"- **{r['skill']}**: [{r['resource']}]({r['url']}) {'(Free)' if r.get('free') else ''}")

if roadmap_btn and career:
    with st.spinner("Generating personalized roadmap..."):
        from agents.roadmap_agent import RoadmapAgent
        agent = RoadmapAgent()
        result = agent.run(
            query=f"Roadmap for {career}",
            session_id=st.session_state.session_id,
            language=st.session_state.language,
            career_name=career,
            current_skills=skills_list,
            duration_months=duration
        )
        
        st.markdown(f"### 💡 Counselor's Advice\n{result.get('response_text')}")
        
        data = result.get("structured_data", {})
        roadmap = data.get("roadmap", [])
        
        if roadmap:
            st.markdown("### 🗺️ Your Step-by-Step Roadmap")
            for step in roadmap:
                st.markdown(
                    f"""
                    <div class='timeline-step'>
                        <div class='timeline-dot'></div>
                        <h4>Month {step['month']}: {step['phase']}</h4>
                        <p><b>Learn:</b> {', '.join(step['skills_to_learn'])}</p>
                        <p><b>Milestone:</b> {step['milestones'][0] if step.get('milestones') else 'Practice and build'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
