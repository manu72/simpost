#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to check article verification using OpenAI web search with a fake news article
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to path to find simpost package
sys.path.append('.')

# Import the required functions from our main script
from simpost.multi_feed_news_automation import verify_rewritten_article

# Load environment variables
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: No OpenAI API key found in .env file!")
    print("Please create a .env file with your OPENAI_API_KEY.")
    sys.exit(1)

def main():
    # Create a deliberately fake news article about Red Bull F1
    fake_article = """
    Red Bull Racing has announced they're pulling out of Formula 1 at the end of the 2025 season 
    due to financial constraints and declining interest in motorsport. 
    Team principal Christian Horner confirmed the news yesterday in a press conference, 
    stating that the team will focus on other sports ventures instead. 
    Max Verstappen is expected to move to Ferrari for the 2026 season.
    The team's withdrawal marks the end of an era in Formula 1, with Red Bull having been dominant 
    for much of the past decade.
    #F1 #Formula1 #RedBullRacing
    """
    
    # URL of a real Red Bull news article for context
    real_article_link = "https://www.formula1.com/en/latest/article.red-bull-racing.html"
    
    print("\n=== Testing verification of fake news article ===")
    print("\nFake article content:")
    print(fake_article)
    
    # Verify the fake content
    print("\nVerifying content using OpenAI web search...")
    try:
        is_verified, verification_message = verify_rewritten_article(fake_article, real_article_link)
        
        print("\n=== Verification Results ===")
        if is_verified:
            print("✅ VERIFIED")
        else:
            print("❌ NOT VERIFIED")
        print(f"Message: {verification_message}")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    main() 