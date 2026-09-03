import random
import aiohttp
from collections import deque

REDGIFS_AUTH = "https://api.redgifs.com/v2/auth/temporary"
REDGIFS_SEARCH = "https://api.redgifs.com/v2/gifs/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# Xoay đều 6 order để tránh trùng
ORDERS = ["latest", "trending", "top7", "top28", "top", "score"]

_GAY = {
    "gay", "gays", "gay sex", "gay porn", "gay male", "gay men", "gay man",
    "gay couple", "gay couples", "gay twink", "gay anal", "gay blowjob",
    "gay bareback", "gay creampie", "gay cum", "gay oral", "gay handjob",
    "gay solo", "gay amateur", "gay homemade", "gay interracial",
    "homosexual", "homosexuality", "yaoi", "bara", "bara gay",
    "mm", "m/m", "men loving men", "man on man", "male on male",
    "male male", "two guys", "two men", "guys only",
    "male only", "males only", "men only", "man only", "only men", "only male",
    "male only sex", "gay male only", "gay male sex",
}
_GAY_SCENE = {
    "twink", "twinks", "twink gay", "otter", "otters",
    "cub", "cubs", "chub", "chubby gay", "chaser",
    "jock gay", "leather gay", "leather daddy",
    "pup", "puppy play", "human pup", "gay pup",
    "frotting", "frottage", "docking", "buddies",
    "brojob", "str8 bait", "straight bait",
    "muscle gay", "hunk gay", "dilf gay",
}
_FEMBOY = {
    "femboy", "femboys", "fem boy", "femboi", "femboy porn",
    "sissy", "sissies", "sissy slut", "sissy hypno", "sissification",
    "crossdress", "crossdressing", "crossdresser", "cross dresser",
    "cd", "tv cd", "trap", "traps", "trappy",
    "boypussy", "boy pussy", "bussy", "boy clit",
    "shemale femboy", "femboy anal", "femboy cum",
}
_TRANS = {
    "trans", "transgender", "transsexual", "transexual",
    "trans woman", "trans women", "transwoman", "transwomen",
    "trans man", "trans men", "transman", "transmen",
    "trans girl", "trans girls", "transgirl", "transgirls",
    "trans boy", "transboy", "trans female", "trans male",
    "trans female only", "trans male only",
    "tgirl", "t girl", "t-girl", "t girls",
    "mtf", "m2f", "ftm", "f2m",
    "shemale", "shemales", "ladyboy", "ladyboys", "lady boy",
    "newhalf", "girlcock", "girl cock", "girldick", "girl dick",
    "trans cock", "trans dick", "big clit trans",
    "nonbinary", "non binary", "enby", "nb trans",
}
_SOLO_MALE = {
    "solo male", "male solo", "solo man", "solo men",
    "male masturbation", "man masturbation",
    "cock solo", "dick solo",
}
_HENTAI_GAY = {"yaoi", "bara", "gay hentai", "bara hentai"}

BLOCKED_TAGS = _GAY | _GAY_SCENE | _FEMBOY | _TRANS | _SOLO_MALE | _HENTAI_GAY

# Lưu 200 ID gần nhất để không trùng
_recent_ids: deque = deque(maxlen=200)


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
    return not tags.intersection(BLOCKED_TAGS)


async def _fetch(session, auth_headers: dict, tags_str: str, order: str, page: int, count: int = 40):
    params = {"type": "g", "tags": tags_str, "order": order, "count": count, "page": page}
    async with session.get(
        REDGIFS_SEARCH, params=params, timeout=aiohttp.ClientTimeout(total=15)
    ) as resp:
        if resp.status != 200:
            print(f"[REDGIFS] status={resp.status} order={order} page={page}")
            return None
        return await resp.json(content_type=None)


async def search_redgifs(query: str):
    token = await _get_token()
    if not token:
        return None

    # Tách theo dấu phẩy, chuyển spaces trong mỗi tag thành underscore rồi Capitalize
    tags_str = ",".join(t.strip().replace(" ", "_").capitalize() for t in query.split(",") if t.strip())
    order = random.choice(ORDERS)
    auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    try:
        async with aiohttp.ClientSession(headers=auth_headers) as session:
            # Request 1: lấy tổng số trang
            first = await _fetch(session, auth_headers, tags_str, order, page=1)
            if not first:
                return None

            total_pages = max(1, min(first.get("pages", 1), 30))
            page = random.randint(1, total_pages)

            # Request 2: chỉ gọi thêm nếu không phải trang 1
            data = first if page == 1 else await _fetch(session, auth_headers, tags_str, order, page) or first

        print(f"[REDGIFS] order={order} page={page}/{total_pages} tags={tags_str}")

        pool = [
            g for g in (data.get("gifs") or [])
            if _is_clean(g) and g.get("id") not in _recent_ids
        ]

        if not pool:
            # Hết pool → reset seen, fallback về trang 1
            _recent_ids.clear()
            pool = [g for g in (first.get("gifs") or []) if _is_clean(g)]

        if not pool:
            return None

        random.shuffle(pool)
        picks = pool[:3]

        results = []
        for gif in picks:
            _recent_ids.append(gif.get("id"))
            urls = gif.get("urls", {})
            video_url = urls.get("hd") or urls.get("sd") or urls.get("gif")
            results.append({
                "id": gif.get("id"),
                "title": query,
                "url": f"https://www.redgifs.com/watch/{gif.get('id')}",
                "video_url": video_url,
                "thumbnail": urls.get("thumbnail") or urls.get("poster", ""),
                "duration": round(gif.get("duration") or 0),
                "views": gif.get("views") or 0,
                "likes": gif.get("likes") or 0,
                "tags": gif.get("tags") or [],
            })

        return results

    except Exception as e:
        print(f"[REDGIFS ERROR] {type(e).__name__}: {e}")
        return None
