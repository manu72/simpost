#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Article Manager - A utility script to browse and manage stored articles
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add the current directory to path to find simpost package
sys.path.append('.')

# Import directory constants from the main script
from simpost.multi_feed_news_automation import (
    DATA_DIR, RETRIEVED_ARTICLES_DIR, REWRITTEN_ARTICLES_DIR
)

def list_feeds():
    """List all feeds that have stored articles"""
    retrieved_feeds = set()
    rewritten_feeds = set()
    
    # Check retrieved articles directory
    if os.path.exists(RETRIEVED_ARTICLES_DIR):
        retrieved_feeds = set([d for d in os.listdir(RETRIEVED_ARTICLES_DIR) 
                              if os.path.isdir(os.path.join(RETRIEVED_ARTICLES_DIR, d))])
    
    # Check rewritten articles directory
    if os.path.exists(REWRITTEN_ARTICLES_DIR):
        rewritten_feeds = set([d for d in os.listdir(REWRITTEN_ARTICLES_DIR) 
                              if os.path.isdir(os.path.join(REWRITTEN_ARTICLES_DIR, d))])
    
    # Combine them
    all_feeds = retrieved_feeds.union(rewritten_feeds)
    
    if not all_feeds:
        print("No feeds found with stored articles.")
        return
    
    print("\n=== Feeds with Stored Articles ===")
    for i, feed in enumerate(sorted(all_feeds), 1):
        # Count articles for this feed
        retrieved_count = count_articles(os.path.join(RETRIEVED_ARTICLES_DIR, feed))
        rewritten_count = count_articles(os.path.join(REWRITTEN_ARTICLES_DIR, feed))
        
        print(f"{i}. {feed.replace('_', ' ')} ({retrieved_count} retrieved, {rewritten_count} rewritten)")

def count_articles(directory):
    """Count articles in a directory"""
    if not os.path.exists(directory):
        return 0
    return len([f for f in os.listdir(directory) if f.endswith('.json')])

def list_articles(feed_name, article_type="rewritten", show_verified_only=False, show_unposted_only=False):
    """List articles for a specific feed"""
    if article_type == "retrieved":
        directory = os.path.join(RETRIEVED_ARTICLES_DIR, feed_name)
    else:
        directory = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name)
    
    if not os.path.exists(directory):
        print(f"No {article_type} articles found for feed: {feed_name}")
        return
    
    articles = []
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
            
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Apply filters
                if article_type == "rewritten":
                    if show_verified_only and not data.get('is_verified', False):
                        continue
                    if show_unposted_only and data.get('is_posted', False):
                        continue
                
                articles.append((filename, data))
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {filepath}")
    
    if not articles:
        print(f"No matching {article_type} articles found for feed: {feed_name}")
        return
    
    print(f"\n=== {article_type.capitalize()} Articles for {feed_name.replace('_', ' ')} ===")
    for i, (filename, data) in enumerate(sorted(articles, key=lambda x: x[1].get('retrieved_at', '')), 1):
        # For retrieved articles
        if article_type == "retrieved":
            title = data.get('title', 'No title')
            retrieved_at = data.get('retrieved_at', 'Unknown')
            print(f"{i}. [{filename}] {title} (Retrieved: {retrieved_at})")
        
        # For rewritten articles
        else:
            title = data.get('original_article', {}).get('title', 'No title')
            rewritten_at = data.get('rewritten_at', 'Unknown')
            is_verified = data.get('is_verified', False)
            is_posted = data.get('is_posted', False)
            
            status = "✅ VERIFIED" if is_verified else "❌ NOT VERIFIED"
            posted = "✅ POSTED" if is_posted else "⏳ NOT POSTED"
            
            print(f"{i}. [{filename}] {title}")
            print(f"   Status: {status} | {posted} (Rewritten: {rewritten_at})")

