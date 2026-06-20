"""
College Agent for Vidya AI.
Uses CollegeRecommendationSkill (MCP tool) to find colleges based on student profile.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.college_recommendation_skill import CollegeRecommendationSkill
from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class CollegeAgent:
    """
    ADK-style College Agent.

    Responsibilities:
    - Recommend government and private colleges
    - Explain eligibility criteria
    - Estimate fee structures
    - Suggest admission routes
    """

    name = "college_agent"
    description = "College recommendation specialist for Indian students"

    def __init__(self):
        self._skill = CollegeRecommendationSkill()
        self._gemini = GeminiService()

    def run(
        self,
        query: str,
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
    ) -> dict[str, Any]:
        logger.info("CollegeAgent.run: session=%s query=%r lang=%s", session_id, query[:60], language)

        profile = MemoryManager.get_profile(session_id)

        # Extract parameters from entities or profile
        state = (entities or {}).get("state") or profile.get("state")
        course = (entities or {}).get("course_preference")
        marks_raw = (entities or {}).get("marks") or profile.get("marks")
        marks = float(marks_raw) if marks_raw else None

        # Infer course from query if not in entities
        if not course:
            course = _infer_course(query)

        skill_result = self._skill.run(
            state=state,
            course=course,
            marks=marks,
            limit=8,
            student_profile=profile,
        )

        if not skill_result.get("success") or not skill_result.get("colleges"):
            text = _no_results_message(state, course, language)
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_response(
                agent=self.name, intent="college_recommendation",
                language=language, text=text, data={},
                follow_ups=["Tell me your state", "What course are you interested in?", "What are your marks?"],
            )

        # Generate Gemini response
        colleges_summary = _colleges_to_text(skill_result["colleges"][:5], marks)
        prompt_text = (
            f"A student asked: '{query}'\n\n"
            f"Here are the top colleges found:\n{colleges_summary}\n\n"
            f"Write a helpful, encouraging response in {'Malayalam (keep college names and fees in English)' if language == 'ml' else 'English'}. "
            f"Mention 3-4 colleges, their fees, type, and admission tips. Keep it concise and actionable."
        )
        response_text = self._gemini._generate(prompt_text, temperature=0.5)
        if not response_text:
            response_text = skill_result.get("summary", "Here are the colleges I found!")

        # Update memory
        college_names = [c.get("college_name", "") for c in skill_result.get("colleges", [])[:3]]
        MemoryManager.add_recommendation(session_id, "colleges", college_names)
        if entities:
            MemoryManager.update_from_entities(session_id, entities)
        MemoryManager.append_conversation(session_id, "assistant", response_text, agent=self.name)

        return _build_response(
            agent=self.name,
            intent="college_recommendation",
            language=language,
            text=response_text,
            data={"colleges": skill_result.get("colleges", []), "total": skill_result.get("total_found", 0)},
            follow_ups=skill_result.get("admission_tips", []) + [
                "Show scholarship options",
                "Generate a study roadmap for this career",
            ],
        )


def _infer_course(query: str) -> str | None:
    q = query.lower()
    if any(k in q for k in ["engineering", "b.tech", "btech", "iit", "nit"]):
        return "B.Tech"
    if any(k in q for k in ["medical", "mbbs", "doctor", "neet"]):
        return "MBBS"
    if any(k in q for k in ["law", "llb", "lawyer", "clat"]):
        return "LLB"
    if any(k in q for k in ["mba", "management", "business"]):
        return "MBA"
    if any(k in q for k in ["arts", "ba ", "humanities"]):
        return "BA"
    if any(k in q for k in ["science", "b.sc", "bsc", "msc"]):
        return "B.Sc"
    return None


def _colleges_to_text(colleges: list[dict], marks: float | None) -> str:
    lines = []
    for c in colleges:
        fee = c.get("fees", {}).get("per_year", 0)
        eligible = c.get("marks_eligible")
        eligible_str = " ✅ Eligible" if eligible is True else (" ⚠️ Competitive" if eligible is False else "")
        lines.append(
            f"- {c.get('college_name')} ({c.get('city')}, {c.get('state')}) | "
            f"Rank #{c.get('ranking')} | ₹{fee:,}/yr | {c.get('type')}{eligible_str}"
        )
    return "\n".join(lines)


def _no_results_message(state: str | None, course: str | None, language: str) -> str:
    parts = []
    if course:
        parts.append(f"for {course}")
    if state:
        parts.append(f"in {state}")
    qualifier = " ".join(parts) if parts else "matching your criteria"
    return (
        f"I couldn't find colleges {qualifier}. "
        f"Try specifying your state, preferred course, or fee range."
    )


def _build_response(agent, intent, language, text, data, follow_ups) -> dict[str, Any]:
    return {
        "agent_used": agent,
        "intent": intent,
        "language": language,
        "response_text": text,
        "structured_data": data,
        "follow_up_suggestions": follow_ups[:4],
    }
