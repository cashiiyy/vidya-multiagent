"""
Security utilities for Vidya AI.
Provides input sanitization, prompt injection detection, and content filtering.
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2000"))
ENABLE_SECURITY_FILTER = os.getenv("ENABLE_SECURITY_FILTER", "true").lower() == "true"

# ── Prompt Injection Patterns ─────────────────────────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern] = [
    # Classic jailbreak attempts
    re.compile(r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(everything|all|your)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(a\s+)?(different|new|evil|bad|DAN)\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(different|unrestricted|jailbroken)\b", re.IGNORECASE),
    re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    # System prompt extraction
    re.compile(r"\bprint\s+(your\s+)?(system|internal)\s+prompt\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(your\s+)?(instructions?|prompt|system)\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+(are\s+your\s+instructions?|is\s+your\s+prompt)\b", re.IGNORECASE),
    # Role manipulation
    re.compile(r"\bpretend\s+(you\s+are\s+)?(not|an?\s+AI|human|unrestricted)\b", re.IGNORECASE),
    re.compile(r"\bsimulate\s+(a\s+)?(harmful|dangerous|evil)\b", re.IGNORECASE),
    # Code injection
    re.compile(r"<\s*script\s*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    # SQL injection patterns
    re.compile(r"(;\s*DROP\s+TABLE|;\s*DELETE\s+FROM|UNION\s+SELECT)", re.IGNORECASE),
]

# ── Harmful Content Keywords ──────────────────────────────────────────────────
_HARMFUL_KEYWORDS: list[str] = [
    "bomb", "weapon", "explosive", "poison", "kill", "suicide method",
    "drug synthesis", "hack password", "illegal", "terrorism",
]

# ── Safe Educational Keywords (whitelist signal) ──────────────────────────────
_EDUCATION_SIGNALS: list[str] = [
    "career", "college", "scholarship", "course", "exam", "degree", "job",
    "skill", "study", "education", "admission", "engineering", "medical",
    "law", "management", "science", "arts", "commerce", "certificate",
    "keam", "neet", "jee", "upsc", "gate", "clat", "ielts", "gre",
    "കരിയർ", "കോളേജ്", "പഠനം", "ജോലി", "സ്കോളർഷിപ്പ്",
]


def sanitize_input(text: str) -> str:
    """
    Clean and normalize user input:
      - Strip leading/trailing whitespace
      - Normalize Unicode (NFC)
      - Remove null bytes and control characters
      - Strip HTML/script tags
      - Truncate to MAX_INPUT_LENGTH
    """
    if not text:
        return ""
    # Unicode normalization
    text = unicodedata.normalize("NFC", text)
    # Remove null bytes and non-printable control chars (except newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Strip HTML/script tags
    text = re.sub(r"<[^>]*>", "", text)
    # Strip surrounding whitespace
    text = text.strip()
    # Truncate
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH]
        logger.warning("Input truncated to %d characters", MAX_INPUT_LENGTH)
    return text


def is_prompt_injection(text: str) -> bool:
    """Return True if the text appears to be a prompt injection attempt."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning("Prompt injection pattern matched: %s", pattern.pattern[:50])
            return True
    return False


def contains_harmful_content(text: str) -> bool:
    """Return True if the text contains clearly harmful keyword combinations."""
    text_lower = text.lower()
    # Simple keyword check – not all appearances are harmful, so we look for
    # combinations that are clearly off-topic for an education platform.
    harmful_hits = sum(1 for kw in _HARMFUL_KEYWORDS if kw in text_lower)
    education_hits = sum(1 for kw in _EDUCATION_SIGNALS if kw in text_lower)
    # If multiple harmful keywords with no educational context, flag it
    if harmful_hits >= 2 and education_hits == 0:
        logger.warning("Harmful content detected (hits=%d)", harmful_hits)
        return True
    return False


def is_safe_input(text: str) -> tuple[bool, str]:
    """
    Full safety check on user input.

    Returns:
        (is_safe: bool, reason: str)  –  reason is empty string if safe.
    """
    if not ENABLE_SECURITY_FILTER:
        return True, ""

    if not text or not text.strip():
        return False, "Empty input received."

    if len(text) > MAX_INPUT_LENGTH:
        return False, f"Input too long (max {MAX_INPUT_LENGTH} characters)."

    if is_prompt_injection(text):
        return (
            False,
            "Your message contains content that cannot be processed by Vidya AI. "
            "Please ask a question about careers, colleges, or scholarships.",
        )

    if contains_harmful_content(text):
        return (
            False,
            "Vidya AI is designed to help with education and career guidance. "
            "Please ask questions related to those topics.",
        )

    return True, ""


