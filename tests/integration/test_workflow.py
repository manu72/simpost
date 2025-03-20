"""
Integration tests for the complete workflow
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from simpost.multi_feed_news_automation import (
    get_articles, rewrite_article, verify_rewritten_article, 
    save_retrieved_article, save_rewritten_article
)

@pytest.fixture
def mock_openai_rewrite():
    """Create a mock OpenAI rewrite response"""
    mock = MagicMock()
    mock.output_text = "This is a rewritten article for social media. #news"
    return mock

@pytest.fixture
def mock_openai_verify():
    """Create a mock OpenAI verification response"""
    mock = MagicMock()
    mock.output_text = "VERIFIED - This content is accurate and matches the source article."
    return mock

@pytest.fixture
def mock_requests_response(mock_rss_response):
    """Create a mock requests response object"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_rss_response.encode()
    return mock_resp

@patch("simpost.multi_feed_news_automation.client.responses.create")
def test_complete_workflow(mock_openai, mock_requests_response, mock_openai_rewrite, 
                          mock_openai_verify, test_data_dir, sample_feed_data):
    """Test the complete article workflow: retrieve → rewrite → verify → save"""
    # Configure mocks
    mock_openai.side_effect = [mock_openai_rewrite, mock_openai_verify]
    
    with patch("requests.get", return_value=mock_requests_response), \
         patch("simpost.multi_feed_news_automation.RETRIEVED_ARTICLES_DIR", str(test_data_dir["retrieved_dir"])), \
         patch("simpost.multi_feed_news_automation.REWRITTEN_ARTICLES_DIR", str(test_data_dir["rewritten_dir"])), \
         patch("simpost.multi_feed_news_automation.LOGS_DIR", str(test_data_dir["logs_dir"])):
        
        # Step 1: Get articles from the feed
        feed = sample_feed_data[0]
        articles = get_articles(feed["rss_url"], max_articles=2)
        
        assert articles is not None
        assert len(articles) > 0
        
        article = articles[0]  # Process the first article for this test
        assert "title" in article
        assert "link" in article
        
        # Step 2: Save the retrieved article
        retrieved_path = save_retrieved_article(feed["name"], article)
        assert os.path.exists(retrieved_path)
        
        # Step 3: Rewrite the article
        system_prompt = feed.get("system_prompt", "You are a professional social media copywriter.")
        rewritten_content = rewrite_article(article, feed["prompt"], system_prompt)
        assert "This is a rewritten article" in rewritten_content
        
        # Step 4: Verify the rewritten content
        is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])
        assert is_verified is True
        assert "VERIFIED" in verification_message
        
        # Step 5: Save the rewritten article
        rewritten_path = save_rewritten_article(
            feed["name"], 
            article["id"], 
            article, 
            rewritten_content, 
            is_verified, 
            verification_message
        )
        assert os.path.exists(rewritten_path)
        
        # Check that the rewritten article has the correct content
        with open(rewritten_path, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data["id"] == article["id"]
        assert saved_data["rewritten_content"] == rewritten_content
        assert saved_data["is_verified"] is True


@patch("simpost.multi_feed_news_automation.client.responses.create")
def test_multiple_articles_workflow(mock_openai, mock_requests_response, mock_openai_rewrite, 
                                   mock_openai_verify, test_data_dir, sample_feed_data):
    """Test processing multiple articles from a feed"""
    # Mock multiple OpenAI calls (for both articles)
    mock_openai.side_effect = [
        mock_openai_rewrite, mock_openai_verify,  # For first article
        mock_openai_rewrite, mock_openai_verify   # For second article
    ]
    
    with patch("requests.get", return_value=mock_requests_response), \
         patch("simpost.multi_feed_news_automation.RETRIEVED_ARTICLES_DIR", str(test_data_dir["retrieved_dir"])), \
         patch("simpost.multi_feed_news_automation.REWRITTEN_ARTICLES_DIR", str(test_data_dir["rewritten_dir"])), \
         patch("simpost.multi_feed_news_automation.LOGS_DIR", str(test_data_dir["logs_dir"])), \
         patch("simpost.multi_feed_news_automation.is_article_processed", return_value=False):
        
        # Get articles from the feed
        feed = sample_feed_data[0]
        articles = get_articles(feed["rss_url"], max_articles=2)
        
        assert len(articles) == 2
        
        processed_articles = []
        
        # Process each article
        for article in articles:
            # Save the retrieved article
            retrieved_path = save_retrieved_article(feed["name"], article)
            assert os.path.exists(retrieved_path)
            
            # Rewrite the article
            system_prompt = feed.get("system_prompt", "You are a professional social media copywriter.")
            rewritten_content = rewrite_article(article, feed["prompt"], system_prompt)
            
            # Verify the rewritten content
            is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])
            
            # Save the rewritten article
            rewritten_path = save_rewritten_article(
                feed["name"], 
                article["id"], 
                article, 
                rewritten_content, 
                is_verified, 
                verification_message
            )
            
            assert os.path.exists(rewritten_path)
            processed_articles.append(article["id"])
        
        # Verify we processed both articles
        assert len(processed_articles) == 2
        
        # Check that both article files exist
        feed_name = feed["name"].replace(' ', '_')
        for article_id in processed_articles:
            rewritten_file = os.path.join(test_data_dir["rewritten_dir"], feed_name, f"{article_id}.json")
            assert os.path.exists(rewritten_file)