import discord
from discord.ext import tasks

from src.globals import bot, TOKEN, allowed_roles

from src.logging import logger_discord, logger_trakt, logger_plex, logger_sonarr, logger_tautulli

from src.tautulli import tautulli_discord_presence

from src.plex import plex_webhook

import src.weekly_trakt_plays_user.main
import src.weekly_trakt_plays_global.main
import src.trakt_ratings_user.ratings
import src.trakt_favorites.favorites
import src.git_commands.git

# On Ready event
@bot.event
async def on_ready():
    logger_discord.info(f'Logged in as {bot.user.name} ({bot.user.id}) and is ready!')
    
    # Load Tasks
    try:
        trakt_ratings_task.start()
        trakt_favorites_task.start()
        tautulli_discord_activity.start()
        logger_discord.info("Trakt Ratings Task, Trakt Favorites Task, and Tautulli Activity started.")
    except Exception as e:
        logger_discord.error(f'Error starting tasks: {str(e)}')
    
    # Logging for plex_webhook
    try:
        logger_plex.info("Calling plex_webhook...")
        await plex_webhook()
        logger_plex.info("plex_webhook call succeeded.")
    except Exception as e:
        logger_plex.error(f'An error occurred while calling plex_webhook: {e}')

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
    logger_trakt.info("Starting Trakt Ratings Task.")
    
    try:
        data = src.trakt_ratings_user.ratings.trakt_ratings()
        
        if data is not None:
            channel = bot.get_channel(1071806800527118367)
            
            for embed in data['embeds']:
                logger_trakt.info(f"Found Trakt ratings and sending to Discord: {embed}")
                await channel.send(embed=discord.Embed.from_dict(embed))
        else:
            logger_trakt.info("No data to send. Trying again in 60 minutes.")
    except Exception as e:
        logger_trakt.error(f'Error occurred: {str(e)}')

# Trakt Favorites Task Loop        
@tasks.loop(hours=24)
async def trakt_favorites_task():
    logger_trakt.info("Starting Trakt Favorites Task")
    
    try:
        data = src.trakt_favorites.favorites.trakt_favorites()
        channel = bot.get_channel(1071806800527118367)
        
        if data is not None:
            for embed in data['embeds']:
                await channel.send(embed=discord.Embed.from_dict(embed))
        else:
            logger_trakt.info("No data to send. Trying again in 24 hours.")
    except Exception as e:
        logger_trakt.error(f'Error occurred: {str(e)}')

# Discord Rich Presence Tautulli Task Loop 
@tasks.loop(seconds=300)
async def tautulli_discord_activity():
    try:
        await tautulli_discord_presence(bot)
    except Exception as e:
        logger_tautulli.error(f'An error occurred while calling Tautulli Discord Activity {e}')
   
if __name__ == '__main__':
    bot.run(TOKEN)