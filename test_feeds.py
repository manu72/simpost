#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check feed retrieval from RSS URLs in feeds.json
"""

import json
import requests
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

def test_feeds():
    print('Testing feed retrieval:')
    
    # Load feed configurations
    with open("feeds.json", "r") as file:
        feeds = json.load(file)
    
    for feed in feeds:
        print(f"\n=== {feed['name']} ===")
        print(f"URL: {feed['rss_url']}")
        print('Fetching feed...')
        
        try:
            # Manual RSS feed parsing without feedparser
            response = requests.get(feed['rss_url'])
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                continue
                
            # Parse XML content
            try:
                root = ET.fromstring(response.content)
                
                # Try to find items in RSS format
                items = root.findall('.//item')
                if not items:
                    # Try Atom format
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                print(f'Found {len(items)} entries')
                
                if items:
                    # Get the first item/entry (latest article)
                    latest = items[0]
                    
                    # Extract title (works for both RSS and Atom)
                    title_elem = latest.find('.//title') or latest.find('.//{http://www.w3.org/2005/Atom}title')
                    title = title_elem.text if title_elem is not None else "No title found"
                    
                    # Extract link (RSS vs Atom formats differ)
                    link_elem = latest.find('.//link') 
                    if link_elem is not None:
                        if link_elem.text:  # RSS format
                            link = link_elem.text
                        else:  # Might be Atom format
                            link = link_elem.get('href', "No link found")
                    else:
                        link = "No link found"
                    
                    # Extract description/summary
                    desc_elem = (
                        latest.find('.//description') or 
                        latest.find('.//summary') or 
                        latest.find('.//{http://www.w3.org/2005/Atom}summary') or
                        latest.find('.//{http://www.w3.org/2005/Atom}content')
                    )
                    
                    description = desc_elem.text if desc_elem is not None else "No description found"
                    if description and len(description) > 100:
                        description = description[:100] + "..."
                    
                    print(f'Latest title: {title}')
                    print(f'Link: {link}')
                    print(f'Description: {description}')
                else:
                    print('No entries found in the feed')
                    
            except ET.ParseError:
                print("Error: Could not parse XML content")
                
        except Exception as e:
            print(f'Error processing feed: {str(e)}')

if __name__ == "__main__":
    test_feeds() 