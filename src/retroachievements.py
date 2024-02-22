import requests
import discord
from discord.utils import utcnow
from datetime import datetime
import collections

from .globals import (
    DISCORD_THUMBNAIL,
    RETRO_USERNAME,
    RETRO_API_KEY,
    RETRO_TARGET_USERNAMES,
    RETRO_TIMEFRAME
)

from .custom_logger import logger

def fetch_completion(username):
    url = 'https://retroachievements.org/API/API_GetUserCompletionProgress.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return {game['GameID']: game for game in response.json()['Results']}
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

def fetch_data(username):
    url = 'https://retroachievements.org/API/API_GetUserRecentAchievements.php'
    params = {'z': RETRO_USERNAME, 'y': RETRO_API_KEY, 'u': username, 'm': RETRO_TIMEFRAME}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        logger.debug(f'Data fetched successfully: {response.json()}')
        return response.json()
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

def create_embed(achievement, completion_cache, new_achievements_count):
    embed = discord.Embed(
        title=achievement['GameTitle'],
        color=discord.Color.blue()
    )
    #timestamp = utcnow()
    #embed.timestamp = timestamp
    embed.url = f"https://retroachievements.org/game/{achievement['GameID']}"
    embed.set_author(name="A new Achievement has been earned", icon_url=f"https://media.retroachievements.org{achievement['GameIcon']}")

    # Add the achievement link to the embed
    achievement_link = f"[{achievement['Title']}](https://retroachievements.org/achievement/{achievement['AchievementID']})"
    embed.add_field(name="Achievement", value=achievement_link, inline=True)
    embed.add_field(name="Points", value=achievement['Points'], inline=True)

    # Hardcore mode is a boolean, so we need to convert it to a string
    hardcore_value = "Yes" if achievement['HardcoreMode'] == 1 else "No"

    embed.add_field(name="Hardcore", value=hardcore_value, inline=True)
    embed.add_field(name="Description", value=achievement['Description'], inline=False)

    # Fetch the completion status of the game
    completion = completion_cache.get(achievement['GameID'])
    if completion is not None:
        num_awarded = int(completion['NumAwarded']) - new_achievements_count
        max_possible = int(completion['MaxPossible'])
        percentage = (num_awarded / max_possible) * 100
        embed.add_field(name="Set Completion", value=f"{num_awarded}/{max_possible} ({percentage:.2f}%)", inline=False)

    # Convert the date to a more friendly format
    date = datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S')
    friendly_date = date.strftime('%d/%m/%Y on %H:%M:%S')

    embed.add_field(name="User", value=f"[{RETRO_USERNAME}](https://retroachievements.org/user/{RETRO_USERNAME})", inline=True)
    embed.add_field(name="Console", value=achievement['ConsoleName'], inline=True)

    embed.set_image(url=DISCORD_THUMBNAIL)
    embed.set_thumbnail(url=f"https://media.retroachievements.org{achievement['BadgeURL']}")
    embed.set_footer(text=f"Earned on: {friendly_date}")

    return embed

def fetch_recent_achievements():
    all_embeds = []
    for username in RETRO_TARGET_USERNAMES:
        completion_cache = fetch_completion(username)
        data = fetch_data(username)
        if data is not None:
            new_achievements_count = collections.defaultdict(int)
            embeds = []
            for achievement in data:
                embed = create_embed(achievement, completion_cache, new_achievements_count[achievement['GameID']])
                embeds.append((datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S'), embed))
                new_achievements_count[achievement['GameID']] += 1
            embeds.sort()
            all_embeds.extend([embed.to_dict() for _, embed in embeds])  # Add the embeds to the list of all embeds
    return all_embeds  # Return all embeds as a list of dictionaries