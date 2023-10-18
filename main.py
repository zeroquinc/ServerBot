import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

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

if __name__ == '__main__':
    bot.run(TOKEN)