"""
Roadmap Agent for Vidya AI.
Uses RoadmapGenerationSkill (MCP tool) to produce month-by-month learning plans.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.roadmap_generation_skill import RoadmapGenerationSkill
from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class RoadmapAgent:
    """
    ADK-style Roadmap Agent.

    Responsibilities:
    - Generate step-by-step monthly learning roadmap
    - Personalise based on current skills
    - Recommend certifications and resources
    - Support English and Malayalam
    """

    name = "roadmap_agent"
    description = "Personalized learning roadmap generator for Indian students"

    def __init__(self):
        self._skill = RoadmapGenerationSkill()
        self._gemini = GeminiService()

    def run(
        self,
        query: str,
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
        career_name: str | None = None,
        current_skills: list[str] | None = None,
        duration_months: int = 12,
    ) -> dict[str, Any]:
        logger.info("RoadmapAgent.run: session=%s career=%r duration=%d", session_id, career_name, duration_months)

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
                "Please specify which career you'd like a roadmap for. "
                "For example: 'Create a roadmap to become an AI Engineer in 12 months.'"
            )
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_response(
                agent=self.name, intent="roadmap_generation",
                language=language, text=text, data={},
                follow_ups=["Roadmap to become an AI Engineer", "Roadmap to become a Data Scientist", "Roadmap for Software Engineer"],
            )

        # Merge current skills from profile
        profile_skills = profile.get("interests", [])
        all_current = list(set((current_skills or []) + profile_skills))

        skill_result = self._skill.run(
            career_name=target_career,
            current_skills=all_current,
            duration_months=duration_months,
            student_profile=profile,
        )

        if not skill_result.get("success"):
            text = f"I couldn't generate a roadmap for '{target_career}'. Please try a different career name."
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_response(
                agent=self.name, intent="roadmap_generation",
                language=language, text=text, data={}, follow_ups=[],
            )

        # Build narrative with Gemini
        roadmap_summary = skill_result.get("summary", "")
        certs = skill_result.get("recommended_certifications", [])
        tips = skill_result.get("tips", [])

        prompt = (
            f"A student wants to become a {target_career}.\n\n"
            f"Roadmap summary:\n{roadmap_summary}\n\n"
            f"Recommended certifications: {', '.join(certs[:3])}\n"
            f"Key tips: {tips[0] if tips else ''}\n\n"
            f"Write an inspiring, motivating introduction to this roadmap "
            f"{'in Malayalam (keep technical terms in English)' if language == 'ml' else 'in English'}. "
            f"2-3 sentences max. Then mention the first 2 steps."
        )
        response_text = self._gemini._generate(prompt, temperature=0.6)
        if not response_text:
            response_text = roadmap_summary or f"Here is your {duration_months}-month roadmap!"

        MemoryManager.append_conversation(session_id, "assistant", response_text, agent=self.name)
        if entities:
            MemoryManager.update_from_entities(session_id, entities)

        return _build_response(
            agent=self.name,
            intent="roadmap_generation",
            language=language,
            text=response_text,
            data={
                "career_name": target_career,
                "duration_months": duration_months,
                "roadmap": skill_result.get("roadmap", []),
                "certifications": certs,
                "tips": tips,
                "skills_to_learn": skill_result.get("skills_to_learn", []),
                "skills_already_have": skill_result.get("skills_already_have", []),
            },
            follow_ups=[
                "Show me colleges for this career",
                "What scholarships can I apply for?",
                "Analyze my skill gap for this career",
            ] + (tips[:1] if tips else []),
        )


def _extract_career_from_query(query: str) -> str | None:
    careers = [
        "AI Engineer", "Data Scientist", "Software Engineer", "Doctor", "Lawyer",
        "Chartered Accountant", "Civil Services Officer", "Architect", "Nurse",
        "Mechanical Engineer", "Electrical Engineer", "Civil Engineer",
        "Data Analyst", "Web Developer", "Game Developer", "Pilot",
        "Pharmacist", "Teacher", "Journalist", "Graphic Designer",
        "Cloud Architect", "Cybersecurity Analyst", "Blockchain Developer",
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
