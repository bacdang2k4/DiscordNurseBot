import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
import praw


# =========================================================
# 1. LOAD CONFIGURATION
# =========================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")


# Kiểm tra biến môi trường
if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

if not REDDIT_CLIENT_ID:
    raise RuntimeError("Missing REDDIT_CLIENT_ID in .env")

if not REDDIT_CLIENT_SECRET:
    raise RuntimeError("Missing REDDIT_CLIENT_SECRET in .env")

if not REDDIT_USER_AGENT:
    raise RuntimeError("Missing REDDIT_USER_AGENT in .env")


# =========================================================
# 2. DISCORD CONFIGURATION
# =========================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None
)


# =========================================================
# 3. REDDIT CONFIGURATION
# =========================================================

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    check_for_async=False
)


# Chỉ dùng các subreddit phù hợp với mục đích không-explicit
SUBREDDITS = [
    "EarthPorn",
    "NatureIsFuckingLit",
    "CityPorn",
    "wallpapers"
]


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
)


# =========================================================
# 4. BOT READY
# =========================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Bot online: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)

    await bot.change_presence(
        activity=discord.Game(
            name=".random | Reddit"
        )
    )


# =========================================================
# 5. HELP COMMAND
# =========================================================

@bot.command(name="help")
async def help_command(ctx):

    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="Các lệnh hiện có:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name=".random",
        value="Lấy một bài Reddit ngẫu nhiên.",
        inline=False
    )

    embed.add_field(
        name=".ping",
        value="Kiểm tra bot có hoạt động không.",
        inline=False
    )

    await ctx.send(embed=embed)


# =========================================================
# 6. PING COMMAND
# =========================================================

@bot.command(name="ping")
async def ping(ctx):

    latency = round(bot.latency * 1000)

    await ctx.send(
        f"🏓 Pong! `{latency} ms`"
    )


# =========================================================
# 7. GET REDDIT POSTS
# =========================================================

def get_random_reddit_post():

    # Chọn subreddit
    subreddit_name = random.choice(SUBREDDITS)

    subreddit = reddit.subreddit(subreddit_name)

    # Lấy một lượng post giới hạn
    posts = list(
        subreddit.hot(limit=50)
    )

    # Lọc bài có ảnh trực tiếp
    image_posts = []

    for post in posts:

        if post.stickied:
            continue

        if not post.url:
            continue

        url = post.url.lower()

        if url.endswith(IMAGE_EXTENSIONS):
            image_posts.append(post)

    if not image_posts:
        return None

    return random.choice(image_posts)


# =========================================================
# 8. RANDOM REDDIT COMMAND
# =========================================================

@bot.command(name="random")
@commands.cooldown(
    1,
    10,
    commands.BucketType.user
)
async def random_post(ctx):

    # Thông báo đang xử lý
    message = await ctx.send(
        "🔍 Đang tìm bài Reddit..."
    )

    try:

        post = get_random_reddit_post()

        if post is None:

            await message.edit(
                content="❌ Không tìm thấy bài phù hợp."
            )

            return

        # Reddit permalink
        reddit_url = (
            f"https://www.reddit.com"
            f"{post.permalink}"
        )

        embed = discord.Embed(
            title=post.title[:256]
            if post.title
            else "Reddit Post",
            url=reddit_url,
            color=discord.Color.blue()
        )

        embed.set_image(
            url=post.url
        )

        embed.set_footer(
            text=(
                f"r/{post.subreddit.display_name} "
                f"| 👍 {post.score}"
            )
        )

        await message.delete()

        await ctx.send(
            embed=embed
        )

    except Exception as e:

        print(
            f"[ERROR] Reddit request failed: {e}"
        )

        await message.edit(
            content=(
                "❌ Không thể lấy dữ liệu Reddit. "
                "Vui lòng thử lại sau."
            )
        )


# =========================================================
# 9. COOLDOWN ERROR
# =========================================================

@random_post.error
async def random_post_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandOnCooldown
    ):

        seconds = round(
            error.retry_after
        )

        await ctx.send(
            f"⏳ Bạn đang dùng lệnh quá nhanh. "
            f"Thử lại sau `{seconds}` giây."
        )


# =========================================================
# 10. UNKNOWN COMMAND
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    if isinstance(
        error,
        commands.CommandOnCooldown
    ):
        return

    print(
        f"[COMMAND ERROR] {error}"
    )


# =========================================================
# 11. START BOT
# =========================================================

print("Starting Discord bot...")

bot.run(DISCORD_TOKEN)