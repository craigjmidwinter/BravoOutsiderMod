import os
import time
import feedparser
import praw
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

# Config
SUBREDDIT = "BravoOutsider"
YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?playlist_id=PLiFBbHnPz5MSqFWfGx_qsLYqLFv3ktLCU"

# Environment variables (with whitespace trimmed)
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "").strip()
USER_AGENT = os.getenv("REDDIT_USER_AGENT", "").strip()
USERNAME = os.getenv("REDDIT_USERNAME", "").strip()
PASSWORD = os.getenv("REDDIT_PASSWORD", "").strip()

print(f"Using Reddit user agent: {USER_AGENT}")

# Reddit Auth
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    username=USERNAME,
    password=PASSWORD
)

def get_last_post_time():
    """Fetch the most recent post by the bot in the subreddit"""
    if not USERNAME:
        raise ValueError("REDDIT_USERNAME is missing or empty.")
    for submission in reddit.redditor(USERNAME).submissions.new(limit=10):
        if submission.subreddit.display_name.lower() == SUBREDDIT.lower():
            print(f"Last post found: {submission.title} at {datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)}")
            return datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    print("No prior posts found. Defaulting to Unix epoch.")
    return datetime.fromtimestamp(0, tz=timezone.utc)

def get_new_videos(since_time):
    """Get playlist videos newer than last Reddit post and within 7 days"""
    feed = feedparser.parse(YOUTUBE_FEED)
    new_videos = []

    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)

    print(f"Checking for videos after: {since_time.isoformat()} and within last 7 days")

    for entry in feed.entries:
        published_time = date_parser.parse(entry.published)
        print(f"→ {entry.title} @ {published_time.isoformat()}")

        if published_time < one_week_ago:
            print(f"  ⛔ Skipping (too old)")
            continue

        if published_time > since_time:
            print(f"  ✅ New video added")
            new_videos.append({
                'title': entry.title,
                'url': entry.link,
                'published': published_time
            })
        else:
            print(f"  🔁 Skipping (already posted)")

    return new_videos[::-1]  # post oldest first

def post_video(video):
    reddit.subreddit(SUBREDDIT).submit(
        title=f"Discussion: {video['title']}",
        url=video['url']
    )
    print(f"✅ Posted: {video['title']}")

def main():
    last_post_time = get_last_post_time()
    print(f"Last Reddit post: {last_post_time.isoformat()}")

    videos_to_post = get_new_videos(last_post_time)
    print(f"Found {len(videos_to_post)} new videos to post")

    for video in videos_to_post:
        post_video(video)
        time.sleep(5)  # avoid Reddit rate limits

if __name__ == "__main__":
    main()
