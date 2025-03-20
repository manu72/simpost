"""
Pytest configuration and fixtures for SimPost tests
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock

@pytest.fixture
def sample_feed_data():
    """Return sample feed data for testing"""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_feeds.json"
    with open(fixture_path, "r") as f:
        return json.load(f)

@pytest.fixture
def mock_rss_response():
    """Return a mock RSS response XML"""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_rss_response.xml"
    with open(fixture_path, "r") as f:
        return f.read()

@pytest.fixture
def mock_openai_response():
    """Mock an OpenAI API response"""
    mock_response = MagicMock()
    mock_response.output_text = "This is a rewritten article for social media."
    return mock_response

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary data directory structure for testing"""
    # Create directory structure
    retrieved_dir = tmp_path / "retrieved_articles"
    rewritten_dir = tmp_path / "rewritten_articles"
    logs_dir = tmp_path / "logs"
    
    retrieved_dir.mkdir()
    rewritten_dir.mkdir()
    logs_dir.mkdir()
    
    # Return paths dictionary
    return {
        "data_dir": tmp_path,
        "retrieved_dir": retrieved_dir,
        "rewritten_dir": rewritten_dir, 
        "logs_dir": logs_dir
    }