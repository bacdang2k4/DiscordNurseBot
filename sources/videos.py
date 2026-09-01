import os

import aiohttp
from dotenv import load_dotenv


load_dotenv()


PEXELS_API_KEY = os.getenv(
    "PEXELS_API_KEY"
)


PEXELS_VIDEO_URL = (
    "https://api.pexels.com/videos/search"
)


async def search_video(
    query: str,
    per_page: int = 10
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
            PEXELS_VIDEO_URL,
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

    videos = data.get("videos", [])

    if not videos:
        return None

    video = videos[0]

    video_files = video.get(
        "video_files",
        []
    )

    if not video_files:
        return None

    # Ưu tiên video mp4
    mp4_files = [
        item
        for item in video_files
        if item.get("file_type") == "video/mp4"
    ]

    if mp4_files:
        selected = mp4_files[0]
    else:
        selected = video_files[0]

    return {
        "source": "pexels",
        "type": "video",
        "id": video.get("id"),
        "title": f"Video: {query}",
        "url": selected.get("link"),
        "page_url": video.get(
            "url",
            ""
        ),
        "width": selected.get("width"),
        "height": selected.get("height"),
        "duration": video.get(
            "duration"
        ),
    }