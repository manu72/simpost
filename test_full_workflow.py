#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check the full workflow (retrieve, rewrite, verify) without posting to Facebook
"""

import os
import sys
import json
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
    # Choose which feed to test (0, 1, or 2)
    feed_index = 0
    
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)
    
    # Get the selected feed
    feed = feeds[feed_index]
    print(f"\n=== Testing full workflow for: {feed['name']} ===")
    print(f"URL: {feed['rss_url']}")
    
    # Step 1: Get the latest article
    print("\n📡 Step 1: Retrieving latest article...")
    article = get_latest_article(feed["rss_url"])
    if not article:
        print("❌ Failed to retrieve article")
        return
    
    print(f"✅ Successfully retrieved article")
    print(f"   Title: {article['title']}")
    print(f"   Link: {article['link']}")
    print(f"   Description preview: {article['description'][:100]}...")
    
    # Step 2: Rewrite the article
    print("\n🖋️ Step 2: Rewriting article with OpenAI...")
    try:
        rewritten_content = rewrite_article(article, feed["prompt"], feed["system_prompt"])
        
        print("✅ Successfully rewrote article")
        print("\n   === Rewritten content ===")
        print(f"   {rewritten_content}")
        print("   === End of rewritten content ===")
        
        # Step 3: Verify the rewritten content
        print("\n🔍 Step 3: Verifying content using OpenAI web search...")
        is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])
        
        print("\n   === Verification Results ===")
        if is_verified:
            print("   ✅ VERIFIED")
        else:
            print("   ❌ NOT VERIFIED")
        print(f"   Message: {verification_message}")
        
        # Step 4: Final result
        print("\n📊 Final Result: ")
        if is_verified:
            print("✅ Article was successfully retrieved, rewritten, and verified")
            print("   In production, this would be posted to Facebook")
        else:
            print("❌ Article was retrieved and rewritten but failed verification")
            print("   In production, this would NOT be posted to Facebook")
        
    except Exception as e:
        print(f"❌ Error during workflow: {str(e)}")

if __name__ == "__main__":
    main() 