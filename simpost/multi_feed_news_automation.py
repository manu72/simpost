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
import time
import requests
import smtplib
from email.message import EmailMessage
from openai import OpenAI
from dotenv import load_dotenv

MODEL = "chatgpt-4o-latest"

# Maximum age of posts to process (in hours)
IGNORE_POSTS_OLDER_THAN = 12

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
SYSTEM_ADMIN_EMAIL = os.getenv("SYSTEM_ADMIN_EMAIL", "manuhume@hotmail.com")

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

    
    if not os.path.exists(rewritten_file):
        return False, False, False
    
    # Read the article data to check verification and posting status
    with open(rewritten_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            is_verified = data.get('is_verified', False)
            is_posted = data.get('is_posted', False)
            return True, is_verified, is_posted
        except json.JSONDecodeError:
            # If file exists but can't be read, consider it not processed
            return False, False, False

    return os.path.exists(rewritten_file)

# Function to parse an individual article item from RSS/Atom feed
def parse_article_item(item, namespaces):
    """Parse a single RSS/Atom item into an article dictionary."""
    # Extract title (works for both RSS and Atom)
    title_elem = item.find('.//title')
    if title_elem is None:
        title_elem = item.find('.//{http://www.w3.org/2005/Atom}title')
    title = title_elem.text if title_elem is not None else "No title found"

    # Extract link (RSS vs Atom formats differ)
    link_elem = item.find('.//link')
    link = None
    if link_elem is not None:
        if link_elem.text:  # RSS format
            link = link_elem.text
        else:  # Might be Atom format
            link = link_elem.get('href')

    # If still no link, try other formats
    if not link:
        # Try to find enclosure URL
        enclosure = item.find('.//enclosure')
        if enclosure is not None:
            link = enclosure.get('url')

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
            content_encoded_elem = item.find(xpath, namespaces)
            if content_encoded_elem is not None and content_encoded_elem.text:
                content = content_encoded_elem.text
                break
        except Exception:
            continue
    
    # If content:encoded not found or empty, fall back to description
    if not content or content.strip() == "":
        # Extract description/summary
        desc_elem = item.find('.//description')
        if desc_elem is None:
            desc_elem = item.find('.//summary')
        if desc_elem is None:
            desc_elem = item.find('.//{http://www.w3.org/2005/Atom}summary')
        if desc_elem is None:
            desc_elem = item.find('.//{http://www.w3.org/2005/Atom}content')

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
        
        content = description

    # Extract publication date
    pub_date_elem = item.find('.//pubDate')
    if pub_date_elem is None:
        pub_date_elem = item.find('.//{http://www.w3.org/2005/Atom}published')
    pub_date = pub_date_elem.text if pub_date_elem is not None else datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Extract guid/id
    guid_elem = item.find('.//guid')
    guid = guid_elem.text if guid_elem is not None else None

    # Extract author/creator
    creator_elem = item.find('.//dc:creator', namespaces) or item.find('.//{http://purl.org/dc/elements/1.1/}creator')
    creator = creator_elem.text if creator_elem is not None else None

    # Extract media:thumbnail if available
    thumbnail_elem = item.find('.//media:thumbnail', namespaces) or item.find('.//{http://search.yahoo.com/mrss/}thumbnail')
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


# Function to fetch articles from RSS Feed
def get_articles(feed_url, max_articles=10):
    """
    Retrieve articles from an RSS or Atom feed.
    
    Args:
        feed_url (str): URL of the RSS/Atom feed
        max_articles (int): Maximum number of articles to retrieve (default: 10)
        
    Returns:
        list: List of article dictionaries or empty list if no articles found
    """
    try:
        response = requests.get(feed_url, timeout=30)
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch feed: {feed_url} (Status code: {response.status_code})")
            return []

        # Debug: Print raw XML content
        print("\n=== Raw XML Content ===")
        print(response.content.decode('utf-8')[:2000] + "...")  # First 2000 chars
        
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
                return []

            total_items = len(items)
            print(f"\n=== Found {total_items} items ===")
            
            # Limit the number of articles to process
            items_to_process = items[:max_articles] if max_articles > 0 else items
            print(f"Processing {len(items_to_process)} of {total_items} articles")
            
            # Process each item
            articles = []
            for i, item in enumerate(items_to_process):
                try:
                    print(f"\n--- Processing article {i+1}/{len(items_to_process)} ---")
                    article = parse_article_item(item, namespaces)
                    if article["title"] and article["link"]:  # Ensure we have at least title and link
                        articles.append(article)
                    else:
                        print(f"⚠️ Skipping article with missing title or link: {article.get('title', 'No title')}")
                except Exception as e:
                    print(f"⚠️ Error parsing article: {str(e)}")
                    continue
            
            print(f"Successfully parsed {len(articles)} articles")
            return articles

        except ET.ParseError as e:
            print(f"⚠️ Error parsing XML from {feed_url}: {str(e)}")
            print("Raw content that failed to parse:")
            print(response.content.decode('utf-8'))
            return []

    except Exception as e:
        print(f"⚠️ Error fetching feed {feed_url}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

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

    # Add retry logic with exponential backoff
    max_retries = 5
    retry_delay = 1  # Start with 1 second delay
    
    for attempt in range(max_retries):
        try:
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
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️ Rate limit exceeded. Waiting {wait_time} seconds before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Maximum retries reached for API call. Error: {str(e)}")
                    raise
            else:
                # If it's not a rate limit error, re-raise it immediately
                print(f"❌ Error calling OpenAI API: {str(e)}")
                raise

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
def verify_rewritten_article(rewritten_content, article_link, article_pub_date=None):
    # Check if article is too old
    if article_pub_date:
        try:
            # Convert pub_date string to datetime
            if isinstance(article_pub_date, str):
                # Try common date formats
                for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"]:
                    try:
                        pub_date = datetime.datetime.strptime(article_pub_date, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If none of the formats work, try without timezone
                    try:
                        pub_date = datetime.datetime.fromisoformat(article_pub_date.replace('Z', ''))
                        # Assume UTC for dates without timezone
                        pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
                    except (ValueError, AttributeError):
                        # If all parsing fails, skip age check
                        pub_date = None
            else:
                pub_date = None
                
            # Calculate age in hours if pub_date was successfully parsed
            if pub_date:
                now = datetime.datetime.now(datetime.timezone.utc)
                age_hours = (now - pub_date).total_seconds() / 3600
                
                if age_hours > IGNORE_POSTS_OLDER_THAN:
                    explanation = f"Article is {age_hours:.1f} hours old, which exceeds the {IGNORE_POSTS_OLDER_THAN} hour limit."
                    print(f"⏭️ Article is too old: {explanation}")
                    return False, f"NOT VERIFIED: {explanation}"
        except Exception as e:
            # If there's any error in date parsing, just log and continue with verification
            print(f"⚠️ Warning: Error checking article age: {str(e)}")
    
    verification_prompt = (
        f"Fact-check this social media post against the latest news. DO NOT use wikipedia or any other sources that are not news sources:\n\n"
        f"{rewritten_content}\n\n"
        f"Original article link: {article_link}\n\n"
        f"Is this post factually accurate journalism based on the latest news information? "
        f"If the post contains outdated or misleading information, respond with 'NOT VERIFIED' followed by a brief explanation of the issues. "
        f"If the post is not outdated or misleading, respond with 'VERIFIED'."
    )

    # Add retry logic with exponential backoff
    max_retries = 5
    retry_delay = 1  # Start with 1 second delay
    
    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                tools=[{"type": "web_search_preview"}],
                input=verification_prompt,
                max_output_tokens=500,
                temperature=0
            )
            
            verification_result = response.output_text.strip()
            
            # Improved verification logic
            # First check if the response explicitly says "NOT VERIFIED" at the beginning
            if verification_result.upper().startswith("NOT VERIFIED"):
                is_verified = False
            # Then check if it explicitly says "VERIFIED" at the beginning
            elif verification_result.upper().startswith("VERIFIED"):
                is_verified = True
            # For mixed messages, check the overall content and meaning
            else:
                # Look for phrases indicating factual accuracy
                positive_indicators = [
                    "factually accurate",
                    "accurately reflects",
                    "no issues found",
                    "correctly states",
                    "accurate representation",
                    "the post is accurate",
                    "is accurate"
                ]
                
                # Look for clear negative indicators
                negative_indicators = [
                    "misleading",
                    "inaccurate",
                    "outdated",
                    "false",
                    "not factual",
                    "incorrect"
                ]
                
                # Count positive and negative signals
                positive_count = sum(1 for indicator in positive_indicators if indicator.lower() in verification_result.lower())
                negative_count = sum(1 for indicator in negative_indicators if indicator.lower() in verification_result.lower())
                
                # Make decision based on indicators
                if positive_count > negative_count:
                    is_verified = True
                else:
                    is_verified = False
            
            return is_verified, verification_result
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️ Rate limit exceeded. Waiting {wait_time} seconds before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Maximum retries reached for API call. Error: {str(e)}")
                    raise
            else:
                # If it's not a rate limit error, re-raise it immediately
                print(f"❌ Error calling OpenAI API: {str(e)}")
                raise

# Function to log rewritten articles to a Markdown file
def log_rewritten_article(feed_name, rewritten_content):
    filename = os.path.join(LOGS_DIR, f"{feed_name.replace(' ', '_')}.md")
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"## {feed_name} - New Post ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
        file.write(rewritten_content + "\n\n---\n\n")
    print(f"📁 Logged rewritten post for {feed_name}")

# Load additional email configuration from environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", SYSTEM_ADMIN_EMAIL)

# Function to send email notification for not verified articles
def send_verification_failure_email(feed_name, article_title, article_link, verification_message, rewritten_content):
    """
    Send an email notification when an article fails verification
    
    Args:
        feed_name (str): Name of the feed
        article_title (str): Title of the article
        article_link (str): Link to the original article
        verification_message (str): Message explaining why verification failed
        rewritten_content (str): The rewritten article that failed verification
    """
    if not SYSTEM_ADMIN_EMAIL:
        print("⚠️ No admin email configured, skipping notification")
        return False
        
    # Create email content
    msg = EmailMessage()
    msg['Subject'] = f'⚠️ SimPost: Article Verification Failed - {feed_name}'
    msg['From'] = EMAIL_SENDER
    msg['To'] = SYSTEM_ADMIN_EMAIL
    
    # Email content
    email_content = f"""
    An article from {feed_name} failed the verification process.
    
    Article: {article_title}
    Original link: {article_link}
    
    Verification failure reason:
    {verification_message}
    
    Rewritten content that failed verification:
    ----------
    {rewritten_content}
    ----------
    
    This is an automated notification from SimPost.
    """
    
    msg.set_content(email_content)
    
    # Save notification to a file as fallback
    fallback_filename = os.path.join(LOGS_DIR, "email_notifications", f"verification_failure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    os.makedirs(os.path.dirname(fallback_filename), exist_ok=True)
    with open(fallback_filename, 'w', encoding='utf-8') as f:
        f.write(f"To: {SYSTEM_ADMIN_EMAIL}\n")
        f.write(f"Subject: {msg['Subject']}\n\n")
        f.write(email_content)
    
    # Try different email sending methods
    sent = False
    
    # Try method 1: Configured SMTP server
    if SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD:
        try:
            print(f"📧 Attempting to send email via configured SMTP server ({SMTP_SERVER})")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                print(f"📧 Sent verification failure notification to {SYSTEM_ADMIN_EMAIL}")
                sent = True
                return True
        except Exception as e:
            print(f"⚠️ Failed to send email via configured SMTP: {str(e)}")
    
    # Try method 2: Local mail server
    if not sent:
        try:
            print("📧 Attempting to send email via local mail server")
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
                print(f"📧 Sent verification failure notification to {SYSTEM_ADMIN_EMAIL}")
                sent = True
                return True
        except Exception as e:
            print(f"⚠️ Failed to send email via local server: {str(e)}")
    
    # Final fallback - inform user about the saved notification
    if not sent:
        print(f"📁 Email notification saved to {fallback_filename}")
        print(f"⚠️ Could not send email notification. Add SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, and SMTP_PASSWORD to your .env file")
        return False

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

# Function to get rewritten articles that are verified but not posted
def get_unposted_verified_articles(feed_name):
    """
    Get verified but unposted articles for a feed
    
    Args:
        feed_name (str): Name of the feed
        
    Returns:
        list: List of tuples containing (article_id, article_data, rewritten_content, article_link)
    """
    feed_dir = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name.replace(' ', '_'))
    
    if not os.path.exists(feed_dir):
        return []
    
    unposted_articles = []
    
    for filename in os.listdir(feed_dir):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(feed_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Check if article is verified but not posted
                if data.get('is_verified', False) and not data.get('is_posted', False):
                    article_id = data.get('id')
                    rewritten_content = data.get('rewritten_content')
                    article_link = data.get('original_article', {}).get('link')
                    article_title = data.get('original_article', {}).get('title', 'No title')
                    
                    if article_id and rewritten_content and article_link:
                        unposted_articles.append((article_id, data, rewritten_content, article_link, article_title))
                        
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {filepath}")
    
    return unposted_articles

# Function to post content to Facebook
def post_to_facebook(post_text, link, page_id, page_access_token=None):
    """
    Post content to a Facebook page
    
    Args:
        post_text (str): The text content to post
        link (str): Link to include in the post
        page_id (str): The Facebook page ID
        page_access_token (str, optional): Page-specific access token. 
                                          If None, falls back to global token.
    
    Returns:
        bool: True if posting was successful, False otherwise
    """
    # Use page-specific token if provided, otherwise fall back to global token
    access_token = page_access_token or FACEBOOK_PAGE_ACCESS_TOKEN
    
    if not access_token:
        print(f"❌ No access token available for page {page_id}")
        print("   Add page_access_token to this feed in feeds.json")
        return False
    
    # Try with latest API version first (v19.0 as of 2024)
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = {
        #"message": f"{post_text}\n\n{link}",
        "message": post_text,
        "link": link,
        "access_token": access_token
    }
    
    try:
        print(f"Attempting to post to Facebook page {page_id}...")
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print(f"✅ Posted successfully to page {page_id}!")
            return True
        else:
            # If v19.0 fails, fallback to v12.0
            print(f"❌ Failed with API v19.0 (Status: {response.status_code})")
            print(f"Error details: {response.text}")
            print("Trying with API v12.0...")
            
            url = f"https://graph.facebook.com/v12.0/{page_id}/feed"
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                print(f"✅ Posted successfully to page {page_id} with API v12.0!")
                return True
            else:
                print(f"❌ Failed to post to page {page_id} with API v12.0 (Status: {response.status_code})")
                print(f"Error details: {response.text}")
                print("Common issues:")
                print("- Invalid or expired access token")
                print("- Missing page permissions (pages_manage_posts, pages_read_engagement)")
                print("- Incorrect page ID")
                print("- Content policy violation")
                return False
    except Exception as e:
        print(f"❌ Exception while posting to Facebook: {str(e)}")
        import traceback
        traceback.print_exc()

    response = requests.post(url, data=data)

    if response.status_code == 200:
        print(f"✅ Posted successfully to page {page_id}!")
        return True
    else:
        print(f"❌ Failed to post to page {page_id}: {response.text}")
        return False

# Main function to process all feeds
def main():
    # Add a small delay between OpenAI API calls to avoid rate limits
    def add_api_call_delay():
        time.sleep(2)  # Small delay between API calls
    
    for feed in feeds:
        if not feed.get("active", True):
            print(f"⏭️ Skipping inactive feed: {feed['name']}")
            continue

        print(f"📢 Processing feed: {feed['name']} ({feed['rss_url']})")
        
        # Get max articles from the feed settings or default to 10
        max_articles = feed.get("max_articles", 10)
        print(f"📊 Max articles to retrieve: {max_articles}")
        
        # Get articles from the feed
        articles = get_articles(feed["rss_url"], max_articles)
        if not articles:
            print(f"⚠️ Could not retrieve any articles from {feed['name']}")
            continue
            
        print(f"📚 Retrieved {len(articles)} articles from {feed['name']}")
        
        # Process each article
        for article in articles:
            print(f"\n🔄 Processing article: {article['title']}")
            
            # Check if we've already processed this article
            is_processed, is_verified, is_posted = is_article_processed(feed['name'].replace(' ', '_'), article['id'])
            
            if is_processed:
                print(f"📝 Article already processed: {article['title']}")
                
                # If the article is verified but not posted, and auto-posting is enabled, post it
                if is_verified and not is_posted and feed.get("facebook_page_id") and feed.get("auto_post", True):
                    print(f"✅ Article already verified but not posted. Attempting to post...")
                    
                    # Get the article data from the file
                    rewritten_file = os.path.join(REWRITTEN_ARTICLES_DIR, feed['name'].replace(' ', '_'), f"{article['id']}.json")
                    with open(rewritten_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Post to Facebook
                    rewritten_content = data.get('rewritten_content')
                    if rewritten_content and post_to_facebook(rewritten_content, article["link"], feed["facebook_page_id"], feed.get("page_access_token")):
                        # Mark the article as posted
                        mark_article_as_posted(feed['name'].replace(' ', '_'), article['id'])
                        print(f"✅ Successfully posted already verified article")
                        
                        # Add delay between posts if specified
                        if len(articles) > 1 and article != articles[-1]:
                            post_delay = feed.get("delay_each_post", 10)  # Default 10 seconds
                            if post_delay > 0:
                                print(f"⏱️ Waiting {post_delay} seconds before processing next article...")
                                time.sleep(post_delay)
                    else:
                        print(f"❌ Failed to post already verified article")
                else:
                    print(f"⏭️ Skipping article (verified: {is_verified}, posted: {is_posted})")
                
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
            
            # Add delay between OpenAI API calls
            add_api_call_delay()
    
            # Verify the rewritten content
            print(f"🔍 Verifying article content...")
            is_verified, verification_message = verify_rewritten_article(rewritten_content, article["link"], article["pub_date"])
            
            # Add delay after OpenAI API call
            add_api_call_delay()
            
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
            print(f"📋 Generated content for {feed['name']}: {article['title']}")
            print("-"*50)
            print(rewritten_content)
            print("-"*50)
    
            if is_verified:
                print(f"✅ VERIFIED: {verification_message}")
                if feed.get("facebook_page_id") and feed.get("auto_post", True):
                    if post_to_facebook(rewritten_content, article["link"], feed["facebook_page_id"], feed.get("page_access_token")):
                        # Mark the article as posted
                        mark_article_as_posted(feed['name'].replace(' ', '_'), article['id'])
                        
                        # Wait before processing next article if more articles to process
                        if len(articles) > 1 and article != articles[-1]:
                            post_delay = feed.get("delay_each_post", 10)  # Default 10 seconds
                            if post_delay > 0:
                                print(f"⏱️ Waiting {post_delay} seconds before processing next article...")
                                time.sleep(post_delay)
                    if post_to_facebook(rewritten_content, article["link"], feed["facebook_page_id"]):
                        # Mark the article as posted

                else:
                    print("ℹ️ No Facebook page ID provided or auto-posting disabled, skipping posting")
            else:
                print(f"❌ NOT VERIFIED: {verification_message}")
                print("⚠️ Content was not published due to verification failure")
                
                # Send email notification for verification failure
                send_verification_failure_email(
                    feed_name=feed['name'], 
                    article_title=article['title'], 
                    article_link=article['link'], 
                    verification_message=verification_message,
                    rewritten_content=rewritten_content
                )
    
            print("="*50 + "\n")
        
        # Check for any additional verified but unposted articles
        if feed.get("facebook_page_id") and feed.get("auto_post", True):
            unposted_articles = get_unposted_verified_articles(feed['name'])
            if unposted_articles:
                print(f"\n📋 Found {len(unposted_articles)} verified but unposted articles for {feed['name']}")
                
                for article_id, data, rewritten_content, article_link, article_title in unposted_articles:
                    print(f"🔄 Posting previously verified article: {article_title}")
                    
                    if post_to_facebook(rewritten_content, article_link, feed["facebook_page_id"], feed.get("page_access_token")):
                        # Mark the article as posted
                        mark_article_as_posted(feed['name'].replace(' ', '_'), article_id)
                        print(f"✅ Successfully posted previously verified article (ID: {article_id})")
                    else:
                        print(f"❌ Failed to post previously verified article (ID: {article_id})")
                    
                    # Add delay between posts if specified
                    post_delay = feed.get("delay_each_post", 10)  # Default 10 seconds
                    if post_delay > 0 and article_id != unposted_articles[-1][0]:  # Don't delay after the last article
                        print(f"⏱️ Waiting {post_delay} seconds before next post...")
                        time.sleep(post_delay)
                        
                print("="*50 + "\n")

# Main script to process all feeds
if __name__ == "__main__":
    main()
