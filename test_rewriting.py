#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check article rewriting from the multi_feed_news_automation.py file
"""

import json
import os
import sys
from dotenv import load_dotenv

sys.path.append('simpost')  # Add simpost directory to path

# Import the required functions from our main script
from multi_feed_news_automation import get_latest_article, rewrite_article

# Load environment variables
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: No OpenAI API key found in .env file!")
    print("Please create a .env file with your OPENAI_API_KEY.")
    sys.exit(1)

def main():
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)
    
    # Test with the first feed only to save API costs
    feed = feeds[0]
    print(f"\n=== Testing article rewriting for: {feed['name']} ===")
    print(f"URL: {feed['rss_url']}")
    
    # Get the latest article
    article = get_latest_article(feed["rss_url"])
    if not article:
        print("Failed to retrieve article")
        return
        
    print(f"\nOriginal article title: {article['title']}")
    print(f"Original article link: {article['link']}")
    print(f"Original description preview: {article['description'][:150]}...")
    
    # Rewrite the article
    print("\nRewriting article with OpenAI...")
    try:
        rewritten_content = rewrite_article(article, feed["prompt"])
        
        print("\n=== Rewritten content ===")
        print(rewritten_content)
        print("=== End of rewritten content ===")
    except Exception as e:
        print(f"❌ Error rewriting article: {str(e)}")

if __name__ == "__main__":
    main() 