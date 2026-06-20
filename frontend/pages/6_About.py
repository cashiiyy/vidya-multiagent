"""
About Page for Vidya AI.
Student-focused information about the platform's purpose and capabilities.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="About – Vidya AI", page_icon="ℹ️", layout="wide")

_CSS = Path(__file__).parent.parent / "styles" / "theme.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ℹ️ About Vidya AI")
    st.markdown("Your personal mentor for career and education in India.")

st.markdown("<h1 class='gradient-text'>ℹ️ About Vidya AI</h1>", unsafe_allow_html=True)

st.markdown("""
<div class='glass-card'>
<h3>Empowering Students in India</h3>

**Vidya AI** is your intelligent, personalized educational mentor. Navigating the choices after 10th, 12th, or college can be overwhelming. We created Vidya to guide you step-by-step toward a successful future.

#### ✨ What Vidya AI Does

- **Career Discovery**: Confused about what to do next? Tell Vidya your interests, and it will recommend high-demand career paths tailored for you.
- **College Recommendations**: Find the best colleges in India that match your marks, desired course, and budget.
- **Scholarship Finder**: Don't let finances hold you back. Vidya actively finds scholarships you are eligible for, prioritizing those with upcoming deadlines.
- **Skill Gap Analysis**: Find out exactly what skills you need to achieve your dream job compared to what you currently know.
- **Learning Roadmaps**: Get personalized, month-by-month study plans to help you acquire new skills efficiently.
- **Bilingual Support**: Chat with Vidya comfortably in English or Malayalam.

#### 🤝 How We Help

Vidya acts as your virtual counselor available 24/7. Whether you need a quick answer about an entrance exam or a comprehensive multi-year study plan, Vidya breaks down complex educational pathways into simple, actionable steps. 

Our goal is simple: to make quality educational guidance accessible to every student in India.
</div>
""", unsafe_allow_html=True)
