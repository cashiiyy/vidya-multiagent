"""
Pydantic models for Vidya AI – type-safe data contracts across agents and MCP tools.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ─────────────────────────────────────────────────────────────

class LanguageCode(str, Enum):
    ENGLISH = "en"
    MALAYALAM = "ml"


class IntentType(str, Enum):
    CAREER_GUIDANCE = "career_guidance"
    COLLEGE_RECOMMENDATION = "college_recommendation"
    SCHOLARSHIP_SEARCH = "scholarship_search"
    SKILL_GAP_ANALYSIS = "skill_gap_analysis"
    ROADMAP_GENERATION = "roadmap_generation"
    GENERAL_HELP = "general_help"


# ── Career Models ─────────────────────────────────────────────────────────────

class SalaryRange(BaseModel):
    min: int = Field(..., description="Minimum annual salary in INR")
    max: int = Field(..., description="Maximum annual salary in INR")
    currency: str = Field(default="INR")

    @property
    def display(self) -> str:
        def fmt(n: int) -> str:
            if n >= 100000:
                return f"₹{n/100000:.1f}L"
            return f"₹{n:,}"
        return f"{fmt(self.min)} – {fmt(self.max)} per year"


class CareerResult(BaseModel):
    id: str
    career_name: str
    description: str
    salary_range: SalaryRange
    required_skills: list[str]
    future_demand: str
    education_path: list[str]
    category: str
    job_roles: list[str] = Field(default_factory=list)
    top_recruiters: list[str] = Field(default_factory=list)

    @field_validator("future_demand")
    @classmethod
    def validate_demand(cls, v: str) -> str:
        allowed = {"Very High", "High", "Moderate", "Stable", "Low"}
        if v not in allowed:
            raise ValueError(f"future_demand must be one of {allowed}")
        return v


# ── College Models ────────────────────────────────────────────────────────────

class Fees(BaseModel):
    per_year: int
    currency: str = "INR"

    @property
    def display(self) -> str:
        return f"₹{self.per_year:,}/year"


class CollegeResult(BaseModel):
    id: str
    college_name: str
    state: str
    city: str
    courses: list[str]
    fees: Fees
    ranking: int
    type: str
    eligibility: str
    website: str
    established: int = Field(default=0)
    naac_grade: str = Field(default="")


# ── Scholarship Models ────────────────────────────────────────────────────────

class ScholarshipResult(BaseModel):
    id: str
    scholarship_name: str
    eligibility: str
    amount: str
    deadline: str
    category: str
    state: str
    website: str
    ministry: str
    renewable: bool


# ── Skill Models ──────────────────────────────────────────────────────────────

class LearningResource(BaseModel):
    title: str
    url: str
    free: bool = True


class SkillInfo(BaseModel):
    id: str
    skill_name: str
    category: str
    level: str
    learning_resources: list[LearningResource] = Field(default_factory=list)
    related_careers: list[str] = Field(default_factory=list)


# ── Roadmap Models ────────────────────────────────────────────────────────────

class RoadmapStep(BaseModel):
    month: int = Field(..., ge=1)
    title: str
    skills_to_learn: list[str]
    resources: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    estimated_hours: int = Field(default=40)


class Roadmap(BaseModel):
    career_name: str
    total_months: int
    steps: list[RoadmapStep]
    certifications: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


# ── Skill Gap Models ──────────────────────────────────────────────────────────

class SkillGapItem(BaseModel):
    skill_name: str
    status: str  # "have" | "missing" | "partial"
    proficiency_needed: str = Field(default="Intermediate")
    resources: list[LearningResource] = Field(default_factory=list)


class SkillGapAnalysis(BaseModel):
    target_career: str
    current_skills: list[str]
    required_skills: list[str]
    gap_items: list[SkillGapItem]
    readiness_percentage: float = Field(..., ge=0.0, le=100.0)
    estimated_learning_months: int


# ── Agent Response ────────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    intent: IntentType
    language: LanguageCode = LanguageCode.ENGLISH
    agent_used: str
    response_text: str
    structured_data: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)


# ── Router Models ─────────────────────────────────────────────────────────────

class RouterDecision(BaseModel):
    intent: IntentType
    language: LanguageCode
    confidence: float = Field(..., ge=0.0, le=1.0)
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    original_query: str
