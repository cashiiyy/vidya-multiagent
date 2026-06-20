"""
Test memory manager.
"""
import pytest
from memory.memory_manager import MemoryManager

def test_memory_profile_creation():
    session = "test_session_1"
    MemoryManager.clear_session(session)
    profile = MemoryManager.get_profile(session)
    assert profile["session_id"] == session
    assert profile["preferred_language"] == "en"

def test_memory_history():
    session = "test_session_2"
    MemoryManager.clear_session(session)
    MemoryManager.append_conversation(session, "user", "Hello")
    history = MemoryManager.get_history(session)
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
