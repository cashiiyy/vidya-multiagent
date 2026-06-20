"""
Scholarship Finder Skill – ADK-compatible skill for scholarship discovery.
Wraps mcp_server/tools.py:scholarship_lookup() with deadline urgency sorting.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from mcp_server.tools import scholarship_lookup

logger = logging.getLogger(__name__)

_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


class ScholarshipFinderSkill:
    """
    ADK Skill: Scholarship Finder

    Searches scholarships by category and state, then sorts by deadline urgency.
    """

    name: str = "scholarship_finder"
    description: str = (
        "Finds government and private scholarships for Indian students based on "
        "category (SC/ST/OBC/Merit/Girl) and state. Sorts by deadline urgency."
    )

    def run(
        self,
        category: str | None = None,
        state: str | None = None,
        limit: int = 8,
        student_profile: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute the scholarship finder skill.

        Args:
            category: Scholarship category (SC, ST, OBC, Merit, Girl, Research, Need-based).
            state: Student's state for state-specific scholarships.
            limit: Max scholarships to return.
            student_profile: Optional student context for auto-filling category/state.

        Returns:
            Structured dict with ranked scholarships sorted by deadline urgency.
        """
        # Fill from profile if not provided
        if student_profile:
            category = category or student_profile.get("category")
            state = state or student_profile.get("state")

        logger.info(
            "ScholarshipFinderSkill.run: category=%r state=%r", category, state
        )

        tool_result = scholarship_lookup(
            category=category, state=state, limit=limit
        )

        if not tool_result.get("success") or not tool_result.get("scholarships"):
            return {
                "success": False,
                "scholarships": [],
                "summary": "No scholarships found. Try 'Merit', 'SC', 'ST', 'OBC', or 'Girl' categories.",
                "urgent": [],
                "tips": [],
            }

        scholarships = tool_result["scholarships"]

        # Add urgency scoring and sort
        now = datetime.utcnow()
        for s in scholarships:
            s["urgency_score"] = _deadline_urgency(s.get("deadline", ""), now)
        scholarships.sort(key=lambda x: x["urgency_score"], reverse=True)

        # Build summary
        top = scholarships[:4]
        summary_lines = ["🎓 Scholarships found for you:"]
        for i, s in enumerate(top, 1):
            urgency_tag = "⚠️ URGENT" if s["urgency_score"] > 80 else ""
            summary_lines.append(
                f"{i}. **{s['scholarship_name']}** | {s['amount']} | Deadline: {s['deadline']} {urgency_tag}"
            )

        # Urgent scholarships (deadline this month or next)
        urgent = [
            s["scholarship_name"]
            for s in scholarships
            if s["urgency_score"] > 70
        ]

        tips = [
            "Apply through https://scholarships.gov.in for all central government scholarships",
            "Keep income certificate, caste certificate, and mark sheets ready",
            "Apply before deadlines — most scholarships do NOT accept late applications",
            "You can apply for multiple scholarships simultaneously",
        ]

        return {
            "success": True,
            "scholarships": scholarships,
            "total_found": tool_result.get("total_found", len(scholarships)),
            "summary": "\n".join(summary_lines),
            "urgent_scholarships": urgent,
            "tips": tips,
        }

    def __call__(self, **kwargs) -> dict[str, Any]:
        return self.run(**kwargs)


def _deadline_urgency(deadline_str: str, now: datetime) -> int:
    """
    Return urgency score 0–100. Higher = more urgent (deadline sooner).
    """
    if not deadline_str or deadline_str.lower() in ("varies", "as per schedule", "as per state schedule"):
        return 30  # neutral

    dl_lower = deadline_str.lower()
    for month_name, month_num in _MONTH_MAP.items():
        if month_name in dl_lower:
            # Extract day if present
            day = 30
            import re
            day_match = re.search(r"\b(\d{1,2})\b", deadline_str)
            if day_match:
                day = int(day_match.group(1))

            current_month = now.month
            current_year = now.year

            # Determine the deadline year (assume current year; if past, use next year)
            try:
                dl_dt = datetime(current_year, month_num, min(day, 28))
            except ValueError:
                dl_dt = datetime(current_year, month_num, 28)

            if dl_dt < now:
                dl_dt = dl_dt.replace(year=current_year + 1)

            days_remaining = (dl_dt - now).days
            if days_remaining <= 7:
                return 100
            elif days_remaining <= 30:
                return 90
            elif days_remaining <= 60:
                return 70
            elif days_remaining <= 90:
                return 50
            else:
                return 20

    return 30


def scholarship_finder_skill(
    category: str | None = None,
    state: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    """
    ADK Tool: Find scholarships for Indian students based on eligibility.

    Args:
        category: Eligibility category - SC, ST, OBC, Merit, Girl, Research, Need-based.
        state: Student's home state (e.g., 'Kerala', 'Tamil Nadu').
        limit: Maximum scholarships to return (default 8).

    Returns:
        Scholarships sorted by deadline urgency with application tips.
    """
    skill = ScholarshipFinderSkill()
    return skill.run(category=category, state=state, limit=limit)
