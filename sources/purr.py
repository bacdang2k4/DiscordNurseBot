import aiohttp


# Một số category NSFW phổ biến của PurrBot
PURR_NSFW_TYPES = {
    "anal": "anal",
    "blowjob": "blowjob",
    "cum": "cum",
    "fuck": "fuck",
    "neko": "neko",
    "pussylick": "pussylick",
    "solo": "solo",
    "threesome_fff": "threesome_fff",
    "threesome_ffm": "threesome_ffm",
    "threesome_mmf": "threesome_mmf",
    "yuri": "yuri",
}


async def get_purr(type_: str = "neko", media: str = "gif"):
    """
    Lấy ảnh/gif từ PurrBot.
    media: "gif" hoặc "img"
    """
    type_ = type_.lower().strip()
    media = media.lower().strip()

    if type_ not in PURR_NSFW_TYPES:
        return None

    if media not in ["gif", "img"]:
        media = "gif"

    url = f"https://api.purrbot.site/v2/img/nsfw/{type_}/{media}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        image_url = data.get("link")
        if not image_url:
            return None

        return {
            "source": "purrbot",
            "type": type_,
            "url": image_url,
            "title": f"PurrBot • {type_}",
        }

    except Exception as e:
        print(f"[PURR ERROR] {e}")
        return None


def get_purr_types():
    return list(PURR_NSFW_TYPES.keys())