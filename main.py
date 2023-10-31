import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, time
import json
from watchfiles import awatch, Change

import src.weekly_trakt_plays_user.main
import src.weekly_trakt_plays_global.main
import src.trakt_ratings_user.ratings
import src.trakt_favorites.favorites
import src.git_commands.git

# Import Logging
logger = logging.getLogger("ServerBot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
# Add a StreamHandler with the specified formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Load dotenv
load_dotenv()

# Discord.py stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!",intents=intents, activity = discord.Activity(type=discord.ActivityType.watching, name="127.0.0.1"))

# Globals
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
TOKEN = os.environ["DISCORD_TOKEN"]
allowed_roles = "Captain"

# On Ready event
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    # Load Tasks
    try:
        trakt_ratings_task.start()
        trakt_favorites_task.start()
        logger.info("Trakt Ratings Task and Trakt Favorites Task started.")
    except Exception as e:
        logger.info(f'Error starting tasks: {str(e)}')

    logger.info('Bot is ready!')
    
    await plex_webhook()

async def plex_webhook():
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        playing_directory = os.path.join(script_directory, 'webhook', 'json', 'playing')
        playing_channel_id = 1025825630668984450
        content_directory = os.path.join(script_directory, 'webhook', 'json', 'content')
        content_channel_id = 1044424524290072587
        async for changes in awatch(playing_directory, content_directory):
            for change, path in changes:
                if change == Change.added:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    channel_id = playing_channel_id if "playing" in path else content_channel_id
                    channel = bot.get_channel(channel_id)
                    if data is not None:
                        embed = discord.Embed.from_dict(data)
                        await channel.send(embed=embed)
                        logger.info(f'A new Embed has been sent to channel ID: {channel_id}')
                    os.remove(path)
    except Exception as e:
        logger.info(f'Error occurred: {str(e)}')

# !traktweeklyuser
@bot.command(name='traktweeklyuser')
async def trakt_weekly_user(ctx):
    data = src.weekly_trakt_plays_user.main.create_weekly_embed()
    channel = bot.get_channel(1046746288412176434)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))

# !traktweeklyglobal
@bot.command(name='traktweeklyglobal')
async def trakt_weekly_global(ctx):
    data = src.weekly_trakt_plays_global.main.create_weekly_embed()
    channel = bot.get_channel(1144085449007177758)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))

# !gitpull
@bot.command(name='gitpull', help='Pulls GitHub', brief='Pulls the latest changes from GitHub.')
async def git_pull(ctx):
    if any(role.name in allowed_roles for role in ctx.author.roles):
        embed = discord.Embed(title='GitHub Pull', color=0xFFFFFF)
        embed.description = 'Pulling the latest changes...'
        message = await ctx.send(embed=embed)
        pull_output = src.git_commands.git.run_git_pull()
        code_block = f'```\n{pull_output}\n```'
        embed.description = f'Pulling the latest changes...\n{code_block}'
        await message.edit(embed=embed)
    else:
        await ctx.send("You are not authorized!")

# !gitstatus
@bot.command(name='gitstatus', help='Status GitHub', brief='Check the current status of the repo on GitHub.')
async def git_status(ctx):
    if any(role.name in allowed_roles for role in ctx.author.roles):
        embed = discord.Embed(title='Git Status', color=0xFFFFFF)
        embed.description = f'Fetching Git changes and checking status...\n'
        message = await ctx.send(embed=embed)
        fetch_output = src.git_commands.git.run_git_fetch()
        code_block_fetch = f'```{fetch_output}```'
        embed.description += f'\nGit fetch result:\n{code_block_fetch}\n'
        git_status_output = src.git_commands.git.run_git_status()
        code_block_status = f'```{git_status_output}```'
        embed.description += f'Git status:\n{code_block_status}\n'
        await message.edit(embed=embed)
    else:
        await ctx.send("You are not authorized!")
        
# Define the !trakt command
@bot.command(name='trakt')
async def send_weekly_embeds(ctx):
    # Put your task loop code here
    try:
        # Weekly Trakt User Plays
        data_user = src.weekly_trakt_plays_user.main.create_weekly_embed()
        channel_user = bot.get_channel(1046746288412176434)
        for embed in data_user['embeds']:
            await channel_user.send(embed=discord.Embed.from_dict(embed))
        # Log success
        await ctx.send("Weekly Trakt User Plays sent successfully.")

        # Weekly Trakt Global Plays
        data_global = src.weekly_trakt_plays_global.main.create_weekly_embed()
        channel_global = bot.get_channel(1144085449007177758)
        for embed in data_global['embeds']:
            await channel_global.send(embed=discord.Embed.from_dict(embed))
        # Log success
        await ctx.send("Weekly Trakt Global Plays sent successfully.")
    except Exception as e:
        # Log and inform about errors
        await ctx.send(f"An error occurred: {str(e)}")

# Trakt Ratings Task Loop
@tasks.loop(minutes=60)
async def trakt_ratings_task():
    logger.info("Starting Trakt Ratings Task")
    
    try:
        logger.info("Loading processed embeds...")
        src.trakt_ratings_user.ratings.load_processed_embeds()
        
        logger.info("Fetching Trakt ratings data...")
        data = src.trakt_ratings_user.ratings.trakt_ratings()
        
        channel = bot.get_channel(1071806800527118367)
        
        if data is not None:
            logger.info("Sending Trakt ratings data to channel...")
            for embed in data['embeds']:
                await channel.send(embed=discord.Embed.from_dict(embed))
        else:
            logger.info("No data to send. Trying again in 60 minutes.")
    except Exception as e:
        logger.info(f'Error occurred: {str(e)}')

# Trakt Favorites Task Loop        
@tasks.loop(minutes=30)
async def trakt_favorites_task():
    now = datetime.now()
    if now.minute == 0:
        try:
            data = src.trakt_favorites.favorites.trakt_favorites()
            channel = bot.get_channel(1071806800527118367)
            if data is not None:
                for embed in data['embeds']:
                    await channel.send(embed=discord.Embed.from_dict(embed))
        except Exception as e:
            logger.info(f'Error occurred: {str(e)}')
   
if __name__ == '__main__':
    bot.run(TOKEN)