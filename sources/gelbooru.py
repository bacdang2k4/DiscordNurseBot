import os
import json
import random
import aiohttp

GELBOORU_API = "https://gelbooru.com/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


EXCLUDED_TAGS = {
    "yaoi", "bara", "gay", "male_only", "femboy", "trap",
    "transgender", "shemale", "ladyboy", "crossdressing",
}


def _build_tags(user_tags: str) -> str:
    return f"{user_tags.strip()} rating:explicit"


def _is_clean(post: dict) -> bool:
    tags = set(post.get("tags", "").split())
    return not tags.intersection(EXCLUDED_TAGS)


async def _get_count(tags: str) -> int:
    params = {
        "page": "dapi", "s": "post", "q": "index",
        "json": 1, "limit": 1, "tags": tags,
        "user_id": os.getenv("GELBOORU_USER_ID", ""),
        "api_key": os.getenv("GELBOORU_API_KEY", ""),
    }
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(GELBOORU_API, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return 0
                text = await resp.text()
                data = json.loads(text)
                return data.get("@attributes", {}).get("count", 0)
    except Exception:
        return 0


async def search_gelbooru(user_tags: str, limit: int = 50):
    tags = _build_tags(user_tags)

    total = await _get_count(tags)
    if total == 0:
        return None

    max_pid = max(0, min((total - limit) // limit, 200))
    pid = random.randint(0, max_pid)

    params = {
        "page": "dapi", "s": "post", "q": "index",
        "json": 1, "limit": limit, "pid": pid,
        "tags": tags,
        "user_id": os.getenv("GELBOORU_USER_ID", ""),
        "api_key": os.getenv("GELBOORU_API_KEY", ""),
    }

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(GELBOORU_API, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"[GELBOORU] status={resp.status} pid={pid} tags={user_tags!r}")
                if resp.status != 200:
                    return None
                text = await resp.text()
                data = json.loads(text)

        posts = data.get("post", [])
        if not posts:
            return None

        clean = [p for p in posts if _is_clean(p) and is_valid_url(p.get("file_url", ""))]
        if not clean:
            return None

        post = random.choice(clean)
        file_url = post["file_url"]

        return {
            "url": file_url,
            "post_url": f"https://gelbooru.com/index.php?page=post&s=view&id={post.get('id')}",
            "tags": post.get("tags", ""),
            "score": post.get("score", 0),
            "id": post.get("id"),
            "is_video": file_url.endswith((".mp4", ".webm")),
        }

    except Exception as e:
        print(f"[GELBOORU ERROR] {type(e).__name__}: {e}")
        return None


def is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))
