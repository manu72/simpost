"""
Used to get the long-lived user token and permanent page tokens for the Facebook page.
python3 fbtoken.py --app_id YOUR_APP_ID --app_secret YOUR_SECRET --user_token YOUR_TOKEN
DO NOT STORE YOUR SECRET OR ACCESS TOKEN HERE
Generated access token should be stored in the feeds.json file.
Ensure the feeds.json file is untracked and included in the .gitignore file.
"""

import argparse
import requests

def get_long_lived_user_token(app_id, app_secret, user_access_token):
    url = "https://graph.facebook.com/v22.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": user_access_token
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("access_token")

def get_permanent_page_tokens(long_lived_user_token):
    url = "https://graph.facebook.com/v22.0/me/accounts"
    params = {"access_token": long_lived_user_token}
    response = requests.get(url, params=params)
    pages = response.json().get("data", [])
    
    page_tokens = {}
    for page in pages:
        page_id = page["id"]
        page_name = page["name"]
        page_token = page.get("access_token")
        page_tokens[page_name] = {"id": page_id, "access_token": page_token}
    
    return page_tokens

def main():
    parser = argparse.ArgumentParser(description="Generate a persistent Facebook Page Access Token.")
    parser.add_argument("--app_id", required=True, help="Facebook App ID")
    parser.add_argument("--app_secret", required=True, help="Facebook App Secret")
    parser.add_argument("--user_token", required=True, help="Short-lived User Access Token")
    
    args = parser.parse_args()
    
    print("Getting long-lived user token...")
    long_lived_token = get_long_lived_user_token(args.app_id, args.app_secret, args.user_token)
    
    if long_lived_token:
        print("Successfully retrieved long-lived user token.")
        print("Fetching permanent page tokens...")
        page_tokens = get_permanent_page_tokens(long_lived_token)
        
        if page_tokens:
            print("Successfully retrieved permanent page access tokens:")
            for page_name, details in page_tokens.items():
                print(f"Page: {page_name}")
                print(f"Access Token: {details['access_token']}")
                print("-")
        else:
            print("Failed to retrieve page access tokens.")
    else:
        print("Failed to retrieve long-lived user token.")

if __name__ == "__main__":
    main()
