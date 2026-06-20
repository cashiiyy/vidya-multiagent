"""
Test Gemini service (mocked).
"""
import pytest
from unittest.mock import patch
from services.gemini_service import GeminiService

@patch("services.gemini_service.GeminiService._generate")
def test_classify_intent(mock_generate):
    mock_generate.return_value = '{"intents": ["career_guidance"], "primary_intent": "career_guidance", "entities": {}, "confidence": 0.9, "is_multi_intent": false}'
    svc = GeminiService()
    result = svc.classify_intent("I want to be an AI engineer")
    assert result["primary_intent"] == "career_guidance"
    assert result["is_multi_intent"] is False
