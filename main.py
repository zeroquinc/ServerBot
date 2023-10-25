import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, time
import json

import src.weekly_trakt_plays_user.main
import src.weekly_trakt_plays_global.main

import src.trakt_ratings_user.ratings

import src.trakt_favorites.favorites

import src.git_commands.git

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
allowed_roles = "Captain"

# On Ready event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    # Load Tasks
    trakt_ratings_task.start()
    trakt_favorites_task.start()
    send_weekly_embeds.start()
    plex_now_playing.start()

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

# Plex Now Playing Notifications
@tasks.loop(seconds=5)
async def plex_now_playing():
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(script_directory, 'webhook')
        channel_id = 1025825630668984450
        for filename, command in [('plex_resuming.json', 'plex_resuming'),
                                 ('plex_finished.json', 'plex_finished'),
                                 ('plex_started.json', 'plex_started')]:
            file_path = os.path.join(directory, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                channel = bot.get_channel(channel_id)
                if data is not None:
                    embed = discord.Embed.from_dict(data)
                    await channel.send(embed=embed)
                    os.remove(file_path)
    except Exception as e:
        print(f'Error occurred: {str(e)}')

# Trakt Ratings Task Loop
@tasks.loop(minutes=10)
async def trakt_ratings_task():
    now = datetime.now()  
    if now.minute == 0:
        src.trakt_ratings_user.ratings.load_processed_embeds()
        try:
            data = src.trakt_ratings_user.ratings.trakt_ratings()
            channel = bot.get_channel(1071806800527118367)
            if data is not None:
                for embed in data['embeds']:
                    await channel.send(embed=discord.Embed.from_dict(embed))
        except Exception as e:
            print(f'Error occurred: {str(e)}')

# Trakt Favorites Task Loop        
@tasks.loop(minutes=10)
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
            print(f'Error occurred: {str(e)}')

# Weekly Trakt User & Global Plays Task Loop            
@tasks.loop(time=[time(12, 0)])
async def send_weekly_embeds():
    # This task will run every day at 12:00 PM, but we can filter it to only run on Mondays
    if datetime.now().weekday() == 0:  # 0 corresponds to Monday
        # Weekly Trakt User Plays
        data_user = src.weekly_trakt_plays_user.main.create_weekly_embed()
        channel_user = bot.get_channel(1046746288412176434)
        for embed in data_user['embeds']:
            await channel_user.send(embed=discord.Embed.from_dict(embed))  
        # Weekly Trakt Global Plays
        data_global = src.weekly_trakt_plays_global.main.create_weekly_embed()
        channel_global = bot.get_channel(1144085449007177758)
        for embed in data_global['embeds']:
            await channel_global.send(embed=discord.Embed.from_dict(embed))
   
if __name__ == '__main__':
    bot.run(TOKEN)