"""
Scholarship Agent for Vidya AI.
Uses ScholarshipFinderSkill (MCP tool) + Gemini to present scholarship opportunities.
"""
from __future__ import annotations

import logging
from typing import Any

from skills.scholarship_finder_skill import ScholarshipFinderSkill
from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ScholarshipAgent:
    """
    ADK-style Scholarship Agent.

    Responsibilities:
    - Search scholarship database
    - Explain eligibility and deadlines
    - Sort by urgency
    - Provide application links and tips
    """

    name = "scholarship_agent"
    description = "Scholarship discovery specialist for Indian students"

    def __init__(self):
        self._skill = ScholarshipFinderSkill()
        self._gemini = GeminiService()

    def run(
        self,
        query: str,
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
    ) -> dict[str, Any]:
        logger.info("ScholarshipAgent.run: session=%s query=%r lang=%s", session_id, query[:60], language)

        profile = MemoryManager.get_profile(session_id)

        # Extract parameters from entities or profile
        category = (entities or {}).get("category") or profile.get("category")
        state = (entities or {}).get("state") or profile.get("state")

        # Infer category from query keywords
        if not category:
            category = _infer_category_from_query(query)

        skill_result = self._skill.run(
            category=category,
            state=state,
            limit=8,
            student_profile=profile,
        )

        if not skill_result.get("success") or not skill_result.get("scholarships"):
            text = (
                "I couldn't find scholarships matching your criteria. "
                "Try searching by category: SC, ST, OBC, Merit, Girl, or Research."
            )
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_response(
                agent=self.name, intent="scholarship_search",
                language=language, text=text, data={},
                follow_ups=["Search SC scholarships", "Search Merit scholarships", "Search Girl scholarships"],
            )

        # Generate Gemini response
        response_text = self._gemini.generate_scholarship_response(
            query=query,
            scholarships_data=skill_result["scholarships"],
            language=language,
        )
        if not response_text:
            response_text = skill_result.get("summary", "Here are the scholarships found!")

        # Update memory
        schol_names = [s.get("scholarship_name", "") for s in skill_result.get("scholarships", [])[:3]]
        MemoryManager.add_recommendation(session_id, "scholarships", schol_names)
        if entities:
            MemoryManager.update_from_entities(session_id, entities)
        MemoryManager.append_conversation(session_id, "assistant", response_text, agent=self.name)

        urgent = skill_result.get("urgent_scholarships", [])
        return _build_response(
            agent=self.name,
            intent="scholarship_search",
            language=language,
            text=response_text,
            data={
                "scholarships": skill_result.get("scholarships", []),
                "total": skill_result.get("total_found", 0),
                "urgent": urgent,
            },
            follow_ups=skill_result.get("tips", [])[:2] + [
                "How do I apply for these scholarships?",
                "Show me colleges too",
            ],
        )


def _infer_category_from_query(query: str) -> str | None:
    q = query.lower()
    if any(k in q for k in ["sc", "scheduled caste", "dalit"]):
        return "SC"
    if any(k in q for k in ["st", "scheduled tribe", "tribal", "adivasi"]):
        return "ST"
    if any(k in q for k in ["obc", "other backward"]):
        return "OBC"
    if any(k in q for k in ["merit", "top", "score", "marks", "rank"]):
        return "Merit"
    if any(k in q for k in ["girl", "woman", "female", "daughter"]):
        return "Girl"
    if any(k in q for k in ["research", "phd", "mphil", "jrf"]):
        return "Research"
    if any(k in q for k in ["need", "poor", "income", "bpl", "financial"]):
        return "Need-based"
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
