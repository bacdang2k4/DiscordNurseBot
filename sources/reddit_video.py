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


ASIAN_SUBS = [
    "asiansgonewild",
    "AsianNSFW",
    "JapanesePorn2",
    "NSFW_Japan",
    "AsianHotties",
    "ChineseGoneWild",
    "KoreanNSFW",
    "ThaiGoneWild",
    "bustyasians",
    "AsianCumsluts",
    "AnalGW",
]

ASIAN_KEYWORDS = [
    "asian",
    "japanese",
    "japanese girl",
    "korean",
    "chinese",
    "thai",
]


def _search_video_sync(query: str):
    if reddit is None:
        raise RuntimeError("Reddit API chưa được cấu hình. Kiểm tra .env")

    results = []

    query_lower = query.lower()
    has_asian_word = any(k in query_lower for k in ["asia", "asian", "japan", "korean", "chinese", "thai", "viet"])

    if not has_asian_word:
        asian_kw = random.choice(ASIAN_KEYWORDS)
        search_query = f"{asian_kw} {query}"
    else:
        search_query = query

    print(f"[SEARCH VIDEO] Gốc: {query} → Thực tế: {search_query}")

    # 1. Ưu tiên sub châu Á
    for sub_name in random.sample(ASIAN_SUBS, min(5, len(ASIAN_SUBS))):
        try:
            sub = reddit.subreddit(sub_name)
            for post in sub.search(search_query, sort="hot", limit=15):
                if not post.over_18 or post.stickied:
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
        except Exception:
            continue

    # 2. Fallback search toàn site
    if len(results) < 4:
        try:
            for post in reddit.subreddit("all").search(search_query, sort="hot", limit=25):
                if not post.over_18 or post.stickied:
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
        except Exception as e:
            print(f"[ALL VIDEO SEARCH ERROR] {e}")

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