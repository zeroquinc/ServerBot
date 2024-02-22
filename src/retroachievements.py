import requests
import discord
from discord.utils import utcnow
from datetime import datetime
import collections

from .globals import (
    DISCORD_THUMBNAIL,
    RETRO_USERNAME,
    RETRO_API_KEY,
    RETRO_TIMEFRAME,
    RETRO_TARGET_USERNAMES
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
        data = response.json()
        if len(data) > 0:
            logger.debug(f'Response data: {data}')
        return data
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

def create_embed(achievement, completion_cache, new_achievements_count, username):
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

    embed.add_field(name="User", value=f"[{username}](https://retroachievements.org/user/{username})", inline=True)
    embed.add_field(name="Console", value=achievement['ConsoleName'], inline=True)

    embed.set_image(url=DISCORD_THUMBNAIL)
    embed.set_thumbnail(url=f"https://media.retroachievements.org{achievement['BadgeURL']}")

    # Set the footer text and image based on the username
    if username == 'Desiler':
        embed.set_footer(text=f"Earned on: {friendly_date}", icon_url='https://i.imgur.com/mJvWGe1.png')
    elif username == 'Lipperdie':
        embed.set_footer(text=f"Earned on: {friendly_date}", icon_url='https://i.imgur.com/TA9LKKW.png')
    else:
        embed.set_footer(text=f"Earned on: {friendly_date}")

    return embed

def fetch_recent_achievements(completion_cache, processed_achievements, username):
    data = fetch_data(username)
    if data is not None:
        new_achievements_count = collections.defaultdict(int)
        embeds = []
        for achievement in data:
            game_id = achievement['GameID']
            achievement_id = achievement['AchievementID']
            if username not in completion_cache:
                completion_cache[username] = {}
            if game_id not in completion_cache[username]:
                completion_cache[username][game_id] = fetch_completion(username)
            if achievement_id not in processed_achievements:
                new_achievements_count[game_id] += 1
                processed_achievements.add(achievement_id)
            embed = create_embed(achievement, completion_cache[username][game_id], new_achievements_count[game_id], username)
            embeds.append((datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S'), embed))
        embeds.sort()
        return [embed.to_dict() for _, embed in embeds]
    else:
        return None