import os
import json
import random
import aiohttp

GELBOORU_API = "https://gelbooru.com/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

EXCLUDED_TAGS = {
    # Gay
    "yaoi", "bara", "gay", "male_only", "multiple_boys",
    # Femboy / trans
    "femboy", "trap", "transgender", "shemale", "ladyboy", "crossdressing",
    # Bestiality
    "animal_penis", "zoophilia", "bestiality",
    # AI
    "ai-generated", "ai_generated", "ai-created", "ai_created",
}


def _is_clean(post: dict) -> bool:
    tags = set(post.get("tags", "").split())
    return not tags.intersection(EXCLUDED_TAGS)


def is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


async def search_gelbooru(user_tags: str, limit: int = 100):
    pid = random.randint(0, 10)

    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "json": 1,
        "limit": limit,
        "pid": pid,
        "tags": user_tags.strip(),
        "user_id": os.getenv("GELBOORU_USER_ID", ""),
        "api_key": os.getenv("GELBOORU_API_KEY", ""),
    }

    print(f"[GELBOORU] Sending request: tags={user_tags!r} pid={pid}")
    print(f"[GELBOORU] user_id={os.getenv('GELBOORU_USER_ID', 'MISSING')} api_key_set={bool(os.getenv('GELBOORU_API_KEY'))}")

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(
                GELBOORU_API,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                text = await resp.text()
                print(f"[GELBOORU] status={resp.status} body={text[:300]}")

                if resp.status != 200:
                    return None

                data = json.loads(text)

        posts = data.get("post", [])
        print(f"[GELBOORU] total posts={len(posts)}")

        if not posts:
            return None

        clean = [p for p in posts if _is_clean(p) and is_valid_url(p.get("file_url", ""))]
        print(f"[GELBOORU] clean posts={len(clean)}")

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
