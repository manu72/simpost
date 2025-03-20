"""
Unit tests for the article storage functionality
"""
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from simpost.multi_feed_news_automation import (
    save_retrieved_article, save_rewritten_article, 
    is_article_processed, mark_article_as_posted
)

@pytest.fixture
def sample_article():
    """Create a sample article for testing"""
    return {
        "id": "20250320_123456789abcdef",
        "title": "Test Article",
        "link": "https://example.com/test",
        "description": "This is a test article description",
        "content": "This is the full content of the test article",
        "pub_date": "2025-03-20T12:00:00Z",
        "retrieved_at": "2025-03-20T13:00:00Z"
    }

def test_save_retrieved_article(test_data_dir, sample_article):
    """Test saving a retrieved article"""
    with patch("simpost.multi_feed_news_automation.RETRIEVED_ARTICLES_DIR", str(test_data_dir["retrieved_dir"])):
        file_path = save_retrieved_article("Test_Feed", sample_article)
        
        # Check that the file exists
        assert os.path.exists(file_path)
        
        # Check that the content is correct
        with open(file_path, "r") as f:
            saved_article = json.load(f)
        
        assert saved_article["id"] == sample_article["id"]
        assert saved_article["title"] == sample_article["title"]

def test_save_rewritten_article(test_data_dir, sample_article):
    """Test saving a rewritten article"""
    with patch("simpost.multi_feed_news_automation.REWRITTEN_ARTICLES_DIR", str(test_data_dir["rewritten_dir"])):
        rewritten_content = "This is the rewritten content for social media"
        verification_msg = "VERIFIED - This article checks out"
        
        file_path = save_rewritten_article(
            "Test_Feed",
            sample_article["id"],
            sample_article,
            rewritten_content,
            True,  # is_verified
            verification_msg
        )
        
        # Check that the file exists
        assert os.path.exists(file_path)
        
        # Check that the content is correct
        with open(file_path, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data["id"] == sample_article["id"]
        assert saved_data["rewritten_content"] == rewritten_content
        assert saved_data["is_verified"] == True
        assert saved_data["verification_message"] == verification_msg
        assert saved_data["is_posted"] == False

def test_is_article_processed(test_data_dir, sample_article):
    """Test checking if an article has been processed"""
    # Create a rewritten article file
    feed_dir = test_data_dir["rewritten_dir"] / "Test_Feed"
    feed_dir.mkdir(exist_ok=True)
    
    file_path = feed_dir / f"{sample_article['id']}.json"
    with open(file_path, "w") as f:
        json.dump({"id": sample_article["id"]}, f)
    
    with patch("simpost.multi_feed_news_automation.REWRITTEN_ARTICLES_DIR", str(test_data_dir["rewritten_dir"])):
        # Test with existing article
        assert is_article_processed("Test_Feed", sample_article["id"]) == True
        
        # Test with non-existing article
        assert is_article_processed("Test_Feed", "nonexistent_id") == False

def test_mark_article_as_posted(test_data_dir, sample_article):
    """Test marking an article as posted"""
    # Create a rewritten article file
    feed_dir = test_data_dir["rewritten_dir"] / "Test_Feed"
    feed_dir.mkdir(exist_ok=True)
    
    file_path = feed_dir / f"{sample_article['id']}.json"
    test_data = {
        "id": sample_article["id"],
        "is_posted": False,
        "rewritten_content": "Test content"
    }
    
    with open(file_path, "w") as f:
        json.dump(test_data, f)
    
    with patch("simpost.multi_feed_news_automation.REWRITTEN_ARTICLES_DIR", str(test_data_dir["rewritten_dir"])):
        mark_article_as_posted("Test_Feed", sample_article["id"])
        
        # Check that the article was marked as posted
        with open(file_path, "r") as f:
            updated_data = json.load(f)
        
        assert updated_data["is_posted"] == True
        assert "posted_at" in updated_data