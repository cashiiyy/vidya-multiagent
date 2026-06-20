"""
Career Agent for Vidya AI.
Uses CareerAdviceSkill (MCP tool) + Gemini to generate personalized career guidance.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.career_advice_skill import CareerAdviceSkill
from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class CareerAgent:
    """
    ADK-style Career Agent.

    Responsibilities:
    - Recommend careers based on student interests and query
    - Explain job roles and future demand in India
    - Show salary ranges
    - Suggest educational paths
    - Support English and Malayalam responses
    """

    name = "career_agent"
    description = "Expert career counselor for Indian students"

    def __init__(self):
        self._skill = CareerAdviceSkill()
        self._gemini = GeminiService()

    def run(
        self,
        query: str,
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
    ) -> dict[str, Any]:
        """
        Process a career guidance request.

        Args:
            query: Student's career question or interest description.
            session_id: Session identifier for memory access.
            language: 'en' or 'ml'.
            entities: Extracted entities from router (e.g., career_interest, state).

        Returns:
            Agent response dict with text, structured data, and follow-ups.
        """
        logger.info("CareerAgent.run: session=%s query=%r lang=%s", session_id, query[:60], language)

        # Load student profile for personalization
        profile = MemoryManager.get_profile(session_id)
        conversation_context = MemoryManager.get_history_as_text(session_id, n=4)

        # Extract query from entities if available
        search_query = query
        category = None
        if entities:
            if entities.get("career_interest"):
                search_query = entities["career_interest"]
            if entities.get("course_preference"):
                category = _infer_category(entities["course_preference"])

        # Run career advice skill (→ MCP tool → data)
        skill_result = self._skill.run(
            query=search_query,
            category=category,
            limit=5,
            student_profile=profile,
        )

        if not skill_result.get("success") or not skill_result.get("careers"):
            response_text = (
                "I couldn't find specific careers matching your query. "
                "Could you tell me more about your interests or subjects you enjoy?"
            )
            if language == "ml":
                response_text = self._gemini.translate_to_malayalam(response_text)
            return _build_response(
                agent=self.name,
                intent="career_guidance",
                language=language,
                text=response_text,
                data={},
                follow_ups=["Tell me about your favourite subjects", "What kind of work do you enjoy?"],
            )

        # Generate rich Gemini response
        profile_summary = self._gemini.summarize_profile(profile) if profile.get("interests") else ""
        response_text = self._gemini.generate_career_response(
            query=query,
            careers_data=skill_result["careers"],
            language=language,
            student_profile=profile_summary,
        )

        if not response_text:
            response_text = skill_result.get("summary", "Here are your career recommendations!")

        # Save recommendations to memory
        career_names = [c.get("career_name", "") for c in skill_result.get("careers", [])[:3]]
        MemoryManager.add_recommendation(session_id, "careers", career_names)
        if entities:
            MemoryManager.update_from_entities(session_id, entities)

        # Log conversation turn
        MemoryManager.append_conversation(session_id, "assistant", response_text, agent=self.name)

        return _build_response(
            agent=self.name,
            intent="career_guidance",
            language=language,
            text=response_text,
            data={"careers": skill_result.get("careers", []), "total": skill_result.get("total_found", 0)},
            follow_ups=skill_result.get("next_steps", []) + [
                "Show me colleges for this career",
                "What scholarships are available?",
                "Generate a learning roadmap",
            ],
        )


def _infer_category(course: str) -> str | None:
    """Infer career category from course preference."""
    c = course.lower()
    if any(k in c for k in ["engineering", "science", "math", "tech", "cs", "ai", "data"]):
        return "STEM"
    if any(k in c for k in ["arts", "humanities", "history", "literature"]):
        return "Arts"
    if any(k in c for k in ["commerce", "business", "management", "finance", "mba"]):
        return "Commerce"
    if any(k in c for k in ["medical", "mbbs", "nursing", "pharmacy", "health"]):
        return "Health"
    if any(k in c for k in ["law", "llb", "legal"]):
        return "Law"
    return None


def _build_response(
    agent: str,
    intent: str,
    language: str,
    text: str,
    data: dict,
    follow_ups: list[str],
) -> dict[str, Any]:
    return {
        "agent_used": agent,
        "intent": intent,
        "language": language,
        "response_text": text,
        "structured_data": data,
        "follow_up_suggestions": follow_ups[:4],
    }
