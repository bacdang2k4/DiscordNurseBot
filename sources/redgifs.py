import random
from collections import deque
from redgifs.aio import API
from redgifs import Order

GAY_TAGS = {"gay", "male_only", "yaoi", "bara", "men_only"}

# Lưu 50 ID gần nhất để không lặp
_recent_ids: deque = deque(maxlen=50)



def _is_clean(gif) -> bool:
    tags = {t.lower() for t in (gif.tags or [])}
    return not tags.intersection(GAY_TAGS)


async def search_redgifs(query: str):
    api = API()
    try:
        await api.login()

        result = await api.search(
            search_text=query.strip(),
            order=Order.TOP28,
            count=20,
            page=1,
        )

        gifs = [
            g for g in (result.gifs or [])
            if _is_clean(g) and g.id not in _recent_ids
        ]

        if not gifs:
            # Nếu tất cả đã xem rồi thì reset và thử lại
            _recent_ids.clear()
            gifs = [g for g in (result.gifs or []) if _is_clean(g)]

        if not gifs:
            return None

        gif = random.choice(gifs)
        _recent_ids.append(gif.id)

        video_url = (
            gif.urls.hd
            or gif.urls.sd
            or gif.urls.file_url
            or gif.urls.vthumbnail
        )

        return {
            "id": gif.id,
            "title": query,
            "url": gif.urls.web_url,
            "video_url": video_url,
            "thumbnail": gif.urls.thumbnail or gif.urls.poster or "",
            "duration": round(gif.duration or 0),
            "views": gif.views or 0,
            "likes": gif.likes or 0,
            "tags": gif.tags or [],
        }

    except Exception as e:
        print(f"[REDGIFS ERROR] {type(e).__name__}: {e}")
        return None
    finally:
        await api.close()
