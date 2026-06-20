"""
Skill Gap Agent for Vidya AI.
Uses SkillGapSkill (MCP tool) to analyze gaps between current and required skills.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.skill_gap_skill import SkillGapSkill
from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class SkillGapAgent:
    """
    ADK-style Skill Gap Agent.

    Responsibilities:
    - Compare current skills vs target career requirements
    - Output missing skills
    - Provide learning resources
    - Estimate readiness percentage
    """

    name = "skill_gap_agent"
    description = "Skill gap analyzer and learning advisor for Indian students"

    def __init__(self):
        self._skill = SkillGapSkill()
        self._gemini = GeminiService()

    def run(
        self,
        query: str,
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
        career_name: str | None = None,
        current_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        logger.info("SkillGapAgent.run: session=%s career=%r lang=%s", session_id, career_name, language)

        profile = MemoryManager.get_profile(session_id)

        # Determine target career
        target_career = (
            career_name
            or (entities or {}).get("career_interest")
            or profile.get("career_interest")
            or _extract_career_from_query(query)
        )

        if not target_career:
            text = (
                "Please tell me which career you're aiming for, "
                "and I'll analyze the skill gap for you."
            )
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_response(
                agent=self.name, intent="skill_gap_analysis",
                language=language, text=text, data={},
                follow_ups=["I want to become an AI Engineer", "I want to be a Data Scientist", "I want to be a Doctor"],
            )

        # Get current skills from profile interests + passed list
        profile_skills = profile.get("interests", [])
        all_current_skills = list(set((current_skills or []) + profile_skills))

        skill_result = self._skill.run(
            career_name=target_career,
            current_skills=all_current_skills,
            student_profile=profile,
        )

        # Build Gemini narrative
        gap_context = skill_result.get("summary", "")
        missing = skill_result.get("missing_skills", [])
        readiness = skill_result.get("readiness_percentage", 0.0)

        prompt = (
            f"A student asked: '{query}'\n\n"
            f"Skill gap analysis result:\n{gap_context}\n"
            f"Missing skills: {', '.join(missing) if missing else 'None'}\n"
            f"Readiness: {readiness:.0f}%\n\n"
            f"Write an encouraging, actionable response {'in Malayalam (keep technical terms in English)' if language == 'ml' else 'in English'}. "
            f"Mention the readiness score, what skills to focus on first, and suggest next steps."
        )
        response_text = self._gemini._generate(prompt, temperature=0.5)
        if not response_text:
            response_text = gap_context or "Here is your skill gap analysis!"

        MemoryManager.append_conversation(session_id, "assistant", response_text, agent=self.name)
        if entities:
            MemoryManager.update_from_entities(session_id, entities)

        return _build_response(
            agent=self.name,
            intent="skill_gap_analysis",
            language=language,
            text=response_text,
            data={
                "career_name": target_career,
                "readiness_percentage": readiness,
                "missing_skills": missing,
                "have_skills": skill_result.get("have_skills", []),
                "top_resources": skill_result.get("top_resources", []),
            },
            follow_ups=[
                f"Generate a roadmap to become a {target_career}",
                "Show me scholarships",
                "Which colleges offer this course?",
                skill_result.get("motivation", "Keep going!"),
            ],
        )


def _extract_career_from_query(query: str) -> str | None:
    """Simple keyword extraction for common career mentions."""
    careers = [
        "AI Engineer", "Data Scientist", "Software Engineer", "Doctor", "Lawyer",
        "Chartered Accountant", "Civil Services", "Architect", "Nurse",
        "Mechanical Engineer", "Electrical Engineer", "Civil Engineer",
        "Data Analyst", "Web Developer", "Game Developer", "Pilot",
        "Pharmacist", "Teacher", "Journalist", "Graphic Designer",
    ]
    q_lower = query.lower()
    for c in careers:
        if c.lower() in q_lower or c.split()[0].lower() in q_lower:
            return c
    return None


def _build_response(agent, intent, language, text, data, follow_ups) -> dict[str, Any]:
    return {
        "agent_used": agent,
        "intent": intent,
        "language": language,
        "response_text": text,
        "structured_data": data,
        "follow_up_suggestions": follow_ups[:4],
    }
