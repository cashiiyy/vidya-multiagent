"""
FastAPI MCP Server for Vidya AI.
Exposes all 9 MCP tools (5 local + 4 Gemini-powered) as REST endpoints
plus an MCP protocol discovery endpoint.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp_server.config import config
from mcp_server.tools import (
    career_lookup,
    college_lookup,
    scholarship_lookup,
    skill_lookup,
    roadmap_generator,
)
from mcp_server.google_tools import (
    search_web,
    google_custom_search,
    fetch_college_information,
    check_scholarship_deadlines,
    career_market_trends,
)
from utils.security import validate_mcp_request, get_gemini_safety_config

logger = logging.getLogger(__name__)


# ── Request / Response Models ─────────────────────────────────────────────────

class CareerLookupRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    category: str | None = Field(None, description="STEM, Arts, Commerce, Health, Law")
    limit: int = Field(default=5, ge=1, le=20)


class CollegeLookupRequest(BaseModel):
    state: str | None = None
    course: str | None = None
    college_type: str | None = None
    max_fee_per_year: int | None = Field(None, ge=0)
    limit: int = Field(default=10, ge=1, le=30)


class ScholarshipLookupRequest(BaseModel):
    category: str | None = None
    state: str | None = None
    limit: int = Field(default=10, ge=1, le=30)


class SkillLookupRequest(BaseModel):
    career_name: str | None = None
    career_id: str | None = None
    current_skills: list[str] | None = None


class RoadmapRequest(BaseModel):
    career_name: str = Field(..., min_length=1, max_length=200)
    current_skills: list[str] | None = None
    duration_months: int = Field(default=12, ge=3, le=24)


class SearchWebRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    context: str = Field(default="Indian education and career guidance")
    num_results: int = Field(default=5, ge=1, le=10)


class CustomSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    num_results: int = Field(default=10, ge=1, le=10)
    start_index: int = Field(default=1, ge=1)
    safe_search: str = Field(default="active")


class CollegeInfoRequest(BaseModel):
    college_name: str = Field(..., min_length=1, max_length=300)
    info_type: str = Field(default="general")


class ScholarshipDeadlineRequest(BaseModel):
    scholarship_names: list[str] = Field(..., min_items=1, max_items=10)


class CareerTrendsRequest(BaseModel):
    career_name: str = Field(..., min_length=1, max_length=200)
    region: str = Field(default="India")


# ── App Lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Vidya AI MCP Server starting up...")
    # Pre-load datasets into cache
    try:
        from utils.data_loader import DataLoader
        DataLoader.get_careers()
        DataLoader.get_colleges()
        DataLoader.get_scholarships()
        logger.info("✅ Datasets loaded into cache")
    except Exception as exc:
        logger.warning("Dataset pre-load failed: %s", exc)
    yield
    logger.info("🛑 Vidya AI MCP Server shutting down")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=config.api_title,
    version=config.api_version,
    description=config.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{duration:.3f}s"
    return response


# ── Health & Discovery ────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "service": "Vidya AI MCP Server", "version": config.api_version}


@app.get("/mcp/tools", tags=["MCP Protocol"])
async def list_mcp_tools():
    """
    MCP Protocol: Tool discovery endpoint.
    Returns all available tools with their schemas.
    """
    return {
        "tools": [
            {
                "name": "career_lookup",
                "description": "Search for careers matching student interests or keywords.",
                "input_schema": {"query": "string", "category": "string|null", "limit": "int"},
                "endpoint": "/tools/career_lookup",
            },
            {
                "name": "college_lookup",
                "description": "Find colleges by state, course, type, and fee.",
                "input_schema": {"state": "string|null", "course": "string|null", "college_type": "string|null", "max_fee_per_year": "int|null"},
                "endpoint": "/tools/college_lookup",
            },
            {
                "name": "scholarship_lookup",
                "description": "Search scholarships by category and state.",
                "input_schema": {"category": "string|null", "state": "string|null"},
                "endpoint": "/tools/scholarship_lookup",
            },
            {
                "name": "skill_lookup",
                "description": "Get required skills for a career and compute skill gap.",
                "input_schema": {"career_name": "string|null", "career_id": "string|null", "current_skills": "list[string]|null"},
                "endpoint": "/tools/skill_lookup",
            },
            {
                "name": "roadmap_generator",
                "description": "Generate a month-by-month learning roadmap for a target career.",
                "input_schema": {"career_name": "string", "current_skills": "list[string]|null", "duration_months": "int"},
                "endpoint": "/tools/roadmap_generator",
            },
            {
                "name": "search_web",
                "description": "Search for education/career information using Gemini knowledge or CSE.",
                "input_schema": {"query": "string", "num_results": "int"},
                "endpoint": "/tools/search_web",
            },
            {
                "name": "google_custom_search",
                "description": "Raw Google Custom Search with full metadata and pagination (requires CSE keys).",
                "input_schema": {"query": "string", "num_results": "int", "start_index": "int", "safe_search": "string"},
                "endpoint": "/tools/google_custom_search",
            },
            {
                "name": "fetch_college_information",
                "description": "Get detailed info about a specific college using Gemini.",
                "input_schema": {"college_name": "string", "info_type": "string"},
                "endpoint": "/tools/fetch_college_information",
            },
            {
                "name": "check_scholarship_deadlines",
                "description": "Check deadlines and urgency for specific scholarships.",
                "input_schema": {"scholarship_names": "list[string]"},
                "endpoint": "/tools/check_scholarship_deadlines",
            },
            {
                "name": "career_market_trends",
                "description": "Get current job market trends for a career in India.",
                "input_schema": {"career_name": "string", "region": "string"},
                "endpoint": "/tools/career_market_trends",
            },
        ]
    }


# ── Local Data Tools ──────────────────────────────────────────────────────────

@app.post("/tools/career_lookup", tags=["Local Tools"])
async def api_career_lookup(req: CareerLookupRequest) -> dict[str, Any]:
    """Search careers by keyword or interest area."""
    return career_lookup(query=req.query, category=req.category, limit=req.limit)


@app.post("/tools/college_lookup", tags=["Local Tools"])
async def api_college_lookup(req: CollegeLookupRequest) -> dict[str, Any]:
    """Find colleges by state, course, type, and fee."""
    return college_lookup(
        state=req.state,
        course=req.course,
        college_type=req.college_type,
        max_fee_per_year=req.max_fee_per_year,
        limit=req.limit,
    )


@app.post("/tools/scholarship_lookup", tags=["Local Tools"])
async def api_scholarship_lookup(req: ScholarshipLookupRequest) -> dict[str, Any]:
    """Search scholarships by category and state."""
    return scholarship_lookup(category=req.category, state=req.state, limit=req.limit)


@app.post("/tools/skill_lookup", tags=["Local Tools"])
async def api_skill_lookup(req: SkillLookupRequest) -> dict[str, Any]:
    """Get required skills for a career and compute skill gap."""
    return skill_lookup(
        career_name=req.career_name,
        career_id=req.career_id,
        current_skills=req.current_skills,
    )


@app.post("/tools/roadmap_generator", tags=["Local Tools"])
async def api_roadmap_generator(req: RoadmapRequest) -> dict[str, Any]:
    """Generate a personalized learning roadmap."""
    return roadmap_generator(
        career_name=req.career_name,
        current_skills=req.current_skills,
        duration_months=req.duration_months,
    )


# ── Gemini-Powered Tools ──────────────────────────────────────────────────────

@app.post("/tools/search_web", tags=["Google Tools"])
async def api_search_web(req: SearchWebRequest) -> dict[str, Any]:
    """Search for education/career information using Gemini knowledge or CSE fallback."""
    return search_web(query=req.query, context=req.context, num_results=req.num_results)


@app.post("/tools/google_custom_search", tags=["Google Tools"])
async def api_google_custom_search(req: CustomSearchRequest) -> dict[str, Any]:
    """Direct Google Custom Search with full metadata."""
    return google_custom_search(
        query=req.query,
        num_results=req.num_results,
        start_index=req.start_index,
        safe_search=req.safe_search,
    )


@app.post("/tools/fetch_college_information", tags=["Google Tools"])
async def api_fetch_college_info(req: CollegeInfoRequest) -> dict[str, Any]:
    """Get detailed info about a specific college."""
    return fetch_college_information(
        college_name=req.college_name,
        info_type=req.info_type,
    )


@app.post("/tools/check_scholarship_deadlines", tags=["Google Tools"])
async def api_check_deadlines(req: ScholarshipDeadlineRequest) -> dict[str, Any]:
    """Check deadlines and urgency for specific scholarships."""
    return check_scholarship_deadlines(scholarship_names=req.scholarship_names)


@app.post("/tools/career_market_trends", tags=["Google Tools"])
async def api_career_trends(req: CareerTrendsRequest) -> dict[str, Any]:
    """Get current job market trends for a career in India."""
    return career_market_trends(career_name=req.career_name, region=req.region)


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error. Please try again."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_server.server:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        log_level=config.log_level,
    )
