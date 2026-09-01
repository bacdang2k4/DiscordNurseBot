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


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

NSFW_SUBS = [
    "nsfw", "RealGirls", "gonewild", "Amateur", "boobs", "ass",
    "pussy", "nsfw_gif", "porn", "LegalTeens", "collegesluts",
    "GodPussy", "OnOff", "curvy", "bigasses", "asiansgonewild",
    "AsianNSFW", "JapanesePorn2", "AnalGW", "anal"
]


def _search_image_sync(query: str):
    if reddit is None:
        raise RuntimeError("Reddit API chưa được cấu hình. Kiểm tra .env")

    results = []

    # 1. Search toàn site (NSFW)
    try:
        for post in reddit.subreddit("all").search(query, sort="hot", limit=40):
            if not post.over_18:
                continue
            if post.stickied:
                continue

            url = (post.url or "").lower()
            is_image = (
                any(url.endswith(ext) for ext in IMAGE_EXTENSIONS)
                or "i.redd.it" in url
                or "i.imgur.com" in url
                or getattr(post, "post_hint", "") == "image"
            )

            if is_image and post.url:
                results.append(post)
    except Exception as e:
        print(f"[PRAW SEARCH ERROR] {e}")

    # 2. Nếu ít kết quả thì tìm thêm trong các sub NSFW
    if len(results) < 5:
        for sub_name in random.sample(NSFW_SUBS, min(5, len(NSFW_SUBS))):
            try:
                sub = reddit.subreddit(sub_name)
                for post in sub.search(query, sort="hot", limit=15):
                    if not post.over_18:
                        continue
                    url = (post.url or "").lower()
                    is_image = (
                        any(url.endswith(ext) for ext in IMAGE_EXTENSIONS)
                        or "i.redd.it" in url
                        or "i.imgur.com" in url
                    )
                    if is_image and post.url:
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


async def search_reddit_image(query: str):
    return await asyncio.to_thread(_search_image_sync, query)