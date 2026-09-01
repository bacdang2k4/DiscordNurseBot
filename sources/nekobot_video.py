import aiohttp


async def get_nekobot_video():
    """
    NekoBot chỉ có pgif (GIF sex).
    """
    url = "https://nekobot.xyz/api/image?type=pgif"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        gif_url = data.get("message")
        if not gif_url:
            return None

        return {
            "source": "nekobot",
            "type": "pgif",
            "url": gif_url,
            "title": "NekoBot • pgif",
        }

    except Exception as e:
        print(f"[NEKOBOT VIDEO ERROR] {e}")
        return None