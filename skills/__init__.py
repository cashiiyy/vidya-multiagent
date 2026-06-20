"""
Skills package – ADK-compatible skill modules for Vidya AI agents.
"""
from skills.career_advice_skill import CareerAdviceSkill
from skills.college_recommendation_skill import CollegeRecommendationSkill
from skills.scholarship_finder_skill import ScholarshipFinderSkill
from skills.skill_gap_skill import SkillGapSkill
from skills.roadmap_generation_skill import RoadmapGenerationSkill

__all__ = [
    "CareerAdviceSkill",
    "CollegeRecommendationSkill",
    "ScholarshipFinderSkill",
    "SkillGapSkill",
    "RoadmapGenerationSkill",
]
