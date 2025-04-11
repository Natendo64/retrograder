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


API_URL = "https://mercuryretrogradeapi.com?format=json"

async def fetch_status(session: aiohttp.ClientSession) -> str:
    """Return 'Yes', 'No', or 'Unknown' from a reliable JSON API."""
    try:
        async with session.get(API_URL, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = await resp.json()
            return "Yes" if data.get("is_retrograde") else "No"
    except Exception as e:
        import traceback
        print("[retrograder] WARN: API fetch failed:")
        traceback.print_exc()
        return "Unknown"




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
    if status == "Unknown":
        reply = "🤷‍♂️ Can’t reach the retrograde site right now—try again later."
    elif status == "Yes":
        reply = "🚨 Yep, Mercury **is** in retrograde. Duck and cover."
    else:
        reply = "✅ All clear—Mercury isn’t in retrograde today."

    await channel.send(reply)
    print(f"[retrograder] Posted daily status: {reply}")


@bot.command(name="mercury")
async def mercury_cmd(ctx: commands.Context):
    """Manual check command: !mercury"""
    async with aiohttp.ClientSession() as session:
        status = await fetch_status(session)
        if status == "Unknown":
            reply = "🤷‍♂️ Can’t reach the retrograde site right now—try again later."
        elif status == "Yes":
            reply = "🚨 Fuck. Yeah, sorry, Mercury's retrograde today. Stay inside, turn off your phone."
        else:
            reply = "✅ Mercury's fine today, My Dude. Blame something else."
    await ctx.send(reply)


if __name__ == "__main__":
    if not TOKEN or CHANNEL_ID == 0:
        raise RuntimeError("Set DISCORD_TOKEN and CHANNEL_ID environment variables.")

    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        print("[retrograder] Shutting down…")
