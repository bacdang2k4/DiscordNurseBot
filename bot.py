import os
import time
from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from sources.redgifs import search_redgifs
from sources.neko import get_neko, get_supported_types
from sources.purr import get_purr, get_purr_types
from sources.rule34 import search_rule34
from sources.gelbooru import search_gelbooru


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
    command_prefix="!",
    intents=intents,
    help_command=None
)


# ============================================================
# COOLDOWN
# ============================================================

user_cooldowns = defaultdict(float)
COOLDOWN_SECONDS = 8


async def check_cooldown(interaction: discord.Interaction) -> bool:
    now = time.time()
    last = user_cooldowns[interaction.user.id]

    if now - last < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last)
        await interaction.response.send_message(
            f"⏳ Bạn cần đợi **{remaining:.1f} giây**.", ephemeral=True
        )
        return False

    user_cooldowns[interaction.user.id] = now
    return True


def is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def is_nsfw(interaction: discord.Interaction) -> bool:
    ch = interaction.channel
    return isinstance(ch, discord.TextChannel) and ch.is_nsfw()


def log(interaction: discord.Interaction, **kwargs):
    parts = [f"[/{interaction.command.name}]", f"user={interaction.user}"]
    parts += [f"{k}={v}" for k, v in kwargs.items()]
    print(" | ".join(parts))


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Bot online: {bot.user}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)
    await bot.change_presence(activity=discord.Game(name="/gif | /gel | /r34 | NSFW"))
    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} slash command(s)")
    except Exception as e:
        print(f"[SYNC ERROR] {e}")


# ============================================================
# AUTOCOMPLETE
# ============================================================

async def neko_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    types = ["random"] + get_supported_types()
    return [
        app_commands.Choice(name=t, value=t)
        for t in types if current.lower() in t.lower()
    ][:25]


async def purr_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=t, value=t)
        for t in get_purr_types() if current.lower() in t.lower()
    ][:25]


# ============================================================
# /help
# ============================================================

@bot.tree.command(name="help", description="Hiển thị danh sách lệnh của bot")
async def help_command(interaction: discord.Interaction):
    log(interaction)
    embed = discord.Embed(
        title="📖 NSFW Bot",
        description="**Chỉ dùng trong kênh NSFW**",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="🎞️ `/gif <từ khóa>`",
        value="Tìm video/GIF NSFW từ RedGifs (play được trong Discord)\nVí dụ: `/gif asian blowjob`",
        inline=False
    )
    embed.add_field(
        name="🌸 `/neko <type>`",
        value="Ảnh từ NekoBot\nVí dụ: `/neko ass` | `/neko random`",
        inline=False
    )
    embed.add_field(
        name="🐱 `/purr <type>`",
        value="Ảnh/GIF từ PurrBot\nVí dụ: `/purr anal` | `/purr yuri`",
        inline=False
    )
    embed.add_field(
        name="🔞 `/r34 <tags>`",
        value="Tìm ảnh/video từ Rule34\nVí dụ: `/r34 asian` | `/r34 hentai blowjob`",
        inline=False
    )
    embed.add_field(
        name="🌐 `/gel <tags>`",
        value="Tìm ảnh/video từ Gelbooru\nVí dụ: `/gel asian` | `/gel asian blowjob`",
        inline=False
    )
    embed.add_field(
        name="🏓 `/ping`",
        value="Kiểm tra bot",
        inline=False
    )
    await interaction.response.send_message(embed=embed)


# ============================================================
# /gif <query>
# ============================================================

@bot.tree.command(name="gif", description="Tìm video/GIF NSFW từ RedGifs (play được trong Discord)")
@app_commands.describe(query="Tags cách nhau bằng dấu phẩy. Ví dụ: asian, blowjob, pov")
async def gif(interaction: discord.Interaction, query: str):
    full_query = query.strip()
    log(interaction, query=full_query)
    await interaction.response.defer()

    if not is_nsfw(interaction):
        return await interaction.edit_original_response(content="❌ Chỉ dùng trong kênh **NSFW**!")

    now = time.time()
    last = user_cooldowns[interaction.user.id]
    if now - last < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last)
        return await interaction.edit_original_response(content=f"⏳ Bạn cần đợi **{remaining:.1f} giây**.")
    user_cooldowns[interaction.user.id] = now

    try:
        results = await search_redgifs(full_query)

        if not results:
            return await interaction.edit_original_response(content="❌ Không tìm thấy kết quả. Thử từ khóa khác.")

        # Embed tổng hợp info cả 3 video
        embed = discord.Embed(
            title=f"🎞️ {full_query} — {len(results)} video",
            color=discord.Color.dark_teal()
        )
        for i, r in enumerate(results):
            tags = r["tags"]
            tag_str = " ".join(f"#{t}" for t in tags[:10]) if tags else "—"
            embed.add_field(
                name=f"[{i+1}] ⏱️{r['duration']}s  👁️{r['views']:,}  ❤️{r['likes']:,}",
                value=tag_str,
                inline=False
            )
        embed.set_footer(text=f"{interaction.user.display_name} • redgifs.com")

        await interaction.edit_original_response(embed=embed)
        # Gửi tất cả 3 URL trong 1 tin → Discord preview cả 3 inline
        await interaction.followup.send("\n".join(r["video_url"] for r in results))

    except Exception as e:
        print(f"[GIF] {e}")
        await interaction.edit_original_response(content="❌ Lỗi khi tìm video.")


