import random
import aiohttp


NEKOBOT_TYPES = [
    "pussy",
    "ass",
    "boobs",
    "4k",
    "gonewild",
    "anal",
    "thigh",
    "hentai",
    "hboobs",
    "hass",
]


async def get_nekobot_image(type_: str = None):
    """
    Lấy ảnh từ NekoBot (không hỗ trợ search từ khóa tự do).
    """
    if type_ is None:
        type_ = random.choice(NEKOBOT_TYPES)

    url = f"https://nekobot.xyz/api/image?type={type_}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        image_url = data.get("message")
        if not image_url:
            return None

        return {
            "source": "nekobot",
            "type": type_,
            "url": image_url,
            "title": f"NekoBot • {type_}",
        }

    except Exception as e:
        print(f"[NEKOBOT IMAGE ERROR] {e}")
        return None