def get_safe_error_response(language: str = "en") -> str:
    """Return a safe, friendly error message in the appropriate language."""
    if language == "ml":
        return (
            "ക്ഷമിക്കണം, ഞാൻ ആ ചോദ്യത്തിന് ഉത്തരം നൽകാൻ കഴിയില്ല. "
            "കരിയർ, കോളേജ്, അല്ലെങ്കിൽ സ്കോളർഷിപ്പ് സംബന്ധിച്ച ചോദ്യങ്ങൾ ചോദിക്കൂ."
        )
    return (
        "I'm sorry, I can't process that request. "
        "Please ask me about careers, colleges, scholarships, or learning roadmaps."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCEMENT: MCP Validation, Gemini Safety Config, ASGI Middleware
# These additions are purely additive — no existing code is modified.
# ═══════════════════════════════════════════════════════════════════════════════

# Required fields for each MCP tool endpoint
_MCP_TOOL_SCHEMAS: dict[str, list[str]] = {
    "career_lookup": ["query"],
    "college_lookup": [],
    "scholarship_lookup": [],
    "skill_lookup": [],
    "roadmap_generator": ["career_name"],
    "search_web": ["query"],
    "fetch_college_information": ["college_name"],
    "check_scholarship_deadlines": ["scholarship_names"],
    "career_market_trends": ["career_name"],
}


def validate_mcp_request(tool_name: str, payload: dict) -> tuple[bool, str]:
    """
    Validate an MCP tool call payload.

    Checks:
    - Tool name is known
    - Required fields are present
    - String fields pass basic safety checks
    - No injections in string values

    Returns:
        (is_valid: bool, error_message: str)
    """
    if tool_name not in _MCP_TOOL_SCHEMAS:
        return False, f"Unknown MCP tool: '{tool_name}'. Valid tools: {list(_MCP_TOOL_SCHEMAS.keys())}"

    required = _MCP_TOOL_SCHEMAS[tool_name]
    for field in required:
        if field not in payload or payload[field] is None:
            return False, f"Missing required field '{field}' for tool '{tool_name}'."

    # Validate all string values in the payload
    for key, value in payload.items():
        if isinstance(value, str):
            sanitized = sanitize_input(value)
            if is_prompt_injection(sanitized):
                return False, f"Field '{key}' contains disallowed content."
            if len(sanitized) > MAX_INPUT_LENGTH:
                return False, f"Field '{key}' exceeds maximum length ({MAX_INPUT_LENGTH} chars)."
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and is_prompt_injection(item):
                    return False, f"List field '{key}' contains disallowed content."

    return True, ""


def get_gemini_safety_config() -> list[dict]:
    """
    Return Gemini API safety settings as a list of dicts.
    Blocks harassment, hate speech, sexually explicit, and dangerous content
    at MEDIUM_AND_ABOVE threshold — appropriate for an educational platform.

    Usage with google-genai SDK:
        from google.genai import types
        safety = get_gemini_safety_config()
        # Pass to GenerateContentConfig(safety_settings=safety)
    """
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]


class SecurityMiddleware:
    """
    ASGI middleware for FastAPI that validates all incoming request bodies.

    Runs is_safe_input() on every string field in JSON request bodies.
    Returns HTTP 400 immediately if any field fails the safety check.

    Usage in FastAPI:
        from utils.security import SecurityMiddleware
        app.add_middleware(SecurityMiddleware)
    """

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] in ("POST", "PUT", "PATCH"):
            # Buffer and inspect the body
            body_chunks = []
            more_body = True

            async def receive_body():
                nonlocal more_body
                if body_chunks:
                    chunk = body_chunks.pop(0)
                    return {"type": "http.request", "body": chunk, "more_body": False}
                message = await receive()
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                return message

            # Read full body
            full_body = b""
            while True:
                message = await receive()
                full_body += message.get("body", b"")
                if not message.get("more_body", False):
                    break

            # Validate text fields
            try:
                import json
                payload = json.loads(full_body)
                if isinstance(payload, dict):
                    for key, val in payload.items():
                        if isinstance(val, str):
                            safe, reason = is_safe_input(val)
                            if not safe:
                                response_body = json.dumps({
                                    "detail": f"Security validation failed on field '{key}': {reason}"
                                }).encode()
                                await send({
                                    "type": "http.response.start",
                                    "status": 400,
                                    "headers": [[b"content-type", b"application/json"]],
                                })
                                await send({"type": "http.response.body", "body": response_body})
                                return
            except Exception:
                pass  # Non-JSON body — let FastAPI handle it

            # Replay body to the app
            async def replay_receive():
                return {"type": "http.request", "body": full_body, "more_body": False}

            await self._app(scope, replay_receive, send)
        else:
            await self._app(scope, receive, send)
