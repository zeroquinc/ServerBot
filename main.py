import discord
from discord import app_commands
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import subprocess

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
    
@bot.command(name='iostat', brief='Get IOStat information', help='Display IOStat information in an embed.')
async def iostat(ctx):
    if ctx.message.author.bot:
        return
    try:
        output = subprocess.check_output(['iostat', '-x', '1', '2'], text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = str(e.output)
    embed = discord.Embed(title='IOStat', description=f'```\n{output}```', color=0x3498db)
    await ctx.message.delete()
    await ctx.send(embed=embed)

if __name__ == '__main__':
    bot.run(TOKEN)