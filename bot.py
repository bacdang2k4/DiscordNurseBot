import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sources.images import search_image
from sources.videos import search_video
from sources.reddit import get_random_reddit_post

from utils.cooldown import (
    CooldownManager
)

from utils.media import (
    is_valid_url
)


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv(
    "DISCORD_TOKEN"
)


if not TOKEN:

    raise RuntimeError(
        "Không tìm thấy DISCORD_TOKEN trong .env"
    )


# ============================================================
# DISCORD INTENTS
# ============================================================

intents = discord.Intents.default()

intents.message_content = True


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None
)


# ============================================================
# COOLDOWN
# ============================================================

cooldown = CooldownManager(
    cooldown_seconds=10
)


# ============================================================
# CHECK COOLDOWN
# ============================================================

async def check_cooldown(ctx):

    allowed, remaining = cooldown.check(
        ctx.author.id
    )

    if not allowed:

        await ctx.send(
            f"⏳ Bạn cần đợi "
            f"**{remaining:.1f} giây** "
            f"trước khi sử dụng lệnh tiếp."
        )

        return False

    return True


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    print("=" * 60)

    print(
        f"Bot online: {bot.user}"
    )

    print(
        f"Bot ID: {bot.user.id}"
    )

    print(
        f"Servers: {len(bot.guilds)}"
    )

    print("=" * 60)

    await bot.change_presence(
        activity=discord.Game(
            name=".help | Media Bot"
        )
    )


# ============================================================
# PING
# ============================================================

@bot.command()
async def ping(ctx):

    latency = round(
        bot.latency * 1000
    )

    await ctx.send(
        f"🏓 Pong! `{latency} ms`"
    )


# ============================================================
# BOT INFO
# ============================================================

