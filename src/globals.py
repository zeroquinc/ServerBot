import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Import Logging
logger = logging.getLogger("ServerBot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Discord.py stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!",intents=intents, activity = discord.Activity(type=discord.ActivityType.watching, name="127.0.0.1"))

# DotEnv
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
path = os.path.join(parent_directory, '.env')
load_dotenv(path)

# Discord Globals
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")
TOKEN = os.environ["DISCORD_TOKEN"]
allowed_roles = "Captain"

# Trakt Globals
TRAKT_USERNAME = os.getenv("TRAKT_USERNAME")
TRAKT_API_URL = f'https://api.trakt.tv/users/{TRAKT_USERNAME}/favorites'
TRAKT_CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
user_link = f'[{TRAKT_USERNAME}](https://trakt.tv/users/{TRAKT_USERNAME})'