"""
MCP Tool implementations for Vidya AI.
All tools are pure functions that take simple types and return dicts
so they can be called both from FastAPI endpoints and from ADK agents.
"""
from __future__ import annotations

import logging
from typing import Any

from utils.data_loader import DataLoader

logger = logging.getLogger(__name__)


# ── Tool 1: career_lookup ─────────────────────────────────────────────────────

def career_lookup(
    query: str,
    category: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Search for careers matching a query string.

    Args:
        query: Free-text search (e.g., "AI", "mathematics", "doctor").
        category: Optional filter – one of STEM, Arts, Commerce, Health, Law.
        limit: Maximum number of results to return (default 5).

    Returns:
        dict with 'careers' list and 'total_found' count.
    """
    try:
        results = DataLoader.search_careers(query=query, category=category)
        results = results[:limit]
        return {
            "success": True,
            "query": query,
            "category_filter": category,
            "total_found": len(results),
            "careers": [r.model_dump() for r in results],
        }
    except Exception as exc:
        logger.error("career_lookup failed: %s", exc)
        return {"success": False, "error": str(exc), "careers": []}


# ── Tool 2: college_lookup ────────────────────────────────────────────────────

def college_lookup(
    state: str | None = None,
    course: str | None = None,
    college_type: str | None = None,
    max_fee_per_year: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Find colleges matching given criteria.

    Args:
        state: State name (e.g., "Kerala", "Tamil Nadu").
        course: Course name (e.g., "B.Tech", "MBBS", "BA").
        college_type: "Government", "Private", "Deemed", "Government-Aided".
        max_fee_per_year: Maximum annual fee in INR.
        limit: Max results to return.

    Returns:
        dict with 'colleges' list sorted by ranking.
    """
    try:
        results = DataLoader.filter_colleges(
            state=state,
            course=course,
            college_type=college_type,
            max_fee=max_fee_per_year,
        )
        results = results[:limit]
        return {
            "success": True,
            "filters": {
                "state": state,
                "course": course,
                "college_type": college_type,
                "max_fee_per_year": max_fee_per_year,
            },
            "total_found": len(results),
            "colleges": [c.model_dump() for c in results],
        }
    except Exception as exc:
        logger.error("college_lookup failed: %s", exc)
        return {"success": False, "error": str(exc), "colleges": []}


# ── Tool 3: scholarship_lookup ────────────────────────────────────────────────

def scholarship_lookup(
    category: str | None = None,
    state: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Search for scholarships matching eligibility criteria.

    Args:
        category: Scholarship category (e.g., "SC", "ST", "OBC", "Merit", "Girl", "Research").
        state: State name for state-specific scholarships (use "All India" for national ones).
        limit: Max results.

    Returns:
        dict with 'scholarships' list.
    """
    try:
        results = DataLoader.filter_scholarships(category=category, state=state)
        results = results[:limit]
        return {
            "success": True,
            "filters": {"category": category, "state": state},
            "total_found": len(results),
            "scholarships": [s.model_dump() for s in results],
        }
    except Exception as exc:
        logger.error("scholarship_lookup failed: %s", exc)
        return {"success": False, "error": str(exc), "scholarships": []}


# ── Tool 4: skill_lookup ──────────────────────────────────────────────────────

def skill_lookup(
    career_name: str | None = None,
    career_id: str | None = None,
    current_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get required skills for a career and compute skill gap if current_skills provided.

    Args:
        career_name: Career name to look up (e.g., "AI Engineer").
        career_id: Direct career ID (e.g., "c001"). Takes priority over career_name.
        current_skills: List of skills the student already has.

    Returns:
        dict with required skills, gap analysis, and learning resources.
    """
    try:
        careers = DataLoader.get_careers()

        # Resolve career
        career = None
        if career_id:
            career = next((c for c in careers if c.id == career_id), None)
        if career is None and career_name:
            name_lower = career_name.lower()
            career = next(
                (c for c in careers if name_lower in c.career_name.lower()), None
            )

        if career is None:
            return {
                "success": False,
                "error": f"Career not found: {career_name or career_id}",
                "skills": [],
            }

        required_skills = DataLoader.get_skills_for_career(career.id)
        required_skill_names = [s.skill_name for s in required_skills]

        gap: list[dict] = []
        readiness_pct = 0.0

        if current_skills is not None:
            current_lower = {s.lower() for s in current_skills}
            have, missing = [], []
            for skill in required_skills:
                if skill.skill_name.lower() in current_lower:
                    have.append(skill.skill_name)
                    gap.append({
                        "skill_name": skill.skill_name,
                        "status": "have",
                        "resources": [r.model_dump() for r in skill.learning_resources],
                    })
                else:
                    missing.append(skill.skill_name)
                    gap.append({
                        "skill_name": skill.skill_name,
                        "status": "missing",
                        "resources": [r.model_dump() for r in skill.learning_resources],
                    })

            total = len(required_skills)
            readiness_pct = round((len(have) / total * 100) if total > 0 else 0.0, 1)

        return {
            "success": True,
            "career_name": career.career_name,
            "career_id": career.id,
            "required_skills": required_skill_names,
            "skill_gap": gap,
            "readiness_percentage": readiness_pct,
        }
    except Exception as exc:
        logger.error("skill_lookup failed: %s", exc)
        return {"success": False, "error": str(exc), "skills": []}


# ── Tool 5: roadmap_generator ─────────────────────────────────────────────────

def roadmap_generator(
    career_name: str,
    current_skills: list[str] | None = None,
    duration_months: int = 12,
) -> dict[str, Any]:
    """
    Generate a month-by-month learning roadmap for a target career.

    Args:
        career_name: Target career (e.g., "AI Engineer", "Data Scientist").
        current_skills: Skills the student already has (to skip covered topics).
        duration_months: Total roadmap duration (6–24 months, default 12).

    Returns:
        dict with a structured roadmap containing monthly milestones.
    """
    try:
        duration_months = max(3, min(24, duration_months))
        current_skills = current_skills or []

        # Find career
        careers = DataLoader.get_careers()
        career = next(
            (c for c in careers if career_name.lower() in c.career_name.lower()),
            None,
        )

        if career is None:
            # Generic roadmap
            return _generic_roadmap(career_name, duration_months)

        # Get missing skills
        required_skills_info = DataLoader.get_skills_for_career(career.id)
        current_lower = {s.lower() for s in current_skills}

        missing_skills = [
            s for s in required_skills_info
            if s.skill_name.lower() not in current_lower
        ]
        have_skills = [
            s for s in required_skills_info
            if s.skill_name.lower() in current_lower
        ]

        # Build roadmap steps
        steps = []
        skills_per_month = max(1, len(missing_skills) // duration_months + 1)

        # Phase 1: Foundation (first 30% of months)
        foundation_months = max(1, duration_months // 3)
        for i in range(foundation_months):
            month = i + 1
            start_idx = i * skills_per_month
            end_idx = start_idx + skills_per_month
            batch = missing_skills[start_idx:end_idx]
            steps.append({
                "month": month,
                "phase": "Foundation",
                "title": f"Month {month}: Building the Foundation",
                "skills_to_learn": [s.skill_name for s in batch],
                "resources": [
                    res.url
                    for s in batch
                    for res in s.learning_resources[:2]
                ],
                "milestones": [
                    f"Complete introductory course for {s.skill_name}" for s in batch
                ],
                "estimated_hours": 40,
            })

        # Phase 2: Core (middle 40% of months)
        core_months = max(1, int(duration_months * 0.4))
        core_offset = foundation_months
        for i in range(core_months):
            month = core_offset + i + 1
            start_idx = (core_offset + i) * skills_per_month
            end_idx = start_idx + skills_per_month
            batch = missing_skills[start_idx:end_idx] if start_idx < len(missing_skills) else []
            steps.append({
                "month": month,
                "phase": "Core Development",
                "title": f"Month {month}: Core Skills & Projects",
                "skills_to_learn": [s.skill_name for s in batch],
                "resources": [
                    res.url
                    for s in batch
                    for res in s.learning_resources[:2]
                ],
                "milestones": [
                    f"Build a small project using {s.skill_name}" for s in batch
                ] + ["Complete 2 practice problems daily", "Join relevant communities (GitHub, Discord)"],
                "estimated_hours": 50,
            })

        # Phase 3: Advanced & Portfolio (remaining months)
        adv_start = foundation_months + core_months
        for i in range(duration_months - adv_start):
            month = adv_start + i + 1
            steps.append({
                "month": month,
                "phase": "Advanced & Portfolio",
                "title": f"Month {month}: Advanced Topics & Portfolio",
                "skills_to_learn": career.required_skills[-2:] if len(career.required_skills) > 2 else [],
                "resources": ["https://kaggle.com", "https://github.com", "https://leetcode.com"],
                "milestones": [
                    "Complete 1 end-to-end portfolio project",
                    "Contribute to an open-source project",
                    "Apply for internships or entry-level roles",
                    f"Prepare for relevant certifications in {career.career_name}",
                ],
                "estimated_hours": 60,
            })

        # Remove duplicates and ensure we have the right count
        steps = steps[:duration_months]

        return {
            "success": True,
            "career_name": career.career_name,
            "duration_months": duration_months,
            "skills_already_have": [s.skill_name for s in have_skills],
            "skills_to_learn": [s.skill_name for s in missing_skills],
            "roadmap": steps,
            "recommended_certifications": _get_certifications(career.career_name),
            "tips": [
                "Consistency beats intensity – dedicate 2 hours daily rather than weekend sprints.",
                "Build projects from Month 1, not just at the end.",
                "Connect with professionals on LinkedIn in your target field.",
                "Track your progress in a GitHub portfolio.",
                f"Consider joining communities related to {career.career_name}.",
            ],
        }
    except Exception as exc:
        logger.error("roadmap_generator failed: %s", exc)
        return {"success": False, "error": str(exc), "roadmap": []}


def _generic_roadmap(career_name: str, duration_months: int) -> dict[str, Any]:
    """Fallback roadmap for unknown careers."""
    steps = []
    for month in range(1, duration_months + 1):
        phase = (
            "Foundation" if month <= duration_months // 3
            else "Core Development" if month <= 2 * duration_months // 3
            else "Advanced & Portfolio"
        )
        steps.append({
            "month": month,
            "phase": phase,
            "title": f"Month {month}: {phase}",
            "skills_to_learn": ["Research relevant skills for this field"],
            "resources": ["https://coursera.org", "https://nptel.ac.in"],
            "milestones": [f"Complete one foundational course for {career_name}"],
            "estimated_hours": 40,
        })
    return {
        "success": True,
        "career_name": career_name,
        "duration_months": duration_months,
        "roadmap": steps,
        "recommended_certifications": [],
        "tips": [
            "Research industry leaders in this field on LinkedIn.",
            "Identify 3 skills most valued for this career and start there.",
            "Find a mentor or community in your target domain.",
        ],
    }


def _get_certifications(career_name: str) -> list[str]:
    """Return relevant certifications for popular careers."""
    certs_map: dict[str, list[str]] = {
        "AI Engineer": ["Google ML Engineer Certificate", "AWS ML Specialty", "DeepLearning.AI TensorFlow Developer"],
        "Data Scientist": ["Google Data Analytics Certificate", "IBM Data Science Professional", "Kaggle Competitions"],
        "Software Engineer": ["AWS Developer Associate", "Google Associate Cloud Engineer", "Microsoft AZ-900"],
        "Cybersecurity Analyst": ["CompTIA Security+", "CEH (Certified Ethical Hacker)", "CISSP"],
        "Cloud Architect": ["AWS Solutions Architect Professional", "GCP Professional Cloud Architect", "Azure Solutions Architect Expert"],
        "Digital Marketing Specialist": ["Google Digital Marketing Certificate", "HubSpot Marketing Certification", "Meta Blueprint"],
        "Data Scientist": ["Google Data Analytics", "IBM Data Science", "Microsoft DP-100"],
    }
    name_lower = career_name.lower()
    for key, certs in certs_map.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return certs
    return ["NPTEL Online Certifications", "Coursera Professional Certificates", "Google Career Certificates"]
