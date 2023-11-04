import discord
import os
from watchfiles import awatch, Change
import json

from src.globals import bot

from src.logging import logger_plex

async def plex_webhook():
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        script_directory = os.path.dirname(script_directory)
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
                        logger_plex.info(f'A new Embed has been sent to channel ID: {channel_id}')
                    os.remove(path)
    except Exception as e:
        logger_plex.error(f'Error occurred: {str(e)}')