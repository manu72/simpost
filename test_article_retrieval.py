#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check article retrieval from the multi_feed_news_automation.py file
"""

import json
import sys
sys.path.append('simpost')  # Add simpost directory to path

# Import the get_latest_article function from our main script
from multi_feed_news_automation import get_latest_article

def main():
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)

    for feed in feeds:
        print(f"\n=== Testing: {feed['name']} ===")
        print(f"URL: {feed['rss_url']}")

        article = get_latest_article(feed["rss_url"])

        if article:
            print("\nSuccessfully retrieved article:")
            print(f"Title: {article['title']}")
            print(f"Link: {article['link']}")
            print(f"Description preview: {article['description'][:150]}...")
        else:
            print("Failed to retrieve article")

if __name__ == "__main__":
    main()
