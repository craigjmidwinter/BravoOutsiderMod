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

# Reddit Auth
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD")
)

def get_last_post_time():
    """Fetch the most recent post by the bot in the subreddit"""
    for submission in reddit.redditor(os.getenv("REDDIT_USERNAME")).submissions.new(limit=10):
        if submission.subreddit.display_name.lower() == SUBREDDIT.lower():
            return datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    return datetime.fromtimestamp(0, tz=timezone.utc)  # fallback: Unix epoch

def get_new_videos(since_time):
    """Get playlist videos newer than last Reddit post and within 7 days"""
    feed = feedparser.parse(YOUTUBE_FEED)
    new_videos = []

    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)

    for entry in feed.entries:
        published_time = date_parser.parse(entry.published)

        if published_time < one_week_ago:
            print(f"Skipping old video: {entry.title}")
            continue

        if published_time > since_time:
            new_videos.append({
                'title': entry.title,
                'url': entry.link,
                'published': published_time
            })

    return new_videos[::-1]  # post oldest first

def post_video(video):
    reddit.subreddit(SUBREDDIT).submit(
        title=f"Discussion: {video['title']}",
        url=video['url']
    )
    print(f"Posted: {video['title']}")

def main():
    last_post_time = get_last_post_time()
    print(f"Last Reddit post: {last_post_time.isoformat()}")

    videos_to_post = get_new_videos(last_post_time)
    print(f"Found {len(videos_to_post)} videos to post")

    for video in videos_to_post:
        post_video(video)
        time.sleep(5)  # avoid Reddit rate limits

if __name__ == "__main__":
    main()
