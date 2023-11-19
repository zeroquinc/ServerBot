import discord
from discord.ext import tasks
from aiohttp import web
import asyncio

from src.globals import bot, TOKEN
from src.sonarr import create_sonarr_embed
from src.radarr import create_radarr_embed
from src.plex import create_plex_embed
from src.tautulli import tautulli_discord_presence
from src.logging import logger_discord, logger_trakt, logger_plex, logger_sonarr, logger_radarr, logger_tautulli

import src.weekly_trakt_plays_user.main
import src.weekly_trakt_plays_global.main
import src.trakt_ratings_user.ratings
import src.trakt_favorites.favorites

@bot.event
async def on_ready():
    logger_discord.info(f'Logged in as {bot.user.name} ({bot.user.id}) and is ready!')
    
    # Load Tasks
    try:
        trakt_ratings_task.start()
        trakt_favorites_task.start()
        tautulli_discord_activity.start()
        logger_discord.info("Tasks started succesfully.")
    except Exception as e:
        logger_discord.error(f'Error starting tasks: {str(e)}')

# Command to send a message to a specific channel
@bot.command()
async def send(ctx, channel_id: int, *, message: str):
    channel = bot.get_channel(channel_id)
    await channel.send(message)
    
# Discord Rich Presence Tautulli Task Loop 
@tasks.loop(seconds=600)
async def tautulli_discord_activity():
    try:
        await tautulli_discord_presence(bot)
    except Exception as e:
        logger_tautulli.error(f'An error occurred while calling Tautulli Discord Activity {e}')
        
# Trakt Ratings Task Loop
@tasks.loop(hours=24)
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
            logger_trakt.info("No data to send. Trying again in 24 hours.")
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

# Webhook setup for Sonarr
async def handle_sonarr(request):
    try:
        data = await request.json()
        embed_data = create_sonarr_embed(data)
        channel_id = 1006483865117937744
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)
        await channel.send(embed=embed)
        logger_sonarr.info("Sonarr webhook received and processed successfully.")
        return web.Response()
    except Exception as e:
        logger_sonarr.error(f"Error processing Sonarr webhook: {e}")
        return web.Response(status=500)

# Webhook setup for Radarr
async def handle_radarr(request):
    try:
        data = await request.json()
        embed_data = create_radarr_embed(data)
        channel_id = 1000190137818431518
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)
        await channel.send(embed=embed)
        logger_radarr.info("Radarr webhook received and processed successfully.")
        return web.Response()
    except Exception as e:
        logger_radarr.error(f"Error processing Radarr webhook: {e}")
        return web.Response(status=500)

# Webhook setup for Plex/Tautulli
async def handle_plex(request):
    try:
        data = await request.json()
        embed_data = create_plex_embed(data)
        channel_id = 1025825630668984450
        channel = bot.get_channel(channel_id)
        embed = discord.Embed.from_dict(embed_data)
        await channel.send(embed=embed)
        logger_plex.info("Plex webhook received and processed successfully.")
        return web.Response()
    except Exception as e:
        logger_plex.error(f"Plex processing Sonarr webhook: {e}")
        return web.Response(status=500)

app = web.Application()
app.router.add_post('/sonarr', handle_sonarr)
app.router.add_post('/radarr', handle_radarr)
app.router.add_post('/plex', handle_plex)

# Start the web server for the webhook
uvicorn_params = {
    "host": "0.0.0.0",
    "port": 1337,
    "access_log": False,
}

uvicorn_app = web.Application()
uvicorn_app.router.add_post("/sonarr", handle_sonarr)
uvicorn_app.router.add_post("/radarr", handle_radarr)
uvicorn_app.router.add_post("/plex", handle_radarr)
uvicorn_server = web.AppRunner(uvicorn_app)

async def start():
    await uvicorn_server.setup()
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