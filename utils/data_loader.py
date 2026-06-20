"""
Data loader – loads and caches JSON datasets with Pydantic validation.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from utils.pydantic_models import CareerResult, CollegeResult, ScholarshipResult, SkillInfo

logger = logging.getLogger(__name__)

# Resolve data directory relative to this file's location
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> Any:
    """Load a JSON file from the data directory."""
    path = _DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class DataLoader:
    """Thread-safe singleton data loader with in-memory caching."""

    _careers: list[CareerResult] | None = None
    _colleges: list[CollegeResult] | None = None
    _scholarships: list[ScholarshipResult] | None = None
    _skills_raw: dict | None = None

    @classmethod
    def get_careers(cls) -> list[CareerResult]:
        if cls._careers is None:
            raw = _load_json("careers.json")
            cls._careers = [CareerResult(**item) for item in raw]
            logger.info("Loaded %d careers", len(cls._careers))
        return cls._careers

    @classmethod
    def get_colleges(cls) -> list[CollegeResult]:
        if cls._colleges is None:
            raw = _load_json("colleges.json")
            cls._colleges = [CollegeResult(**item) for item in raw]
            logger.info("Loaded %d colleges", len(cls._colleges))
        return cls._colleges

    @classmethod
    def get_scholarships(cls) -> list[ScholarshipResult]:
        if cls._scholarships is None:
            raw = _load_json("scholarships.json")
            cls._scholarships = [ScholarshipResult(**item) for item in raw]
            logger.info("Loaded %d scholarships", len(cls._scholarships))
        return cls._scholarships

    @classmethod
    def get_skills(cls) -> list[SkillInfo]:
        if cls._skills_raw is None:
            cls._skills_raw = _load_json("skills.json")
        return [SkillInfo(**s) for s in cls._skills_raw.get("skills", [])]

    @classmethod
    def get_career_skill_map(cls) -> dict[str, list[str]]:
        if cls._skills_raw is None:
            cls._skills_raw = _load_json("skills.json")
        return cls._skills_raw.get("career_skill_map", {})

    @classmethod
    def search_careers(cls, query: str, category: str | None = None) -> list[CareerResult]:
        """Fuzzy search careers by name, description, or skills."""
        query_lower = query.lower()
        results = []
        for career in cls.get_careers():
            # Match on name, description, or required skills
            name_match = query_lower in career.career_name.lower()
            desc_match = query_lower in career.description.lower()
            skill_match = any(query_lower in s.lower() for s in career.required_skills)
            role_match = any(query_lower in r.lower() for r in career.job_roles)
            cat_match = (category is None) or (
                category.lower() == career.category.lower()
            )
            if (name_match or desc_match or skill_match or role_match) and cat_match:
                results.append(career)
        return results

    @classmethod
    def filter_colleges(
        cls,
        state: str | None = None,
        course: str | None = None,
        college_type: str | None = None,
        max_fee: int | None = None,
    ) -> list[CollegeResult]:
        """Filter colleges by state, course, type, and max fee."""
        results = cls.get_colleges()
        if state:
            results = [c for c in results if state.lower() in c.state.lower() or state.lower() in c.city.lower()]
        if course:
            results = [c for c in results if any(course.lower() in co.lower() for co in c.courses)]
        if college_type:
            results = [c for c in results if college_type.lower() in c.type.lower()]
        if max_fee is not None:
            results = [c for c in results if c.fees.per_year <= max_fee]
        # Sort by ranking
        return sorted(results, key=lambda c: c.ranking)

    @classmethod
    def filter_scholarships(
        cls,
        category: str | None = None,
        state: str | None = None,
    ) -> list[ScholarshipResult]:
        """Filter scholarships by category and state."""
        results = cls.get_scholarships()
        if category:
            results = [s for s in results if category.lower() in s.category.lower()]
        if state:
            results = [
                s for s in results
                if s.state == "All India"
                or (state.lower() in s.state.lower())
            ]
        return results

    @classmethod
    def get_skills_for_career(cls, career_id: str) -> list[SkillInfo]:
        """Return skill objects for a given career ID."""
        skill_map = cls.get_career_skill_map()
        skill_ids = skill_map.get(career_id, [])
        all_skills = cls.get_skills()
        return [s for s in all_skills if s.id in skill_ids]

    @classmethod
    def reload(cls) -> None:
        """Force reload of all datasets (for testing)."""
        cls._careers = None
        cls._colleges = None
        cls._scholarships = None
        cls._skills_raw = None
