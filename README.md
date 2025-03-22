# SimPost

A Python project for automating the processing of multiple news feeds, rewriting them for social media, verifying content, and posting to social platforms.

## Setup

### Option 1: Local Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd simpost
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. For development, install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. Configure your environment:
   - Copy `.env.example` to `.env` (if available)
   - Edit `.env` with your API keys:
     - `OPENAI_API_KEY`: Your OpenAI API key for rewriting and verification
     - `FACEBOOK_PAGE_ACCESS_TOKEN`: Your Facebook access token for posting (see below for instructions)

### Option 2: Docker Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd simpost
   ```

2. Create a `.env` file with your API keys as described above.

3. Build the Docker image:

   ```bash
   docker build --no-cache -t simpost-app .
   ```

4. Run the container:

   ```bash
   docker run -d --name simpost \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     --env-file .env \
     --restart unless-stopped \
     simpost-app
   ```

5. Check container logs:

   ```bash
   docker logs -f simpost
   ```

6. To update the application:

   ```bash
   # Pull latest code
   git pull

   # Rebuild the Docker image with latest code
   docker build --no-cache -t simpost-app .

   # Stop and remove existing container
   docker stop simpost
   docker rm simpost

   # Start new container with updated image
   docker run -d --name simpost \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     --env-file .env \
     --restart unless-stopped \
     simpost-app
   ```

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

**Important:** If you're posting to multiple Facebook Pages, you'll need a separate access token for each page. In your `feeds.json` configuration, specify the different tokens for each feed using the `page_access_token` property. - `FACEBOOK_PAGE_ACCESS_TOKEN`: Your Facebook access token for posting

### Using the Facebook Token Utility

For convenience, you can use the included `fbtoken.py` utility to generate long-lived Facebook Page tokens:

```bash
python -m simpost.fbtoken --app_id YOUR_APP_ID --app_secret YOUR_APP_SECRET --user_token YOUR_SHORT_LIVED_TOKEN
```

This utility will:

1. Exchange your short-lived user token for a long-lived user token
2. Fetch permanent page access tokens for all pages you manage
3. Display the page tokens for you to copy into your feeds.json file

## Usage

Run the main script to process all feeds:

```bash
python3 -m simpost.multi_feed_news_automation
```

### API Rate Limit Handling

The system includes built-in retry logic with exponential backoff for API calls to OpenAI:

- Automatically retries API calls when rate limits are hit
- Uses exponential backoff (increasing wait times between retries)
- Maximum of 5 retry attempts for each API call
- Helps maintain stable operation during high volume processing
- Applies to both article rewriting and content verification calls

### Article Manager

Use the article manager to browse and manage stored articles:

```bash
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
  "page_access_token": "your-page-specific-access-token",
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
- `page_access_token`: Facebook Page-specific access token for this feed

## Project Structure

- `simpost/multi_feed_news_automation.py`: Main script for processing feeds
- `simpost/utils.py`: Utility functions
- `simpost/fbtoken.py`: Utility to generate long-lived Facebook tokens
- `article_manager.py`: Command-line utility to manage stored articles
- `feeds.json`: Configuration file for RSS feeds
- `.env`: Environment variables for the project
- `requirements.txt`: Python dependencies
- `requirements-dev.txt`: Development dependencies
- `data/`: Directory for storing retrieved and rewritten articles
- `logs/`: Directory for storing logs of rewritten articles
- `Dockerfile`: Configuration for Docker container

## Docker Configuration

The included Dockerfile creates a lightweight Python container that:

1. Uses Python 3.8 as the base image
2. Installs all required dependencies
3. Copies the application code into the container
4. Sets up the application to run automatically

The Docker setup preserves data by mounting these volumes:

- `./data:/app/data`: Persists all retrieved and rewritten articles
- `./logs:/app/logs`: Keeps logs across container restarts

Environment variables are passed via `.env` file, ensuring secrets stay secure.

## Development

Run tests:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/unit/test_feed_retrieval.py -v
```

Format code:

```bash
black simpost/ tests/
```

Lint code:

```bash
flake8 simpost/ tests/
```

## License

[Specify your license here]
