import random
import aiohttp
from urllib.parse import quote_plus


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


async def search_reddit_image(query: str, limit: int = 40):
    """
    Tìm ảnh NSFW trên Reddit theo từ khóa.
    """
    q = quote_plus(query)
    url = f"https://www.reddit.com/search.json?q={q}&type=link&sort=hot&limit={limit}&include_over_18=on"

    headers = {"User-Agent": "DiscordNSFWBot/1.0"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        posts = data.get("data", {}).get("children", [])
        results = []

        for item in posts:
            post = item.get("data", {})

            if not post.get("over_18", False):
                continue

            post_url = (post.get("url") or "").lower()

            is_image = (
                any(post_url.endswith(ext) for ext in IMAGE_EXTENSIONS)
                or "i.redd.it" in post_url
                or "i.imgur.com" in post_url
                or post.get("post_hint") == "image"
            )

            if is_image and post.get("url"):
                results.append(post)

        if not results:
            return None

        post = random.choice(results)

        return {
            "source": "reddit",
            "subreddit": post.get("subreddit", "unknown"),
            "title": post.get("title", "No title"),
            "url": post.get("url"),
            "permalink": f"https://www.reddit.com{post.get('permalink', '')}",
            "score": post.get("score", 0),
        }

    except Exception as e:
        print(f"[REDDIT IMAGE ERROR] {e}")
        return None