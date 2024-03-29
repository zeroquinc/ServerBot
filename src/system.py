import subprocess
from time import sleep
import re
from discord import Embed, Colour
from discord.utils import utcnow
import getpass
from datetime import datetime, timedelta
import pytz

from .globals import DISCORD_THUMBNAIL, SYSTEM_ICON_URL, TIMEZONE

from .custom_logger import logger

# Initialize previous free space and used space to None
previous_free_space = None
previous_used_space = None

def get_hostname():
    try:
        hostname = subprocess.check_output('hostname', shell=True).decode('utf-8').strip()
        return hostname
    except Exception as e:
        logger.error(f'An error occurred while fetching hostname: {e}')
        return None

def get_os_version():
    try:
        os_version = subprocess.check_output('lsb_release -d', shell=True).decode('utf-8').strip().split(":")[1].strip()
        return os_version
    except Exception as e:
        logger.error(f'An error occurred while fetching OS version: {e}')
        return None
    
def get_generation_info():
    # Get the current date and time
    now = datetime.now(pytz.timezone(TIMEZONE))
    # Calculate the date and time 24 hours from now
    regenerate_time = now + timedelta(hours=24)

    # Convert the regenerate time to a Unix timestamp
    regenerate_timestamp = int(regenerate_time.timestamp())

    return f"This will regenerate on <t:{regenerate_timestamp}:F>"
    
