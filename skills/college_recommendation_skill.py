"""
College Recommendation Skill – ADK-compatible skill for college search.
Wraps mcp_server/tools.py:college_lookup() with scoring and eligibility logic.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp_server.tools import college_lookup

logger = logging.getLogger(__name__)


class CollegeRecommendationSkill:
    """
    ADK Skill: College Recommendation

    Filters and ranks colleges based on state, course, marks, and type preference.
    """

    name: str = "college_recommendation"
    description: str = (
        "Recommends colleges in India based on student's state, course preference, "
        "marks percentage, and type (Government/Private). Returns ranked list with fees and eligibility."
    )

    def run(
        self,
        state: str | None = None,
        course: str | None = None,
        marks: float | None = None,
        college_type: str | None = None,
        max_fee: int | None = None,
        limit: int = 8,
        student_profile: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the college recommendation skill.

        Args:
            state: Target state (e.g., "Kerala", "Tamil Nadu").
            course: Course preference (e.g., "B.Tech", "MBBS", "BA").
            marks: Student's percentage (used to estimate eligibility).
            college_type: "Government", "Private", "Deemed", "Government-Aided".
            max_fee: Maximum annual fee in INR.
            limit: Max colleges to return.
            student_profile: Optional student context.

        Returns:
            Structured dict with ranked colleges and admission tips.
        """
        # Pull from profile if not explicitly provided
        if student_profile:
            state = state or student_profile.get("state")
            marks = marks or student_profile.get("marks")

        logger.info(
            "CollegeRecommendationSkill.run: state=%r course=%r marks=%r",
            state, course, marks,
        )

        tool_result = college_lookup(
            state=state,
            course=course,
            college_type=college_type,
            max_fee_per_year=max_fee,
            limit=limit,
        )

        if not tool_result.get("success") or not tool_result.get("colleges"):
            return {
                "success": False,
                "colleges": [],
                "summary": "No colleges found with the given criteria. Try broader filters.",
                "admission_tips": [],
            }

        colleges = tool_result["colleges"]

        # Estimate eligibility match if marks provided
        if marks is not None:
            for c in colleges:
                c["marks_eligible"] = _estimate_eligibility(c, marks)

        # Build summary
        top = colleges[:3]
        summary_lines = ["🏫 Top college recommendations:"]
        for i, c in enumerate(top, 1):
            fee = c.get("fees", {}).get("per_year", 0)
            fee_str = f"₹{fee:,}/year"
            ctype = c.get("type", "")
            rank = c.get("ranking", "")
            summary_lines.append(
                f"{i}. **{c['college_name']}**, {c.get('city', '')} ({ctype}) | {fee_str} | Rank #{rank}"
            )

        admission_tips = _get_admission_tips(course, state)

        return {
            "success": True,
            "colleges": colleges,
            "total_found": tool_result.get("total_found", len(colleges)),
            "summary": "\n".join(summary_lines),
            "admission_tips": admission_tips,
        }

    def __call__(self, **kwargs) -> dict[str, Any]:
        return self.run(**kwargs)


def _estimate_eligibility(college: dict, marks: float) -> bool:
    """Rough eligibility estimate based on college type and ranking."""
    rank = college.get("ranking", 50)
    ctype = college.get("type", "")
    if "IIT" in college.get("college_name", "") or rank <= 5:
        return marks >= 95
    elif "NIT" in college.get("college_name", "") or rank <= 20:
        return marks >= 85
    elif "Government" in ctype and rank <= 50:
        return marks >= 70
    else:
        return marks >= 60


def _get_admission_tips(course: str | None, state: str | None) -> list[str]:
    tips = []
    if course:
        c = course.lower()
        if "b.tech" in c or "engineering" in c:
            tips = [
                "Prepare for JEE Main (National) or state-level entrance like KEAM/TNEA",
                "Top government colleges fill up fast — apply early",
                "Government colleges offer similar quality at 5–10x lower cost than private",
            ]
        elif "mbbs" in c or "medical" in c:
            tips = [
                "NEET-UG is mandatory for all medical admissions in India",
                "Score 550+ for government medical college seats",
                "Apply for NEET counselling through MCC or state authority",
            ]
        elif "law" in c or "llb" in c:
            tips = [
                "Appear for CLAT for National Law Schools or state CEE for state colleges",
                "Top NLUs accept CLAT rank under 1000",
            ]
        else:
            tips = [
                "Apply through your state's common admission portal",
                "Check the official college website for exact cut-offs",
            ]
    if state:
        tips.append(f"In {state}, check the official state admission portal for merit lists and schedules.")
    return tips


def college_recommendation_skill(
    state: str | None = None,
    course: str | None = None,
    marks: float | None = None,
    college_type: str | None = None,
    max_fee: int | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    """
    ADK Tool: Find and rank colleges matching the student's criteria.

    Args:
        state: Student's preferred state (e.g., 'Kerala', 'Tamil Nadu').
        course: Preferred course (e.g., 'B.Tech', 'MBBS', 'BA').
        marks: Student's 12th / Plus Two percentage.
        college_type: Preference - 'Government', 'Private', 'Deemed', 'Government-Aided'.
        max_fee: Maximum annual tuition fee in INR.
        limit: Maximum colleges to return (default 8).

    Returns:
        Ranked colleges with fees, eligibility, and admission tips.
    """
    skill = CollegeRecommendationSkill()
    return skill.run(
        state=state, course=course, marks=marks,
        college_type=college_type, max_fee=max_fee, limit=limit,
    )
