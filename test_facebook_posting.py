#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for isolating and debugging Facebook posting functionality
Uses page-specific access tokens from feeds.json
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fallback global token (deprecated)
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# Load feed configurations to get Facebook page IDs and tokens
with open("feeds.json", "r") as file:
    feeds = json.load(file)

def test_facebook_token(access_token, token_description=""):
    """Test if a Facebook access token is valid by making a simple request"""
    if not access_token:
        print(f"❌ No access token provided for {token_description}")
        return False
        
    url = "https://graph.facebook.com/v19.0/me"  # Updated to latest API version
    params = {"access_token": access_token}
    
    print(f"Testing Facebook access token {token_description}...")
    try:
        response = requests.get(url, params=params)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Access token is valid!")
            data = response.json()
            print(f"Token belongs to: {data.get('name', 'Unknown')} (ID: {data.get('id', 'Unknown')})")
            return True
        else:
            print(f"❌ Access token validation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing access token: {str(e)}")
        return False

def test_page_permissions(page_id, access_token, feed_name=""):
    """Test if the token has permissions to post to a specific page"""
    if not access_token:
        print(f"❌ No access token provided for page {page_id} ({feed_name})")
        return False
        
    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {"access_token": access_token, "fields": "name,access_token"}
    
    print(f"\nTesting permissions for page ID: {page_id} ({feed_name})")
    try:
        response = requests.get(url, params=params)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Can access page: {data.get('name', 'Unknown')}")
            if 'access_token' in data:
                print("✅ Have access token for this page (can publish content)")
                return True
            else:
                print("❌ Missing page access token (cannot publish content)")
                return False
        else:
            print(f"❌ Cannot access page: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error checking page permissions: {str(e)}")
        return False

def post_to_facebook(post_text, link, page_id, access_token, feed_name=""):
    """Attempt to post to a Facebook page"""
    if not access_token:
        print(f"❌ No access token provided for page {page_id} ({feed_name})")
        return False
        
    # First try with v19.0 (latest as of 2024)
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = {
        "message": f"{post_text}\n\nRead more: {link}",
        "access_token": access_token
    }
    
    print(f"\nAttempting to post to page ID: {page_id} ({feed_name})")
    print(f"Using API version: v19.0")
    print(f"Message preview: {post_text[:50]}...")
    
    try:
        response = requests.post(url, data=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Posted successfully to page {page_id}!")
            return True
        else:
            # If v19.0 fails, fallback to v12.0 (which is used in the main script)
            print(f"❌ Failed with v19.0, trying v12.0...")
            url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
            response = requests.post(url, data=data)
            print(f"v12.0 Response status code: {response.status_code}")
            print(f"v12.0 Response content: {response.text}")
            
            if response.status_code == 200:
                print(f"✅ Posted successfully to page {page_id} with v12.0!")
                return True
            else:
                print(f"❌ Failed to post to page {page_id} with both API versions")
                return False
    except Exception as e:
        print(f"❌ Error posting to Facebook: {str(e)}")
        return False

def check_feeds_json_structure():
    """Check if feeds.json has the right structure for page access tokens"""
    missing_tokens = 0
    empty_tokens = 0
    
    for feed in feeds:
        if "facebook_page_id" in feed:
            if "page_access_token" not in feed:
                print(f"❌ Missing page_access_token field for {feed.get('name', 'Unknown feed')}")
                missing_tokens += 1
            elif not feed["page_access_token"]:
                print(f"❌ Empty page_access_token for {feed.get('name', 'Unknown feed')}")
                empty_tokens += 1
    
    if missing_tokens > 0:
        print(f"⚠️ Found {missing_tokens} feeds missing page_access_token field")
        print("   Run the fix_facebook_tokens.py script to update your feeds.json file")
    
    if empty_tokens > 0:
        print(f"⚠️ Found {empty_tokens} feeds with empty page_access_token")
        print("   Fill in these tokens with valid Facebook Page Access Tokens")
    
    return missing_tokens == 0 and empty_tokens == 0

def suggest_fixes(page_tokens_valid, structure_ok):
    """Suggest fixes based on test results"""
    print("\n" + "="*50)
    print("DIAGNOSTIC SUMMARY")
    print("="*50)
    
    if not structure_ok:
        print("❌ CONFIGURATION ISSUE:")
        print("   1. Your feeds.json file is missing page_access_token fields")
        print("   2. Run the fix_facebook_tokens.py script to update its structure")
        print("   3. Fill in the page_access_token for each feed with a Facebook page ID")
    
    if not page_tokens_valid:
        print("❌ PAGE ACCESS TOKEN ISSUES:")
        print("   1. One or more page access tokens are invalid or have insufficient permissions")
        print("   2. For each page, generate a new token with these permissions:")
        print("      - pages_read_engagement")
        print("      - pages_manage_posts")
        print("      - publish_pages")
        print("   3. Make sure you're generating Page Access Tokens (not User Access Tokens)")
        print("   4. Update your feeds.json with these tokens")
    
    if structure_ok and page_tokens_valid:
        print("✅ YOUR CONFIGURATION LOOKS GOOD!")
        print("   If you're still experiencing issues, it might be related to:")
        print("   1. Content policy violations")
        print("   2. Rate limiting")
        print("   3. Page restrictions based on category")

def main():
    print("="*50)
    print("FACEBOOK POSTING DIAGNOSTIC TEST")
    print("="*50)
    
    # Test 1: Check if feeds.json has the right structure
    structure_ok = check_feeds_json_structure()
    
    # Test 2: Check legacy global token if available
    if FACEBOOK_PAGE_ACCESS_TOKEN:
        print("\n📌 Testing legacy global token (deprecated):")
        test_facebook_token(FACEBOOK_PAGE_ACCESS_TOKEN, "from .env file")
        print("⚠️ The global token approach is deprecated, please use page-specific tokens")
    
    # Test 3: Check each page's token and permissions
    page_tokens_valid = True
    for feed in feeds:
        page_id = feed.get("facebook_page_id")
        page_token = feed.get("page_access_token")
        feed_name = feed.get("name", "Unknown feed")
        
        if page_id and page_token:
            print(f"\n📌 Testing token for {feed_name} (ID: {page_id}):")
            token_valid = test_facebook_token(page_token, f"for {feed_name}")
            
            if token_valid:
                permissions_valid = test_page_permissions(page_id, page_token, feed_name)
                page_tokens_valid = page_tokens_valid and permissions_valid
                
                # Only attempt posting if the token and permissions are valid
                if permissions_valid:
                    test_message = f"This is a test post from {feed_name} via SimPost diagnostic tool."
                    test_link = "https://example.com"
                    post_to_facebook(test_message, test_link, page_id, page_token, feed_name)
            else:
                page_tokens_valid = False
    
    # Suggest fixes based on test results
    suggest_fixes(page_tokens_valid, structure_ok)

if __name__ == "__main__":
    main() 