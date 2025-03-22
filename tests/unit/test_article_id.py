"""
Unit tests for the article ID creation functionality
"""
import datetime
import pytest
from unittest.mock import patch
from simpost.multi_feed_news_automation import create_article_id

def test_article_id_contains_date():
    """Test article ID contains current date when no pub_date provided"""
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

def test_article_id_with_pub_date():
    """Test article ID contains publication date when provided"""
    title = "Sample Article"
    link = "https://example.com/sample"
    pub_date = "Wed, 12 Mar 2025 15:30:00 +0000"
    
    # Generate ID with pub_date
    article_id = create_article_id(title, link, pub_date)
    
    # Should use pub_date, not current date
    assert article_id.startswith("20250312_")
    
def test_article_id_is_consistent():
    """Test that same inputs produce same ID"""
    title = "Test Article"
    link = "https://example.com/test"
    pub_date = "Tue, 18 Mar 2025 10:45:00 +0000"
    
    id1 = create_article_id(title, link, pub_date)
    id2 = create_article_id(title, link, pub_date)
    
    assert id1 == id2

def test_article_id_with_mocked_time():
    """Test article ID with mocked time when no pub_date provided"""
    mocked_date = datetime.datetime(2025, 3, 20)
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = mocked_date
        mock_dt.strftime = datetime.datetime.strftime  # Keep the strftime method
        
        title = "Test Article with Mocked Time"
        link = "https://example.com/mocked-time"
        
        article_id = create_article_id(title, link)
        
        assert article_id.startswith("20250320_")

def test_different_links_different_ids():
    """Test that different links produce different IDs"""
    title = "Same Article Title"
    link1 = "https://example.com/first"
    link2 = "https://example.com/second"
    pub_date = "Fri, 21 Mar 2025 08:15:00 +0000"
    
    id1 = create_article_id(title, link1, pub_date)
    id2 = create_article_id(title, link2, pub_date)
    
    # Check only hash part differs
    assert id1.split("_")[0] == id2.split("_")[0]  # Date prefix should be same
    assert id1.split("_")[1] != id2.split("_")[1]  # Hash should differ
    
def test_different_titles_same_ids():
    """Test that different titles but same links produce identical IDs"""
    title1 = "First Article Title"
    title2 = "Second Article Title"
    link = "https://example.com/same-article"
    pub_date = "Fri, 21 Mar 2025 08:15:00 +0000"
    
    id1 = create_article_id(title1, link, pub_date)
    id2 = create_article_id(title2, link, pub_date)
    
    # Both title and hash parts should be identical since links are the same
    assert id1 == id2
    
def test_invalid_pub_date_fallback():
    """Test that invalid pub_date falls back to current date"""
    title = "Test Article"
    link = "https://example.com/test"
    invalid_pub_date = "Not a valid date format"
    
    # Get today's date in YYYYMMDD format for comparison
    today_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Generate ID with invalid pub_date
    article_id = create_article_id(title, link, invalid_pub_date)
    
    # Should fall back to current date
    assert article_id.startswith(f"{today_date}_")