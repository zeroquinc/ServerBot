import discord
from discord.ext import tasks, commands
from aiohttp import web
from datetime import datetime, timedelta, time   
import asyncio

from src.custom_logger import logger

from src.globals import (
    bot, 
    TOKEN, 
    CHANNEL_PLEX_CONTENT, 
    CHANNEL_PLEX_PLAYING, 
    CHANNEL_RADARR_GRABS, 
    CHANNEL_SONARR_GRABS, 
    CHANNEL_WATCHTOWER,
    CHANNEL_SYSTEM_INFO,
    CHANNEL_TRAKT_USER,
    CHANNEL_TRAKT_GLOBAL,
    CHANNEL_TRAKT_RATINGS,
    CHANNEL_PLEXTRAKTSYNC,
    CHANNEL_ACHIEVEMENTS,
    CHANNEL_MASTERED,
    CHANNEL_RETRO_OVERVIEW,
    RETRO_TARGET_USERNAMES
)

from src.plex import (
    plex_play, 
    plex_resume, 
    plex_episode_content, 
    plex_season_content, 
    plex_movie_content
)

from src.trakt_favorites import trakt_favorites
from src.trakt_ratings import trakt_ratings
from src.trakt_user_weekly import create_weekly_user_embed
from src.trakt_global_weekly import create_weekly_global_embed
from src.tautulli_presence import tautulli_discord_presence
from src.watchtower import create_watchtower_embed
from src.sonarr import create_sonarr_embed
from src.radarr import create_radarr_embed
from src.system import system_info
from src.plextraktsync import plextraktsync
from src.retroachievements import fetch_completion, fetch_recent_achievements, create_daily_overview

import asyncio
from datetime import datetime, timedelta

import asyncio
from datetime import datetime, timedelta

import asyncio
from datetime import datetime, timedelta

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id}) and is ready!')

    # Start the tasks immediately
    trakt_ratings_task.start()
    logger.info("Trakt Ratings Task started")
    trakt_favorites_task.start()
    logger.info("Trakt Favorites Task started")
    tautulli_discord_activity.start()
    logger.info("Tautulli Discord Activity Task started")
    fetch_retroachievements.start()
    logger.info("RetroAchievements Achievement Fetch Task started")

    # Calculate the time until the next midnight
    now = datetime.now()
    midnight = datetime.combine(now + timedelta(days=1), time(0))
    delta_s = (midnight - now).total_seconds()

    # Convert the seconds into hours, minutes, and seconds
    hours, remainder = divmod(delta_s, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Delay the start of the fetch_retro_overview, fetch_system_info and fetch_plextraktsync tasks until the next midnight
    logger.info(f"Waiting for {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds before starting Fetch Retro Overview, Fetch System Info and Fetch PlexTraktSync Tasks.")
    await asyncio.sleep(delta_s)
    fetch_retro_overview.start()
    logger.info("Fetch Retro Overview Task started")
    fetch_system_info.start()
    logger.info("Fetch System Info Task started")
    fetch_plextraktsync.start()
    logger.info("Fetch PlexTraktSync Task started")

# Command to send a message to a specific channel
@bot.command()
async def send(ctx, channel_id: int, *, message: str):
    channel = bot.get_channel(channel_id)
    await channel.send(message)

# Command to purge messages in a channel
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx):
    await ctx.channel.purge()

@tasks.loop(minutes=30)
async def fetch_retroachievements():
    try:
        for username in RETRO_TARGET_USERNAMES:
            # Fetch the completion progress for all games
            completion_cache = fetch_completion(username)
            # Fetch the recent achievements
            achievements = fetch_recent_achievements(completion_cache, username)
            # Convert the achievements to Discord embeds
            embeds = [discord.Embed.from_dict(achievement) for achievement in achievements]
            for embed in embeds:
                # Get the channel where you want to send the message
                if 'Mastered' in embed.author.name:
                    channel = bot.get_channel(CHANNEL_MASTERED)  # Replace with your channel ID for Mastered
                elif 'Achievement Unlocked' in embed.author.name:
                    channel = bot.get_channel(CHANNEL_ACHIEVEMENTS)  # Replace with your channel ID for Unlocks
                else:
                    channel = bot.get_channel(CHANNEL_ACHIEVEMENTS)  # Replace with your default channel ID
                # Send a new message
                await channel.send(embed=embed)
            if len(achievements) > 0:
                logger.info(f'Fetched {len(achievements)} recent achievements for {username}')
                logger.debug(f'Fetched achievements: {achievements}')
    except Exception as e:
        logger.error(f'An error occurred while fetching retroachievements: {e}')

