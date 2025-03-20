"""
Unit tests for the feed retrieval functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from simpost.multi_feed_news_automation import get_latest_article

@pytest.fixture
def mock_requests_response(mock_rss_response):
    """Create a mock requests response object"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = mock_rss_response.encode()
    return mock_resp

def test_get_latest_article_success(mock_requests_response):
    """Test successful article retrieval"""
    with patch("requests.get", return_value=mock_requests_response):
        article = get_latest_article("https://example.com/rss")
        
        assert article is not None
        assert article["title"] == "Sample Article Title"
        assert article["link"] == "https://example.com/sample-article"
        assert "This is a description" in article["description"]
        assert "id" in article

def test_get_latest_article_http_error():
    """Test article retrieval with HTTP error"""
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    
    with patch("requests.get", return_value=mock_resp):
        article = get_latest_article("https://example.com/rss")
        assert article is None

def test_get_latest_article_connection_error():
    """Test article retrieval with connection error"""
    with patch("requests.get", side_effect=Exception("Connection error")):
        article = get_latest_article("https://example.com/rss")
        assert article is None

@pytest.mark.parametrize("content,expected", [
    (b"<invalid>xml</", None),  # Invalid XML
    (b"<?xml version='1.0'?><rss><channel></channel></rss>", None),  # No items
])
def test_get_latest_article_xml_parsing(content, expected):
    """Test article retrieval with XML parsing issues"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = content
    
    with patch("requests.get", return_value=mock_resp):
        article = get_latest_article("https://example.com/rss")
        assert article == expected