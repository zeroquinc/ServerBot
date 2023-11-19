import discord
from discord.utils import utcnow
import requests

from src.globals import TMDB_API_KEY

from src.logging import logger_sonarr

def convert_bytes_to_human_readable(size_in_bytes):
    # Convert bytes to human-readable format
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
        print(f"Error fetching data from TMDB: {str(e)}")
        return None

def create_sonarr_embed(json_data):
    event_type = json_data.get('eventType', 'N/A')
    instance_name = json_data.get('instanceName', 'N/A')
    embed_data = {}

    if event_type == "Test":
        embed = discord.Embed(
            title=f"Test Event",
            description=f"This is a test event from Sonarr, it was a success!",
            color=0x00ff00
        )
        embed.set_author(name=f"{instance_name} - {event_type}", icon_url="https://i.imgur.com/dZSIKZE.png")
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url='https://imgur.com/a/D3MxSNM')
        
        embed_data = embed.to_dict()

    elif event_type == "Grab":
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
        indexer_words = release_indexer.split()
        indexer_value = "\n".join(indexer_words)
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

        embed.set_author(name=f"{instance_name} - {event_type}", icon_url="https://i.imgur.com/dZSIKZE.png")
        embed.add_field(name="Episode", value=episode_title, inline=False)
        embed.add_field(name="Size", value=release_size_human_readable, inline=True)
        embed.add_field(name="Quality", value=release_quality, inline=True)
        embed.add_field(name="Indexer", value=indexer_value, inline=True)

        # Process the "Release" field to split lines after hyphen (-) or period (.)
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
        embed.add_field(name='Release', value=release_value, inline=False)
        
        if custom_formats:
            embed.add_field(
                name="Custom Formats",
                value=f"```Score: {custom_format_score}\nFormat: {', '.join(custom_formats)}```",
                inline=False
            )

        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url='https://imgur.com/a/D3MxSNM')
        
        embed_data = embed.to_dict()

    elif event_type == "Download":
        embed = discord.Embed(
            title=f"{series_title} - Download Started",
            color=0xffa500
        )
        embed.set_author(name=f"{instance_name} - {event_type}", icon_url="https://i.imgur.com/dZSIKZE.png")
        
        embed_data = embed.to_dict()
    else:
        embed = discord.Embed(
            title=f"Unknown Event Type: {event_type}",
            color=0xff0000
        )
        
        embed_data = embed.to_dict()

    return embed_data