def view_article(feed_name, article_id, article_type="rewritten"):
    """View a specific article"""
    if article_type == "retrieved":
        filepath = os.path.join(RETRIEVED_ARTICLES_DIR, feed_name, f"{article_id}")
    else:
        filepath = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name, f"{article_id}")
    
    # Add .json extension if needed
    if not filepath.endswith('.json'):
        filepath += '.json'
    
    if not os.path.exists(filepath):
        print(f"Article not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            
            print("\n" + "="*50)
            if article_type == "retrieved":
                print(f"Title: {data.get('title', 'No title')}")
                print(f"Link: {data.get('link', 'No link')}")
                print(f"Retrieved at: {data.get('retrieved_at', 'Unknown')}")
                print(f"ID: {data.get('id', 'No ID')}")
                print("\nContent:")
                print("-"*50)
                print(data.get('content', 'No content'))
            else:
                title = data.get('original_article', {}).get('title', 'No title')
                print(f"Title: {title}")
                print(f"Link: {data.get('original_article', {}).get('link', 'No link')}")
                print(f"Rewritten at: {data.get('rewritten_at', 'Unknown')}")
                print(f"Is verified: {data.get('is_verified', False)}")
                print(f"Is posted: {data.get('is_posted', False)}")
                
                print("\nOriginal Content:")
                print("-"*50)
                print(data.get('original_article', {}).get('content', 'No content'))
                
                print("\nRewritten Content:")
                print("-"*50)
                print(data.get('rewritten_content', 'No content'))
                
                print("\nVerification Message:")
                print("-"*50)
                print(data.get('verification_message', 'No verification message'))
            
            print("="*50)
            
        except json.JSONDecodeError:
            print(f"Error: Could not decode {filepath}")

def delete_article(feed_name, article_id, article_type="rewritten"):
    """Delete a specific article"""
    if article_type == "retrieved":
        filepath = os.path.join(RETRIEVED_ARTICLES_DIR, feed_name, f"{article_id}")
    else:
        filepath = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name, f"{article_id}")
    
    # Add .json extension if needed
    if not filepath.endswith('.json'):
        filepath += '.json'
    
    if not os.path.exists(filepath):
        print(f"Article not found: {filepath}")
        return
    
    confirm = input(f"Are you sure you want to delete {filepath}? (y/n): ")
    if confirm.lower() != 'y':
        print("Deletion cancelled.")
        return
    
    os.remove(filepath)
    print(f"Deleted: {filepath}")

def mark_as_posted(feed_name, article_id):
    """Mark a rewritten article as posted"""
    filepath = os.path.join(REWRITTEN_ARTICLES_DIR, feed_name, f"{article_id}")
    
    # Add .json extension if needed
    if not filepath.endswith('.json'):
        filepath += '.json'
    
    if not os.path.exists(filepath):
        print(f"Article not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['is_posted'] = True
    data['posted_at'] = datetime.now().isoformat()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Marked as posted: {filepath}")

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Article Manager - Browse and manage stored articles')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List feeds command
    list_feeds_parser = subparsers.add_parser('feeds', help='List all feeds with stored articles')
    
    # List articles command
    list_articles_parser = subparsers.add_parser('list', help='List articles for a specific feed')
    list_articles_parser.add_argument('feed_name', help='Name of the feed (as shown in the feeds list)')
    list_articles_parser.add_argument('--type', choices=['retrieved', 'rewritten'], default='rewritten',
                                      help='Type of articles to list (default: rewritten)')
    list_articles_parser.add_argument('--verified-only', action='store_true', help='Show verified articles only')
    list_articles_parser.add_argument('--unposted-only', action='store_true', help='Show unposted articles only')
    
    # View article command
    view_parser = subparsers.add_parser('view', help='View a specific article')
    view_parser.add_argument('feed_name', help='Name of the feed')
    view_parser.add_argument('article_id', help='ID or filename of the article')
    view_parser.add_argument('--type', choices=['retrieved', 'rewritten'], default='rewritten',
                             help='Type of article to view (default: rewritten)')
    
    # Delete article command
    delete_parser = subparsers.add_parser('delete', help='Delete a specific article')
    delete_parser.add_argument('feed_name', help='Name of the feed')
    delete_parser.add_argument('article_id', help='ID or filename of the article')
    delete_parser.add_argument('--type', choices=['retrieved', 'rewritten'], default='rewritten',
                               help='Type of article to delete (default: rewritten)')
    
    # Mark as posted command
    mark_parser = subparsers.add_parser('mark-posted', help='Mark a rewritten article as posted')
    mark_parser.add_argument('feed_name', help='Name of the feed')
    mark_parser.add_argument('article_id', help='ID or filename of the article')
    
    return parser.parse_args()

def main():
    """Main function to run the article manager"""
    args = parse_args()
    
    if args.command == 'feeds':
        list_feeds()
    elif args.command == 'list':
        list_articles(args.feed_name, args.type, args.verified_only, args.unposted_only)
    elif args.command == 'view':
        view_article(args.feed_name, args.article_id, args.type)
    elif args.command == 'delete':
        delete_article(args.feed_name, args.article_id, args.type)
    elif args.command == 'mark-posted':
        mark_as_posted(args.feed_name, args.article_id)
    else:
        # If no command is provided, show help text
        list_feeds()
        print("\nUse one of the following commands:")
        print("  python article_manager.py feeds")
        print("  python article_manager.py list <feed_name> [--type retrieved|rewritten] [--verified-only] [--unposted-only]")
        print("  python article_manager.py view <feed_name> <article_id> [--type retrieved|rewritten]")
        print("  python article_manager.py delete <feed_name> <article_id> [--type retrieved|rewritten]")
        print("  python article_manager.py mark-posted <feed_name> <article_id>")

if __name__ == "__main__":
    main() 