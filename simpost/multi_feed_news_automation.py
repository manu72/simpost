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
import hashlib
import datetime
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

# Create directory structure for storing articles
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RETRIEVED_ARTICLES_DIR = os.path.join(DATA_DIR, "retrieved_articles")
REWRITTEN_ARTICLES_DIR = os.path.join(DATA_DIR, "rewritten_articles")
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RETRIEVED_ARTICLES_DIR, exist_ok=True)
os.makedirs(REWRITTEN_ARTICLES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Load feed configurations from JSON file
with open("feeds.json", "r") as file:
    feeds = json.load(file)

# Function to create a unique ID for an article
def create_article_id(title, link):
    # Add date prefix in YYYYMMDD_ format
    date_prefix = datetime.datetime.now().strftime("%Y%m%d_")
    unique_string = f"{title}|{link}"
    return date_prefix + hashlib.md5(unique_string.encode()).hexdigest()

# Function to check if article has already been processed
def is_article_processed(feed_name, article_id):
    # Check if the article has been rewritten
    rewritten_file = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name, f"{article_id}.json")
    return os.path.exists(rewritten_file)

# Function to fetch latest article from RSS Feed
def get_latest_article(feed_url):
    try:
        response = requests.get(feed_url, timeout=30)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch feed: {feed_url} (Status code: {response.status_code})")
            return None

        # Debug: Print raw XML content
        print("\n=== Raw XML Content ===")
        print(response.content.decode('utf-8')[:2000] + "...")  # First 1000 chars
        
        # Parse XML content
        try:
            # Parse root first to inspect namespaces
            root = ET.fromstring(response.content)
            
            # Debug: Print actual namespaces from the XML
            print("\n=== XML Namespaces ===")
            for prefix, uri in root.nsmap.items() if hasattr(root, 'nsmap') else []:
                print(f"Prefix: {prefix}, URI: {uri}")
            
            # Extract namespaces from root element attributes
            namespaces = {}
            for key, value in root.attrib.items():
                if key.startswith('xmlns:'):
                    prefix = key.split(':')[1]
                    namespaces[prefix] = value
            
            print("\n=== Extracted Namespaces ===")
            print(namespaces)
            
            # Register common namespaces plus any found in the document
            namespaces.update({
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'atom': 'http://www.w3.org/2005/Atom',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'media': 'http://search.yahoo.com/mrss/'
            })

            # Try to find items in RSS format
            items = root.findall('.//item')
            if not items:
                # Try Atom format
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

            if not items:
                print(f"⚠️ No articles found in {feed_url}")
                return None

            print(f"\n=== Found {len(items)} items ===")
            
            # Get the first item/entry (latest article)
            latest = items[0]
            
            # Debug: Print the first item's XML
            print("\n=== Latest Item XML ===")
            print(ET.tostring(latest, encoding='unicode', method='xml'))

            # Extract title (works for both RSS and Atom)
            title_elem = latest.find('.//title')
            if title_elem is None:
                title_elem = latest.find('.//{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else "No title found"
            print(f"\nTitle: {title}")

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
            print(f"Link: {link}")

            # First try to get the full content from content:encoded
            content = ""
            
            # Try different namespace patterns for content:encoded
            content_encoded_elem = None
            for xpath in [
                './/content:encoded',
                './/{http://purl.org/rss/1.0/modules/content/}encoded',
                './/content:encoded',
                './/encoded'
            ]:
                try:
                    content_encoded_elem = latest.find(xpath, namespaces)
                    if content_encoded_elem is not None and content_encoded_elem.text:
                        content = content_encoded_elem.text
                        print(f"\nFound content using xpath: {xpath}")
                        break
                except Exception as e:
                    print(f"XPath {xpath} failed: {str(e)}")
                    continue
            
            # If content:encoded not found or empty, fall back to description
            if not content or content.strip() == "":
                print("\nFalling back to description...")
                # Extract description/summary
                desc_elem = latest.find('.//description')
                if desc_elem is None:
                    desc_elem = latest.find('.//summary')
                if desc_elem is None:
                    desc_elem = latest.find('.//{http://www.w3.org/2005/Atom}summary')
                if desc_elem is None:
                    desc_elem = latest.find('.//{http://www.w3.org/2005/Atom}content')

                description = desc_elem.text if desc_elem is not None else ""
                print(f"Description found: {bool(description)}")

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
                
                content = description

            print(f"\nFinal content length: {len(content)}")

            # Extract publication date
            pub_date_elem = latest.find('.//pubDate')
            if pub_date_elem is None:
                pub_date_elem = latest.find('.//{http://www.w3.org/2005/Atom}published')
            pub_date = pub_date_elem.text if pub_date_elem is not None else datetime.datetime.now().isoformat()

            # Extract guid/id
            guid_elem = latest.find('.//guid')
            guid = guid_elem.text if guid_elem is not None else None

            # Extract author/creator
            creator_elem = latest.find('.//dc:creator', namespaces) or latest.find('.//{http://purl.org/dc/elements/1.1/}creator')
            creator = creator_elem.text if creator_elem is not None else None

            # Extract media:thumbnail if available
            thumbnail_elem = latest.find('.//media:thumbnail', namespaces) or latest.find('.//{http://search.yahoo.com/mrss/}thumbnail')
            thumbnail_url = thumbnail_elem.get('url') if thumbnail_elem is not None else None

            article = {
                "title": title,
                "description": content[:500] + "..." if len(content) > 500 else content,  # First 500 chars as description
                "content": content,  # Full content
                "link": link,
                "pub_date": pub_date,
                "retrieved_at": datetime.datetime.now().isoformat(),
                "guid": guid,
                "creator": creator,
                "thumbnail_url": thumbnail_url
            }

            # Create a unique ID for the article
            article_id = create_article_id(title, link)
            article["id"] = article_id

            return article

        except ET.ParseError as e:
            print(f"⚠️ Error parsing XML from {feed_url}: {str(e)}")
            print("Raw content that failed to parse:")
            print(response.content.decode('utf-8'))
            return None

    except Exception as e:
        print(f"⚠️ Error fetching feed {feed_url}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Function to save retrieved article
def save_retrieved_article(feed_name, article):
    feed_dir = os.path.join(RETRIEVED_ARTICLES_DIR, feed_name.replace(' ', '_'))
    os.makedirs(feed_dir, exist_ok=True)
    
    file_path = os.path.join(feed_dir, f"{article['id']}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(article, f, indent=2, ensure_ascii=False)
    
    return file_path

# Function to generate custom post content using OpenAI
def rewrite_article(article, prompt, system_prompt):
    prompt_text = f"{prompt}\n\nTitle: {article['title']}\nDescription: {article['description']}\nContent: {article['content']}"

    response = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text}
        ],
        temperature=0.5,
        max_output_tokens=1000
    )

    return response.output_text.strip()

