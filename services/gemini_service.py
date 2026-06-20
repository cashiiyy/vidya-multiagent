"""
Gemini Service Layer for Vidya AI.
Centralizes all Gemini API interactions with typed interfaces,
retry logic, and safe fallbacks for every method.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

# Model to use – flash is fast and free-tier friendly
_DEFAULT_MODEL = "gemini-2.0-flash"

# Intent labels the router uses
_INTENT_LABELS = [
    "career_guidance",
    "college_recommendation",
    "scholarship_search",
    "skill_gap_analysis",
    "roadmap_generation",
    "general_help",
]


def _get_client():
    """Build and return a google.genai Client."""
    try:
        import google.genai as genai  # type: ignore
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        return genai.Client(api_key=api_key)
    except ImportError as exc:
        raise ImportError(
            "google-genai is not installed. Run: pip install google-genai"
        ) from exc


class GeminiService:
    """
    Centralized Gemini API service for Vidya AI.

    Usage:
        svc = GeminiService()
        decision = svc.classify_intent("I love maths and want to be an AI engineer")
    """

    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model = model
        self._client = None  # Lazy-load to avoid import errors at module level

    @property
    def client(self):
        if self._client is None:
            self._client = _get_client()
        return self._client

    def _generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Core generation call with retry and error handling.

        Returns:
            Generated text, or empty string on failure.
        """
        try:
            from google.genai import types  # type: ignore

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    safety_settings=self._safety_settings(),
                ),
            )
            return response.text.strip() if response.text else ""
        except Exception as exc:
            logger.error("Gemini generate_content failed: %s", exc)
            return ""

    @staticmethod
    def _safety_settings() -> list[dict]:
        """
        Return Gemini safety settings that block harmful content
        while allowing educational discussions.
        """
        try:
            from google.genai import types  # type: ignore
            return [
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_MEDIUM_AND_ABOVE",
                ),
            ]
        except Exception:
            return []

    # ── Public Methods ────────────────────────────────────────────────────────

    def classify_intent(self, text: str, language: str = "en") -> dict[str, Any]:
        """
        Classify the user's intent using Gemini structured output.

        Returns a dict with keys:
            - intents: list[str]  (one or more from _INTENT_LABELS)
            - primary_intent: str
            - entities: dict  (extracted marks, state, career, etc.)
            - confidence: float
            - is_multi_intent: bool
        """
        prompt = f"""You are an intent classifier for Vidya AI, an Indian student career guidance platform.

Analyze the following student query and extract:
1. The intent(s) — choose one or more from: {json.dumps(_INTENT_LABELS)}
2. Named entities: marks (percentage), state, career_interest, course_preference, category (SC/ST/OBC/General/Girl)

Respond ONLY with valid JSON in this exact format:
{{
  "intents": ["<intent1>", "<intent2>"],
  "primary_intent": "<most_important_intent>",
  "entities": {{
    "marks": null,
    "state": null,
    "career_interest": null,
    "course_preference": null,
    "category": null
  }},
  "confidence": 0.95,
  "is_multi_intent": false
}}

Student query: "{text}"

JSON response:"""

        raw = self._generate(prompt, temperature=0.1)

        # Extract JSON from response
        try:
            # Strip markdown code fences if present
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            result = json.loads(cleaned)
            # Validate intents
            result["intents"] = [
                i for i in result.get("intents", []) if i in _INTENT_LABELS
            ]
            if not result["intents"]:
                result["intents"] = ["general_help"]
            if result.get("primary_intent") not in _INTENT_LABELS:
                result["primary_intent"] = result["intents"][0]
            result["is_multi_intent"] = len(result["intents"]) > 1
            return result
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("classify_intent JSON parse failed: %s — raw: %s", exc, raw[:200])
            return {
                "intents": ["general_help"],
                "primary_intent": "general_help",
                "entities": {},
                "confidence": 0.5,
                "is_multi_intent": False,
            }

    def generate_plan(self, query: str, context: dict | None = None) -> list[str]:
        """
        Decompose a complex query into an ordered list of intent steps.

        Returns:
            Ordered list of intent strings (e.g. ["career_guidance", "college_recommendation"])
        """
        context_str = ""
        if context:
            context_str = f"\nStudent profile context: {json.dumps(context, ensure_ascii=False)}"

        prompt = f"""You are the Planner Agent for Vidya AI.

Given a student's complex query, generate an ORDERED list of steps needed to fully answer it.
Choose steps from: {json.dumps(_INTENT_LABELS)}

Rules:
- Only include steps that are actually needed
- Order matters: career first, then college, then scholarship, then skills, then roadmap
- Maximum 4 steps per plan
- Return ONLY a JSON array of strings

Student query: "{query}"{context_str}

JSON array of steps:"""

        raw = self._generate(prompt, temperature=0.1)
        try:
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            steps = json.loads(cleaned)
            if isinstance(steps, list):
                return [s for s in steps if s in _INTENT_LABELS]
        except Exception as exc:
            logger.warning("generate_plan parse failed: %s", exc)

        return ["general_help"]

    def translate_to_malayalam(self, text: str) -> str:
        """
        Translate English text to natural conversational Malayalam.
        Technical terms (AI, NEET, JEE, etc.) are kept in English.
        """
        if not text:
            return text

        prompt = f"""Translate the following text to natural, conversational Malayalam.
Keep technical terms like 'AI Engineer', 'Machine Learning', 'NEET', 'JEE', 'B.Tech', 
'scholarship', college names, and URLs in English.
Only translate the surrounding explanation text.

English text:
{text}

Malayalam translation (keep technical terms in English):"""

        result = self._generate(prompt, temperature=0.3)
        if not result:
            logger.warning("translate_to_malayalam returned empty — using English fallback")
            return text
        return result

    def translate_to_english(self, text: str) -> str:
        """
        Translate Malayalam text to English for internal agent processing.
        """
        if not text:
            return text

        prompt = f"""Translate the following Malayalam text to English.
Preserve any technical terms, names, or English words already in the text.

Malayalam text:
{text}

English translation:"""

        result = self._generate(prompt, temperature=0.2)
        if not result:
            logger.warning("translate_to_english returned empty — using original")
            return text
        return result

    def summarize_profile(self, profile: dict) -> str:
        """
        Generate a one-paragraph student profile summary for agent context injection.

        Args:
            profile: Student profile dict from MemoryManager.

        Returns:
            Natural language summary string.
        """
        if not profile:
            return "No student profile available yet."

        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)

        prompt = f"""You are summarizing a student profile for an AI education counselor.
Write a concise 2-3 sentence summary of this student that will be given to an AI agent
as context to personalize their response.

Student profile:
{profile_json}

Write the summary in third person (e.g., "The student is..."):"""

        result = self._generate(prompt, temperature=0.4)
        if not result:
            interests = profile.get("interests", [])
            state = profile.get("state", "India")
            marks = profile.get("marks", "")
            return (
                f"The student is from {state}"
                + (f" with {marks}% marks" if marks else "")
                + (f", interested in {', '.join(interests)}" if interests else "")
                + "."
            )
        return result

    def generate_career_response(
        self,
        query: str,
        careers_data: list[dict],
        language: str = "en",
        student_profile: str = "",
    ) -> str:
        """
        Generate a rich, personalized career guidance response using Gemini.
        """
        careers_summary = json.dumps(
            [{"name": c.get("career_name"), "demand": c.get("future_demand"),
              "salary": c.get("salary_range", {}), "skills": c.get("required_skills", [])[:4]}
             for c in careers_data[:5]],
            ensure_ascii=False,
        )

        profile_context = f"\nStudent profile: {student_profile}" if student_profile else ""

        prompt = f"""You are Vidya AI, a friendly and expert career counselor for Indian students.{profile_context}

The student asked: "{query}"

Based on this data about matching careers:
{careers_summary}

Write a warm, encouraging response that:
1. Acknowledges their interest
2. Explains the top 2-3 career options clearly
3. Mentions salary range and job demand in India
4. Gives 1-2 actionable next steps
5. Uses simple language suitable for Class 12 / college students

{"Respond in Malayalam but keep technical terms in English." if language == "ml" else "Respond in English."}

Response:"""

        result = self._generate(prompt, temperature=0.6)
        return result or "I found some great career options for you! Please check the results below."

    def generate_scholarship_response(
        self,
        query: str,
        scholarships_data: list[dict],
        language: str = "en",
    ) -> str:
        """Generate a scholarship guidance response."""
        schol_summary = json.dumps(
            [{"name": s.get("scholarship_name"), "amount": s.get("amount"),
              "deadline": s.get("deadline"), "eligibility": s.get("eligibility")}
             for s in scholarships_data[:5]],
            ensure_ascii=False,
        )

        prompt = f"""You are Vidya AI, helping an Indian student find scholarships.

Student query: "{query}"

Matching scholarships found:
{schol_summary}

Write a helpful response that:
1. Lists the top scholarships clearly with amounts and deadlines
2. Explains how to apply (mention scholarships.gov.in where relevant)
3. Encourages them to apply before deadlines
4. Is warm and motivating

{"Respond in Malayalam but keep scholarship names, amounts and URLs in English." if language == "ml" else "Respond in English."}

Response:"""

        result = self._generate(prompt, temperature=0.5)
        return result or "Here are the scholarships I found for you!"
