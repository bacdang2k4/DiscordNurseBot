import os
import json
import random
import aiohttp

RULE34_API = "https://api.rule34.xxx/index.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


EXCLUDED_TAGS = {
    "ai", "ai-created", "ai_art", "ai_assisted", "ai_generated",
    "trap", "yaoi",
}


def _build_tags(user_tags: str) -> str:
    negative = " ".join(f"-{t}" for t in EXCLUDED_TAGS)
    return f"{user_tags.strip()} {negative}"


async def search_rule34(tags: str, limit: int = 50):
    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "tags": _build_tags(tags),
        "limit": limit,
        "pid": 0,
        "json": 1,
    }

    if uid := os.getenv("RULE34_USER_ID"):
        params["user_id"] = uid
    if key := os.getenv("RULE34_API_KEY"):
        params["api_key"] = key

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(
                RULE34_API,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                print(f"[RULE34] status={resp.status} url={resp.url}")
                if resp.status != 200:
                    return None

                text = await resp.text()
                if not text or text.strip() in ("", "[]", "null"):
                    return None

                try:
                    data = json.loads(text)
                except Exception:
                    print(f"[RULE34] JSON parse failed: {text[:100]}")
                    return None

        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        clean = [
            p for p in data
            if not EXCLUDED_TAGS.intersection(p.get("tags", "").split())
        ]
        if not clean:
            return None

        post = random.choice(clean)
        file_url = post.get("file_url", "")

        if not file_url:
            return None

        return {
            "source": "rule34",
            "url": file_url,
            "tags": post.get("tags", ""),
            "score": post.get("score", 0),
            "id": post.get("id"),
            "post_url": f"https://rule34.xxx/index.php?page=post&s=view&id={post.get('id')}",
            "is_video": file_url.endswith((".mp4", ".webm")),
        }

    except Exception as e:
        print(f"[RULE34 ERROR] {type(e).__name__}: {e}")
        return None
