import asyncio
import os
import random
import praw
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

reddit = None

if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


NSFW_SUBS = [
    "nsfw", "nsfw_gif", "porn", "AnalGW", "anal",
    "asiansgonewild", "AsianNSFW", "JapanesePorn2",
    "gonewild", "RealGirls"
]


def _search_video_sync(query: str):
    if reddit is None:
        raise RuntimeError("Reddit API chưa được cấu hình. Kiểm tra .env")

    results = []

    # 1. Search toàn site
    try:
        for post in reddit.subreddit("all").search(query, sort="hot", limit=40):
            if not post.over_18:
                continue
            if post.stickied:
                continue

            url = (post.url or "").lower()
            is_video = (
                post.is_video
                or "v.redd.it" in url
                or url.endswith((".mp4", ".gifv", ".webm"))
                or "redgifs.com" in url
                or "gfycat.com" in url
            )

            if is_video and post.url:
                results.append(post)
    except Exception as e:
        print(f"[PRAW VIDEO SEARCH ERROR] {e}")

    # 2. Tìm thêm trong sub NSFW nếu ít kết quả
    if len(results) < 5:
        for sub_name in random.sample(NSFW_SUBS, min(4, len(NSFW_SUBS))):
            try:
                sub = reddit.subreddit(sub_name)
                for post in sub.search(query, sort="hot", limit=15):
                    if not post.over_18:
                        continue
                    url = (post.url or "").lower()
                    is_video = (
                        post.is_video
                        or "v.redd.it" in url
                        or "redgifs.com" in url
                        or url.endswith((".mp4", ".gifv"))
                    )
                    if is_video and post.url:
                        results.append(post)
            except Exception:
                continue

    if not results:
        return None

    post = random.choice(results)

    return {
        "source": "reddit",
        "subreddit": str(post.subreddit),
        "title": post.title,
        "url": post.url,
        "permalink": f"https://www.reddit.com{post.permalink}",
        "score": post.score,
    }


async def search_reddit_video(query: str):
    return await asyncio.to_thread(_search_video_sync, query)