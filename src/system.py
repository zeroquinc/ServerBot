import subprocess
from time import sleep
import re
from discord import Embed, Colour
import datetime

from .globals import DISCORD_THUMBNAIL, SYSTEM_ICON_URL

from .custom_logger import logger

# Initialize previous free space to None
previous_free_space = None

def get_hostname():
    try:
        hostname = subprocess.check_output('hostname', shell=True).decode('utf-8').strip()
        return hostname
    except Exception as e:
        print(f'An error occurred while fetching hostname: {e}')
        return None
    
def get_os_version():
    try:
        os_version = subprocess.check_output('lsb_release -d', shell=True).decode('utf-8').strip().split(":")[1].strip()
        return os_version
    except Exception as e:
        print(f'An error occurred while fetching OS version: {e}')
        return None

async def system_info():
    try:
        global previous_free_space
        # Get disk space usage for /dev/ filesystems only
        df_output = subprocess.check_output(['df']).decode('utf-8').splitlines()[1:]
        total_space = 0
        used_space = 0
        free_space = 0
        for line in df_output:
            parts = line.split()
            if parts[0].startswith('/dev/'):
                total_space += int(parts[1]) * 1024  # in bytes
                used_space += int(parts[2]) * 1024  # in bytes
                free_space += int(parts[3]) * 1024  # in bytes

        # Convert bytes to terabytes
        total_space_tb = round(total_space / (1024 ** 4), 2)
        used_space_tb = round(used_space / (1024 ** 4), 2)
        free_space_tb = round(free_space / (1024 ** 4), 2)

        # Check if free space has increased or decreased
        if previous_free_space is not None:
            if free_space_tb > previous_free_space:
                arrow = '↑'
            elif free_space_tb < previous_free_space:
                arrow = '↓'
            else:
                arrow = ''
        else:
            arrow = ''

        # Format the output
        storage_info = f'Total: {total_space_tb}T → Used: {used_space_tb}T → Free: {free_space_tb}T {arrow}'
        
        # Update previous free space
        previous_free_space = free_space_tb

        # Get RAM usage
        free = subprocess.check_output(['free']).decode('utf-8').splitlines()[1]
        ram_usage = round(int(free.split()[2]) / int(free.split()[1]) * 100, 2)  # in percentage

        # Get CPU usage
        with open('/proc/stat') as f:
            stat1 = f.readline()
        sleep(1)
        with open('/proc/stat') as f:
            stat2 = f.readline()
        stat1 = list(map(int, stat1.split()[1:]))
        stat2 = list(map(int, stat2.split()[1:]))
        diff = [b - a for a, b in zip(stat1, stat2)]
        cpu_usage = round(100 * (diff[0] + diff[1]) / sum(diff), 2)  # in percentage

        # Get CPU temperature
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = f.read()
        cpu_temp = int(temp) / 1000  # in Celsius
        
        # Get system uptime, load, and users
        uptime_output = subprocess.check_output(['uptime']).decode('utf-8')

        # Extract uptime
        uptime_match = re.search('up (.*),', uptime_output)
        if uptime_match:
            uptime = uptime_match.group(1)
            # Convert uptime to desired format
            if 'day' in uptime:
                parts = uptime.split(", ")
                days = parts[0].split()[0]
                time_str = parts[1].strip() if len(parts) > 1 else '0:0'
            else:
                days = '0'
                time_str = uptime.strip()

            hours, minutes = time_str.split(":")
            uptime = f"{days}d {hours}h {minutes}m"

        # Extract load
        load_match = re.search('load average: (.*)', uptime_output)
        load = load_match.group(1) if load_match else ''

        # Extract users
        users_match = re.search('(\d+) user', uptime_output)
        users = users_match.group(1) if users_match else ''

        # Log the information
        logger.debug(f'Free space: {storage_info}')
        logger.debug(f'RAM usage: {ram_usage}%')
        logger.debug(f'CPU usage: {cpu_usage}%')
        logger.debug(f'CPU temperature: {cpu_temp}°C')
        logger.debug(f'Uptime: {uptime}')
        logger.debug(f'Load: {load}')
        logger.debug(f'Users: {users}')
        
        # Create a Discord embed
        embed = Embed(title=get_hostname(), colour=Colour.yellow())
        embed.set_author(name="Server Snapshot", icon_url=SYSTEM_ICON_URL)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(text=get_os_version())
        embed.set_image(url=DISCORD_THUMBNAIL)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Load", value=load, inline=True)
        embed.add_field(name="Users", value=users, inline=True)
        embed.add_field(name="Storage", value=storage_info, inline=False)
        embed.add_field(name="CPU Temp", value=f"{cpu_temp}°C", inline=True)
        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="RAM", value=f"{ram_usage}%", inline=True)

        return embed

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')