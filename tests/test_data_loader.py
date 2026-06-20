"""
Test data loader.
"""
from utils.data_loader import DataLoader

def test_data_loader_careers():
    careers = DataLoader.get_careers()
    assert len(careers) > 0
    assert careers[0].id == "c001"

def test_data_loader_search_careers():
    results = DataLoader.search_careers("ai engineer")
    assert len(results) > 0
    assert "AI" in results[0].career_name

def test_data_loader_colleges():
    colleges = DataLoader.get_colleges()
    assert len(colleges) > 0
