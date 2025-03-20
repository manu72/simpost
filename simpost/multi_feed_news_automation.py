#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Multi-feed news automation script for the simpost project.
This script processes multiple RSS feeds as defined in feeds.json
rewrites the articles using OpenAI, verifies them using OpenAI web search,
and posts verified content to Facebook Pages.
"""

# Import statements will go here
import xml.etree.ElementTree as ET
import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

MODEL = "gpt-4o"

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Load feed configurations from JSON file
with open("feeds.json", "r") as file:
    feeds = json.load(file)

# Function to fetch latest article from RSS Feed
def get_latest_article(feed_url):
    try:
        response = requests.get(feed_url, timeout=30)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch feed: {feed_url} (Status code: {response.status_code})")
            return None

        # Parse XML content
        try:
            root = ET.fromstring(response.content)

            # Try to find items in RSS format
            items = root.findall('.//item')
            if not items:
                # Try Atom format
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

            if not items:
                print(f"⚠️ No articles found in {feed_url}")
                return None

            # Get the first item/entry (latest article)
            latest = items[0]

            # Extract title (works for both RSS and Atom)
            title_elem = latest.find('.//title')
            if title_elem is None:
                title_elem = latest.find('.//{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else "No title found"

            # Extract link (RSS vs Atom formats differ)
            link_elem = latest.find('.//link')
            link = None
            if link_elem is not None:
                if link_elem.text:  # RSS format
                    link = link_elem.text
                else:  # Might be Atom format
                    link = link_elem.get('href')

            # If still no link, try other formats
            if not link:
                # Try to find enclosure URL
                enclosure = latest.find('.//enclosure')
                if enclosure is not None:
                    link = enclosure.get('url')

            # Extract description/summary
            desc_elem = latest.find('.//description')
            if desc_elem is None:
                desc_elem = latest.find('.//summary')
            if desc_elem is None:
                desc_elem = latest.find('.//{http://www.w3.org/2005/Atom}summary')
            if desc_elem is None:
                desc_elem = latest.find('.//{http://www.w3.org/2005/Atom}content')

            description = desc_elem.text if desc_elem is not None else ""

            # If CDATA content
            if description and description.strip() == "" and desc_elem is not None:
                # Try to get CDATA content
                if len(desc_elem) > 0:  # Has child elements
                    description = ET.tostring(desc_elem, encoding='unicode')
                    # Remove the outer tags
                    start_tag = description.find('>') + 1
                    end_tag = description.rfind('</')
                    if start_tag > 0 and end_tag > start_tag:
                        description = description[start_tag:end_tag]

            # Extract content if description is still empty
            if not description or description.strip() == "":
                content_elem = latest.find('.//content:encoded')
                if content_elem is not None:
                    description = content_elem.text

            return {
                "title": title,
                "description": description,
                "content": description,  # Using description as content
                "link": link
            }

        except ET.ParseError as e:
            print(f"⚠️ Error parsing XML from {feed_url}: {str(e)}")
            return None

    except Exception as e:
        print(f"⚠️ Error fetching feed {feed_url}: {str(e)}")
        return None

# Function to generate custom post content using OpenAI
def rewrite_article(article, prompt):
    prompt_text = f"{prompt}\n\nTitle: {article['title']}\nContent: {article['content']}"

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": "You are a professional social media copywriter."},
            {"role": "user", "content": prompt_text}
        ],
        temperature=0.7,
        max_output_tokens=1000
    )

    return response.output_text.strip()

# Function to verify rewritten content using OpenAI web search
def verify_rewritten_article(rewritten_content, article_link):
    verification_prompt = (
        f"Fact-check this social media post against the latest news:\n\n"
        f"{rewritten_content}\n\n"
        f"Original article link: {article_link}\n\n"
        f"Is this post factually accurate based on the latest information? "
        f"If the post is factually correct, respond with 'VERIFIED' followed by a brief explanation. "
        f"If it contains outdated or misleading information, respond with 'NOT VERIFIED' followed by a brief explanation of the issues."
    )

    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search_preview"}],
        input=verification_prompt,
        max_output_tokens=500,
        temperature=0
    )

    verification_result = response.output_text.strip()
    
    # Fix verification logic to avoid false positives
    # Check if it starts with "VERIFIED" or has "NOT VERIFIED"
    is_verified = (
        "NOT VERIFIED" not in verification_result.upper() and 
        "VERIFIED" in verification_result.upper()
    )
    
    return is_verified, verification_result

# Function to log rewritten articles to a Markdown file
def log_rewritten_article(feed_name, rewritten_content):
    filename = f"logs/{feed_name.replace(' ', '_')}.md"
    os.makedirs("logs", exist_ok=True)
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"## {feed_name} - New Post\n\n")
        file.write(rewritten_content + "\n\n---\n\n")
    print(f"📁 Logged rewritten post for {feed_name}")

# Function to post content to Facebook
def post_to_facebook(post_text, link, page_id):
    url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
    data = {
        "message": f"{post_text}\n\nRead more: {link}",
        "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        print(f"✅ Posted successfully to page {page_id}!")
    else:
        print(f"❌ Failed to post to page {page_id}: {response.text}")

# Main script to process all feeds
if __name__ == "__main__":
    for feed in feeds:
        print(f"📢 Processing feed: {feed['name']} ({feed['rss_url']})")

        article = get_latest_article(feed["rss_url"])
        if not article:
            continue

        print(f"📝 Rewriting article: {article['title']}")
        rewritten_content = rewrite_article(article, feed["prompt"])
        log_rewritten_article(feed["name"], rewritten_content)

        print(f"🔍 Verifying article content...")
        is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])

        print("\n" + "="*50)
        print(f"📋 Generated content for {feed['name']}:")
        print("-"*50)
        print(rewritten_content)
        print("-"*50)

        if is_verified:
            print(f"✅ VERIFIED: {verification_message}")
            if feed.get("facebook_page_id"):
                post_to_facebook(rewritten_content, article["link"], feed["facebook_page_id"])
            else:
                print("ℹ️ No Facebook page ID provided, skipping posting")
        else:
            print(f"❌ NOT VERIFIED: {verification_message}")
            print("⚠️ Content was not published due to verification failure")

        print("="*50 + "\n")