# Function to save rewritten article
def save_rewritten_article(feed_name, article_id, original_article, rewritten_content, is_verified, verification_message):
    feed_dir = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name.replace(' ', '_'))
    os.makedirs(feed_dir, exist_ok=True)
    
    data = {
        "id": article_id,
        "original_article": original_article,
        "rewritten_content": rewritten_content,
        "is_verified": is_verified,
        "verification_message": verification_message,
        "rewritten_at": datetime.datetime.now().isoformat(),
        "is_posted": False
    }
    
    file_path = os.path.join(feed_dir, f"{article_id}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return file_path

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
    filename = os.path.join(LOGS_DIR, f"{feed_name.replace(' ', '_')}.md")
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"## {feed_name} - New Post ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        file.write(rewritten_content + "\n\n---\n\n")
    print(f"📁 Logged rewritten post for {feed_name}")

# Function to mark article as posted
def mark_article_as_posted(feed_name, article_id):
    file_path = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name.replace(' ', '_'), f"{article_id}.json")
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["is_posted"] = True
        data["posted_at"] = datetime.datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

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
        return True
    else:
        print(f"❌ Failed to post to page {page_id}: {response.text}")
        return False

# Main function to process all feeds
def main():
    for feed in feeds:
        if not feed.get("active", True):
            print(f"⏭️ Skipping inactive feed: {feed['name']}")
            continue

        print(f"📢 Processing feed: {feed['name']} ({feed['rss_url']})")
        
        # Get the latest article
        article = get_latest_article(feed["rss_url"])
        if not article:
            print(f"⚠️ Could not retrieve article from {feed['name']}")
            continue
        
        # Check if we've already processed this article
        if is_article_processed(feed['name'].replace(' ', '_'), article['id']):
            print(f"⏭️ Skipping already processed article: {article['title']}")
            continue
        
        # Save the retrieved article
        retrieved_path = save_retrieved_article(feed['name'].replace(' ', '_'), article)
        print(f"💾 Saved retrieved article to {retrieved_path}")

        # Rewrite the article
        print(f"📝 Rewriting article: {article['title']}")
        # Use feed-specific system prompt or default to a generic one if not provided
        system_prompt = feed.get("system_prompt", "You are a professional social media copywriter specializing in news and current events.")
        rewritten_content = rewrite_article(article, feed["prompt"], system_prompt)
        log_rewritten_article(feed["name"], rewritten_content)

        # Verify the rewritten content
        print(f"🔍 Verifying article content...")
        is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"])
        
        # Save the rewritten article
        rewritten_path = save_rewritten_article(
            feed['name'].replace(' ', '_'), 
            article['id'], 
            article, 
            rewritten_content, 
            is_verified, 
            verification_message
        )
        print(f"💾 Saved rewritten article to {rewritten_path}")

        # Display results
        print("\n" + "="*50)
        print(f"📋 Generated content for {feed['name']}:")
        print("-"*50)
        print(rewritten_content)
        print("-"*50)

        if is_verified:
            print(f"✅ VERIFIED: {verification_message}")
            if feed.get("facebook_page_id"):
                if post_to_facebook(rewritten_content, article["link"], feed["facebook_page_id"]):
                    # Mark the article as posted
                    mark_article_as_posted(feed['name'].replace(' ', '_'), article['id'])
            else:
                print("ℹ️ No Facebook page ID provided, skipping posting")
        else:
            print(f"❌ NOT VERIFIED: {verification_message}")
            print("⚠️ Content was not published due to verification failure")

        print("="*50 + "\n")

# Main script to process all feeds
if __name__ == "__main__":
    main()
