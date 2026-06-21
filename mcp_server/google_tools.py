"""
Google-powered MCP Tools for Vidya AI.

search_web / google_custom_search use the Google Custom Search JSON API (CSE)
when GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID are present in the environment.
They fall back gracefully to Gemini-knowledge responses when credentials are
missing or the daily quota (100 free queries) is exhausted.

The remaining tools (fetch_college_information, check_scholarship_deadlines,
career_market_trends) continue to use Gemini for structured synthesis.

Architecture:
    Agent → ADK Skill → MCP Tool (google_tools.py) → CSE API / Gemini
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GEMINI_MODEL = "gemini-2.5-flash"
_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

# ── CSE credential helpers ────────────────────────────────────────────────────

def _cse_credentials() -> tuple[str, str] | None:
    """Return (api_key, cx) if both env vars are set, else None."""
    api_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    cx = os.getenv("GOOGLE_CSE_ID", "").strip()
    if api_key and cx:
        return api_key, cx
    return None


# ── Gemini fallback ───────────────────────────────────────────────────────────

def _gemini_generate(prompt: str, temperature: float = 0.3) -> str:
    """Shared Gemini call used by all google_tools."""
    try:
        import google.genai as genai  # type: ignore
        from google.genai import types  # type: ignore

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            try:
                import streamlit as st
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = st.secrets["GEMINI_API_KEY"]
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text.strip() if response.text else ""
    except Exception as exc:
        logger.error("Gemini call failed in google_tools: %s", exc)
        return ""


# ── CSE HTTP caller ───────────────────────────────────────────────────────────

def _cse_search(
    query: str,
    api_key: str,
    cx: str,
    num: int = 10,
    start: int = 1,
    safe: str = "active",
) -> dict[str, Any]:
    """
    Call the Google Custom Search JSON API and return the raw response dict.

    Raises:
        httpx.HTTPStatusError: on 4xx/5xx responses.
        Exception: on network or parse errors.
    """
    params: dict[str, Any] = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": min(num, 10),   # API max per page is 10
        "start": start,        # 1-indexed
        "safe": safe,
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.get(_CSE_ENDPOINT, params=params)
        resp.raise_for_status()
        return resp.json()


def _parse_cse_items(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract the useful fields from CSE response items."""
    items = raw.get("items", [])
    results = []
    for item in items:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", "").replace("\n", " ").strip(),
            "link": item.get("link", ""),
            "displayLink": item.get("displayLink", ""),
            "source_type": _classify_source(item.get("displayLink", "")),
        })
    return results


def _classify_source(domain: str) -> str:
    """Heuristically tag the domain type."""
    gov_indicators = [".gov.in", "gov.in", "nic.in", "scholarships.gov", "ugc.ac.in"]
    edu_indicators = [".ac.in", ".edu", "university", "college", "iit.", "nit.", "iim."]
    news_indicators = ["ndtv", "hindustan", "thehindu", "timesofindia", "indiatoday", "scroll", "wire"]
    org_indicators = [".org", "ngo", "foundation"]

    d = domain.lower()
    if any(g in d for g in gov_indicators):
        return "government"
    if any(e in d for e in edu_indicators):
        return "university"
    if any(n in d for n in news_indicators):
        return "news"
    if any(o in d for o in org_indicators):
        return "organization"
    return "general"


# ── Tool 1: search_web ────────────────────────────────────────────────────────

def search_web(
    query: str,
    context: str = "Indian education and career guidance",
    num_results: int = 5,
) -> dict[str, Any]:
    """
    Search the web for education and career information.

    Uses the Google Custom Search API when GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID
    are configured; falls back to Gemini-knowledge synthesis otherwise.

    Results are focused on Indian education, career, and scholarship topics.

    Args:
        query: Search query string.
        context: Domain context to focus results (default: Indian education).
        num_results: Number of results to return (1–10).

    Returns:
        dict with 'results' list and 'source' field ('cse' or 'gemini').
    """
    num_results = max(1, min(10, num_results))
    creds = _cse_credentials()

    # ── Real CSE path ────────────────────────────────────────
    if creds:
        api_key, cx = creds
        # Enrich query with context keyword for better Indian edu relevance
        enriched_query = f"{query} {context}" if context and context not in query else query
        try:
            raw = _cse_search(enriched_query, api_key, cx, num=num_results)
            items = _parse_cse_items(raw)
            search_info = raw.get("searchInformation", {})
            return {
                "success": True,
                "source": "cse",
                "query": query,
                "enriched_query": enriched_query,
                "total_results_approx": search_info.get("formattedTotalResults", "unknown"),
                "search_time_seconds": search_info.get("searchTime", 0),
                "results": items[:num_results],
                "total": len(items),
            }
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning(
                "CSE API HTTP error %s for query '%s' — falling back to Gemini: %s",
                status_code, query, exc,
            )
            if status_code == 429:
                logger.warning("CSE daily quota likely exhausted (429). Using Gemini fallback.")
        except Exception as exc:
            logger.warning("CSE search failed for query '%s' — falling back to Gemini: %s", query, exc)

    # ── Gemini fallback path ─────────────────────────────────
    logger.info("search_web using Gemini-knowledge fallback for: %s", query)
    prompt = f"""You are a search engine assistant for Indian education and career guidance.

Search query: "{query}"
Context: {context}

Provide {num_results} relevant, factual search results about this topic as it applies to Indian students.
Focus on current, accurate information about Indian education system, career paths, and opportunities.

Format your response as a JSON array:
[
  {{
    "title": "Result title",
    "snippet": "2-3 sentence summary of the result",
    "link": "",
    "displayLink": "",
    "relevance": "Why this is relevant to Indian students",
    "source_type": "government|university|news|organization|general"
  }}
]

JSON results only:"""

    raw_text = _gemini_generate(prompt, temperature=0.2)
    try:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw_text).strip()
        results = json.loads(cleaned)
        if isinstance(results, list):
            return {
                "success": True,
                "source": "gemini",
                "query": query,
                "results": results[:num_results],
                "total": len(results),
                "note": "Results from Gemini knowledge (CSE credentials not configured or quota exceeded).",
            }
    except Exception as exc:
        logger.warning("search_web Gemini JSON parse failed: %s", exc)

    # Last-resort plain text fallback
    return {
        "success": True,
        "source": "gemini",
        "query": query,
        "results": [{"title": query, "snippet": raw_text[:500], "link": "", "source_type": "general"}],
        "total": 1,
        "note": "Structured parse failed; returning raw Gemini response.",
    }


