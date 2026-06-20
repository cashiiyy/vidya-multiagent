"""
Student Memory System for Vidya AI.
File-based, thread-safe persistence for student profiles and conversation history.
No external database required – works on Streamlit Community Cloud and Render.
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MEMORY_DIR = Path(__file__).parent
_PROFILES_FILE = _MEMORY_DIR / "student_profiles.json"
_CONVERSATIONS_FILE = _MEMORY_DIR / "conversation_memory.json"

# Maximum conversation turns kept per session
_MAX_HISTORY = 20

# Global file locks (thread-safe for Streamlit's multi-thread model)
_profiles_lock = threading.Lock()
_conversations_lock = threading.Lock()


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning empty dict if missing or invalid."""
    try:
        if path.exists() and path.stat().st_size > 0:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load %s: %s", path, exc)
    return {}


def _save_json(path: Path, data: dict) -> None:
    """Write data to a JSON file atomically."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except OSError as exc:
        logger.error("Failed to save %s: %s", path, exc)


class MemoryManager:
    """
    Manages per-session student profiles and conversation history.

    Session ID is typically the Streamlit session_id or a UUID generated
    at the start of a chat session.

    Profile schema:
        {
            "session_id": str,
            "created_at": str (ISO),
            "updated_at": str (ISO),
            "preferred_language": "en" | "ml",
            "interests": list[str],
            "marks": float | None,
            "state": str | None,
            "category": str | None,   # SC/ST/OBC/General
            "course_preference": str | None,
            "career_interest": str | None,
            "previous_recommendations": {
                "careers": list[str],
                "colleges": list[str],
                "scholarships": list[str],
            }
        }
    """

    # ── Profile Methods ───────────────────────────────────────────────────────

    @classmethod
    def get_profile(cls, session_id: str) -> dict[str, Any]:
        """Return the student profile for a session, or a default empty profile."""
        with _profiles_lock:
            profiles = _load_json(_PROFILES_FILE)
        profile = profiles.get(session_id)
        if profile is None:
            return cls._default_profile(session_id)
        return profile

    @classmethod
    def save_profile(cls, session_id: str, data: dict[str, Any]) -> None:
        """Merge data into the existing profile and persist."""
        with _profiles_lock:
            profiles = _load_json(_PROFILES_FILE)
            existing = profiles.get(session_id, cls._default_profile(session_id))
            existing.update(data)
            existing["updated_at"] = datetime.utcnow().isoformat()
            existing["session_id"] = session_id
            profiles[session_id] = existing
            _save_json(_PROFILES_FILE, profiles)
        logger.debug("Saved profile for session %s", session_id)

    @classmethod
    def update_interests(cls, session_id: str, interests: list[str]) -> None:
        """Add interests to the profile without removing existing ones."""
        profile = cls.get_profile(session_id)
        existing = set(profile.get("interests", []))
        existing.update(interests)
        cls.save_profile(session_id, {"interests": list(existing)})

    @classmethod
    def update_marks(cls, session_id: str, marks: float) -> None:
        cls.save_profile(session_id, {"marks": marks})

    @classmethod
    def update_language(cls, session_id: str, lang_code: str) -> None:
        cls.save_profile(session_id, {"preferred_language": lang_code})

    @classmethod
    def update_state(cls, session_id: str, state: str) -> None:
        cls.save_profile(session_id, {"state": state})

    @classmethod
    def add_recommendation(
        cls, session_id: str, rec_type: str, items: list[str]
    ) -> None:
        """
        Record items that were recommended to this student.
        rec_type: 'careers' | 'colleges' | 'scholarships'
        """
        profile = cls.get_profile(session_id)
        recs = profile.get("previous_recommendations", {"careers": [], "colleges": [], "scholarships": []})
        existing = set(recs.get(rec_type, []))
        existing.update(items)
        recs[rec_type] = list(existing)
        cls.save_profile(session_id, {"previous_recommendations": recs})

    @classmethod
    def update_from_entities(cls, session_id: str, entities: dict) -> None:
        """
        Auto-update profile from entities extracted by Gemini classify_intent.
        Only updates fields that have non-None values.
        """
        updates: dict[str, Any] = {}
        if entities.get("marks") is not None:
            try:
                updates["marks"] = float(entities["marks"])
            except (ValueError, TypeError):
                pass
        if entities.get("state"):
            updates["state"] = entities["state"]
        if entities.get("career_interest"):
            updates["career_interest"] = entities["career_interest"]
        if entities.get("course_preference"):
            updates["course_preference"] = entities["course_preference"]
        if entities.get("category"):
            updates["category"] = entities["category"]
        if updates:
            cls.save_profile(session_id, updates)

    # ── Conversation Methods ──────────────────────────────────────────────────

    @classmethod
    def append_conversation(
        cls,
        session_id: str,
        role: str,
        content: str,
        agent: str = "",
    ) -> None:
        """
        Append a turn to the conversation history.

        Args:
            session_id: Session identifier.
            role: 'user' or 'assistant'.
            content: Message text.
            agent: Name of the agent that produced the response (if assistant).
        """
        turn = {
            "role": role,
            "content": content[:2000],  # cap stored content
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with _conversations_lock:
            conversations = _load_json(_CONVERSATIONS_FILE)
            history = conversations.get(session_id, [])
            history.append(turn)
            # Keep only the last N turns
            if len(history) > _MAX_HISTORY:
                history = history[-_MAX_HISTORY:]
            conversations[session_id] = history
            _save_json(_CONVERSATIONS_FILE, conversations)

    @classmethod
    def get_history(cls, session_id: str, n: int = 10) -> list[dict]:
        """Return the last n turns of conversation for a session."""
        with _conversations_lock:
            conversations = _load_json(_CONVERSATIONS_FILE)
        history = conversations.get(session_id, [])
        return history[-n:]

    @classmethod
    def get_history_as_text(cls, session_id: str, n: int = 6) -> str:
        """
        Return recent conversation history formatted as a string
        for injection into agent prompts.
        """
        history = cls.get_history(session_id, n)
        if not history:
            return ""
        lines = []
        for turn in history:
            prefix = "Student" if turn["role"] == "user" else "Vidya AI"
            lines.append(f"{prefix}: {turn['content'][:300]}")
        return "\n".join(lines)

    @classmethod
    def clear_session(cls, session_id: str) -> None:
        """Remove all memory for a session (profile + history)."""
        with _profiles_lock:
            profiles = _load_json(_PROFILES_FILE)
            profiles.pop(session_id, None)
            _save_json(_PROFILES_FILE, profiles)
        with _conversations_lock:
            conversations = _load_json(_CONVERSATIONS_FILE)
            conversations.pop(session_id, None)
            _save_json(_CONVERSATIONS_FILE, conversations)
        logger.info("Cleared memory for session %s", session_id)

    @classmethod
    def list_sessions(cls) -> list[str]:
        """Return all active session IDs with profiles."""
        with _profiles_lock:
            profiles = _load_json(_PROFILES_FILE)
        return list(profiles.keys())

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _default_profile(session_id: str) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        return {
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "preferred_language": "en",
            "interests": [],
            "marks": None,
            "state": None,
            "category": None,
            "course_preference": None,
            "career_interest": None,
            "previous_recommendations": {
                "careers": [],
                "colleges": [],
                "scholarships": [],
            },
        }
