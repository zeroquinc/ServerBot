import discord
from discord.utils import utcnow

from .globals import (
    WATCHTOWER_ICON_URL,
    DISCORD_THUMBNAIL
)

from .custom_logger import logger

def create_watchtower_embed(data):
    logger.debug("Watchtower API Response: {}", data)
    if data['message'].startswith('Watchtower'):
        return create_checking_watchtower_embed(data)
    elif data['message'][0].isdigit():
        return create_update_watchtower_embed(data)

def create_checking_watchtower_embed(data):
    # Extract the version from the message
    version = data['message'].split('\n')[0]

    # Extract the message starting from "Checking all containers"
    description_index = data['message'].index('Checking all containers')
    description = data['message'][description_index:]

    # Wrap the description in code blocks
    description = f"```{description}```"

    # Create a new Discord embed
    embed = discord.Embed(
        title=version,  # Set the title of the embed to the version
        description=description,  # Set the description (main content) of the embed
        color=0xADD8E6  # Set the color of the embed
    )

    # Set the author name and url
    embed.set_author(name="Watchtower: Checking", icon_url=WATCHTOWER_ICON_URL)

    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=DISCORD_THUMBNAIL)

    return embed.to_dict()  # Return the embed as a dictionary

def create_update_watchtower_embed(data):
    # Split the message into lines
    lines = data['message'].split('\n')

    # Skip the first line and process the rest
    lines = lines[1:]

    # Initialize the description
    description = ''

    # Process each line
    for i, line in enumerate(lines):
        # Split the line into parts
        parts = line.split(' ')
        
        # Extract the container name, image, and versions
        container_name = parts[1].strip('\/')
        image = parts[2].strip('()')
        old_version, new_version = parts[4].split(' updated to ')

        # Add the container info to the description
        description += f"{i+1}: {container_name} {image}\n    From: {old_version} → {new_version}\n"

    # Wrap the description in a code block
    description = f"```{description}```"

    # Create a new Discord embed
    embed = discord.Embed(
        title="Watchtower: Update",  # Set the title of the embed
        description=description,  # Set the description (main content) of the embed
        color=0x00ff00  # Set the color of the embed
    )

    # Set the author name and url
    embed.set_author(name="Watchtower: Update", icon_url=WATCHTOWER_ICON_URL)

    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=DISCORD_THUMBNAIL)

    return embed.to_dict()  # Return the embed as a dictionary