"""
Planner Agent for Vidya AI.
Decomposes complex multi-intent queries into an ordered task plan,
orchestrates multiple sub-agents sequentially, and merges their responses
into one coherent, structured answer.

Flow:
    RouterAgent (detects multi-intent)
        → PlannerAgent.execute_plan()
            → Career Agent   (if career_guidance in plan)
            → College Agent  (if college_recommendation in plan)
            → Scholarship Agent (if scholarship_search in plan)
            → Skill Gap Agent   (if skill_gap_analysis in plan)
            → Roadmap Agent     (if roadmap_generation in plan)
        → Merged response

Example:
    "I scored 82%, love AI and need scholarships"
    → Plan: [career_guidance, college_recommendation, scholarship_search, roadmap_generation]
    → All 4 agents run → results merged
"""
from __future__ import annotations

import logging
from typing import Any

from services.gemini_service import GeminiService
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Maximum sub-agents to run per plan (prevent runaway execution)
_MAX_PLAN_STEPS = 4

# Intent execution order (ensures logical flow)
_EXECUTION_ORDER = [
    "career_guidance",
    "college_recommendation",
    "scholarship_search",
    "skill_gap_analysis",
    "roadmap_generation",
    "general_help",
]


class PlannerAgent:
    """
    ADK-style Planner Agent — multi-intent orchestrator.

    Receives a list of intents from the Router Agent,
    orders them logically, executes each sub-agent,
    then synthesizes a unified response.
    """

    name = "planner_agent"

    def __init__(self):
        self._gemini = GeminiService()

    def execute_plan(
        self,
        query: str,
        original_query: str,
        intents: list[str],
        session_id: str = "default",
        language: str = "en",
        entities: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute a multi-intent plan.

        Args:
            query: Processed (translated-to-English) query.
            original_query: Raw user query (for display).
            intents: List of intent strings detected by Router.
            session_id: Session identifier.
            language: Output language ('en' or 'ml').
            entities: Extracted entities from Gemini classify_intent.

        Returns:
            Merged agent response dict.
        """
        # Order intents logically
        ordered = _order_intents(intents)[:_MAX_PLAN_STEPS]
        logger.info("PlannerAgent: executing plan %s for session=%s", ordered, session_id)

        profile = MemoryManager.get_profile(session_id)
        results: list[dict[str, Any]] = []
        all_structured_data: dict[str, Any] = {}

        # ── Execute each step ────────────────────────────────────────────────
        for intent in ordered:
            try:
                agent = _get_agent_for_intent(intent)
                if agent is None:
                    continue

                step_result = agent.run(
                    query=query,
                    session_id=session_id,
                    language="en",  # Always process in English; translate at the end
                    entities=entities or {},
                )
                results.append(step_result)

                # Collect structured data by intent
                all_structured_data[intent] = step_result.get("structured_data", {})
                logger.debug("PlannerAgent: completed step %s", intent)

            except Exception as exc:
                logger.error("PlannerAgent: step %s failed: %s", intent, exc)
                continue

        if not results:
            text = "I encountered an issue processing your request. Please try again."
            if language == "ml":
                text = self._gemini.translate_to_malayalam(text)
            return _build_plan_response(
                language=language,
                text=text,
                plan=ordered,
                structured_data={},
                follow_ups=[],
            )

        # ── Synthesise merged response ─────────────────────────────────────
        merged_text = self._synthesize(
            original_query=original_query,
            plan=ordered,
            results=results,
            language=language,
            profile=profile,
        )

        # Collect all follow-ups from sub-agents (deduplicated)
        all_follow_ups: list[str] = []
        seen: set[str] = set()
        for r in results:
            for f in r.get("follow_up_suggestions", []):
                if f not in seen:
                    all_follow_ups.append(f)
                    seen.add(f)

        # Save merged response to memory
        MemoryManager.append_conversation(
            session_id, "assistant",
            merged_text[:800],
            agent=self.name,
        )

        return _build_plan_response(
            language=language,
            text=merged_text,
            plan=ordered,
            structured_data=all_structured_data,
            follow_ups=all_follow_ups[:4],
        )

    def _synthesize(
        self,
        original_query: str,
        plan: list[str],
        results: list[dict],
        language: str,
        profile: dict,
    ) -> str:
        """
        Use Gemini to synthesize a coherent merged response from multiple agent outputs.
        Falls back to concatenated summaries if Gemini fails.
        """
        # Build context from each agent's response
        context_parts = []
        for result in results:
            intent = result.get("intent", "")
            text = result.get("response_text", "")
            if text:
                label = _intent_label(intent)
                context_parts.append(f"### {label}\n{text[:500]}")

        context = "\n\n".join(context_parts)

        profile_note = ""
        if profile.get("marks"):
            profile_note = f"Student marks: {profile['marks']}%. "
        if profile.get("state"):
            profile_note += f"State: {profile['state']}. "

        prompt = (
            f"You are Vidya AI, a comprehensive career counselor for Indian students.\n"
            f"{profile_note}\n"
            f"The student asked: '{original_query}'\n\n"
            f"You gathered information from multiple specialized agents:\n\n"
            f"{context}\n\n"
            f"Now write ONE cohesive, well-structured response that:\n"
            f"1. Directly addresses the student's full question\n"
            f"2. Presents each topic (career, college, scholarship, roadmap) in clear sections\n"
            f"3. Uses encouraging, friendly language for a student audience\n"
            f"4. Keeps the total response under 400 words\n"
            f"{'5. Write in Malayalam but keep technical terms, college names, and amounts in English.' if language == 'ml' else '5. Write in English.'}\n\n"
            f"Response:"
        )

        result = self._gemini._generate(prompt, temperature=0.5)
        if result:
            return result

        # Fallback: join individual responses with section headers
        sections = []
        for r in results:
            label = _intent_label(r.get("intent", ""))
            text = r.get("response_text", "")
            if text:
                sections.append(f"**{label}**\n{text[:300]}")
        merged = "\n\n".join(sections)

        if language == "ml":
            merged = self._gemini.translate_to_malayalam(merged)

        return merged or "Here is a comprehensive response to your question."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _order_intents(intents: list[str]) -> list[str]:
    """Sort intents by logical execution order."""
    return sorted(intents, key=lambda i: _EXECUTION_ORDER.index(i) if i in _EXECUTION_ORDER else 99)


def _get_agent_for_intent(intent: str):
    """Lazy-import the correct agent for each intent."""
    try:
        if intent == "career_guidance":
            from agents.career_agent import CareerAgent
            return CareerAgent()
        elif intent == "college_recommendation":
            from agents.college_agent import CollegeAgent
            return CollegeAgent()
        elif intent == "scholarship_search":
            from agents.scholarship_agent import ScholarshipAgent
            return ScholarshipAgent()
        elif intent == "skill_gap_analysis":
            from agents.skill_gap_agent import SkillGapAgent
            return SkillGapAgent()
        elif intent == "roadmap_generation":
            from agents.roadmap_agent import RoadmapAgent
            return RoadmapAgent()
        else:
            return None
    except Exception as exc:
        logger.error("Failed to instantiate agent for %s: %s", intent, exc)
        return None


def _intent_label(intent: str) -> str:
    labels = {
        "career_guidance": "🎯 Career Recommendations",
        "college_recommendation": "🏫 College Options",
        "scholarship_search": "🎓 Scholarships",
        "skill_gap_analysis": "📊 Skill Gap Analysis",
        "roadmap_generation": "🗺️ Learning Roadmap",
        "general_help": "ℹ️ General Information",
    }
    return labels.get(intent, intent.replace("_", " ").title())


def _build_plan_response(
    language: str,
    text: str,
    plan: list[str],
    structured_data: dict,
    follow_ups: list[str],
) -> dict[str, Any]:
    return {
        "agent_used": "planner_agent",
        "intent": "multi_intent",
        "language": language,
        "response_text": text,
        "plan_executed": plan,
        "structured_data": structured_data,
        "follow_up_suggestions": follow_ups,
    }
