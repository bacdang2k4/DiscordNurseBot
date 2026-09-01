import os

import aiohttp
from dotenv import load_dotenv


load_dotenv()


PEXELS_API_KEY = os.getenv(
    "PEXELS_API_KEY"
)


PEXELS_IMAGE_URL = (
    "https://api.pexels.com/v1/search"
)


async def search_image(
    query: str,
    per_page: int = 15
):

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY chưa được cấu hình."
        )

    if not query:
        raise ValueError(
            "Bạn chưa nhập từ khóa."
        )

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "per_page": per_page,
        "page": 1,
    }

    timeout = aiohttp.ClientTimeout(
        total=15
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        async with session.get(
            PEXELS_IMAGE_URL,
            headers=headers,
            params=params,
        ) as response:

            if response.status != 200:

                text = await response.text()

                raise RuntimeError(
                    f"Pexels API lỗi "
                    f"{response.status}: {text[:300]}"
                )

            data = await response.json()

    photos = data.get("photos", [])

    if not photos:
        return None

    photo = photos[0]

    return {
        "source": "pexels",
        "type": "image",
        "id": photo.get("id"),
        "title": f"Ảnh: {query}",
        "url": photo["src"]["large"],
        "original_url": photo["src"]["original"],
        "page_url": photo.get(
            "url",
            ""
        ),
        "photographer": photo.get(
            "photographer",
            "Unknown"
        ),
    }