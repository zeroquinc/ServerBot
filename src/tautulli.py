import requests
import discord

from src.globals import TAUTULLI_API_URL, TAUTULLI_API_KEY, TAUTULLI_USER_ID

import src.logging

logger = src.logging.logging.getLogger("tautulli")

# Start of Home Stats User, not finished, only logs now, will fix later.
def home_stats():
    try:
        response = requests.get(
            f'{TAUTULLI_API_URL}/api/v2',
            params={
                'apikey': TAUTULLI_API_KEY,
                'cmd': 'get_history',
                'after': '2023-10-29',
                'media_type': 'movie, episode',
                'user_id': TAUTULLI_USER_ID
            }
        )

        logger.info(f"Tautulli API Response Status Code: {response.status_code}")
        response_content = response.text
        logger.info(f"Tautulli API Response Content: {response_content}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                data = response_data.get('response', {}).get('data', {}).get('data', [])
            except (ValueError, KeyError):
                logger.error("Invalid JSON response or missing data from the API.")
                return

            episodes_watched, movies_watched = 0, 0
            grandparent_titles, movie_titles = {}, {}

            for item in data:
                media_type = item.get('media_type')
                grandparent_title = item.get('grandparent_title')
                title = item.get('title')
                year = item.get('year')

                if media_type == 'episode':
                    episodes_watched += 1
                    grandparent_titles.setdefault(grandparent_title, {'years': set(), 'count': 0})
                    grandparent_titles[grandparent_title]['years'].add(year)
                    grandparent_titles[grandparent_title]['count'] += 1
                elif media_type == 'movie':
                    movies_watched += 1
                    movie_titles.setdefault(title, {'year': None, 'count': 0})
                    if movie_titles[title]['year'] is None:
                        movie_titles[title]['year'] = year
                    movie_titles[title]['count'] += 1

            sorted_grandparent_titles = sorted(
                grandparent_titles.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

            sorted_movie_titles = sorted(
                movie_titles.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

            episodes_label = "episode" if episodes_watched == 1 else "episodes"
            logger.info(f"Episodes - {episodes_watched} {episodes_label} watched")

            for title, info in sorted_grandparent_titles:
                years_str = ', '.join(map(str, info['years']))
                episode_count = info['count']
                episode_label = "episode" if episode_count == 1 else "episodes"
                logger.info(f"{title} ({years_str}) - {episode_count} {episode_label}")

            logger.info(f"Movies - {movies_watched} watched")
            for title, info in sorted_movie_titles:
                year = info['year']
                logger.info(f"{title} ({year})")

        else:
            return

    except Exception as e:
        logger.error(f"An error occurred while fetching home stats for user: {e}")

# Start of Tautulli Discord Task
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
            return data.get('response', {}).get('data', [])
        else:
            logger.error(f"Failed to fetch Tautulli data. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"An error occurred while fetching Tautulli data: {e}")
        return []

async def tautulli_discord_presence(bot):
    global previous_activity
    try:
        tautulli_data = fetch_tautulli_activity()
        if tautulli_data:
            stream_count = int(tautulli_data.get('stream_count', 0))
            if stream_count > 0:
                await update_discord_presence(bot, tautulli_data)
            elif previous_activity != '127.0.0.1':
                await set_discord_presence(bot, '127.0.0.1')
        else:
            if previous_activity != '127.0.0.1':
                await set_discord_presence(bot, '127.0.0.1')
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def update_discord_presence(bot, tautulli_data):
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
        activity_name = f'{title}'
        logger.info(f"Discord presence updated: {activity_name}")
        await set_discord_presence(bot, activity_name)
    else:
        logger.debug("Discord presence is the same as before, not updating.")

async def set_discord_presence(bot, activity_name):
    logger.info(f"No Tautulli activity, setting Discord presence to '{activity_name}'")
    activity = discord.Activity(name=activity_name, type=discord.ActivityType.watching)
    await bot.change_presence(activity=activity)