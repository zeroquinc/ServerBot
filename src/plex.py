import discord
import os
from watchfiles import awatch, Change
import json
from datetime import datetime

from src.globals import bot

from src.logging import logger_plex

def setup_directories():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    json_directory = os.path.join(script_directory, '..', 'webhook', 'json')
    content_directory = os.path.join(json_directory, 'content')
    playing_directory = os.path.join(json_directory, 'playing')
    return script_directory, content_directory, playing_directory

def handle_webhook_data(data, script_directory, content_directory, playing_directory):
    try:
        if data and 'embeds' in data:
            embeds = data['embeds']
            for i, embed in enumerate(embeds):
                author_name = embed['author']['name']
                if "Resumed Playing" in author_name:
                    filename = os.path.join(playing_directory, f'plex_resuming_{i}.json')
                elif "has finished playing" in author_name:
                    filename = os.path.join(playing_directory, f'plex_finished_{i}.json')
                elif "Now Playing" in author_name:
                    filename = os.path.join(playing_directory, f'plex_started_{i}.json')
                elif "added" in author_name:
                    filename = os.path.join(content_directory, f'plex_new_content_{i}.json')
                else:
                    filename = os.path.join(script_directory, f'event_{i}_{datetime.now().strftime("%Y%m%d%H%M%S")}.json')

                with open(filename, 'w') as f:
                    f.write(json.dumps(embed, indent=4))
                logger_plex.info(f"Event saved as {filename}")
            return "Webhook received and events saved successfully!", 200
        else:
            # If no 'embeds' are found, save the whole data to a JSON file with the current date and time
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(script_directory, f'no_embeds_{current_time}.json')
            with open(filename, 'w') as f:
                f.write(json.dumps(data, indent=4))
            logger_plex.info(f"Webhook data saved as {filename}")
            return "Webhook received, but no events found. Data saved to a file.", 200
    except Exception as e:
        logger_plex.error(f"Error while processing JSON payload: {str(e)}")
        return "Internal server error", 500

async def plex_webhook():
    logger_plex.info('Plex Webhook started and listening for events')
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