"""
Unit tests for the feed retrieval functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from simpost.multi_feed_news_automation import get_articles, parse_article_item

@pytest.fixture
def mock_requests_response(mock_rss_response):
    """Create a mock requests response object"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_rss_response.encode()
    return mock_resp

def test_get_articles_success(mock_requests_response):
    """Test successful articles retrieval"""
    with patch("requests.get", return_value=mock_requests_response):
        articles = get_articles("https://example.com/rss")
        
        assert articles is not None
        assert len(articles) == 2  # Sample XML has 2 items
        
        # First article checks
        assert articles[0]["title"] == "Sample Article Title"
        assert articles[0]["link"] == "https://example.com/sample-article"
        assert "This is a description" in articles[0]["description"]
        assert "id" in articles[0]
        
        # Second article checks
        assert articles[1]["title"] == "Second Sample Article"
        assert articles[1]["link"] == "https://example.com/second-article"

def test_get_articles_with_max_limit(mock_requests_response):
    """Test articles retrieval with max limit"""
    with patch("requests.get", return_value=mock_requests_response):
        articles = get_articles("https://example.com/rss", max_articles=1)
        
        assert articles is not None
        assert len(articles) == 1  # Only first article returned
        assert articles[0]["title"] == "Sample Article Title"

def test_get_articles_http_error():
    """Test article retrieval with HTTP error"""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    
    with patch("requests.get", return_value=mock_resp):
        articles = get_articles("https://example.com/rss")
        assert articles == []

def test_get_articles_connection_error():
    """Test article retrieval with connection error"""
    with patch("requests.get", side_effect=Exception("Connection error")):
        articles = get_articles("https://example.com/rss")
        assert articles == []

@pytest.mark.parametrize("content,expected", [
    (b"<invalid>xml</", []),  # Invalid XML
    (b"<?xml version='1.0'?><rss><channel></channel></rss>", []),  # No items
])
def test_get_articles_xml_parsing(content, expected):
    """Test article retrieval with XML parsing issues"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = content
    
    with patch("requests.get", return_value=mock_resp):
        articles = get_articles("https://example.com/rss")
        assert articles == expected