# ── Tool 2: google_custom_search ─────────────────────────────────────────────

def google_custom_search(
    query: str,
    num_results: int = 10,
    start_index: int = 1,
    safe_search: str = "active",
) -> dict[str, Any]:
    """
    Perform a raw Google Custom Search and return full result metadata.

    Unlike search_web (which adds context enrichment and a Gemini fallback),
    this tool provides direct access to the CSE API for precise, paginated
    searches with richer metadata. Requires GOOGLE_CSE_API_KEY and
    GOOGLE_CSE_ID to be configured.

    Args:
        query: Search query string.
        num_results: Results per page (1–10, API limit).
        start_index: Pagination start index (1-indexed). Use 11 for page 2, etc.
        safe_search: SafeSearch level — 'active' or 'off'.

    Returns:
        dict with results, pagination info, and full CSE metadata.
    """
    creds = _cse_credentials()
    if not creds:
        return {
            "success": False,
            "error": (
                "Google Custom Search is not configured. "
                "Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in your .env file. "
                "See .env.example for setup instructions."
            ),
            "results": [],
        }

    api_key, cx = creds
    num_results = max(1, min(10, num_results))

    try:
        raw = _cse_search(query, api_key, cx, num=num_results, start=start_index, safe=safe_search)
        items = _parse_cse_items(raw)
        search_info = raw.get("searchInformation", {})
        queries_info = raw.get("queries", {})

        # Pagination helpers
        next_page = queries_info.get("nextPage", [{}])[0] if queries_info.get("nextPage") else None
        prev_page = queries_info.get("previousPage", [{}])[0] if queries_info.get("previousPage") else None

        return {
            "success": True,
            "source": "cse",
            "query": query,
            "total_results_approx": search_info.get("formattedTotalResults", "unknown"),
            "search_time_seconds": search_info.get("searchTime", 0),
            "results": items,
            "total_returned": len(items),
            "pagination": {
                "current_start": start_index,
                "next_start": next_page.get("startIndex") if next_page else None,
                "previous_start": prev_page.get("startIndex") if prev_page else None,
            },
        }

    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        error_body = {}
        try:
            error_body = exc.response.json()
        except Exception:
            pass
        logger.error("google_custom_search HTTP %s: %s", status_code, error_body)

        if status_code == 429:
            msg = "Google CSE daily quota exhausted (100 free queries/day). Try again tomorrow."
        elif status_code == 403:
            msg = "Invalid GOOGLE_CSE_API_KEY or Custom Search API not enabled in your Google Cloud project."
        elif status_code == 400:
            msg = f"Bad request to CSE API: {error_body.get('error', {}).get('message', 'unknown')}"
        else:
            msg = f"CSE API returned HTTP {status_code}."

        return {"success": False, "error": msg, "results": []}

    except httpx.TimeoutException:
        logger.error("google_custom_search timed out for query: %s", query)
        return {"success": False, "error": "Request to Google CSE timed out. Try again.", "results": []}

    except Exception as exc:
        logger.error("google_custom_search failed: %s", exc)
        return {"success": False, "error": f"Unexpected error: {exc}", "results": []}


# ── Tool 3: fetch_college_information ────────────────────────────────────────

