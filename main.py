import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta

import src.weekly_trakt_plays_user

# Import Logging
logger = logging.getLogger("ServerBot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt = "%d-%m-%Y %I:%M:%S %p")

# Load dotenv
load_dotenv()

# Discord.py stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!",intents=intents)

# Globals
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
TOKEN = os.environ["DISCORD_TOKEN"]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    now = datetime.now()
    time_until_monday = (7 - now.weekday()) % 7
    target_time = datetime(now.year, now.month, now.day, 0, 0) + timedelta(days=time_until_monday)
    seconds_until_target = (target_time - now).total_seconds()
    await asyncio.sleep(seconds_until_target)
    data = src.weekly_trakt_plays_user.create_weekly_embed()
    channel = bot.get_channel(1046746288412176434)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))
        
@bot.command(name='traktweekly')
async def trakt_weekly(ctx):
    data = src.weekly_trakt_plays_user.create_weekly_embed()
    channel = bot.get_channel(1046746288412176434)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))

if __name__ == '__main__':
    bot.run(TOKEN)