# Task to fetch the RetroAchievements daily overview
@tasks.loop(hours=24)
async def fetch_retro_overview():
    try:
        for username in RETRO_TARGET_USERNAMES:
            logger.info(f"Fetching Retro Daily Overview for {username}")
            embed = create_daily_overview(username)
            if embed is not None:
                channel = bot.get_channel(CHANNEL_RETRO_OVERVIEW)
                logger.info(f"Sending Retro Daily Overview for {username}. Checking again in 24 hours.")
                await channel.send(embed=embed)
            else:
                logger.debug(f"No embed to send for {username}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

# Command to manually send the RetroAchievements daily overview
@bot.command()
async def retrooverview(ctx):
    try:
        for username in RETRO_TARGET_USERNAMES:
            logger.info(f"Fetching Retro Daily Overview for {username}")
            embed = create_daily_overview(username)
            if embed is not None:
                channel = bot.get_channel(CHANNEL_RETRO_OVERVIEW)
                logger.info(f"Sending Retro Daily Overview for {username}. Checking again in 24 hours.")
                await channel.send(embed=embed)
            else:
                logger.debug(f"No embed to send for {username}")
        await ctx.send("Retro Daily Manual Overview sent successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await ctx.send("An error occurred while sending the Retro Daily Manual Overview.")
    
# Define the !trakt command
@bot.command(name='trakt')
async def send_weekly_embeds(ctx):
    try:
        # Weekly Trakt User Plays
        data_user = create_weekly_user_embed()
        channel_user = bot.get_channel(CHANNEL_TRAKT_USER)
        for embed in data_user['embeds']:
            await channel_user.send(embed=discord.Embed.from_dict(embed))
        await ctx.send("Weekly Trakt User Plays sent successfully.")
        # Weekly Trakt Global Plays
        data_global = create_weekly_global_embed()
        channel_global = bot.get_channel(CHANNEL_TRAKT_GLOBAL)
        for embed in data_global['embeds']:
            await channel_global.send(embed=discord.Embed.from_dict(embed))
        await ctx.send("Weekly Trakt Global Plays sent successfully.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@tasks.loop(hours=24)
async def fetch_system_info():
    try:
        # Get the system info embed
        embed = await system_info()
        # Get the channel where you want to send the message
        channel = bot.get_channel(CHANNEL_SYSTEM_INFO)
        # Fetch the history of the channel
        history = []
        async for message in channel.history(limit=100):
            history.append(message)
        # Find the last message sent by the bot with the author "Server Snapshot"
        message_to_edit = next((message for message in reversed(history) if message.author == bot.user and message.embeds and message.embeds[0].author.name == "Server Snapshot"), None)
        if message_to_edit:
            # Edit the message
            await message_to_edit.edit(embed=embed)
        else:
            # Send a new message
            await channel.send(embed=embed)
    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')

@tasks.loop(hours=24)
async def fetch_plextraktsync():
    try:
        # Get the system info embed
        embed = await plextraktsync()
        # Get the channel where you want to send the message
        channel = bot.get_channel(CHANNEL_PLEXTRAKTSYNC)
        # Fetch the history of the channel
        history = []
        async for message in channel.history(limit=100):
            history.append(message)
        # Find the last message sent by the bot with the author "Server Snapshot"
        message_to_edit = next((message for message in reversed(history) if message.author == bot.user and message.embeds and "PlexTraktSync" in message.embeds[0].author.name), None)
        if message_to_edit:
            # Edit the message
            await message_to_edit.edit(embed=embed)
        else:
            # Send a new message
            await channel.send(embed=embed)
    except Exception as e:
        logger.error(f'An error occurred while fetching plextraktsync: {e}')
    
# Discord Rich Presence Tautulli Task Loop 
@tasks.loop(seconds=600)
async def tautulli_discord_activity():
    try:
        await tautulli_discord_presence(bot)
    except Exception as e:
        logger.error(f'An error occurred while calling Tautulli Discord Activity {e}')
        
# Trakt Ratings Task Loop
@tasks.loop(minutes=60)
async def trakt_ratings_task():
    logger.info("Starting Trakt Ratings Task.")
    try:
        data = trakt_ratings()
        if data is not None:
            channel = bot.get_channel(CHANNEL_TRAKT_RATINGS)
            for embed in data['embeds']:
                await channel.send(embed=discord.Embed.from_dict(embed))
        else:
            logger.info("No rating data to send. Trying again in 1 hour.")
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')

# Trakt Favorites Task Loop        
@tasks.loop(hours=24)
async def trakt_favorites_task():
    logger.info("Starting Trakt Favorites Task")
    try:
        data = trakt_favorites()
        channel = bot.get_channel(CHANNEL_TRAKT_RATINGS)
        if data is not None:
            for embed in data['embeds']:
                await channel.send(embed=discord.Embed.from_dict(embed))
        else:
            logger.info("No favorite data to send. Trying again in 24 hours.")
    except Exception as e:
        logger.error(f'Error occurred: {str(e)}')

# Create a queue for the messages
message_queue = asyncio.Queue()

# This dictionary will store the last message ID for each series and season
last_messages = {}

# Webhook setup for Sonarr
async def handle_sonarr(request):
    try:
        data = await request.json()
        logger.debug(f"Sonarr webhook data: {data}")
        event_type = data.get('eventType', 'N/A')
        embed_data = create_sonarr_embed(data)
        channel_id = CHANNEL_SONARR_GRABS
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)

        if event_type in ['Grab', 'EpisodeFileDelete']:
            # Create a key for the series and season
            series_title = data['series'].get('title',)
            season_number = data['episodes'][0].get('seasonNumber')
            key = (series_title, season_number)

            # Check if there's an existing message for this series and season
            if key in last_messages:
                # If there is, edit the message
                message_id = last_messages[key]
                message = await channel.fetch_message(message_id)
                # Get the existing embeds
                embeds = message.embeds
                # Check if the message already has 10 embeds
                if len(embeds) < 10:
                    # If not, add the new embed
                    embeds.append(embed)
                    # Update the message with the new list of embeds
                    await message.edit(embeds=embeds)
                else:
                    # If it does, send a new message and store its ID
                    message = await channel.send(embed=embed)
                    last_messages[key] = message.id
            else:
                # If there isn't, send a new message and store its ID
                message = await channel.send(embed=embed)
                last_messages[key] = message.id
        else:
            # If the event type is not Grab or EpisodeFileDelete, send a new message without storing its ID
            await channel.send(embed=embed)

        logger.info("Sonarr webhook received and processed successfully.")
        logger.debug(f"Sonarr embed data: {embed_data}")
        return web.Response()
    except Exception as e:
        logger.error(f"Error processing Sonarr webhook: {e}")
        return web.Response(status=500)

# Webhook setup for Radarr
async def handle_radarr(request):
    try:
        data = await request.json()
        logger.debug(f"Radarr webhook data: {data}")
        embed_data = create_radarr_embed(data)
        channel_id = CHANNEL_RADARR_GRABS
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)
        await message_queue.put((channel, embed))
        logger.info("Radarr webhook received and processed successfully.")
        logger.debug(f"Radarr embed data: {embed_data}")
        return web.Response()
    except Exception as e:
        logger.error(f"Error processing Radarr webhook: {e}")
        return web.Response(status=500)
    
# Webhook setup for Watchtower
async def handle_watchtower(request):
    try:
        data = await request.json()
        embed_data = create_watchtower_embed(data)
        channel_id = CHANNEL_WATCHTOWER
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)
        await message_queue.put((channel, embed))
        logger.info("Watchtower webhook received and processed successfully.")
        return web.Response()
    except Exception as e:
        logger.error(f"Error processing Watchtower webhook: {e}")
        return web.Response(status=500)

