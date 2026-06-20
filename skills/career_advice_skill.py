"""
Career Advice Skill – ADK-compatible skill for career guidance.
Wraps mcp_server/tools.py:career_lookup() and formats a rich response.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp_server.tools import career_lookup

logger = logging.getLogger(__name__)


class CareerAdviceSkill:
    """
    ADK Skill: Career Advice

    Agents invoke this skill to get structured career recommendations.
    The skill handles data fetching (via MCP tool) and formats the output
    into a structured dict that agents can use directly or pass to Gemini.

    Usage (inside an agent):
        skill = CareerAdviceSkill()
        result = skill.run(query="I love mathematics and AI", category="STEM")
    """

    name: str = "career_advice"
    description: str = (
        "Recommends careers based on student interests, skills, or educational background. "
        "Returns structured career data including salary, demand, and required skills."
    )

    def run(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
        student_profile: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the career advice skill.

        Args:
            query: Free-text describing interests or asking about careers.
            category: Optional STEM / Arts / Commerce / Health / Law filter.
            limit: Max careers to return.
            student_profile: Optional student context for personalization.

        Returns:
            Structured dict with 'careers', 'summary', and 'next_steps'.
        """
        logger.info("CareerAdviceSkill.run: query=%r category=%r", query, category)

        # Call MCP tool
        tool_result = career_lookup(query=query, category=category, limit=limit)

        if not tool_result.get("success") or not tool_result.get("careers"):
            return {
                "success": False,
                "careers": [],
                "summary": f"No careers found matching '{query}'. Try broader terms like 'engineering', 'medical', or 'arts'.",
                "next_steps": ["Try searching by interest area (e.g., 'I like computers')"],
            }

        careers = tool_result["careers"]

        # Build a formatted summary
        top = careers[:3]
        summary_lines = [f"🎯 Top career recommendations for '{query}':"]
        for i, c in enumerate(top, 1):
            salary = c.get("salary_range", {})
            min_s = salary.get("min", 0)
            max_s = salary.get("max", 0)
            salary_str = f"₹{min_s//100000:.0f}L–₹{max_s//100000:.0f}L/year"
            demand = c.get("future_demand", "Moderate")
            summary_lines.append(
                f"{i}. **{c['career_name']}** | {salary_str} | Demand: {demand}"
            )

        next_steps = [
            "Check the required skills for your top choice",
            "Look for colleges offering relevant courses",
            "Search for scholarships matching your profile",
        ]

        # Personalize if profile available
        if student_profile:
            state = student_profile.get("state")
            if state:
                next_steps.insert(0, f"Find engineering/medical colleges in {state}")

        return {
            "success": True,
            "careers": careers,
            "total_found": tool_result.get("total_found", len(careers)),
            "summary": "\n".join(summary_lines),
            "next_steps": next_steps,
        }

    def __call__(self, query: str, **kwargs) -> dict[str, Any]:
        """Make the skill directly callable as an ADK tool function."""
        return self.run(query=query, **kwargs)


# Module-level callable for ADK tool registration
def career_advice_skill(query: str, category: str | None = None, limit: int = 5) -> dict[str, Any]:
    """
    ADK Tool: Get career recommendations for a student based on their interests.

    Args:
        query: Student interests or career question (e.g., 'I love maths and AI').
        category: Career category filter: STEM, Arts, Commerce, Health, Law.
        limit: Maximum number of careers to return (default 5).

    Returns:
        Structured career recommendations with salary, demand, and skills.
    """
    skill = CareerAdviceSkill()
    return skill.run(query=query, category=category, limit=limit)
