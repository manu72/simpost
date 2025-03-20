#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the new article ID format with date prefix
"""

import sys
import datetime

# Add the current directory to path to find simpost package
sys.path.append('.')

# Import the required function from our main script
from simpost.multi_feed_news_automation import create_article_id

def test_article_id_format():
    """Test the article ID format with date prefix"""
    print("\n=== Testing Article ID Format ===")
    
    # Test with sample article data
    title = "Sample Article Title"
    link = "https://example.com/sample-article"
    
    # Generate ID
    article_id = create_article_id(title, link)
    
    # Get today's date in YYYYMMDD format
    today_date = datetime.datetime.now().strftime("%Y%m%d")
    
    # Check if ID starts with today's date followed by underscore
    if article_id.startswith(f"{today_date}_"):
        print(f"✅ ID has correct date prefix: {article_id}")
        print(f"   Date prefix: {article_id.split('_')[0]}")
        print(f"   Hash part: {article_id.split('_')[1]}")
    else:
        print(f"❌ ID does not have correct date prefix: {article_id}")
        print(f"   Expected prefix: {today_date}_")

if __name__ == "__main__":
    test_article_id_format() 