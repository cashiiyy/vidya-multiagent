"""
Language detection and translation utilities for Vidya AI.
Supports English (en) and Malayalam (ml).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Malayalam Unicode range: U+0D00–U+0D7F
_MALAYALAM_RANGE = range(0x0D00, 0x0D80)

# Common Malayalam words for quick detection fallback
_MALAYALAM_KEYWORDS = {
    "എനിക്ക്", "ആകണം", "വേണം", "ഉണ്ട്", "ഇല്ല", "ആണ്", "എന്ത്",
    "എവിടെ", "എങ്ങനെ", "കോളേജ്", "സ്കോളർഷിപ്പ്", "കരിയർ", "പഠനം",
    "ജോലി", "ഇന്ത്യ", "കേരള", "ബിരുദം", "ഡിഗ്രി",
}


def detect_language(text: str) -> str:
    """
    Detect whether the input is in English ('en') or Malayalam ('ml').

    Strategy:
      1. Count Malayalam Unicode characters – if >10% of chars, it's Malayalam.
      2. Check for known Malayalam keywords as a secondary signal.
      3. Fall back to langdetect library if available.
      4. Default to English.

    Returns:
        'ml' for Malayalam, 'en' for English (default).
    """
    if not text or not text.strip():
        return "en"

    text_stripped = text.strip()

    # Strategy 1: Unicode character ratio
    malayalam_chars = sum(
        1 for ch in text_stripped if ord(ch) in _MALAYALAM_RANGE
    )
    if len(text_stripped) > 0:
        ratio = malayalam_chars / len(text_stripped)
        if ratio > 0.10:
            logger.debug("Detected Malayalam via Unicode ratio: %.2f", ratio)
            return "ml"

    # Strategy 2: Keyword presence
    words = set(text_stripped.split())
    if words & _MALAYALAM_KEYWORDS:
        logger.debug("Detected Malayalam via keyword match")
        return "ml"

    # Strategy 3: langdetect library (optional dependency)
    try:
        from langdetect import detect, LangDetectException  # type: ignore
        detected = detect(text_stripped)
        if detected == "ml":
            return "ml"
    except Exception:
        pass  # langdetect not available or failed – use default

    return "en"


def translate_to_language(text: str, target_lang: str, gemini_model=None) -> str:
    """
    Translate text to the target language using Gemini if available,
    or return original text if translation is not needed/possible.

    Args:
        text: Text to translate.
        target_lang: Target language code ('en' or 'ml').
        gemini_model: Optional google.genai GenerativeModel instance.

    Returns:
        Translated text (or original if no translation needed).
    """
    if target_lang == "en":
        return text  # Already in English, no translation needed

    if gemini_model is None:
        # Try to build a quick Gemini client
        try:
            import google.genai as genai  # type: ignore
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                try:
                    import streamlit as st
                    if "GEMINI_API_KEY" in st.secrets:
                        api_key = st.secrets["GEMINI_API_KEY"]
                except ImportError:
                    pass
            if not api_key:
                logger.warning("GEMINI_API_KEY not set – returning English response")
                return text
            client = genai.Client(api_key=api_key)
            gemini_model = client.models
        except ImportError:
            logger.warning("google-genai not installed – returning English response")
            return text

    prompt = (
        f"Translate the following text to Malayalam. "
        f"Keep technical terms (like 'AI Engineer', 'Machine Learning', 'NEET') in English "
        f"but translate the surrounding explanation to natural, conversational Malayalam.\n\n"
        f"Text to translate:\n{text}\n\n"
        f"Malayalam translation:"
    )
    try:
        import google.genai as genai  # type: ignore
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            try:
                import streamlit as st
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = st.secrets["GEMINI_API_KEY"]
            except ImportError:
                pass
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        translated = response.text.strip()
        logger.debug("Translated %d chars to Malayalam", len(translated))
        return translated
    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        return text  # Graceful fallback


def get_language_label(lang_code: str) -> str:
    """Return human-readable language label."""
    return {"en": "English", "ml": "Malayalam"}.get(lang_code, "English")
