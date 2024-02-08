import subprocess
from discord import Embed, Colour
from discord.utils import utcnow
import getpass
from datetime import datetime, timedelta
import pytz
import shutil

from .globals import DISCORD_THUMBNAIL, SYSTEM_ICON_URL, TIMEZONE

from .custom_logger import logger

import subprocess

def get_generation_info():
    # Get the current date and time
    now = datetime.now(pytz.timezone(TIMEZONE))
    # Calculate the date and time 24 hours from now
    regenerate_time = now + timedelta(hours=24)

    # Convert the regenerate time to a Unix timestamp
    regenerate_timestamp = int(regenerate_time.timestamp())

    return f"This will regenerate on <t:{regenerate_timestamp}:F>"

def run_plextraktsync_sync():
    try:
        # Find the full path of the plextraktsync command
        command = shutil.which('plextraktsync')
        if command is None:
            print('plextraktsync command not found')
            return None

        # Run the command
        output = subprocess.check_output(f'{command} sync', shell=True).decode('utf-8').strip()
        return output
    except Exception as e:
        print(f'An error occurred while running {command} sync: {e}')
        return None

async def plextraktsync():
    try:
        # Run the command and get the output
        sync_output = run_plextraktsync_sync()
        generation_info = get_generation_info()
        
        # Create a Discord embed
        embed = Embed(colour=Colour.red())
        embed.set_author(name="PlexTraktSync Sync", icon_url=SYSTEM_ICON_URL)
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url=DISCORD_THUMBNAIL)

        # Set the output as the description in a code block
        embed.description = f'```{sync_output}```'

        # Add the generation info to the embed
        embed.add_field(name=":loudspeaker: Info", value=generation_info, inline=False)

        logger.info("PlexTraktSync Sync Embed has been created")
        logger.debug(f"PlexTraktSync Sync Embed: {embed.to_dict()}")
        return embed

    except Exception as e:
        logger.error(f'An error occurred while creating PlexTraktSync Sync embed: {e}')