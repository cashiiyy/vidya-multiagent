"""
Agents package for Vidya AI.
Exports all agents and provides a simple dispatch function.
"""
from agents.career_agent import CareerAgent
from agents.college_agent import CollegeAgent
from agents.scholarship_agent import ScholarshipAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.roadmap_agent import RoadmapAgent
from agents.router_agent import RouterAgent
from agents.planner_agent import PlannerAgent

__all__ = [
    "CareerAgent",
    "CollegeAgent",
    "ScholarshipAgent",
    "SkillGapAgent",
    "RoadmapAgent",
    "RouterAgent",
    "PlannerAgent",
]
