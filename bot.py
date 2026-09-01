import os
import time
from collections import defaultdict

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sources.reddit_image import search_reddit_image
from sources.reddit_video import search_reddit_video
from sources.neko import get_neko, get_supported_types


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("Không tìm thấy DISCORD_TOKEN trong .env")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    help_command=None
)


# ============================================================
# COOLDOWN
# ============================================================

user_cooldowns = defaultdict(float)
COOLDOWN_SECONDS = 8


async def check_cooldown(ctx):
    now = time.time()
    last = user_cooldowns[ctx.author.id]

    if now - last < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last)
        await ctx.send(f"⏳ Bạn cần đợi **{remaining:.1f} giây**.")
        return False

    user_cooldowns[ctx.author.id] = now
    return True


def is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Bot online: {bot.user}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)
    await bot.change_presence(activity=discord.Game(name=".image | .video | NSFW"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Thiếu từ khóa.\nVí dụ: `.image asia anal`")
        return
    print(f"[ERROR] {error}")


# ============================================================
# HELP
# ============================================================

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 NSFW Bot",
        description="**Chỉ dùng trong kênh NSFW**",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="🖼️ `.image <từ khóa>`",
        value="Tìm ảnh NSFW (ưu tiên châu Á)\nVí dụ: `.image anal`",
        inline=False
    )
    embed.add_field(
        name="🎬 `.video <từ khóa>`",
        value="Tìm video NSFW (ưu tiên châu Á)\nVí dụ: `.video blowjob`",
        inline=False
    )
    embed.add_field(
        name="🌸 `.neko <type>`",
        value=(
            "Ảnh từ NekoBot\n"
            "Ví dụ: `.neko ass` | `.neko pussy` | `.neko random`\n"
            f"Type: `ass`, `pussy`, `boobs`, `anal`, `thigh`, `4k`, `hentai`..."
        ),
        inline=False
    )
    embed.add_field(
        name="🏓 `.ping`",
        value="Kiểm tra bot",
        inline=False
    )
    await ctx.send(embed=embed)


# ============================================================
# .image <query>
# ============================================================

@bot.command(name="image")
async def image(ctx, *, query: str = None):
    if not ctx.channel.is_nsfw():
        return await ctx.send("❌ Chỉ dùng trong kênh **NSFW**!")

    if not query:
        return await ctx.send("❌ Ví dụ: `.image asia anal`")

    if not await check_cooldown(ctx):
        return

    msg = await ctx.send(f"🔍 Đang tìm ảnh: **{query}**...")

    try:
        result = await search_reddit_image(query)

        if not result or not is_valid_url(result.get("url")):
            return await msg.edit(content="❌ Không tìm thấy ảnh.")

        embed = discord.Embed(
            title=result["title"][:200],
            url=result.get("permalink"),
            color=discord.Color.dark_red()
        )
        embed.set_image(url=result["url"])
        embed.add_field(name="Subreddit", value=f"r/{result['subreddit']}", inline=True)
        embed.add_field(name="Upvotes", value=str(result["score"]), inline=True)
        embed.set_footer(text=f"{ctx.author.display_name} • {query}")

        await msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"[IMAGE] {e}")
        await msg.edit(content="❌ Lỗi khi tìm ảnh.")


# ============================================================
# .video <query>
# ============================================================

@bot.command(name="video")
async def video(ctx, *, query: str = None):
    if not ctx.channel.is_nsfw():
        return await ctx.send("❌ Chỉ dùng trong kênh **NSFW**!")

    if not query:
        return await ctx.send("❌ Ví dụ: `.video asia anal`")

    if not await check_cooldown(ctx):
        return

    msg = await ctx.send(f"🔍 Đang tìm video: **{query}**...")

    try:
        result = await search_reddit_video(query)

        if not result or not is_valid_url(result.get("url")):
            return await msg.edit(content="❌ Không tìm thấy video.")

        embed = discord.Embed(
            title=result["title"][:200],
            url=result.get("permalink"),
            description=f"**Link:** {result['url']}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Subreddit", value=f"r/{result['subreddit']}", inline=True)
        embed.add_field(name="Upvotes", value=str(result["score"]), inline=True)
        embed.set_footer(text=f"{ctx.author.display_name} • {query}")

        await msg.delete()
        await ctx.send(embed=embed)
        await ctx.send(result["url"])   # gửi link để Discord preview

    except Exception as e:
        print(f"[VIDEO] {e}")
        await msg.edit(content="❌ Lỗi khi tìm video.")


# ============================================================
# .neko <type>
# ============================================================

@bot.command(name="neko")
async def neko(ctx, type_: str = "random"):
    if not ctx.channel.is_nsfw():
        return await ctx.send("❌ Chỉ dùng trong kênh **NSFW**!")

    if not await check_cooldown(ctx):
        return

    type_ = type_.lower().strip()

    # Hiện danh sách nếu gõ sai
    supported = get_supported_types()
    if type_ not in ["random"] + supported:
        return await ctx.send(
            f"❌ Type không hợp lệ.\n"
            f"Các type hỗ trợ: `{'`, `'.join(supported)}`, `random`\n"
            f"Ví dụ: `.neko ass` | `.neko pussy` | `.neko random`"
        )

    msg = await ctx.send(f"🔍 Đang lấy **{type_}** từ NekoBot...")

    try:
        result = await get_neko(type_)

        if not result or not is_valid_url(result.get("url")):
            return await msg.edit(content="❌ Không lấy được ảnh.")

        embed = discord.Embed(
            title=result["title"],
            color=discord.Color.dark_magenta()
        )
        embed.set_image(url=result["url"])
        embed.set_footer(text=f"NekoBot • {ctx.author.display_name}")

        await msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"[NEKO CMD ERROR] {e}")
        await msg.edit(content="❌ Có lỗi xảy ra.")


# ============================================================
# .ping
# ============================================================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)} ms`")


# ============================================================
# START
# ============================================================

print("Đang khởi động NSFW Bot...")
bot.run(TOKEN)