"""
Router Agent for Vidya AI.
Uses Gemini (GeminiService.classify_intent) for accurate intent detection
and language identification, then routes to the correct sub-agent or Planner.
"""
from __future__ import annotations

import logging
from typing import Any

from services.gemini_service import GeminiService
from utils.language import detect_language
from utils.security import sanitize_input, is_safe_input, get_safe_error_response
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Intent → agent name mapping
_INTENT_AGENT_MAP = {
    "career_guidance": "career_agent",
    "college_recommendation": "college_agent",
    "scholarship_search": "scholarship_agent",
    "skill_gap_analysis": "skill_gap_agent",
    "roadmap_generation": "roadmap_agent",
    "general_help": "career_agent",
}


class RouterAgent:
    """
    ADK-style Router Agent — the entry point for all user queries.

    Flow:
        User Query
          → Security check
          → Language detection
          → Gemini classify_intent (structured JSON)
          → Single intent  → direct sub-agent
          → Multi intent   → PlannerAgent
          → Memory update
    """

    name = "router_agent"

    def __init__(self):
        self._gemini = GeminiService()

    def route(
        self,
        query: str,
        session_id: str = "default",
    ) -> dict[str, Any]:
        """
        Route a user query to the appropriate agent.

        Args:
            query: Raw user message.
            session_id: Session identifier.

        Returns:
            Agent response dict — same shape as individual agent outputs.
        """
        # ── 1. Security validation ────────────────────────────────────────────
        query = sanitize_input(query)
        safe, reason = is_safe_input(query)
        if not safe:
            logger.warning("RouterAgent: unsafe input blocked. reason=%s", reason)
            lang = MemoryManager.get_profile(session_id).get("preferred_language", "en")
            return _error_response(get_safe_error_response(lang), lang)

        # ── 2. Language detection ─────────────────────────────────────────────
        language = detect_language(query)
        logger.info("RouterAgent: lang=%s session=%s query=%r", language, session_id, query[:60])

        # Update preferred language in memory
        MemoryManager.update_language(session_id, language)

        # Translate Malayalam to English for processing
        processing_query = query
        if language == "ml":
            processing_query = self._gemini.translate_to_english(query)
            logger.debug("Translated query: %r", processing_query[:80])

        # ── 3. Save user turn to memory ───────────────────────────────────────
        MemoryManager.append_conversation(session_id, "user", query)

        # ── 4. Intent classification via Gemini ───────────────────────────────
        classification = self._gemini.classify_intent(processing_query, language)
        intents: list[str] = classification.get("intents", ["general_help"])
        primary_intent: str = classification.get("primary_intent", "general_help")
        entities: dict = classification.get("entities", {})
        is_multi: bool = classification.get("is_multi_intent", False)

        logger.info(
            "RouterAgent: intents=%s multi=%s entities=%s",
            intents, is_multi, entities,
        )

        # Update memory from extracted entities
        MemoryManager.update_from_entities(session_id, entities)

        # ── 5. Route to Planner (multi-intent) or direct sub-agent ───────────
        if is_multi and len(intents) >= 2:
            from agents.planner_agent import PlannerAgent
            planner = PlannerAgent()
            return planner.execute_plan(
                query=processing_query,
                original_query=query,
                intents=intents,
                session_id=session_id,
                language=language,
                entities=entities,
            )

        # Single intent — route directly
        return self._dispatch(
            intent=primary_intent,
            query=processing_query,
            original_query=query,
            session_id=session_id,
            language=language,
            entities=entities,
        )

    def _dispatch(
        self,
        intent: str,
        query: str,
        original_query: str,
        session_id: str,
        language: str,
        entities: dict,
    ) -> dict[str, Any]:
        """Instantiate and run the appropriate sub-agent."""
        agent_name = _INTENT_AGENT_MAP.get(intent, "career_agent")
        logger.info("RouterAgent: dispatching to %s", agent_name)

        try:
            agent = _get_agent(agent_name)
            result = agent.run(
                query=query,
                session_id=session_id,
                language=language,
                entities=entities,
            )
            result["routed_intent"] = intent
            result["original_query"] = original_query
            return result
        except Exception as exc:
            logger.error("RouterAgent dispatch failed (%s): %s", agent_name, exc)
            lang_code = language
            return _error_response(get_safe_error_response(lang_code), lang_code)


def _get_agent(name: str):
    """Lazy-import agents to avoid circular imports."""
    if name == "career_agent":
        from agents.career_agent import CareerAgent
        return CareerAgent()
    elif name == "college_agent":
        from agents.college_agent import CollegeAgent
        return CollegeAgent()
    elif name == "scholarship_agent":
        from agents.scholarship_agent import ScholarshipAgent
        return ScholarshipAgent()
    elif name == "skill_gap_agent":
        from agents.skill_gap_agent import SkillGapAgent
        return SkillGapAgent()
    elif name == "roadmap_agent":
        from agents.roadmap_agent import RoadmapAgent
        return RoadmapAgent()
    else:
        from agents.career_agent import CareerAgent
        return CareerAgent()


def _error_response(text: str, language: str) -> dict[str, Any]:
    return {
        "agent_used": "router_agent",
        "intent": "general_help",
        "language": language,
        "response_text": text,
        "structured_data": {},
        "follow_up_suggestions": [
            "Ask about careers in India",
            "Find colleges in Kerala",
            "Search for scholarships",
        ],
    }