# Webhook setup for Plex/Tautulli
async def handle_plex(request):
    try:
        data = await request.json()
        playing_channel_id = CHANNEL_PLEX_PLAYING
        content_channel_id = CHANNEL_PLEX_CONTENT

        webhook_type = data.get('server_info', {}).get('webhook_type', '')

        if webhook_type == 'nowplaying':
            embed_data, status_code = plex_play(data)
            channel_id = playing_channel_id
        elif webhook_type == 'nowresuming':
            embed_data, status_code = plex_resume(data)
            channel_id = playing_channel_id
        elif webhook_type == 'newcontent_episode':
            embed_data, status_code = plex_episode_content(data)
            channel_id = content_channel_id
        elif webhook_type == 'newcontent_season':
            embed_data, status_code = plex_season_content(data)
            channel_id = content_channel_id
        elif webhook_type == 'newcontent_movie':
            embed_data, status_code = plex_movie_content(data)
            channel_id = content_channel_id    
        else:
            logger.info("Webhook received, but no relevant data found. Data not saved.")
            return {'message': "Webhook received, but no relevant data found. Data not saved."}, 200

        if 'embeds' in embed_data and isinstance(embed_data['embeds'], list):
            for embed_dict in embed_data['embeds']:
                channel = bot.get_channel(channel_id)
                embed = discord.Embed.from_dict(embed_dict)
                await channel.send(embed=embed)
            logger.info("Plex webhook received and processed successfully.")
        else:
            logger.warning("No valid 'embeds' data found.")
        
        return web.Response(status=status_code)
    
    except Exception as e:
        logger.error(f"Error processing Plex webhook: {e}")
        return web.Response(status=500)
    
# Task for sending the messages
async def send_messages():
    while True:
        channel, embed = await message_queue.get()
        await channel.send(embed=embed)
        await asyncio.sleep(1)

app = web.Application()
app.router.add_post('/sonarr', handle_sonarr)
app.router.add_post('/radarr', handle_radarr)
app.router.add_post('/plex', handle_plex)
app.router.add_post('/watchtower', handle_watchtower)

# Start the web server for the webhook
uvicorn_params = {
    "host": "0.0.0.0",
    "port": 1337,
    "access_log": False,
}

uvicorn_app = web.Application()
uvicorn_app.router.add_post("/sonarr", handle_sonarr)
uvicorn_app.router.add_post("/radarr", handle_radarr)
uvicorn_app.router.add_post("/plex", handle_plex)
uvicorn_app.router.add_post("/watchtower", handle_watchtower)
uvicorn_server = web.AppRunner(uvicorn_app)

async def start():
    await uvicorn_server.setup()
    asyncio.create_task(send_messages())
    await web._run_app(uvicorn_app, **uvicorn_params)

async def cleanup():
    await uvicorn_server.cleanup()

async def run_bot():
    await bot.start(TOKEN)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start())
    loop.create_task(run_bot())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(cleanup())