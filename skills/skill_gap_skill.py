"""
Skill Gap Skill – ADK-compatible skill for skill gap analysis.
Wraps mcp_server/tools.py:skill_lookup() and generates a prose gap summary.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp_server.tools import skill_lookup

logger = logging.getLogger(__name__)


class SkillGapSkill:
    """
    ADK Skill: Skill Gap Analyzer

    Compares a student's current skills against a target career's requirements
    and returns a detailed gap analysis with learning resources.
    """

    name: str = "skill_gap_analysis"
    description: str = (
        "Analyzes the gap between a student's current skills and what's needed for "
        "a target career. Returns missing skills, readiness percentage, and resources."
    )

    def run(
        self,
        career_name: str,
        current_skills: list[str] | None = None,
        student_profile: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the skill gap analysis skill.

        Args:
            career_name: Target career (e.g., 'AI Engineer', 'Data Scientist').
            current_skills: Skills the student already has.
            student_profile: Optional student context.

        Returns:
            Structured gap analysis with readiness score and resources.
        """
        if current_skills is None:
            current_skills = []

        # Merge profile interests as implicit skills if available
        if student_profile:
            interests = student_profile.get("interests", [])
            current_skills = list(set(current_skills + interests))

        logger.info(
            "SkillGapSkill.run: career=%r current_skills=%r",
            career_name, current_skills,
        )

        tool_result = skill_lookup(
            career_name=career_name,
            current_skills=current_skills if current_skills else None,
        )

        if not tool_result.get("success"):
            return {
                "success": False,
                "summary": f"Could not find skill requirements for '{career_name}'. Try the full career name.",
                "gap_items": [],
                "readiness_percentage": 0.0,
                "missing_skills": [],
                "have_skills": [],
            }

        gap_items = tool_result.get("skill_gap", [])
        readiness = tool_result.get("readiness_percentage", 0.0)
        required = tool_result.get("required_skills", [])

        have = [g["skill_name"] for g in gap_items if g.get("status") == "have"]
        missing = [g["skill_name"] for g in gap_items if g.get("status") == "missing"]

        # Summary prose
        if not gap_items:
            summary = (
                f"📊 Skill analysis for **{career_name}**:\n"
                f"Required skills: {', '.join(required)}\n"
                f"Please provide your current skills for a gap analysis."
            )
        else:
            readiness_emoji = (
                "🟢" if readiness >= 70
                else "🟡" if readiness >= 40
                else "🔴"
            )
            summary_lines = [
                f"📊 Skill Gap Analysis for **{career_name}**",
                f"{readiness_emoji} Readiness: **{readiness:.0f}%**",
            ]
            if have:
                summary_lines.append(f"✅ Skills you have: {', '.join(have)}")
            if missing:
                summary_lines.append(f"❌ Skills to learn: {', '.join(missing)}")
            summary = "\n".join(summary_lines)

        # Top learning resources for missing skills
        top_resources: list[dict] = []
        for g in gap_items:
            if g.get("status") == "missing":
                for r in g.get("resources", [])[:2]:
                    top_resources.append({
                        "skill": g["skill_name"],
                        "resource": r.get("title", ""),
                        "url": r.get("url", ""),
                        "free": r.get("free", True),
                    })

        return {
            "success": True,
            "career_name": tool_result.get("career_name", career_name),
            "required_skills": required,
            "have_skills": have,
            "missing_skills": missing,
            "gap_items": gap_items,
            "readiness_percentage": readiness,
            "top_resources": top_resources[:6],
            "summary": summary,
            "motivation": _get_motivation(readiness, career_name),
        }

    def __call__(self, career_name: str, current_skills: list[str] | None = None, **kwargs) -> dict[str, Any]:
        return self.run(career_name=career_name, current_skills=current_skills, **kwargs)


def _get_motivation(readiness: float, career: str) -> str:
    if readiness >= 70:
        return f"You're well on your way to becoming a {career}! Focus on polishing the remaining skills."
    elif readiness >= 40:
        return f"Good foundation! With consistent effort over 6–12 months, you can bridge the gap for {career}."
    else:
        return (
            f"Every expert was once a beginner. Start with the foundational skills and "
            f"you'll be ready for a career as {career} sooner than you think!"
        )


def skill_gap_skill(
    career_name: str,
    current_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    ADK Tool: Analyze the skill gap between current skills and a target career.

    Args:
        career_name: Target career name (e.g., 'AI Engineer', 'Data Scientist').
        current_skills: List of skills the student currently has.

    Returns:
        Gap analysis with readiness percentage, missing skills, and learning resources.
    """
    skill = SkillGapSkill()
    return skill.run(career_name=career_name, current_skills=current_skills)