def bytes_to_human_readable(bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while bytes >= 1024:
        bytes /= 1024
        i += 1
    return f'{round(bytes, 2)} {units[i]}'

def get_network_usage():
    total_rx = 0
    total_tx = 0
    with open('/proc/net/dev') as f:
        lines = f.readlines()
    for line in lines[2:]:  # skip the first two lines, as they don't contain interface data
        data = line.split()
        rx_bytes = int(data[1])  # received data in bytes
        tx_bytes = int(data[9])  # transmitted data in bytes
        total_rx += rx_bytes
        total_tx += tx_bytes
    total_data = total_rx + total_tx
    return bytes_to_human_readable(total_rx), bytes_to_human_readable(total_tx), bytes_to_human_readable(total_data)

def get_storage_info():
    global previous_free_space
    global previous_used_space
    # Get disk space usage for /dev/ filesystems only
    df_output = subprocess.check_output(['df']).decode('utf-8').splitlines()[1:]
    total_space = 0
    used_space = 0
    free_space = 0
    for line in df_output:
        parts = line.split()
        if parts[0].startswith('/dev/'):
            # Sum bytes (multiply by 1024 because df output is in 1K-blocks)
            total_space += int(parts[1]) * 1024
            used_space += int(parts[2]) * 1024
            free_space += int(parts[3]) * 1024

    # Convert to human readable format
    total_space = bytes_to_human_readable(total_space)
    used_space = bytes_to_human_readable(used_space)
    free_space = bytes_to_human_readable(free_space)

    # Check if free space has increased or decreased
    if previous_free_space is not None:
        if float(free_space.split()[0]) > float(previous_free_space.split()[0]):
            arrow_free = '↑'
        elif float(free_space.split()[0]) < float(previous_free_space.split()[0]):
            arrow_free = '↓'
        else:
            arrow_free = ''

    else:
        arrow_free = ''

    # Check if used space has increased or decreased
    if previous_used_space is not None:
        if float(used_space.split()[0]) > float(previous_used_space.split()[0]):
            arrow_used = '↑'
        elif float(used_space.split()[0]) < float(previous_used_space.split()[0]):
            arrow_used = '↓'
        else:
            arrow_used = ''

    else:
        arrow_used = ''

    # Update previous free space and used space
    previous_free_space = free_space
    previous_used_space = used_space

    return f'{total_space}', f'{used_space} {arrow_used}', f'{free_space} {arrow_free}'

def get_package_updates():
    try:
        output = subprocess.check_output('apt list --upgradable', shell=True).decode('utf-8')
        lines = output.splitlines()
        updates = len(lines) - 1  # Subtract 1 for the header line
        package_names = [line.split('/')[0] for line in lines[1:]]  # Skip the header line
        package_names_str = ', '.join(package_names)
        return f'{updates} updates available\n```{package_names_str}```'
    except Exception as e:
        logger.error(f'An error occurred while checking for package updates: {e}')
        return None

def get_ram_usage():
    free = subprocess.check_output(['free', '-b']).decode('utf-8').splitlines()[1]
    total_ram = int(free.split()[1])
    used_ram = int(free.split()[2])
    ram_usage = round(used_ram / total_ram * 100, 2)  # in percentage
    total_ram_gb = round(total_ram / (1024**3), 2)  # convert bytes to GB
    return ram_usage, f"{total_ram_gb}GB"

def get_cpu_usage():
    with open('/proc/stat') as f:
        stat1 = f.readline()
    sleep(1)
    with open('/proc/stat') as f:
        stat2 = f.readline()
    stat1 = list(map(int, stat1.split()[1:]))
    stat2 = list(map(int, stat2.split()[1:]))
    diff = [b - a for a, b in zip(stat1, stat2)]
    cpu_usage = round(100 * (diff[0] + diff[1]) / sum(diff), 2)  # in percentage

    with open('/proc/cpuinfo') as f:
        lines = f.readlines()
    for line in lines:
        if 'cpu MHz' in line:
            cpu_mhz = float(line.split(':')[1].strip())
            cpu_ghz = round(cpu_mhz / 1000, 2)  # convert MHz to GHz
            break

    return cpu_usage, f"{cpu_ghz}GHz"

def get_cpu_temp():
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        temp = f.read()
    cpu_temp = int(temp) / 1000  # in Celsius
    return cpu_temp

def get_uptime_load_users():
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
            if ":" in time_str:
                hours, minutes = time_str.split(":")
            else:
                hours = '0'
                minutes = time_str.split()[0]
        else:
            days = '0'
            hours, minutes = '0', uptime.strip().split()[0]

        uptime = f"{days}d {hours}h {minutes}m"

    # Extract load
    load_match = re.search('load average: (.*)', uptime_output)
    load = load_match.group(1) if load_match else ''

    # Extract users
    users_match = re.search('(\d+) user', uptime_output)
    users = users_match.group(1) if users_match else ''

    return uptime, load, users

async def system_info():
    try:
        # Get system info
        storage_total, storage_used, storage_free = get_storage_info()
        ram_usage, total_ram = get_ram_usage()
        cpu_usage, cpu_ghz = get_cpu_usage()
        cpu_temp = get_cpu_temp()
        uptime, load, users = get_uptime_load_users()
        rx, tx, total = get_network_usage()
        package_updates = get_package_updates()
        generation_info = get_generation_info()
        
        # Get the current username and hostname
        username = getpass.getuser()
        hostname = get_hostname()
        
        # Create a Discord embed
        embed = Embed(title=f"{username}@{hostname}", colour=Colour.yellow())
        embed.set_author(name="Server Snapshot", icon_url=SYSTEM_ICON_URL)
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_footer(text=get_os_version())
        embed.set_image(url=DISCORD_THUMBNAIL)
        embed.add_field(name=":stopwatch: Uptime", value=uptime, inline=True)
        embed.add_field(name=":scales: Load", value=load, inline=True)
        embed.add_field(name=":busts_in_silhouette: Users", value=users, inline=True)
        embed.add_field(name=":minidisc: Total Space", value=storage_total, inline=True)
        embed.add_field(name=":rocket: Used Space", value=storage_used, inline=True)
        embed.add_field(name=":milky_way: Free Space", value=storage_free, inline=True)
        embed.add_field(name=":fire: CPU Temp", value=f"{cpu_temp}°C", inline=True)
        embed.add_field(name=":desktop: CPU Usage", value=f"{cpu_usage}% [{cpu_ghz}]", inline=True)
        embed.add_field(name=":ram: RAM Usage", value=f"{ram_usage}% [{total_ram}]", inline=True)
        embed.add_field(name=":arrow_down: Network RX", value=rx, inline=True)
        embed.add_field(name=":arrow_up: Network TX", value=tx, inline=True)
        embed.add_field(name=":bar_chart: Total Data", value=total, inline=True)
        embed.add_field(name=":package: Packages", value=package_updates, inline=False)
        embed.add_field(name=":zap: Info", value=generation_info, inline=False)

        logger.info("System Info Embed has been created")
        logger.debug(f"System Info Embed: {embed.to_dict()}")
        return embed

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')