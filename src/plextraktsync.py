import subprocess
from discord import Embed, Colour
from discord.utils import utcnow
import getpass
from datetime import datetime, timedelta
import pytz
import re

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

        # Extract warnings and remove 'WARNING' from the start
        warnings = [re.sub(r'\s*\(\d{4}\)\s*|<PlexGuid:.*>$', '', line.lstrip('WARNING  ')) for line in lines if line.startswith('WARNING')]

        # Remove 'INFO', 'WARNING' and leading spaces from lines
        lines = [line.replace('INFO     ', '', 1) if line.startswith('INFO     ') else line.replace('WARNING  ', '', 1) if line.startswith('WARNING  ') else line for line in lines]

        # Extract 'Adding to collection' lines and remove 'Adding to collection: ' from the start
        adding_to_collection = [re.sub(r'\s*\(\d{4}\)\s*$', '', line.replace('Adding to collection: ', '').strip()) for line in lines if 'Adding to collection: ' in line]

        # Set the title to the first line and the description to the rest
        title = lines[0].strip()

        # Join the lines back into a single string
        output = '\n'.join(lines)
        
        logger.debug(f'Output: {output}\nSync time: {sync_time}\nWarnings: {warnings}\nAdding to collection: {adding_to_collection}')
        return sync_time, warnings, adding_to_collection, title
    except subprocess.CalledProcessError as e:
        logger.error(f'Command failed with error code {e.returncode}, output: {e.output}')
        return None, None, None, None
    except Exception as e:
        logger.error(f'An error occurred while running {full_command}: {e}')
        return None, None, None, None

async def plextraktsync():
    try:
        # Run the command and get the output
        sync_time, warnings, adding_to_collection, title = run_plextraktsync_sync()
        generation_info = get_generation_info()

        # Create a Discord embed
        embed = Embed(colour=Colour.red())
        embed.set_author(name=title, icon_url=SYSTEM_ICON_URL)
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_image(url=DISCORD_THUMBNAIL)

        # If 'Adding to collection' was not found, set description to "Nothing new added to collection!"
        if not adding_to_collection:
            description = 'Nothing new added to collection in the last 24 hours.'
            embed.description = description
        else:
            # Add 'Adding to collection' as a field in the embed
            adding_to_collection_value = '```' + "\n".join(adding_to_collection) + '```'
            embed.add_field(name=":open_file_folder: Adding to collection", value=adding_to_collection_value, inline=False)

        # Add the warnings to the embed
        if warnings:
            embed.add_field(name=":warning: Warnings", value='```{}```'.format('\n'.join(warnings)), inline=False)

        # Add the generation info to the embed
        embed.add_field(name=":zap: Info", value=generation_info, inline=False)

        # Set the footer to the sync time
        if sync_time is not None:
            embed.set_footer(text=sync_time)

        logger.info("PlexTraktSync Sync Embed has been created")
        logger.debug(f"PlexTraktSync Sync Embed: {embed.to_dict()}")
        return embed

    except Exception as e:
        logger.error(f'An error occurred while creating PlexTraktSync Sync embed: {e}')