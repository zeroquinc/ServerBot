import subprocess
from time import sleep
import re

from .custom_logger import logger

# Initialize previous free space to None
previous_free_space = None

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
        storage_info = f'Total Storage\nTotal: {total_space_tb}T → Used: {used_space_tb}T → Free: {free_space_tb}T {arrow}'
        
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
        uptime = re.search('up (.*),', uptime_output).group(1)
        load = re.search('load average: (.*)', uptime_output).group(1)
        users = re.search(', (.*) user', uptime_output).group(1)

        # Log the information
        logger.info(f'Free space: {storage_info}')
        logger.info(f'RAM usage: {ram_usage}%')
        logger.info(f'CPU usage: {cpu_usage}%')
        logger.info(f'CPU temperature: {cpu_temp}°C')
        logger.info(f'Uptime: {uptime}')
        logger.info(f'Load: {load}')
        logger.info(f'Users: {users}')

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')