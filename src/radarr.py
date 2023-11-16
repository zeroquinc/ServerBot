import datetime
import json
import os
import discord
from discord.utils import utcnow
from watchfiles import awatch, Change
import requests

from src.globals import bot, TMDB_API_KEY

from src.logging import logger_radarr

def get_tmdb_poster_path(tmdb_id):
    tmdb_api_key = TMDB_API_KEY
    tmdb_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={tmdb_api_key}&language=en-US"

    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()

        tmdb_data = response.json()

        # Extract the poster path from the response
        poster_path = tmdb_data.get("poster_path")
        return poster_path
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from TMDB: {str(e)}")
        return None

def radarr_directories():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    json_directory = os.path.join(script_directory, '..', 'webhook', 'json')
    radarr_directory = os.path.join(json_directory, 'radarr')
    return script_directory, radarr_directory

def create_discord_embed(json_data):
    
    # Check if the event type is "test" and return a custom message
    event_type = json_data['eventType']
    instance_name = json_data['instanceName']
    
    movie_title = json_data['movie']['title']
    movie_year = json_data['movie']['year']
    release_quality = json_data['release']['quality']
    release_size_bytes = json_data['release']['size']
    release_size_human_readable = convert_bytes_to_human_readable(release_size_bytes)
    release_title = json_data['release']['releaseTitle']
    release_indexer = json_data['release']['indexer']
    # Split the release indexer into a list of words
    indexer_words = release_indexer.split()
    # Join the words with newline characters
    indexer_value = "\n".join(indexer_words)
    custom_format_score = json_data['release']['customFormatScore']
    custom_formats = json_data['release']['customFormats']
    tmdb_id = json_data['movie']['tmdbId']
    
    # Get the poster path from TMDB using the TVDB ID
    poster_path = get_tmdb_poster_path(tmdb_id)

    if event_type == "Grab":
        embed = discord.Embed(
            title=f"{movie_title} ({movie_year})",
            color=0x00ff00
        )
        
        # Set the thumbnail using the poster path from TMDB
        if poster_path:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w200{poster_path}")

        embed.set_author(name=f"{instance_name} - {event_type}", icon_url="https://i.imgur.com/dZSIKZE.png")
        embed.add_field(name="Size", value=release_size_human_readable, inline=True)
        embed.add_field(name="Quality", value=release_quality, inline=True)
        embed.add_field(name="Indexer", value=indexer_value, inline=True)
        
        # Process the "Release" field to split lines after hyphen (-)
        release_lines = []
        current_line = ""
        count = 0
        for char in release_title:
            current_line += char
            count += 1
            if count >= 35 and char == '-':
                release_lines.append(current_line)
                current_line = ""
                count = 0

        # Add the remaining characters after the loop
        if current_line:
            release_lines.append(current_line)

        # Add Release field with multiple lines
        release_value = "\n".join(release_lines)
        embed.add_field(name='Release', value=release_value, inline=False)
        
        # Add Custom Formats field if customFormats is filled in
        if custom_formats:
            embed.add_field(
                name="Custom Formats",
                value=f"```Score: {custom_format_score}\nFormat: {', '.join(custom_formats)}```",
                inline=False
            )

        # Add timestamp
        timestamp = utcnow()
        embed.timestamp = timestamp
        
        # Add whitespace thumbnail to fix width of the Embed
        embed.set_image(url='https://imgur.com/a/D3MxSNM')

    elif event_type == "Download":
        embed = discord.Embed(
            title=f"{movie_title} - Download Started",
            color=0xffa500
        )
        embed.set_author(name=f"{instance_name} - {event_type}", icon_url="https://i.imgur.com/dZSIKZE.png")
    # Add more conditions for other event types as needed

    return embed

def radarr_embed_to_json(data, script_directory, radarr_directory):
    try:
        # Ensure the directories exist, create them if necessary
        os.makedirs(radarr_directory, exist_ok=True)

        # Create Discord embed from JSON data
        discord_embed = create_discord_embed(data)

        # Get the event type from the data
        event_type = data['eventType']
        
        if event_type == "Test":
            return "Test event received successfully", 200

        # Write the Discord embed to a file with the current date and time
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{event_type}_{timestamp}.json"
        file_path = os.path.join(radarr_directory, file_name)

        with open(file_path, 'w') as file:
            json.dump(discord_embed.to_dict(), file, indent=2)

        return "Data dumped successfully", 200
    except Exception as e:
        print(f"Error dumping Discord embed to JSON: {str(e)}")
        return "Internal server error", 500
    
def convert_bytes_to_human_readable(size_in_bytes):
    # Convert bytes to human-readable format
    if size_in_bytes < 1024 ** 3:  # Less than 1 GB
        result = size_in_bytes / (1024 ** 2)
        return "{:.2f}MB".format(result)
    else:  # 1 GB or greater
        result = size_in_bytes / (1024 ** 3)
        return "{:.2f}GB".format(result)
    
async def radarr_webhook():
    logger_radarr.info('Radarr Webhook started and listening for events')
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        script_directory = os.path.dirname(script_directory)
        grab_directory = os.path.join(script_directory, 'webhook', 'json', 'radarr')
        grab_channel_id = 1000190137818431518
        async for changes in awatch(grab_directory):
            for change, path in changes:
                if change == Change.added:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    channel_id = grab_channel_id
                    channel = bot.get_channel(channel_id)
                    if data is not None:
                        embed = discord.Embed.from_dict(data)
                        await channel.send(embed=embed)
                        logger_radarr.info(f'A new Embed has been sent to channel ID: {channel_id}')
                    os.remove(path)
    except Exception as e:
        logger_radarr.error(f'Error occurred: {str(e)}')