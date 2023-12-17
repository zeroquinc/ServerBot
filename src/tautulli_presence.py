import requests
import discord

from src.globals import TAUTULLI_API_URL, TAUTULLI_API_KEY

import src.logging

logger = src.logging.logging.getLogger("tautulli")

previous_activity = None

def fetch_tautulli_activity():
    try:
        response = requests.get(
            f'{TAUTULLI_API_URL}/api/v2',
            params={
                'apikey': TAUTULLI_API_KEY,
                'cmd': 'get_activity'
            }
        )
        logger.debug(f"Tautulli API Response Status Code: {response.status_code}")
        response_content = response.text
        logger.debug(f"Tautulli API Response Content: {response_content}")
        if response.status_code == 200:
            data = response.json()
            logger.debug("Tautulli JSON data: %s", data)
            return data.get('response', {}).get('data', {})
        else:
            logger.error(f"Failed to fetch Tautulli data. Status code: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"An error occurred while fetching Tautulli data: {e}")
        return {}

async def tautulli_discord_presence(bot):
    global previous_activity
    try:
        tautulli_data = fetch_tautulli_activity()
        if tautulli_data:
            stream_count = int(tautulli_data.get('stream_count', 0))
            sessions = tautulli_data.get('sessions', [])
            current_activity = sessions[0].get('title', '') if sessions else ''
            if stream_count > 0 and current_activity != previous_activity:
                await update_discord_presence(bot, tautulli_data)
                previous_activity = current_activity
            elif stream_count == 0 and previous_activity != '127.0.0.1':
                await set_discord_presence(bot, '127.0.0.1')
                previous_activity = '127.0.0.1'
        else:
            if previous_activity != '127.0.0.1':
                await set_discord_presence(bot, '127.0.0.1')
                previous_activity = '127.0.0.1'
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def update_discord_presence(bot, tautulli_data):
    global previous_activity
    sessions = tautulli_data.get('sessions', [])
    if sessions:
        activity = sessions[0]
        media_type = activity.get('media_type', 'Unknown Media Type')
        if media_type == 'movie':
            title = activity.get('title', 'Unknown Movie Title')
            year = activity.get('year', 'Unknown Year')
            title = f"{title} ({year})"
        elif media_type == 'episode':
            title = activity.get('grandparent_title', 'Unknown Show Title')
        else:
            title = 'Unknown Title'
        activity_name = f'{title}'
        if activity_name != previous_activity:
            logger.info(f"Discord presence updated: {activity_name}")
            await set_discord_presence(bot, activity_name)
            previous_activity = activity_name

async def set_discord_presence(bot, activity_name):
    global previous_activity
    if activity_name != previous_activity:
        logger.info(f"Setting Discord presence to '{activity_name}'")
        activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
        await bot.change_presence(activity=activity)
        previous_activity = activity_name
    else:
        logger.debug(f"Discord presence is the same as before ('{activity_name}'), not updating.")