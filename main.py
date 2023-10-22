import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta
import json

import src.weekly_trakt_plays_user.main
import src.weekly_trakt_plays_global.main

import src.trakt_ratings_user.ratings

import src.git_commands.git

import src.docker_commands.main

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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    
    # Load Tasks
    trakt_ratings_task.start()
    
    now = datetime.now()
    time_until_monday = (7 - now.weekday()) % 7
    target_time = datetime(now.year, now.month, now.day, 0, 0) + timedelta(days=time_until_monday)
    seconds_until_target = (target_time - now).total_seconds()
    await asyncio.sleep(seconds_until_target)
    # Weekly Trakt User Plays
    data = src.weekly_trakt_plays_user.main.create_weekly_embed()
    channel = bot.get_channel(1046746288412176434)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))
    # Weekly Trakt Global Plays
    data = src.weekly_trakt_plays_global.main.create_weekly_embed()
    channel = bot.get_channel(1144085449007177758)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))

@bot.command(name='traktweeklyuser')
async def trakt_weekly_user(ctx):
    data = src.weekly_trakt_plays_user.main.create_weekly_embed()
    channel = bot.get_channel(1046746288412176434)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))
        
@bot.command(name='traktweeklyglobal')
async def trakt_weekly_global(ctx):
    data = src.weekly_trakt_plays_global.main.create_weekly_embed()
    channel = bot.get_channel(1144085449007177758)
    for embed in data['embeds']:
        await channel.send(embed=discord.Embed.from_dict(embed))
        
@bot.command(name='dockerps')
async def docker_ps(ctx):
    docker_info = src.docker.run_docker_ps()
    for info in docker_info:
        message = "```"
        for key, value in info.items():
            message += f"{key}: {value}\n"
        message += "```"
        await ctx.send(message)
        
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
        
@tasks.loop(minutes=5)
async def trakt_ratings_task():
    src.trakt_ratings_user.ratings.load_processed_embeds()
    try:
        data = src.trakt_ratings_user.ratings.trakt_ratings()
        channel = bot.get_channel(1071806800527118367)
        if data is not None:
            for embed in data['embeds']:
                await channel.send(embed=discord.Embed.from_dict(embed))
    except Exception as e:
        print(f'Error occurred: {str(e)}')
        
if __name__ == '__main__':
    bot.run(TOKEN)