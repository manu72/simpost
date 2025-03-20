# SimPost

A Python project for automating the processing of multiple news feeds, rewriting them for social media, verifying content, and posting to social platforms.

## Setup

1. Clone the repository:

   ```
   git clone <repository-url>
   cd simpost
   ```

2. Create and activate a virtual environment:

   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. For development, install development dependencies:

   ```
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. Configure your environment:
   - Copy `.env.example` to `.env` (if available)
   - Edit `.env` with your API keys:
     - `OPENAI_API_KEY`: Your OpenAI API key for rewriting and verification
     - `FACEBOOK_PAGE_ACCESS_TOKEN`: Your Facebook access token for posting (see below for instructions)

### Getting a Facebook Page Access Token

Each Facebook Page requires its own unique Page Access Token. Follow these steps to obtain a token:

1. Create a Facebook Developer account at [developers.facebook.com](https://developers.facebook.com/)
2. Create a new App in the Facebook Developer Dashboard
3. Add the "Facebook Login" product to your app
4. Configure settings and add the necessary permissions (pages_manage_posts, pages_read_engagement)
5. Navigate to the Graph API Explorer tool
6. Select your App from the dropdown menu
7. Click on "Get Token" and select "Page Access Token"
8. Choose the Facebook Page you want to post to
9. Request a long-lived token to avoid frequent token refreshes
10. Copy the generated token to your feeds.json file as page_access_token

**Important:** If you're posting to multiple Facebook Pages, you'll need a separate access token for each page. In your `feeds.json` configuration, specify the different tokens for each feed using the `page_access_token` property.
     - `FACEBOOK_PAGE_ACCESS_TOKEN`: Your Facebook access token for posting

## Usage

Run the main script to process all feeds:

```
python3 -m simpost.multi_feed_news_automation
```

### Article Manager

Use the article manager to browse and manage stored articles:

```
python article_manager.py [command] [options]
```

Commands:

- `feeds`: List all feeds with stored articles
- `list <feed_name>`: List articles for a specific feed
- `view <feed_name> <article_id>`: View a specific article
- `delete <feed_name> <article_id>`: Delete a specific article
- `mark-posted <feed_name> <article_id>`: Mark a rewritten article as posted

## Configuration

Edit `feeds.json` to configure your feeds. Each feed has the following properties:

```json
{
  "name": "Feed Name",
  "category": "Category",
  "active": true,
  "rss_url": "https://example.com/feed.xml",
  "facebook_page_id": "your-facebook-page-id",
  "max_articles": 10,
  "auto_post": true,

  "delay_each_post": 10,
  "system_prompt": "System prompt for the AI model",
  "prompt": "Specific instructions for rewriting articles"
}
```

- `max_articles`: Maximum number of articles to retrieve from the feed (default: 10)
- `auto_post`: Whether to automatically post verified articles (default: true)
- `delay_each_post`: Number of seconds to wait between posting articles (default: 10)

## Project Structure

- `simpost/multi_feed_news_automation.py`: Main script for processing feeds
- `simpost/utils.py`: Utility functions
- `article_manager.py`: Command-line utility to manage stored articles
- `feeds.json`: Configuration file for RSS feeds
- `.env`: Environment variables for the project
- `requirements.txt`: Python dependencies
- `requirements-dev.txt`: Development dependencies
- `data/`: Directory for storing retrieved and rewritten articles
- `logs/`: Directory for storing logs of rewritten articles

## Development

Run tests:

```
pytest
```

Run specific tests:

```
pytest tests/unit/test_feed_retrieval.py -v
```

Format code:

```
black simpost/ tests/
```

Lint code:

```
flake8 simpost/ tests/
```

## License

[Specify your license here]
