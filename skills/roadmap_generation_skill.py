"""
Roadmap Generation Skill – ADK-compatible skill for learning roadmap creation.
Wraps mcp_server/tools.py:roadmap_generator() and formats a milestone timeline.
"""
from __future__ import annotations

import logging
from typing import Any

from mcp_server.tools import roadmap_generator

logger = logging.getLogger(__name__)


class RoadmapGenerationSkill:
    """
    ADK Skill: Roadmap Generator

    Generates a month-by-month learning roadmap for a target career,
    accounting for skills the student already has.
    """

    name: str = "roadmap_generation"
    description: str = (
        "Generates a personalized step-by-step learning roadmap for a target career. "
        "Adapts to the student's current skill level and desired timeline."
    )

    def run(
        self,
        career_name: str,
        current_skills: list[str] | None = None,
        duration_months: int = 12,
        student_profile: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the roadmap generation skill.

        Args:
            career_name: Target career (e.g., 'AI Engineer').
            current_skills: Skills the student already has.
            duration_months: Total roadmap duration (3–24 months).
            student_profile: Optional student context.

        Returns:
            Structured roadmap with monthly milestones, resources, and tips.
        """
        if current_skills is None:
            current_skills = []

        # Pull skills from profile if available
        if student_profile:
            profile_interests = student_profile.get("interests", [])
            current_skills = list(set(current_skills + profile_interests))

        duration_months = max(3, min(24, duration_months))

        logger.info(
            "RoadmapGenerationSkill.run: career=%r duration=%d months",
            career_name, duration_months,
        )

        tool_result = roadmap_generator(
            career_name=career_name,
            current_skills=current_skills,
            duration_months=duration_months,
        )

        if not tool_result.get("success"):
            return {
                "success": False,
                "summary": f"Could not generate a roadmap for '{career_name}'.",
                "roadmap": [],
                "milestones": [],
            }

        roadmap_steps = tool_result.get("roadmap", [])
        certifications = tool_result.get("recommended_certifications", [])
        tips = tool_result.get("tips", [])

        # Build text summary of the roadmap
        summary_lines = [
            f"🗺️ **{duration_months}-Month Roadmap to Become a {career_name}**",
            "",
        ]

        # Group steps by phase
        phases: dict[str, list] = {}
        for step in roadmap_steps:
            phase = step.get("phase", "Learning")
            phases.setdefault(phase, []).append(step)

        for phase_name, steps in phases.items():
            months = [str(s["month"]) for s in steps]
            skills_in_phase = []
            for s in steps:
                skills_in_phase.extend(s.get("skills_to_learn", []))
            skills_in_phase = list(dict.fromkeys(skills_in_phase))  # deduplicate
            summary_lines.append(
                f"**Phase: {phase_name}** (Month{'s' if len(months) > 1 else ''} {', '.join(months)})"
            )
            if skills_in_phase:
                summary_lines.append(f"  → Learn: {', '.join(skills_in_phase[:4])}")

        if certifications:
            summary_lines.append(f"\n🏆 Target Certifications: {', '.join(certifications[:3])}")

        # Key milestones (one per phase)
        milestones = []
        for step in roadmap_steps:
            for m in step.get("milestones", [])[:1]:
                milestones.append({"month": step["month"], "milestone": m})

        return {
            "success": True,
            "career_name": tool_result.get("career_name", career_name),
            "duration_months": duration_months,
            "roadmap": roadmap_steps,
            "skills_to_learn": tool_result.get("skills_to_learn", []),
            "skills_already_have": tool_result.get("skills_already_have", []),
            "recommended_certifications": certifications,
            "key_milestones": milestones,
            "tips": tips,
            "summary": "\n".join(summary_lines),
        }

    def __call__(self, career_name: str, **kwargs) -> dict[str, Any]:
        return self.run(career_name=career_name, **kwargs)


def roadmap_generation_skill(
    career_name: str,
    current_skills: list[str] | None = None,
    duration_months: int = 12,
) -> dict[str, Any]:
    """
    ADK Tool: Generate a personalized learning roadmap for a target career.

    Args:
        career_name: Target career name (e.g., 'AI Engineer', 'Data Scientist').
        current_skills: Skills the student already has (to skip already-known topics).
        duration_months: Total roadmap length in months (3–24, default 12).

    Returns:
        Month-by-month roadmap with skills, resources, milestones, and certifications.
    """
    skill = RoadmapGenerationSkill()
    return skill.run(
        career_name=career_name,
        current_skills=current_skills,
        duration_months=duration_months,
    )
