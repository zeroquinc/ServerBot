import requests
import discord

from src.globals import TAUTULLI_API_URL, TAUTULLI_API_KEY, TAUTULLI_USER_ID

from src.logging import logger_tautulli

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

        logger_tautulli.info(f"Tautulli API Response Status Code: {response.status_code}")
        response_content = response.text
        logger_tautulli.info(f"Tautulli API Response Content: {response_content}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                data = response_data.get('response', {}).get('data', {}).get('data', [])
            except (ValueError, KeyError):
                logger_tautulli.error("Invalid JSON response or missing data from the API.")
                return

            episodes_watched = 0
            movies_watched = 0
            grandparent_titles = {}
            movie_titles = {}

            for item in data:
                media_type = item.get('media_type')
                grandparent_title = item.get('grandparent_title')
                title = item.get('title')
                year = item.get('year')

                if media_type == 'episode':
                    episodes_watched += 1
                    if grandparent_title:
                        if grandparent_title not in grandparent_titles:
                            grandparent_titles[grandparent_title] = {'years': set(), 'count': 0}
                        grandparent_titles[grandparent_title]['years'].add(year)
                        grandparent_titles[grandparent_title]['count'] += 1
                elif media_type == 'movie':
                    movies_watched += 1
                    if title:
                        if title not in movie_titles:
                            movie_titles[title] = {'year': None, 'count': 0}
                        if movie_titles[title]['year'] is None:
                            movie_titles[title]['year'] = year
                        movie_titles[title]['count'] += 1

            # Sort the grandparent_titles by count in descending order
            sorted_grandparent_titles = sorted(
                grandparent_titles.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

            # Sort the movie_titles by count in descending order
            sorted_movie_titles = sorted(
                movie_titles.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )

            # Modify the log message to handle "episode" or "episodes" based on count
            episodes_label = "episode" if episodes_watched == 1 else "episodes"
            logger_tautulli.info(f"Episodes - {episodes_watched} {episodes_label} watched")

            for title, info in sorted_grandparent_titles:
                years_str = ', '.join(map(str, info['years']))
                episode_count = info['count']
                episode_label = "episode" if episode_count == 1 else "episodes"
                logger_tautulli.info(f"{title} ({years_str}) - {episode_count} {episode_label}")

            logger_tautulli.info(f"Movies - {movies_watched} watched")
            for title, info in sorted_movie_titles:
                year = info['year']
                logger_tautulli.info(f"{title} ({year})")

        else:
            return

    except Exception as e:
        logger_tautulli.error(f"An error occurred while fetching home stats for user: {e}")

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