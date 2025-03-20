#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check article verification using OpenAI web search from multi_feed_news_automation.py
"""

import json
import os
import sys
from dotenv import load_dotenv

# Add the current directory to path to find simpost package
sys.path.append('.')

# Import the required functions from our main script
from simpost.multi_feed_news_automation import get_latest_article, rewrite_article, verify_rewritten_article

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
    print(f"\n=== Testing article verification for: {feed['name']} ===")
    print(f"URL: {feed['rss_url']}")
    
    # Get the latest article
    article = get_latest_article(feed["rss_url"])
    if not article:
        print("Failed to retrieve article")
        return
        
    print(f"\nOriginal article title: {article['title']}")
    print(f"Original article link: {article['link']}")
    
    # Rewrite the article
    print("\nRewriting article with OpenAI...")
    try:
        rewritten_content = rewrite_article(article, feed["prompt"], feed["system_prompt"])
        
        print("\n=== Rewritten content ===")
        print(rewritten_content)
        print("=== End of rewritten content ===")
        
        # Verify the rewritten content
        print("\nVerifying content using OpenAI web search...")
        is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])
        
        print("\n=== Verification Results ===")
        if is_verified:
            print("✅ VERIFIED")
        else:
            print("❌ NOT VERIFIED")
        print(f"Message: {verification_message}")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 