#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the storage and duplicate checking functionality
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to path to find simpost package
sys.path.append('.')

# Import the required functions from our main script
from simpost.multi_feed_news_automation import (
    create_article_id, is_article_processed, 
    save_retrieved_article, save_rewritten_article, mark_article_as_posted,
    get_articles, parse_article_item,
    DATA_DIR, RETRIEVED_ARTICLES_DIR, REWRITTEN_ARTICLES_DIR
)

# Function to get the latest article from a feed (replacement for get_latest_article)
def get_latest_article(feed_url):
    """Get the latest article from a feed"""
    articles = get_articles(feed_url, 1)
    if articles and len(articles) > 0:
        return articles[0]
    return None

def view_directory_structure():
    """Display the data directory structure"""
    print("\n=== Data Directory Structure ===")
    for root, dirs, files in os.walk(DATA_DIR):
        level = root.replace(DATA_DIR, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

def test_article_storage():
    """Test the article storage functionality"""
    print("\n=== Testing Article Storage ===")
    
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)
    
    # Use the first feed for testing
    feed = feeds[0]
    feed_name = feed['name'].replace(' ', '_')
    
    print(f"Using feed: {feed['name']}")
    
    # Get the latest article
    article = get_latest_article(feed["rss_url"])
    if not article:
        print("Failed to retrieve article")
        return
    
    # Print article details
    print(f"\nRetrieved article:")
    print(f"Title: {article['title']}")
    print(f"ID: {article['id']}")
    print(f"Link: {article['link']}")
    
    # Check if the article has already been processed
    if is_article_processed(feed_name, article['id']):
        print(f"\n✅ Article already exists in storage (duplicate detection working)")
        
        # Display the existing article
        rewritten_file = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name, f"{article['id']}.json")
        with open(rewritten_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        print(f"\nExisting rewritten article:")
        print(f"Rewritten at: {existing_data['rewritten_at']}")
        print(f"Is verified: {existing_data['is_verified']}")
        print(f"Is posted: {existing_data['is_posted']}")
        
    else:
        print(f"\n✅ Article is new (not in storage yet)")
        
        # Save the retrieved article
        retrieved_path = save_retrieved_article(feed_name, article)
        print(f"Saved retrieved article to: {retrieved_path}")
        
        # Create a dummy rewritten article for testing
        rewritten_content = f"Test rewritten content for {article['title']}"
        verification_message = "VERIFIED - Test verification"
        
        # Save the rewritten article
        rewritten_path = save_rewritten_article(
            feed_name,
            article['id'],
            article,
            rewritten_content,
            True,  # is_verified
            verification_message
        )
        print(f"Saved rewritten article to: {rewritten_path}")
        
        # Mark it as posted
        mark_article_as_posted(feed_name, article['id'])
        print(f"Marked article as posted")
        
        # Verify it was marked as posted
        with open(rewritten_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data['is_posted']:
            print(f"✅ Article was successfully marked as posted")
        else:
            print(f"❌ Article was NOT marked as posted")

if __name__ == "__main__":
    # First, show the directory structure
    view_directory_structure()
    
    # Then test article storage
    test_article_storage() 