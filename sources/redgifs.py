import random
import aiohttp
from collections import deque

REDGIFS_AUTH = "https://api.redgifs.com/v2/auth/temporary"
REDGIFS_SEARCH = "https://api.redgifs.com/v2/gifs/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

GAY_TAGS = {"gay", "male_only", "yaoi", "bara", "men_only", "gay_sex", "gay_male", "femboy", "gay_male_only", "gay_male_sex"}

_recent_ids: deque = deque(maxlen=50)


async def _get_token() -> str | None:
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(REDGIFS_AUTH, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json(content_type=None)
                return data.get("token")
    except Exception as e:
        print(f"[REDGIFS AUTH ERROR] {e}")
        return None


def _is_clean(gif: dict) -> bool:
    tags = {t.lower() for t in (gif.get("tags") or [])}
    return not tags.intersection(GAY_TAGS)


async def search_redgifs(query: str, count: int = 20):
    token = await _get_token()
    if not token:
        return None

    # Chuyển "anal asian" → "Anal,Asian"
    tags = ",".join(w.capitalize() for w in query.strip().split())

    params = {
        "type": "g",
        "tags": tags,
        "order": "top28",
        "count": count,
        "page": 1,
    }
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    try:
        async with aiohttp.ClientSession(headers=auth_headers) as session:
            async with session.get(
                REDGIFS_SEARCH,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                print(f"[REDGIFS] status={resp.status} tags={tags}")
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)

        gifs = [
            g for g in (data.get("gifs") or [])
            if _is_clean(g) and g.get("id") not in _recent_ids
        ]

        if not gifs:
            _recent_ids.clear()
            gifs = [g for g in (data.get("gifs") or []) if _is_clean(g)]

        if not gifs:
            return None

        gif = random.choice(gifs)
        _recent_ids.append(gif.get("id"))

        urls = gif.get("urls", {})
        video_url = urls.get("hd") or urls.get("sd") or urls.get("gif")

        return {
            "id": gif.get("id"),
            "title": query,
            "url": f"https://www.redgifs.com/watch/{gif.get('id')}",
            "video_url": video_url,
            "thumbnail": urls.get("thumbnail") or urls.get("poster", ""),
            "duration": round(gif.get("duration") or 0),
            "views": gif.get("views") or 0,
            "likes": gif.get("likes") or 0,
            "tags": gif.get("tags") or [],
        }

    except Exception as e:
        print(f"[REDGIFS ERROR] {type(e).__name__}: {e}")
        return None
