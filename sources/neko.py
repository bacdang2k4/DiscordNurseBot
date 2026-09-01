import random
import aiohttp


# Các type hỗ trợ của NekoBot
NEKO_TYPES = {
    "pussy": "pussy",
    "ass": "ass",
    "boobs": "boobs",
    "anal": "anal",
    "thigh": "thigh",
    "4k": "4k",
    "gonewild": "gonewild",
    "hentai": "hentai",
    "hboobs": "hboobs",
    "hass": "hass",
    "pgif": "pgif",          # gif
    "random": None,          # random
}


async def get_neko(type_: str = "random"):
    """
    Lấy ảnh/gif từ NekoBot.
    """
    type_ = type_.lower().strip()

    if type_ not in NEKO_TYPES:
        return None

    # Nếu là random thì chọn ngẫu nhiên
    if type_ == "random" or NEKO_TYPES[type_] is None:
        actual_type = random.choice([
            "pussy", "ass", "boobs", "anal", "thigh",
            "4k", "gonewild", "hentai", "hboobs", "hass"
        ])
    else:
        actual_type = NEKO_TYPES[type_]

    url = f"https://nekobot.xyz/api/image?type={actual_type}"

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
            "type": actual_type,
            "url": image_url,
            "title": f"NekoBot • {actual_type}",
        }

    except Exception as e:
        print(f"[NEKO ERROR] {e}")
        return None


def get_supported_types():
    """Trả về danh sách type hỗ trợ (để hiện help)."""
    return [t for t in NEKO_TYPES.keys() if t != "random"]