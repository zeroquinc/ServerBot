import requests
import discord
from discord.utils import utcnow
from datetime import datetime

from .globals import (
    DISCORD_THUMBNAIL,
    RETRO_USERNAME,
    RETRO_API_KEY,
    RETRO_TARGET_USERNAME,
    RETRO_TIMEFRAME
)

from .custom_logger import logger

def fetch_data():
    url = 'https://retroachievements.org/API/API_GetUserRecentAchievements.php'
    params = {'z': {RETRO_USERNAME}, 'y': {RETRO_API_KEY}, 'u': {RETRO_TARGET_USERNAME}, 'm': {RETRO_TIMEFRAME}}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        logger.debug('Data fetched successfully')
        return response.json()
    else:
        logger.debug(f'Error: {response.status_code}')
        return None

def create_embed(achievement):
    embed = discord.Embed(
        title=achievement['GameTitle'],
        color=discord.Color.blue()
    )
    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.url = f"https://retroachievements.org/achievement/{achievement['AchievementID']}"
    embed.set_author(name="A new Achievement has been earned", icon_url=f"https://media.retroachievements.org{achievement['GameIcon']}")
    embed.add_field(name="Title", value=achievement['Title'], inline=True)
    embed.add_field(name="Points", value=achievement['Points'], inline=True)

    # Hardcore mode is a boolean, so we need to convert it to a string
    hardcore_value = "Yes" if achievement['HardcoreMode'] == 1 else "No"

    embed.add_field(name="Hardcore", value=hardcore_value, inline=True)
    embed.add_field(name="Description", value=achievement['Description'], inline=False)

    # Convert the date to a more friendly format
    date = datetime.strptime(achievement['Date'], '%Y-%m-%d %H:%M:%S')
    friendly_date = date.strftime('%d %B %Y, %H:%M')

    embed.add_field(name="User", value=f"https://retroachievements.org/user/{RETRO_USERNAME}", inline=True)
    embed.add_field(name="Console", value=achievement['ConsoleName'], inline=True)
    embed.add_field(name="Date", value=friendly_date, inline=True)
    embed.set_image(url=DISCORD_THUMBNAIL)
    embed.set_thumbnail(url=f"https://media.retroachievements.org{achievement['BadgeURL']}")

    return embed

def fetch_recent_achievements():
    data = fetch_data()
    if data is not None:
        embeds = [create_embed(achievement) for achievement in data]
        return [embed.to_dict() for embed in embeds]  # Return the embeds as a list of dictionaries