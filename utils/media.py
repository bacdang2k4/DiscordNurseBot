from urllib.parse import urlparse


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
)


VIDEO_EXTENSIONS = (
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
)


def is_valid_url(url: str):

    if not url:
        return False

    try:

        parsed = urlparse(url)

        return (
            parsed.scheme in (
                "http",
                "https"
            )
            and bool(parsed.netloc)
        )

    except Exception:

        return False


def is_image_url(url: str):

    if not is_valid_url(url):
        return False

    path = urlparse(url).path.lower()

    return path.endswith(
        IMAGE_EXTENSIONS
    )


def is_video_url(url: str):

    if not is_valid_url(url):
        return False

    path = urlparse(url).path.lower()

    return path.endswith(
        VIDEO_EXTENSIONS
    )