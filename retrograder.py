"""retrograder.py – Mercury Retrograde Discord Bot
Checks https://ismercuryinretrograde.com/ once a day and posts the result to a
specified Discord channel.  Rename this file however you like, but the repo is
called **retrograder**, so we keep the filename consistent.

The bot does two things:
  • Replies to the command  !mercury  (or  /mercury  if you add an app command)
  • Posts the day’s status automatically at 14:00 UTC every day

Dependencies (see requirements.txt):
  discord.py  |  aiohttp
"""

import os
import asyncio
import datetime

import aiohttp
import discord
from discord.ext import commands, tasks


TOKEN      = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
POST_TIME  = datetime.time(hour=14, minute=0, tzinfo=datetime.timezone.utc)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
print("DEBUG ‑ message_content =", intents.message_content)


bot = commands.Bot(command_prefix="!", intents=intents)


async def fetch_status(session: aiohttp.ClientSession) -> str:
    """Grab the single‑word answer (Yes/No) from ismercuryinretrograde.com"""
    async with session.get("https://ismercuryinretrograde.com/") as resp:
        text = (await resp.text()).strip()
        return text.split()[0]  # "Yes" or "No"


@bot.event
async def on_ready():
    print(f"[retrograder] Logged in as {bot.user} (ID: {bot.user.id})")
    if not daily_post.is_running():
        daily_post.start()


@tasks.loop(time=POST_TIME)
async def daily_post():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("[retrograder] ERROR: Channel not found – check CHANNEL_ID")
        return

    async with aiohttp.ClientSession() as session:
        status = await fetch_status(session)

    today = datetime.datetime.utcnow().date()
    if status.lower().startswith("yes"):
        msg = f"🚨 Heads up! Mercury **is** in retrograde – {today}."
    else:
        msg = f"✅ All clear – Mercury is **not** in retrograde – {today}."

    await channel.send(msg)
    print(f"[retrograder] Posted daily status: {msg}")


@bot.command(name="mercury")
async def mercury_cmd(ctx: commands.Context):
    """Manual check command: !mercury"""
    async with aiohttp.ClientSession() as session:
        status = await fetch_status(session)
    reply = (
        "Fuck. Yeah, sorry, it's retrograde today. Stay inside, turn off your phone." if status.lower().startswith("yes")
        else "Mercury's fine today, My Dude. Blame something else."
    )
    await ctx.send(reply)


if __name__ == "__main__":
    if not TOKEN or CHANNEL_ID == 0:
        raise RuntimeError("Set DISCORD_TOKEN and CHANNEL_ID environment variables.")

    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("[retrograder] Shutting down…")