@bot.command()
async def botinfo(ctx):

    embed = discord.Embed(
        title="🤖 DiscordNurseBot",
        description=(
            "Bot tìm kiếm media "
            "từ nhiều nguồn."
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Servers",
        value=str(
            len(bot.guilds)
        ),
        inline=True
    )

    embed.add_field(
        name="Latency",
        value=(
            f"{round(bot.latency * 1000)} ms"
        ),
        inline=True
    )

    embed.add_field(
        name="Prefix",
        value=".",
        inline=True
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# HELP
# ============================================================

@bot.command(name="help")
async def help_command(ctx):

    embed = discord.Embed(
        title="📖 DiscordNurseBot",
        description=(
            "Các lệnh có sẵn:"
        ),
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🖼️ `.image <keyword>`",
        value=(
            "Tìm ảnh trên Pexels.\n"
            "Ví dụ: `.image cat`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎬 `.video <keyword>`",
        value=(
            "Tìm video trên Pexels.\n"
            "Ví dụ: `.video minecraft`"
        ),
        inline=False
    )

    embed.add_field(
        name="🔴 `.reddit`",
        value=(
            "Lấy một bài media SFW "
            "từ Reddit."
        ),
        inline=False
    )

    embed.add_field(
        name="🏓 `.ping`",
        value=(
            "Kiểm tra bot."
        ),
        inline=False
    )

    embed.add_field(
        name="ℹ️ `.botinfo`",
        value=(
            "Thông tin bot."
        ),
        inline=False
    )

    await ctx.send(
        embed=embed
    )


# ============================================================
# IMAGE
# ============================================================

@bot.command()
async def image(ctx, *, query: str = None):

    if not query:

        await ctx.send(
            "❌ Ví dụ:\n"
            "`.image cat`"
        )

        return


    if not await check_cooldown(ctx):
        return


    processing = await ctx.send(
        "🔍 Đang tìm ảnh..."
    )


    try:

        result = await search_image(
            query
        )

        if not result:

            await processing.edit(
                content=(
                    "❌ Không tìm thấy ảnh."
                )
            )

            return


        url = result["url"]


        if not is_valid_url(url):

            await processing.edit(
                content=(
                    "❌ URL ảnh không hợp lệ."
                )
            )

            return


        embed = discord.Embed(
            title=(
                f"🖼️ {result['title']}"
            ),
            color=discord.Color.green()
        )


        embed.set_image(
            url=url
        )


        embed.add_field(
            name="Nguồn",
            value="Pexels",
            inline=True
        )


        embed.add_field(
            name="Tác giả",
            value=result.get(
                "photographer",
                "Unknown"
            ),
            inline=True
        )


        if result.get("page_url"):

            embed.url = result[
                "page_url"
            ]


        embed.set_footer(
            text=(
                f"Requested by "
                f"{ctx.author.display_name}"
            )
        )


        await processing.delete()

        await ctx.send(
            embed=embed
        )


    except Exception as e:

        print(
            f"[IMAGE ERROR] {e}"
        )

        await processing.edit(
            content=(
                "❌ Có lỗi khi tìm ảnh."
            )
        )


# ============================================================
# VIDEO
# ============================================================

@bot.command()
async def video(ctx, *, query: str = None):

    if not query:

        await ctx.send(
            "❌ Ví dụ:\n"
            "`.video minecraft`"
        )

        return


    if not await check_cooldown(ctx):
        return


    processing = await ctx.send(
        "🔍 Đang tìm video..."
    )


    try:

        result = await search_video(
            query
        )


        if not result:

            await processing.edit(
                content=(
                    "❌ Không tìm thấy video."
                )
            )

            return


        url = result["url"]


        if not is_valid_url(url):

            await processing.edit(
                content=(
                    "❌ URL video không hợp lệ."
                )
            )

            return


        embed = discord.Embed(
            title=(
                f"🎬 {result['title']}"
            ),
            description=(
                f"⏱️ Thời lượng: "
                f"{result.get('duration', '?')} giây"
            ),
            color=discord.Color.purple()
        )


        if result.get("page_url"):

            embed.url = result[
                "page_url"
            ]


        embed.add_field(
            name="Video",
            value=(
                f"[▶️ Xem video]({url})"
            ),
            inline=False
        )


        embed.set_footer(
            text=(
                f"Requested by "
                f"{ctx.author.display_name}"
            )
        )


        await processing.delete()

        await ctx.send(
            embed=embed
        )


    except Exception as e:

        print(
            f"[VIDEO ERROR] {e}"
        )

        await processing.edit(
            content=(
                "❌ Có lỗi khi tìm video."
            )
        )


# ============================================================
# REDDIT
# ============================================================

@bot.command()
async def reddit(ctx):

    if not await check_cooldown(ctx):
        return


    processing = await ctx.send(
        "🔍 Đang lấy media từ Reddit..."
    )


    try:

        result = await get_random_reddit_post()


        if not result:

            await processing.edit(
                content=(
                    "❌ Không tìm thấy media Reddit."
                )
            )

            return


        url = result["url"]


        if not is_valid_url(url):

            await processing.edit(
                content=(
                    "❌ URL Reddit không hợp lệ."
                )
            )

            return


        embed = discord.Embed(
            title=(
                f"🔴 r/{result['subreddit']}"
            ),
            description=(
                result["title"][:300]
            ),
            url=result["permalink"],
            color=discord.Color.red()
        )


        embed.set_image(
            url=url
        )


        embed.add_field(
            name="Upvotes",
            value=str(
                result["score"]
            ),
            inline=True
        )


        embed.set_footer(
            text=(
                f"Requested by "
                f"{ctx.author.display_name}"
            )
        )


        await processing.delete()

        await ctx.send(
            embed=embed
        )


    except Exception as e:

        print(
            f"[REDDIT ERROR] {e}"
        )

        await processing.edit(
            content=(
                "❌ Không thể lấy dữ liệu Reddit.\n"
                "Kiểm tra Reddit API credentials."
            )
        )


# ============================================================
# ERROR HANDLER
# ============================================================

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
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Thiếu thông tin cho lệnh."
        )

        return


    print(
        f"[COMMAND ERROR] {error}"
    )


# ============================================================
# START
# ============================================================

print(
    "Đang khởi động DiscordNurseBot..."
)

bot.run(TOKEN)