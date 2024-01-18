import discord
import re
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

    # Initialize the details and counters
    details = ''
    updated_count = 0
    failed_count = 0

    # Process each line
    for i, line in enumerate(lines):
        # Split the line into two parts using ' updated to ' as the delimiter
        parts = line.split(' updated to ')

        # Check if the line contains ' updated to '
        if len(parts) == 2:
            # Split the first part into subparts using a space as the delimiter
            subparts = parts[0].split(' ')
            
            # Extract the container name, image, and old version
            container_name = subparts[1].strip('\/')
            image = re.sub(r'\W+', '', subparts[2])  # Remove all non-alphanumeric characters
            old_version = subparts[3]
            
            # The second part is the new version
            new_version = parts[1]

            # Increment the updated count
            updated_count += 1

            # Add the container info to the description
            details += f"{i+1}: {container_name} {image}\n    From: {old_version} → {new_version}\n"

        else:
            # Check if the line contains 'failed'
            if 'failed' in line:
                # Increment the failed count
                failed_count += 1

    # Check if there were any updates
    if updated_count == 0:
        details = "```No updates found!```"
    else:
        # Wrap the description in a code block
        details = f"```{details}```"

    # Create a new Discord embed
    embed = discord.Embed(
        color=0x00ff00  # Set the color of the embed
    )

    # Set the author name and url
    embed.set_author(name="Watchtower: Update", icon_url=WATCHTOWER_ICON_URL)

    # Add fields for Containers, Updated, and Failed
    embed.add_field(name="Containers", value=str(len(lines)), inline=True)
    embed.add_field(name="Updated", value=str(updated_count), inline=True)
    embed.add_field(name="Failed", value=str(failed_count), inline=True)

    # Set the description (main content) of the embed
    embed.add_field(name="Details", value=details, inline=False)

    timestamp = utcnow()
    embed.timestamp = timestamp
    embed.set_image(url=DISCORD_THUMBNAIL)

    return embed.to_dict()  # Return the embed as a dictionary