def fetch_college_information(
    college_name: str,
    info_type: str = "general",
) -> dict[str, Any]:
    """
    Fetch detailed information about a specific Indian college using Gemini knowledge.

    Args:
        college_name: Full or partial college name.
        info_type: Type of info needed - 'general', 'admission', 'courses', 'placements'.

    Returns:
        dict with structured college information.
    """
    info_prompts = {
        "general": "overview, location, ranking, accreditation, and key facts",
        "admission": "admission process, entrance exams required, important dates, and eligibility criteria",
        "courses": "all undergraduate and postgraduate courses offered with duration and fees",
        "placements": "placement statistics, average package, top recruiters, and highest package",
    }
    info_focus = info_prompts.get(info_type, info_prompts["general"])

    prompt = f"""Provide accurate, current information about "{college_name}" in India.

Focus on: {info_focus}

Important: Only provide factual information. If you're uncertain about specific numbers, 
indicate approximate ranges rather than exact figures.

Format as JSON:
{{
  "college_name": "{college_name}",
  "info_type": "{info_type}",
  "data": {{
    "summary": "2-3 sentence overview",
    "key_facts": ["fact1", "fact2", "fact3"],
    "official_website": "URL if known",
    "additional_details": {{}}
  }},
  "note": "Any important caveats or verification suggestions"
}}

JSON only:"""

    raw = _gemini_generate(prompt, temperature=0.1)

    try:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        result = json.loads(cleaned)
        result["success"] = True
        return result
    except Exception as exc:
        logger.warning("fetch_college_information parse failed: %s", exc)
        return {
            "success": True,
            "college_name": college_name,
            "info_type": info_type,
            "data": {"summary": raw[:600], "key_facts": []},
        }


# ── Tool 4: check_scholarship_deadlines ──────────────────────────────────────

def check_scholarship_deadlines(
    scholarship_names: list[str],
) -> dict[str, Any]:
    """
    Check and verify scholarship deadlines with urgency analysis.

    Args:
        scholarship_names: List of scholarship names to check.

    Returns:
        dict with deadline info, urgency ratings, and application guidance.
    """
    if not scholarship_names:
        return {"success": False, "error": "No scholarship names provided", "deadlines": []}

    names_str = ", ".join(f'"{n}"' for n in scholarship_names[:5])

    prompt = f"""For the following Indian scholarships, provide deadline and application information:
Scholarships: {names_str}

For each scholarship, provide:
1. Typical application deadline (month and day)
2. Application portal (URL)
3. Documents usually required
4. Urgency level: HIGH (within 30 days), MEDIUM (30-90 days), LOW (90+ days)

Format as JSON array:
[
  {{
    "scholarship_name": "name",
    "deadline": "Month DD (e.g., October 31)",
    "portal": "URL",
    "documents_required": ["document1", "document2"],
    "urgency": "HIGH|MEDIUM|LOW",
    "tips": "One key application tip"
  }}
]

JSON only:"""

    raw = _gemini_generate(prompt, temperature=0.1)

    try:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        deadlines = json.loads(cleaned)
        if isinstance(deadlines, list):
            return {
                "success": True,
                "scholarships_checked": len(scholarship_names),
                "deadlines": deadlines,
                "general_tip": "Apply at least 2 weeks before the deadline to avoid last-minute technical issues.",
            }
    except Exception as exc:
        logger.warning("check_scholarship_deadlines parse failed: %s", exc)

    return {
        "success": True,
        "deadlines": [{"scholarship_name": n, "deadline": "Check official portal", "urgency": "MEDIUM"} for n in scholarship_names],
        "general_tip": "Always verify deadlines on https://scholarships.gov.in",
    }


# ── Tool 5: career_market_trends ─────────────────────────────────────────────

def career_market_trends(
    career_name: str,
    region: str = "India",
) -> dict[str, Any]:
    """
    Get current job market trends and outlook for a career in India.

    Args:
        career_name: Career to analyze (e.g., 'AI Engineer', 'Data Scientist').
        region: Geographic focus (default: India).

    Returns:
        dict with demand trends, salary outlook, growth areas, and top cities.
    """
    prompt = f"""Provide a current job market analysis for "{career_name}" in {region}.

Include:
1. Current demand level and trend (growing/stable/declining)
2. Salary range for freshers and experienced professionals (in INR)
3. Top hiring cities in India
4. Key industries hiring for this role
5. Skills most in demand right now
6. 5-year outlook

Format as JSON:
{{
  "career_name": "{career_name}",
  "region": "{region}",
  "demand_level": "Very High|High|Moderate|Low",
  "trend": "Growing|Stable|Declining",
  "salary": {{
    "fresher_range": "₹X – ₹Y LPA",
    "experienced_range": "₹X – ₹Y LPA",
    "top_earner": "₹X+ LPA"
  }},
  "top_cities": ["city1", "city2", "city3"],
  "top_industries": ["industry1", "industry2"],
  "in_demand_skills": ["skill1", "skill2", "skill3"],
  "five_year_outlook": "2-3 sentence forecast",
  "opportunities_for_freshers": "Specific advice for new graduates"
}}

JSON only:"""

    raw = _gemini_generate(prompt, temperature=0.2)

    try:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        result = json.loads(cleaned)
        result["success"] = True
        return result
    except Exception as exc:
        logger.warning("career_market_trends parse failed: %s", exc)
        return {
            "success": True,
            "career_name": career_name,
            "region": region,
            "summary": raw[:800],
        }
