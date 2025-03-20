# SimPost

A Python project for automating the processing of multiple news feeds.

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

4. Configure your environment:
   - Copy `.env.example` to `.env` (if available)
   - Edit `.env` with your specific configuration

## Usage

Run the main script to process all feeds:

```
python3 -m simpost.multi_feed_news_automation
```

## Project Structure

- `simpost/multi_feed_news_automation.py`: Main script for processing feeds
- `feeds.json`: Configuration file for RSS feeds
- `.env`: Environment variables for the project
- `requirements.txt`: Python dependencies

## License

[Specify your license here]
