"""
Test language utilities.
"""
from utils.language import detect_language

def test_detect_language():
    assert detect_language("Hello how are you?") == "en"
    assert detect_language("എനിക്ക് AI Engineer ആകണം") == "ml"
