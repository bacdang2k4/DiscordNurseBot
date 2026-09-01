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

# Subreddit châu Á (ưu tiên)
ASIAN_SUBS = [
    "asiansgonewild",
    "AsianNSFW",
    "JapanesePorn2",
    "NSFW_Japan",
    "AsianHotties",
    "ChineseGoneWild",
    "KoreanNSFW",
    "ThaiGoneWild",
    "VietnameseNSFW",
    "bustyasians",
    "AsiansGoneWild",
    "AsianCumsluts",
    "AsianBlowjob",
    "AnalGW",           # vẫn để vì nhiều nội dung châu Á
]

# Từ khóa châu Á tự động thêm vào
ASIAN_KEYWORDS = [
    "asian",
    "japanese",
    "japanese girl",
    "korean",
    "chinese",
    "thai",
    "vietnamese",
]


def _search_image_sync(query: str):
    if reddit is None:
        raise RuntimeError("Reddit API chưa được cấu hình. Kiểm tra .env")

    results = []

    # Tự động thêm từ khóa châu Á nếu người dùng không ghi
    query_lower = query.lower()
    has_asian_word = any(k in query_lower for k in ["asia", "asian", "japan", "korean", "chinese", "thai", "viet"])

    if not has_asian_word:
        # Random 1 từ khóa châu Á để ghép vào
        asian_kw = random.choice(ASIAN_KEYWORDS)
        search_query = f"{asian_kw} {query}"
    else:
        search_query = query

    print(f"[SEARCH IMAGE] Gốc: {query} → Thực tế: {search_query}")

    # 1. Ưu tiên search trong các sub châu Á
    for sub_name in random.sample(ASIAN_SUBS, min(6, len(ASIAN_SUBS))):
        try:
            sub = reddit.subreddit(sub_name)
            for post in sub.search(search_query, sort="hot", limit=20):
                if not post.over_18 or post.stickied:
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
            print(f"[SUB {sub_name} ERROR] {e}")
            continue

    # 2. Nếu vẫn ít kết quả thì search toàn site với từ khóa đã thêm asian
    if len(results) < 5:
        try:
            for post in reddit.subreddit("all").search(search_query, sort="hot", limit=30):
                if not post.over_18 or post.stickied:
                    continue

                url = (post.url or "").lower()
                is_image = (
                    any(url.endswith(ext) for ext in IMAGE_EXTENSIONS)
                    or "i.redd.it" in url
                    or "i.imgur.com" in url
                )
                if is_image and post.url:
                    results.append(post)
        except Exception as e:
            print(f"[ALL SEARCH ERROR] {e}")

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