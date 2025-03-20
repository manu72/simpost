"""
Unit tests for the article ID creation functionality
"""
import datetime
import pytest
from unittest.mock import patch
from simpost.multi_feed_news_automation import create_article_id

def test_article_id_contains_date():
    """Test article ID contains current date"""
    title = "Sample Article Title"
    link = "https://example.com/sample-article"
    
    # Generate ID
    article_id = create_article_id(title, link)
    
    # Get today's date in YYYYMMDD format
    today_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Check if ID starts with today's date followed by underscore
    assert article_id.startswith(f"{today_date}_")
    # Check that there's content after the prefix
    assert len(article_id.split("_")[1]) > 0

def test_article_id_is_consistent():
    """Test that same inputs produce same ID"""
    title = "Test Article"
    link = "https://example.com/test"
    
    id1 = create_article_id(title, link)
    id2 = create_article_id(title, link)
    
    assert id1 == id2

def test_article_id_with_mocked_time():
    """Test article ID with mocked time"""
    mocked_date = datetime.datetime(2025, 3, 20)
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = mocked_date
        mock_dt.strftime = datetime.datetime.strftime  # Keep the strftime method
        
        title = "Test Article with Mocked Time"
        link = "https://example.com/mocked-time"
        
        article_id = create_article_id(title, link)
        
        assert article_id.startswith("20250320_")

def test_different_inputs_different_ids():
    """Test that different inputs produce different IDs"""
    title1 = "First Article"
    link1 = "https://example.com/first"
    
    title2 = "Second Article"
    link2 = "https://example.com/second"
    
    id1 = create_article_id(title1, link1)
    id2 = create_article_id(title2, link2)
    
    # Check only hash part differs
    assert id1.split("_")[0] == id2.split("_")[0]  # Date prefix should be same
    assert id1.split("_")[1] != id2.split("_")[1]  # Hash should differ