# ============================================================
# /neko <type>
# ============================================================

@bot.tree.command(name="neko", description="Lấy ảnh NSFW từ NekoBot")
@app_commands.describe(type="Loại ảnh, ví dụ: ass, pussy, random")
@app_commands.autocomplete(type=neko_autocomplete)
async def neko(interaction: discord.Interaction, type: str = "random"):
    log(interaction, type=type)
    if not is_nsfw(interaction):
        return await interaction.response.send_message(
            "❌ Chỉ dùng trong kênh **NSFW**!", ephemeral=True
        )

    if not await check_cooldown(interaction):
        return

    type_ = type.lower().strip()
    supported = get_supported_types()

    if type_ not in ["random"] + supported:
        return await interaction.response.send_message(
            f"❌ Type không hợp lệ.\n"
            f"Các type hỗ trợ: `{'`, `'.join(supported)}`, `random`",
            ephemeral=True
        )

    await interaction.response.defer()

    try:
        result = await get_neko(type_)

        if not result or not is_valid_url(result.get("url")):
            return await interaction.edit_original_response(content="❌ Không lấy được ảnh.")

        embed = discord.Embed(title=result["title"], color=discord.Color.dark_magenta())
        embed.set_image(url=result["url"])
        embed.set_footer(text=f"NekoBot • {interaction.user.display_name}")

        await interaction.edit_original_response(embed=embed)

    except Exception as e:
        print(f"[NEKO CMD ERROR] {e}")
        await interaction.edit_original_response(content="❌ Có lỗi xảy ra.")


# ============================================================
# /purr <type>
# ============================================================

@bot.tree.command(name="purr", description="Lấy ảnh/GIF NSFW từ PurrBot")
@app_commands.describe(type="Loại ảnh, ví dụ: anal, blowjob, yuri")
@app_commands.autocomplete(type=purr_autocomplete)
async def purr(interaction: discord.Interaction, type: str = "neko"):
    log(interaction, type=type)
    if not is_nsfw(interaction):
        return await interaction.response.send_message(
            "❌ Chỉ dùng trong kênh **NSFW**!", ephemeral=True
        )

    if not await check_cooldown(interaction):
        return

    type_ = type.lower().strip()
    supported = get_purr_types()

    if type_ not in supported:
        return await interaction.response.send_message(
            f"❌ Type không hợp lệ.\n"
            f"Các type hỗ trợ: `{'`, `'.join(supported)}`",
            ephemeral=True
        )

    await interaction.response.defer()

    try:
        result = await get_purr(type_)

        if not result or not is_valid_url(result.get("url")):
            return await interaction.edit_original_response(content="❌ Không lấy được ảnh.")

        embed = discord.Embed(title=result["title"], color=discord.Color.orange())
        embed.set_image(url=result["url"])
        embed.set_footer(text=f"PurrBot • {interaction.user.display_name}")

        await interaction.edit_original_response(embed=embed)

    except Exception as e:
        print(f"[PURR CMD ERROR] {e}")
        await interaction.edit_original_response(content="❌ Có lỗi xảy ra.")


# ============================================================
# /rule34 <tags>
# ============================================================

