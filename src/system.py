import subprocess
from time import sleep
import re
from discord import Embed, Colour
from discord.utils import utcnow
import getpass

from .globals import DISCORD_THUMBNAIL, SYSTEM_ICON_URL

from .custom_logger import logger

# Initialize previous free space to None
previous_free_space = None

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

    return storage_info

def get_package_updates():
    try:
        output = subprocess.check_output('apt list --upgradable', shell=True).decode('utf-8')
        lines = output.splitlines()
        updates = len(lines) - 1  # Subtract 1 for the header line
        package_names = [line.split('/')[0] for line in lines[1:]]  # Skip the header line
        package_names_str = ', '.join(package_names)
        return f'{updates} updates available\n\n{package_names_str}'
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
        storage_info = get_storage_info()
        ram_usage, total_ram = get_ram_usage()
        cpu_usage, cpu_ghz = get_cpu_usage()
        cpu_temp = get_cpu_temp()
        uptime, load, users = get_uptime_load_users()
        rx, tx, total = get_network_usage()
        package_updates = get_package_updates()
        
        # Get the current username and hostname
        username = getpass.getuser()
        hostname = get_hostname()
        
        # Log the information
        logger.debug(f'Free space: {storage_info}')
        logger.debug(f'RAM usage: {ram_usage}%')
        logger.debug(f'CPU usage: {cpu_usage}%')
        logger.debug(f'CPU temperature: {cpu_temp}°C')
        logger.debug(f'Uptime: {uptime}')
        logger.debug(f'Load: {load}')
        logger.debug(f'Users: {users}')
        logger.debug(f'Network RX: {rx}')
        logger.debug(f'Network TX: {tx}')
        logger.debug(f'Total Data: {total}')
        logger.debug(f'Package updates: {package_updates}')
        
        # Create a Discord embed
        embed = Embed(title=f"{username}@{hostname}", colour=Colour.yellow())
        embed.set_author(name="Server Snapshot", icon_url=SYSTEM_ICON_URL)
        timestamp = utcnow()
        embed.timestamp = timestamp
        embed.set_footer(text=get_os_version())
        embed.set_image(url=DISCORD_THUMBNAIL)
        embed.add_field(name="Uptime", value=uptime, inline=True)
        embed.add_field(name="Load", value=load, inline=True)
        embed.add_field(name="Users", value=users, inline=True)
        embed.add_field(name="Storage", value=storage_info, inline=False)
        embed.add_field(name="CPU Temp", value=f"{cpu_temp}°C", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}% [{cpu_ghz}]", inline=True)
        embed.add_field(name="RAM Usage", value=f"{ram_usage}% [{total_ram}]", inline=True)
        embed.add_field(name="Network RX", value=rx, inline=True)
        embed.add_field(name="Network TX", value=tx, inline=True)
        embed.add_field(name="Total Data", value=total, inline=True)
        embed.add_field(name="Packages", value=f"```{package_updates}```", inline=False)

        logger.info("System Info Embed has been created")
        return embed

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')