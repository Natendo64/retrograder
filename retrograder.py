# mercury_retro_bot.py
"""
Mercury Retrograde Discord Bot

Daily checks https://ismercuryinretrograde.com/ and posts the answer
to a specific Discord channel.

Quick‑start
-----------
1. python -m pip install discord.py aiohttp
2. export DISCORD_TOKEN="your bot token"
   export CHANNEL_ID="123456789012345678"   # target text channel ID
3. python mercury_retro_bot.py

The bot will post once per day at 14:00 UTC and responds to !mercury.
Edit the `POST_TIME_UTC` below if you want a different schedule.
"""

import os
import datetime
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks

# === Config ===
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
POST_TIME_UTC = datetime.time(hour=14, minute=0, tzinfo=datetime.timezone.utc)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def fetch_retrograde_status(session: aiohttp.ClientSession) -> str:
    """Grab the first word from ismercuryinretrograde.com ('Yes' or 'No')."""
    url = "https://ismercuryinretrograde.com/"
    async with session.get(url) as resp:
        text = await resp.text()
        return text.strip().split()[0]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    if not daily_post.is_running():
        daily_post.start()


@tasks.loop(time=POST_TIME_UTC)
async def daily_post():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel {CHANNEL_ID} not found.")
        return

    async with aiohttp.ClientSession() as session:
        status = await fetch_retrograde_status(session)

    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y‑%m‑%d")
    if status.lower().startswith("yes"):
        message = f"🌌 Heads up! Mercury **is** in retrograde as of {today}. Buckle up. 🚀"
    else:
        message = f"All good! Mercury is **not** in retrograde as of {today}. Chill. 😎"

    await channel.send(message)


@bot.command(name="mercury", help="Manually check Mercury retrograde status.")
async def mercury_cmd(ctx: commands.Context):
    async with aiohttp.ClientSession() as session:
        status = await fetch_retrograde_status(session)

    if status.lower().startswith("yes"):
        await ctx.send("Yep, Mercury's in retrograde. Brace yourself.")
    else:
        await ctx.send("Nope, Mercury's behaving. We're fine.")


if __name__ == "__main__":
    if not TOKEN or CHANNEL_ID == 0:
        raise RuntimeError(
            "Set DISCORD_TOKEN and CHANNEL_ID environment variables before running."
        )

    bot.run(TOKEN)