@bot.tree.command(name="r34", description="Tìm kiếm ảnh/video từ Rule34 theo tags")
@app_commands.describe(tags="Tags tìm kiếm, cách nhau bằng dấu cách. Ví dụ: asian blowjob")
async def r34(interaction: discord.Interaction, tags: str):
    log(interaction, tags=tags)
    await interaction.response.defer()

    if not is_nsfw(interaction):
        return await interaction.edit_original_response(content="❌ Chỉ dùng trong kênh **NSFW**!")

    now = time.time()
    last = user_cooldowns[interaction.user.id]
    if now - last < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last)
        return await interaction.edit_original_response(content=f"⏳ Bạn cần đợi **{remaining:.1f} giây**.")
    user_cooldowns[interaction.user.id] = now

    try:
        result = await search_rule34(tags)

        if not result or not is_valid_url(result.get("url")):
            return await interaction.edit_original_response(content="❌ Không tìm thấy kết quả. Thử tags khác.")

        tag_list = result["tags"].split()[:8]
        tag_display = " ".join(f"`{t}`" for t in tag_list)

        embed = discord.Embed(
            title=f"Rule34 • {tags}",
            url=result["post_url"],
            color=discord.Color.from_rgb(0, 153, 255)
        )
        embed.add_field(name="Tags", value=tag_display or "—", inline=False)
        embed.add_field(name="Score", value=str(result["score"]), inline=True)
        embed.add_field(name="ID", value=str(result["id"]), inline=True)
        embed.set_footer(text=f"{interaction.user.display_name} • rule34.xxx")

        if result["is_video"]:
            embed.description = f"🎬 **Video:** {result['url']}"
            await interaction.edit_original_response(embed=embed)
            await interaction.followup.send(result["url"])
        else:
            embed.set_image(url=result["url"])
            await interaction.edit_original_response(embed=embed)

    except Exception as e:
        print(f"[RULE34 CMD] {e}")
        await interaction.edit_original_response(content="❌ Lỗi khi tìm kiếm.")


# ============================================================
# /gel <tags>
# ============================================================

@bot.tree.command(name="gel", description="Tìm ảnh/video NSFW từ Gelbooru")
@app_commands.describe(tags="Tags cách nhau bằng dấu phẩy. Ví dụ: asian, anal, cum in mouth")
async def gel(interaction: discord.Interaction, tags: str):
    full_tags = tags.strip()
    log(interaction, tags=full_tags)
    await interaction.response.defer()

    if not is_nsfw(interaction):
        return await interaction.edit_original_response(content="❌ Chỉ dùng trong kênh **NSFW**!")

    now = time.time()
    last = user_cooldowns[interaction.user.id]
    if now - last < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last)
        return await interaction.edit_original_response(content=f"⏳ Bạn cần đợi **{remaining:.1f} giây**.")
    user_cooldowns[interaction.user.id] = now

    try:
        result = await search_gelbooru(full_tags)

        if not result:
            return await interaction.edit_original_response(content="❌ Không tìm thấy kết quả. Thử tags khác.")

        tag_list = result["tags"].split()[:10]
        tag_display = " ".join(f"`{t}`" for t in tag_list)

        embed = discord.Embed(
            title=f"Gelbooru • {full_tags}",
            url=result["post_url"],
            color=discord.Color.from_rgb(0, 200, 100)
        )
        embed.add_field(name="Tags", value=tag_display or "—", inline=False)
        embed.add_field(name="Score", value=str(result["score"]), inline=True)
        embed.add_field(name="ID", value=str(result["id"]), inline=True)
        embed.set_footer(text=f"{interaction.user.display_name} • gelbooru.com")

        await interaction.edit_original_response(embed=embed)
        await interaction.followup.send(result["url"])

    except Exception as e:
        print(f"[GEL CMD] {e}")
        await interaction.edit_original_response(content="❌ Lỗi khi tìm kiếm.")


# ============================================================
# /ping
# ============================================================

@bot.tree.command(name="ping", description="Kiểm tra độ trễ của bot")
async def ping(interaction: discord.Interaction):
    log(interaction)
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)} ms`")


# ============================================================
# /sync  (chỉ bot owner dùng được)
# ============================================================

@bot.tree.command(name="sync", description="Sync slash commands (chỉ owner)")
async def sync_slash(interaction: discord.Interaction):
    if interaction.user.id != (await bot.application_info()).owner.id:
        return await interaction.response.send_message("❌ Chỉ owner mới dùng được.", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    synced = await bot.tree.sync()
    await interaction.edit_original_response(content=f"✅ Đã sync **{len(synced)}** lệnh.")


# Prefix command !sync — dùng được ngay mà không cần restart
@bot.command(name="sync")
async def sync_prefix(ctx):
    app_info = await bot.application_info()
    if ctx.author.id != app_info.owner.id:
        return await ctx.send("❌ Chỉ owner mới dùng được.")
    msg = await ctx.send("⏳ Đang sync...")
    synced = await bot.tree.sync()
    await msg.edit(content=f"✅ Đã sync **{len(synced)}** slash command(s).")


# ============================================================
# START
# ============================================================

print("Đang khởi động NSFW Bot...")
bot.run(TOKEN)
