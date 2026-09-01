import asyncio
import os
import random

import praw
from dotenv import load_dotenv


load_dotenv()


REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")


reddit = None

if (
    REDDIT_CLIENT_ID
    and REDDIT_CLIENT_SECRET
    and REDDIT_USER_AGENT
):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


# Các subreddit SFW để test bot
SUBREDDITS = [
    "aww",
    "cats",
    "dogs",
    "EarthPorn",
    "space",
    "minecraft",
    "gaming",
    "interestingasfuck",
]


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
)


def _get_reddit_post_sync():

    if reddit is None:
        raise RuntimeError(
            "Reddit API chưa được cấu hình."
        )

    subreddit_name = random.choice(SUBREDDITS)

    subreddit = reddit.subreddit(subreddit_name)

    posts = []

    for post in subreddit.hot(limit=50):

        if post.stickied:
            continue

        if getattr(post, "over_18", False):
            continue

        url = post.url.lower()

        if any(
            url.endswith(ext)
            for ext in IMAGE_EXTENSIONS
        ):
            posts.append(post)

        elif "i.redd.it" in url:
            posts.append(post)

    if not posts:
        return None

    post = random.choice(posts)

    return {
        "source": "reddit",
        "subreddit": subreddit_name,
        "title": post.title,
        "url": post.url,
        "permalink": f"https://www.reddit.com{post.permalink}",
        "score": post.score,
    }


async def get_random_reddit_post():

    return await asyncio.to_thread(
        _get_reddit_post_sync
    )