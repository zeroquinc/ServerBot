import requests
import discord

from src.globals import TAUTULLI_API_URL, TAUTULLI_API_KEY

from src.logging import logger_tautulli

# Initialize the previous_activity variable to None
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

        logger_tautulli.debug(f"Tautulli API Response Status Code: {response.status_code}")
        response_content = response.text
        logger_tautulli.debug(f"Tautulli API Response Content: {response_content}")

        if response.status_code == 200:
            data = response.json()
            logger_tautulli.debug("Tautulli JSON data: %s", data)
            return data.get('response', {}).get('data', [])
        else:
            logger_tautulli.error(f"Failed to fetch Tautulli data. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger_tautulli.error(f"An error occurred while fetching Tautulli data: {e}")
        return []

async def tautulli_discord_presence(bot):
    global previous_activity

    try:
        # Fetch data from Tautulli API
        tautulli_data = fetch_tautulli_activity()

        if tautulli_data:
            stream_count = int(tautulli_data.get('stream_count', 0))

            if stream_count > 0:
                sessions = tautulli_data.get('sessions', [])
                if sessions:
                    activity = sessions[0]
                    media_type = activity.get('media_type', 'Unknown Media Type')

                    if media_type == 'movie':
                        title = activity.get('title', 'Unknown Movie Title')
                    elif media_type == 'episode':
                        title = activity.get('grandparent_title', 'Unknown Show Title')
                    else:
                        title = 'Unknown Title'

                    activity_name = f'{title}'  # Set the activity_name before creating discord.Activity

                    # Check if the current activity is different from the previous one
                    if activity_name != previous_activity:
                        logger_tautulli.info(f"Discord presence updated: {activity_name}")
                        activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
                        await bot.change_presence(activity=activity)
                        previous_activity = activity_name
                    else:
                        logger_tautulli.debug("Discord presence is the same as before, not updating.")
            elif previous_activity != '127.0.0.1':  # Check if not already '127.0.0.1'
                # No activity, and stream_count is 0, set the activity_name to "127.0.0.1"
                activity_name = '127.0.0.1'
                logger_tautulli.info("No Tautulli activity, setting Discord presence to '127.0.0.1'")
                activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
                await bot.change_presence(activity=activity)
                previous_activity = activity_name
        else:
            if previous_activity != '127.0.0.1':  # Check if not already '127.0.0.1'
                # No data returned, set the activity_name to "127.0.0.1"
                activity_name = '127.0.0.1'
                logger_tautulli.info("No Tautulli data, setting Discord presence to '127.0.0.1'")
                activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
                await bot.change_presence(activity=activity)
                previous_activity = activity_name
    except Exception as e:
        logger_tautulli.error(f"An error occurred: {e}")