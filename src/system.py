import subprocess
from time import sleep

from .custom_logger import logger

async def system_info():
    try:
        # Get free disk space
        df = subprocess.check_output(['df', '/']).splitlines()[1]
        free_space = df.split()[3]  # in bytes

        # Get RAM usage
        free = subprocess.check_output(['free']).splitlines()[1]
        ram_usage = int(free.split()[2]) / int(free.split()[1]) * 100  # in percentage

        # Get CPU usage
        with open('/proc/stat') as f:
            stat1 = f.readline()
        sleep(1)
        with open('/proc/stat') as f:
            stat2 = f.readline()
        stat1 = list(map(int, stat1.split()[1:]))
        stat2 = list(map(int, stat2.split()[1:]))
        diff = [b - a for a, b in zip(stat1, stat2)]
        cpu_usage = 100 * (diff[0] + diff[1]) / sum(diff)  # in percentage

        # Get CPU temperature
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = f.read()
        cpu_temp = int(temp) / 1000  # in Celsius

        # Log the information
        logger.info(f'Free space: {free_space} bytes')
        logger.info(f'RAM usage: {ram_usage}%')
        logger.info(f'CPU usage: {cpu_usage}%')
        logger.info(f'CPU temperature: {cpu_temp}°C')

    except Exception as e:
        logger.error(f'An error occurred while fetching system info: {e}')