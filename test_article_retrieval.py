#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check article retrieval from the multi_feed_news_automation.py file
"""

import json
import os
import sys
#from pprint import pprint

# Import the get_latest_article function from our main script
from simpost.multi_feed_news_automation import get_latest_article

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)



def main():
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)

    for feed in feeds:
        print(f"\n{'='*50}")
        print(f"Testing Feed: {feed['name']}")
        print(f"URL: {feed['rss_url']}")
        print('='*50)

        article = get_latest_article(feed["rss_url"])

        if article:
            print("\n✅ Successfully retrieved article:")
            print(f"\nArticle Details:")
            print(f"Title: {article['title']}")
            print(f"Description: {article['description']}")
            print(f"Link: {article['link']}")
            print(f"GUID: {article.get('guid', 'Not found')}")
            print(f"Author: {article.get('creator', 'Not found')}")
            print(f"Thumbnail: {article.get('thumbnail_url', 'Not found')}")
            print(f"Publication Date: {article['pub_date']}")
            
            print("\nContent Preview:")
            content_preview = article['content'][:500] + "..." if len(article['content']) > 500 else article['content']
            print("-"*50)
            print(content_preview)
            print("-"*50)
            
            print(f"\nFull Content Length: {len(article['content'])} characters")
            
        else:
            print("❌ Failed to retrieve article")

        print("\n")

if __name__ == "__main__":
    main()
