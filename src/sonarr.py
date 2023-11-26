import discord
from discord.utils import utcnow
import requests

from src.globals import TMDB_API_KEY

import src.logging

logger = src.logging.logging.getLogger("sonarr")

ICON_URL = "https://i.imgur.com/dZSIKZE.png"
THUMBNAIL_URL = 'https://imgur.com/a/D3MxSNM'

def convert_bytes_to_human_readable(size_in_bytes):
    if size_in_bytes < 1024 ** 3:  # Less than 1 GB
        result = size_in_bytes / (1024 ** 2)
        return "{:.2f}MB".format(result)
    else:  # 1 GB or greater
        result = size_in_bytes / (1024 ** 3)
        return "{:.2f}GB".format(result)

def get_tmdb_poster_path(tvdb_id):
    tmdb_api_key = TMDB_API_KEY
    tmdb_url = f"https://api.themoviedb.org/3/find/{tvdb_id}?api_key={tmdb_api_key}&language=en-US&external_source=tvdb_id"
    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()
        tmdb_data = response.json()
        result = tmdb_data.get("tv_results", [])
        if result:
            poster_path = result[0].get("poster_path")
            return poster_path
        else:
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from TMDB: {str(e)}")
        return None

def create_sonarr_embed(json_data):
    event_type = json_data.get('eventType', 'N/A')
    instance_name = json_data.get('instanceName', 'N/A')
    embed_data = {}

    if event_type == "Test":
        embed_data = create_test_event_embed(instance_name)
    elif event_type == "Grab":
        embed_data = create_grab_event_embed(json_data, instance_name)
    elif event_type == "EpisodeFileDelete":
        embed_data = create_episode_delete_event_embed(json_data, instance_name)
    elif event_type == "ApplicationUpdate":
        embed_data = create_update_event_embed(json_data, instance_name)
    else:
        embed_data = create_unknown_event_embed(event_type)

    return embed_data

def create_test_event_embed(instance_name):
    embed = discord.Embed(
        title="Test Event",
        description="This is a test event from Sonarr, it was a success!",
        color=0x00ff00
    )
    embed.set_author(name=f"{instance_name} - Test", icon_url=ICON_URL)
    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=THUMBNAIL_URL)
    return embed.to_dict()

def create_grab_event_embed(json_data, instance_name):
    series_title = json_data['series'].get('title', 'N/A')
    episode_title = json_data['episodes'][0].get('title', 'N/A')
    episode_number = json_data['episodes'][0].get('episodeNumber', 'N/A')
    season_number = json_data['episodes'][0].get('seasonNumber', 'N/A')
    release_data = json_data.get('release', {})
    release_quality = release_data.get('quality', 'N/A')
    release_size_bytes = release_data.get('size', 'N/A')
    release_size_human_readable = convert_bytes_to_human_readable(release_size_bytes)
    release_title = release_data.get('releaseTitle', 'N/A')
    release_indexer = release_data.get('indexer', 'N/A')
    indexer_value = format_indexer_value(release_indexer)
    custom_format_score = release_data.get('customFormatScore', 'N/A')
    custom_formats = release_data.get('customFormats', [])
    tvdb_id = json_data['series'].get('tvdbId', 'N/A')
    poster_path = get_tmdb_poster_path(tvdb_id)
    formatted_episode_number = f"{episode_number:02d}"
    formatted_season_number = f"{season_number:02d}"
    embed = discord.Embed(
        title=f"{series_title} (S{formatted_season_number}E{formatted_episode_number})",
        color=0x67B7D1
    )
    if poster_path:
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w200{poster_path}")
    embed.set_author(name=f"{instance_name} - Grab", icon_url=ICON_URL)
    embed.add_field(name="Episode", value=episode_title, inline=False)
    embed.add_field(name="Size", value=release_size_human_readable, inline=True)
    embed.add_field(name="Quality", value=release_quality, inline=True)
    embed.add_field(name="Indexer", value=indexer_value, inline=True)
    release_value = format_release_value(release_title)
    embed.add_field(name='Release', value=release_value, inline=False)
    if custom_formats:
        custom_formats_value = format_custom_formats(custom_format_score, custom_formats)
        embed.add_field(name="Custom Formats", value=custom_formats_value, inline=False)
    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=THUMBNAIL_URL)
    return embed.to_dict()

def create_episode_delete_event_embed(json_data, instance_name):
    series_title = json_data['series'].get('title', 'N/A')
    episode_number = json_data['episodes'][0].get('episodeNumber', 'N/A')
    season_number = json_data['episodes'][0].get('seasonNumber', 'N/A')
    episode_data = json_data.get('episodeFile', {})
    episode_path = episode_data.get('path', 'N/A')
    episode_size_bytes = episode_data.get('size', 'N/A')
    episode_size_human_readable = convert_bytes_to_human_readable(episode_size_bytes)
    tvdb_id = json_data['series'].get('tvdbId', 'N/A')
    poster_path = get_tmdb_poster_path(tvdb_id)
    formatted_episode_number = f"{episode_number:02d}"
    formatted_season_number = f"{season_number:02d}"
    embed = discord.Embed(
        title=f"{series_title} (S{formatted_season_number}E{formatted_episode_number})",
        color=0xFF0000
    )
    if poster_path:
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w200{poster_path}")
    embed.set_author(name=f"{instance_name} - Episode Deleted", icon_url=ICON_URL)
    embed.add_field(name="Size", value=episode_size_human_readable, inline=False)
    embed.add_field(name="Path", value=episode_path, inline=False)
    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=THUMBNAIL_URL)
    return embed.to_dict()

def create_update_event_embed(json_data, instance_name):
    old_version = json_data.get('previousVersion', 'N/A')
    new_version = json_data.get('newVersion', 'N/A')
    embed = discord.Embed(
        color=0x00ff00
    )
    embed.set_author(name=f"{instance_name} - ApplicationUpdate", icon_url=ICON_URL)
    embed.add_field(name="Old Version", value=old_version, inline=True)
    embed.add_field(name="New Version", value=new_version, inline=True)
    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=THUMBNAIL_URL)
    return embed.to_dict()

def create_unknown_event_embed(event_type):
    embed = discord.Embed(
        title=f"Unknown Event Type: {event_type}",
        color=0xff0000
    )
    return embed.to_dict()

def format_indexer_value(release_indexer):
    indexer_words = release_indexer.split()
    indexer_value = "\n".join(indexer_words)
    return indexer_value

def format_release_value(release_title):
    release_lines = []
    current_line = ""
    count = 0
    for char in release_title:
        current_line += char
        count += 1
        if count >= 35 and (char == '-' or char == '.'):
            release_lines.append(current_line.rstrip('-').rstrip('.'))
            current_line = ""
            count = 0
    if current_line:
        release_lines.append(current_line)
    release_value = "\n".join(release_lines)
    return release_value

def format_custom_formats(custom_format_score, custom_formats):
    return f"```Score: {custom_format_score}\nFormat: {', '.join(custom_formats)}```"
