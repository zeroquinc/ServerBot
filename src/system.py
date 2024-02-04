import subprocess
from time import sleep

from .custom_logger import logger

async def system_info():
    try:
        # Get disk space usage
        df = subprocess.check_output(['df', '/']).decode('utf-8').splitlines()[1]
        total_space = int(df.split()[1]) * 1024  # in bytes
        used_space = int(df.split()[2]) * 1024  # in bytes
        free_space = int(df.split()[3]) * 1024  # in bytes

        # Convert bytes to terabytes
        total_space_tb = round(total_space / (1024 ** 4), 2)
        used_space_tb = round(used_space / (1024 ** 4), 2)
        free_space_tb = round(free_space / (1024 ** 4), 2)

        # Format the output
        storage_info = f'Storage\nTotal: {total_space_tb}T → Used: {used_space_tb}T → Free: {free_space_tb}T ↑'

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

        # Log the information
        logger.info(f'Free space: {storage_info}')
        logger.info(f'RAM usage: {ram_usage}%')
        logger.info(f'CPU usage: {cpu_usage}%')
        logger.info(f'CPU temperature: {cpu_temp}°C')

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')