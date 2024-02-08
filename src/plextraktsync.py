import subprocess
from discord import Embed, Colour
from discord.utils import utcnow
import getpass
from datetime import datetime, timedelta
import pytz

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
        # Run the command
        user = getpass.getuser()
        full_command = f'/home/{user}/.local/bin/plextraktsync sync'
        logger.info(f'Running command: {full_command}')
        output = subprocess.check_output(full_command, shell=True).decode('utf-8').strip()

        # Split the output into lines
        lines = output.split('\n')

        # Find the line with the sync time and remove it from the lines
        sync_time = None
        for i, line in enumerate(lines):
            if 'Completed full sync in' in line:
                sync_time = line.replace('INFO     ', '')
                del lines[i]
                break

        # Remove lines starting with 'INFO', 'Processing', and 'WARNING'
        lines = [line for line in lines if not line.startswith(('INFO', 'Processing', 'WARNING'))]

        # Remove 'Adding to collection:' from lines
        lines = [line.replace('Adding to collection:', '') for line in lines]

        # Join the lines back into a single string
        output = '\n'.join(lines)

        return output, sync_time
    except subprocess.CalledProcessError as e:
        logger.error(f'Command failed with error code {e.returncode}, output: {e.output}')
        return None, None
    except Exception as e:
        logger.error(f'An error occurred while running {full_command}: {e}')
        return None, None

async def plextraktsync():
    try:
        # Run the command and get the output
        sync_output, sync_time = run_plextraktsync_sync()
        generation_info = get_generation_info()

        # Split the output into lines
        lines = sync_output.split('\n')

        # Set the title to the first line and the description to the rest
        title = lines[0]
        description = '\n'.join(lines[1:])

        # If the description is empty, set it to "Nothing new added to collection!"
        if not description.strip():
            description = f'**Nothing new added to collection!**'
        else:
            description = f'**Adding to collection:**\n```{description}```'

        # Create a Discord embed
        embed = Embed(colour=Colour.red())
        embed.set_author(name=title, icon_url=SYSTEM_ICON_URL)
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url=DISCORD_THUMBNAIL)

        # Set the output as the description in a code block
        embed.description = description

        # Add the generation info to the embed
        embed.add_field(name=":loudspeaker: Info", value=generation_info, inline=False)

        # Set the footer to the sync time
        if sync_time is not None:
            embed.set_footer(text=sync_time)

        logger.info("PlexTraktSync Sync Embed has been created")
        logger.debug(f"PlexTraktSync Sync Embed: {embed.to_dict()}")
        return embed

    except Exception as e:
        logger.error(f'An error occurred while creating PlexTraktSync Sync embed: {e}')